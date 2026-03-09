from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any

from app.config import Settings

try:  # pragma: no cover - optional runtime dependency
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - optional runtime dependency
    AsyncOpenAI = None

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        if AsyncOpenAI is None:
            raise RuntimeError("openai SDK 未安装，请执行 pip install openai")

        api_key = (settings.llm.api_key or "").strip()
        if not api_key or api_key == "your_api_key":
            raise RuntimeError("LLM API Key 未配置，请在配置文件中设置 llm.api_key")

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.llm.base_url,
            timeout=180.0,
        )

        logger.info(
            "LLMClient ready | model=%s | light=%s | vision=%s | base_url=%s",
            settings.llm.model_name,
            settings.llm.light_model_name or settings.llm.model_name,
            settings.llm.vision_model_name,
            settings.llm.base_url,
        )

    async def generate_with_vision(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.6,
    ) -> str:
        b64 = base64.b64encode(image_bytes).decode()
        data_uri = f"data:{mime_type};base64,{b64}"
        model = self.settings.llm.vision_model_name
        resp = await self._client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": data_uri}},
                    {"type": "text", "text": user_prompt},
                ]},
            ],
        )
        content = resp.choices[0].message.content if resp.choices else None
        if not content:
            raise RuntimeError(f"LLM vision 返回空内容（model={model}）")
        return str(content).strip()

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        light: bool = False,
        temperature: float = 0.6,
    ) -> str:
        chosen_model = model or (self.settings.llm_light_model_name if light else self.settings.llm_model_name)
        resp = await self._client.chat.completions.create(
            model=chosen_model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = resp.choices[0].message.content if resp.choices else None
        if not content:
            raise RuntimeError(f"LLM 返回空内容（model={chosen_model}）")
        return str(content).strip()

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        light: bool = False,
        temperature: float = 0.4,
    ) -> dict[str, Any] | list[Any]:
        raw = await self.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            light=light,
            temperature=temperature,
        )
        result = self._parse_json(raw)
        if result is None:
            raise RuntimeError(f"LLM 返回内容无法解析为 JSON：{raw[:200]}")
        return result

    def _parse_json(self, raw: str) -> dict[str, Any] | list[Any] | None:
        text = raw.strip()
        # 去除 Qwen3 等思考模型的推理块
        text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()

        for candidate in self._candidate_json_strings(text):
            try:
                payload = json.loads(candidate)
                if isinstance(payload, (dict, list)):
                    return payload
            except json.JSONDecodeError:
                continue
        return None

    def _candidate_json_strings(self, text: str) -> list[str]:
        candidates: list[str] = [text]

        left_obj, right_obj = text.find("{"), text.rfind("}")
        if left_obj != -1 and right_obj > left_obj:
            candidates.append(text[left_obj : right_obj + 1])

        left_arr, right_arr = text.find("["), text.rfind("]")
        if left_arr != -1 and right_arr > left_arr:
            candidates.append(text[left_arr : right_arr + 1])

        uniq: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                uniq.append(candidate)
        return uniq
