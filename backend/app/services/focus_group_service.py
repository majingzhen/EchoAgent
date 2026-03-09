from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from app.llm.client import LLMClient
from app.models.persona import (
    FocusGroupAskRequest,
    FocusGroupCreateRequest,
    FocusGroupMessage,
    FocusGroupSession,
    PersonaProfile,
)
from app.repositories.focus_group_repository import FocusGroupRepository
from app.repositories.persona_memory_repository import PersonaMemoryRepository
from app.services.task_service import TaskService
from app.ws.manager import WSConnectionManager

logger = logging.getLogger(__name__)

_REPLY_CONCURRENCY = 5


class FocusGroupService:
    def __init__(
        self,
        repository: FocusGroupRepository,
        llm_client: LLMClient,
        ws_manager: WSConnectionManager,
        task_service: TaskService,
        persona_memory_repository: PersonaMemoryRepository | None = None,
    ) -> None:
        self.repository = repository
        self.llm_client = llm_client
        self.ws_manager = ws_manager
        self.task_service = task_service
        self.persona_memory_repository = persona_memory_repository

    async def create_session(self, request: FocusGroupCreateRequest) -> FocusGroupSession:
        return await self.repository.create_session(
            tenant_id=1,
            persona_group_id=request.persona_group_id,
            topic=request.topic,
            product_context=request.product_context.model_dump(),
        )

    async def ask_async(
        self,
        session_id: int,
        tenant_id: int,
        request: FocusGroupAskRequest,
        personas: list[PersonaProfile],
        product_context: dict,
        mode: str = "independent",
        image_bytes: bytes | None = None,
        mime_type: str = "image/jpeg",
    ) -> str:
        """立即返回 task_id，后台执行画像回复并逐条推送 WS。
        mode: independent（并行独立作答）| discussion（三段式讨论）
        """
        task = await self.task_service.create_task(tenant_id, "focus_group_ask", session_id)
        if mode == "discussion":
            asyncio.create_task(self._run_discussion(session_id, request, personas, task.id, product_context))
        else:
            asyncio.create_task(self._run_ask(session_id, request, personas, task.id, product_context, image_bytes, mime_type))
        return task.id

    async def _run_ask(
        self,
        session_id: int,
        request: FocusGroupAskRequest,
        personas: list[PersonaProfile],
        task_id: str,
        product_context: dict,
        image_bytes: bytes | None = None,
        mime_type: str = "image/jpeg",
    ) -> None:
        channel = f"focus-group:{session_id}"
        try:
            user_message = FocusGroupMessage(sender_type="user", content=request.question)
            await self.repository.append_messages(session_id, [user_message])
            await self.ws_manager.broadcast(channel, {
                "type": "user_message",
                "content": request.question,
            })

            # 加载画像历史记忆（失败不阻塞主流程）
            memories_map: dict[int, str] = {}
            if self.persona_memory_repository:
                try:
                    persona_ids = [p.id for p in personas]
                    memories_map = await self.persona_memory_repository.list_memories_batch(persona_ids)
                except Exception:
                    logger.warning("load persona memories failed, skip", exc_info=True)

            semaphore = asyncio.Semaphore(_REPLY_CONCURRENCY)
            total = len(personas)

            async def reply_one(idx: int, persona: PersonaProfile) -> None:
                try:
                    async with semaphore:
                        text = await self._build_persona_reply(
                            persona, request.question, product_context,
                            memory=memories_map.get(persona.id),
                            image_bytes=image_bytes,
                            mime_type=mime_type,
                        )
                except Exception:
                    logger.warning("persona %s reply failed, skip", persona.name, exc_info=True)
                    return
                msg = FocusGroupMessage(
                    sender_type="persona",
                    persona_id=persona.id,
                    persona_name=persona.name,
                    content=text,
                )
                # 每条回复完成后立即入库，不等全部完成再批量写
                try:
                    await self.repository.append_messages(session_id, [msg])
                except Exception:
                    logger.warning("save message failed for persona %s", persona.name, exc_info=True)
                await self.ws_manager.broadcast(channel, {
                    "type": "persona_reply",
                    "index": idx,
                    "total": total,
                    "persona_id": persona.id,
                    "persona_name": persona.name,
                    "content": text,
                })

            await asyncio.gather(*[reply_one(i, p) for i, p in enumerate(personas)])
            await self.ws_manager.broadcast(channel, {"type": "done", "total": total})
            await self.task_service.update_task(task_id, status="completed", progress=100)

        except Exception as exc:
            logger.exception("focus group ask failed: session_id=%d", session_id)
            await self.ws_manager.broadcast(channel, {"type": "error", "message": str(exc)})
            await self.task_service.update_task(task_id, status="failed", error=str(exc))

    async def _run_discussion(
        self,
        session_id: int,
        request: FocusGroupAskRequest,
        personas: list[PersonaProfile],
        task_id: str,
        product_context: dict,
    ) -> None:
        """三段式讨论模式：独立作答 → 主持人梳理分歧 → 两方交叉回应。"""
        channel = f"focus-group:{session_id}"
        try:
            # 保存用户提问
            user_message = FocusGroupMessage(sender_type="user", content=request.question)
            await self.repository.append_messages(session_id, [user_message])
            await self.ws_manager.broadcast(channel, {"type": "user_message", "content": request.question})

            # 加载画像历史记忆
            memories_map: dict[int, str] = {}
            if self.persona_memory_repository:
                try:
                    memories_map = await self.persona_memory_repository.list_memories_batch([p.id for p in personas])
                except Exception:
                    logger.warning("load persona memories failed", exc_info=True)

            # ── Phase 1: 所有画像独立作答 ────────────────────────────────
            await self.ws_manager.broadcast(channel, {
                "type": "phase_start", "phase": 1, "label": "独立作答",
            })
            semaphore = asyncio.Semaphore(_REPLY_CONCURRENCY)
            total = len(personas)
            answers: dict[int, str] = {}  # persona_id → answer text

            async def reply_one(idx: int, persona: PersonaProfile) -> None:
                async with semaphore:
                    try:
                        text = await self._build_persona_reply(
                            persona, request.question, product_context,
                            memory=memories_map.get(persona.id),
                        )
                    except Exception:
                        logger.warning("persona %s reply failed", persona.name, exc_info=True)
                        return
                answers[persona.id] = text
                msg = FocusGroupMessage(
                    sender_type="persona", persona_id=persona.id,
                    persona_name=persona.name, content=text,
                )
                try:
                    await self.repository.append_messages(session_id, [msg])
                except Exception:
                    logger.warning("save message failed for persona %s", persona.name)
                await self.ws_manager.broadcast(channel, {
                    "type": "persona_reply", "phase": 1,
                    "index": idx, "total": total,
                    "persona_id": persona.id, "persona_name": persona.name, "content": text,
                })

            await asyncio.gather(*[reply_one(i, p) for i, p in enumerate(personas)])

            if not answers:
                await self.ws_manager.broadcast(channel, {"type": "done", "total": 0})
                await self.task_service.update_task(task_id, status="completed", progress=100)
                return

            # ── Phase 2: 主持人梳理核心分歧 ──────────────────────────────
            await self.ws_manager.broadcast(channel, {
                "type": "phase_start", "phase": 2, "label": "主持人梳理",
            })
            divergence = await self._extract_divergence(request.question, personas, answers)
            facilitator_msg = FocusGroupMessage(
                sender_type="facilitator", persona_name="主持人",
                content=divergence["summary"],
            )
            await self.repository.append_messages(session_id, [facilitator_msg])
            await self.ws_manager.broadcast(channel, {
                "type": "facilitator",
                "content": divergence["summary"],
                "point": divergence["point"],
                "side_a_ids": divergence["side_a_ids"],
                "side_b_ids": divergence["side_b_ids"],
            })

            # ── Phase 3: 两方代表交叉回应 ────────────────────────────────
            await self.ws_manager.broadcast(channel, {
                "type": "phase_start", "phase": 3, "label": "交叉讨论",
            })
            side_a = [p for p in personas if p.id in divergence["side_a_ids"]][:1]
            side_b = [p for p in personas if p.id in divergence["side_b_ids"]][:1]

            debate_pairs = []
            if side_a and side_b:
                debate_pairs = [(side_a[0], side_b[0]), (side_b[0], side_a[0])]

            for speaker, opponent in debate_pairs:
                opponent_view = answers.get(opponent.id, "")
                debate_reply = await self._build_debate_reply(
                    speaker, request.question, divergence["point"],
                    opponent_name=opponent.name, opponent_view=opponent_view,
                    product_context=product_context,
                )
                msg = FocusGroupMessage(
                    sender_type="persona", persona_id=speaker.id,
                    persona_name=speaker.name, content=debate_reply,
                )
                await self.repository.append_messages(session_id, [msg])
                await self.ws_manager.broadcast(channel, {
                    "type": "debate_reply", "phase": 3,
                    "persona_id": speaker.id, "persona_name": speaker.name,
                    "responding_to": opponent.name, "content": debate_reply,
                })

            await self.ws_manager.broadcast(channel, {"type": "done", "total": total})
            await self.task_service.update_task(task_id, status="completed", progress=100)

        except Exception as exc:
            logger.exception("discussion ask failed: session_id=%d", session_id)
            await self.ws_manager.broadcast(channel, {"type": "error", "message": str(exc)})
            await self.task_service.update_task(task_id, status="failed", error=str(exc))

    async def _extract_divergence(
        self,
        question: str,
        personas: list[PersonaProfile],
        answers: dict[int, str],
    ) -> dict:
        """让 LLM 从所有回答中提取核心分歧，返回两方代表 ID 和主持人总结。"""
        lines = []
        for p in personas:
            ans = answers.get(p.id, "")
            if ans:
                lines.append(f"- {p.name}（{p.occupation}）：{ans}")
        transcript = "\n".join(lines)

        system_prompt = (
            "你是焦点小组主持人。请从回答中找出最核心的一个分歧点，"
            "并各选一位代表正反方的发言人。只输出 JSON，不要解释。"
        )
        user_prompt = (
            f"问题：{question}\n\n各画像回答：\n{transcript}\n\n"
            "输出 JSON：\n"
            '{"point":"核心分歧一句话","summary":"主持人向全组的梳理语（2-3句）",'
            '"side_a_names":["姓名"],"side_b_names":["姓名"]}'
        )
        try:
            result = await self.llm_client.generate_json(
                system_prompt=system_prompt, user_prompt=user_prompt,
                light=True, temperature=0.3,
            )
            name_to_id = {p.name: p.id for p in personas}
            side_a_ids = [name_to_id[n] for n in (result.get("side_a_names") or []) if n in name_to_id]
            side_b_ids = [name_to_id[n] for n in (result.get("side_b_names") or []) if n in name_to_id]
            # 兜底：若 LLM 没找到两方，取前两个画像
            if not side_a_ids and personas:
                side_a_ids = [personas[0].id]
            if not side_b_ids and len(personas) > 1:
                side_b_ids = [personas[1].id]
            return {
                "point": result.get("point", "观点存在分歧"),
                "summary": result.get("summary", "各画像对此问题存在不同看法。"),
                "side_a_ids": side_a_ids,
                "side_b_ids": side_b_ids,
            }
        except Exception:
            logger.warning("extract divergence failed, using fallback", exc_info=True)
            return {
                "point": "观点存在分歧",
                "summary": "各画像对此问题存在不同看法，主持人邀请代表进一步交流。",
                "side_a_ids": [personas[0].id] if personas else [],
                "side_b_ids": [personas[1].id] if len(personas) > 1 else [],
            }

    async def _build_debate_reply(
        self,
        persona: PersonaProfile,
        question: str,
        divergence_point: str,
        opponent_name: str,
        opponent_view: str,
        product_context: dict,
    ) -> str:
        """让画像针对分歧点回应对方观点。"""
        pc = product_context or {}
        product_section = ""
        raw_text = (pc.get("raw_text") or "").strip()
        if raw_text:
            product_section = f"\n背景资料：\n{raw_text[:4000]}\n"

        system_prompt = (
            "你正在扮演一个虚拟消费者参与焦点小组讨论。"
            "请针对分歧点回应对方观点，保持人设立场，语气自然口语化。"
            "只输出 JSON：{\"answer\":\"回应内容\"}，禁止输出其他内容。"
        )
        user_prompt = (
            f"【你的身份】{persona.name}，{persona.age}岁，{persona.occupation}，{persona.city}\n"
            f"价格敏感度：{persona.consumer_profile.price_sensitivity}，"
            f"关注点：{','.join(persona.consumer_profile.decision_factors)}\n"
            f"{product_section}"
            f"【原问题】{question}\n"
            f"【分歧焦点】{divergence_point}\n"
            f"【{opponent_name} 的观点】{opponent_view}\n"
            f"【要求】以你的立场，用第一人称口语化地回应 {opponent_name} 的观点（50-120字）。"
            '输出 JSON：{"answer":"你的回应"}'
        )
        raw = await self.llm_client.generate_text(
            system_prompt=system_prompt, user_prompt=user_prompt,
            light=True, temperature=0.7,
        )
        return self._extract_answer(raw)

    async def summarize_async(self, session_id: int, tenant_id: int) -> str | None:
        """立即返回 task_id，后台生成总结并通过 WS 推送结果。"""
        session = await self.get_session(session_id)
        if not session:
            return None
        task = await self.task_service.create_task(tenant_id, "focus_group_summarize", session_id)
        asyncio.create_task(self._run_summarize(session_id, task.id))
        return task.id

    async def _run_summarize(self, session_id: int, task_id: str) -> None:
        channel = f"focus-group:{session_id}"
        try:
            await self.ws_manager.broadcast(channel, {"type": "summary_start"})
            session = await self.get_session(session_id)
            if not session:
                raise RuntimeError("session not found")

            persona_messages = [m for m in session.messages if m.sender_type == "persona"]
            if not persona_messages:
                result = {
                    "consensus": ["当前暂无画像回答"],
                    "divergence": [],
                    "key_insights": [],
                    "recommendations": [],
                }
            else:
                result = await self._summarize_with_llm(persona_messages)
                await self.repository.update_summary(session_id, result)
                if self.persona_memory_repository:
                    try:
                        await self._save_persona_memories(session_id, persona_messages)
                    except Exception:
                        logger.warning("save persona memories failed", exc_info=True)

            await self.ws_manager.broadcast(channel, {"type": "summary_done", "data": result})
            await self.task_service.update_task(task_id, status="completed", progress=100)
        except Exception as exc:
            logger.exception("summarize failed: session_id=%d", session_id)
            await self.ws_manager.broadcast(channel, {"type": "error", "message": str(exc)})
            await self.task_service.update_task(task_id, status="failed", error=str(exc))

    async def summarize(self, session_id: int) -> dict[str, list[str]] | None:
        session = await self.get_session(session_id)
        if not session:
            return None

        persona_messages = [m for m in session.messages if m.sender_type == "persona"]
        if not persona_messages:
            return {
                "consensus": ["当前暂无画像回答"],
                "divergence": [],
                "key_insights": [],
                "recommendations": [],
            }

        summary = await self._summarize_with_llm(persona_messages)
        session.summary = summary
        session.updated_at = datetime.utcnow()
        await self.repository.update_summary(session.id, summary)

        # 写入画像记忆（失败不影响总结结果）
        if self.persona_memory_repository:
            try:
                await self._save_persona_memories(session_id, persona_messages)
            except Exception:
                logger.warning("save persona memories failed", exc_info=True)

        return summary

    async def get_session(self, session_id: int) -> FocusGroupSession | None:
        return await self.repository.get_session(session_id)

    async def list_sessions(self, tenant_id: int) -> list[dict]:
        return await self.repository.list_sessions(tenant_id)

    async def _build_persona_reply(
        self, persona: PersonaProfile, question: str, product_context: dict,
        memory: str | None = None,
        image_bytes: bytes | None = None,
        mime_type: str = "image/jpeg",
    ) -> str:
        pc = product_context or {}
        product_section = ""
        raw_text = (pc.get("raw_text") or "").strip()
        if raw_text:
            product_section = f"\n背景资料（作答时请结合以下内容）：\n{raw_text[:8000]}\n"
        memory_section = ""
        if memory:
            memory_section = f"\n历史记忆：{memory}\n"

        system_prompt = (
            "你正在扮演一个虚拟消费者，必须严格保持人设用中文回答。"
            "只能输出一个 JSON 对象，格式为 {\"answer\":\"回答内容\"}，禁止输出任何其他内容。"
        )
        user_prompt = (
            f"【画像信息】\n"
            f"姓名：{persona.name}，年龄：{persona.age}，职业：{persona.occupation}，城市：{persona.city}\n"
            f"价格敏感度：{persona.consumer_profile.price_sensitivity}，"
            f"品牌忠诚度：{persona.consumer_profile.brand_loyalty}\n"
            f"关注点：{','.join(persona.consumer_profile.decision_factors)}\n"
            f"广告态度：{persona.social_behavior.stance_on_ads}\n"
            f"{product_section}"
            f"{memory_section}"
            f"【问题】{question}\n"
            f"【要求】以该画像身份用第一人称回答，只输出 JSON，格式：{{\"answer\":\"你的回答\"}}"
        )

        if image_bytes:
            vision_prompt = (
                user_prompt + "\n【附件】请同时评价上面这张图片，将对图片的看法融入回答中。"
            )
            raw = await self.llm_client.generate_with_vision(
                image_bytes=image_bytes,
                mime_type=mime_type,
                system_prompt=system_prompt,
                user_prompt=vision_prompt,
                temperature=0.6,
            )
        else:
            raw = await self.llm_client.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                light=True,
                temperature=0.6,
            )

        return self._extract_answer(raw)

    def _extract_answer(self, raw: str) -> str:
        """从 LLM 原始输出中提取回答文本，兼容 JSON 和纯文本两种格式。"""
        parsed = self.llm_client._parse_json(raw)
        if isinstance(parsed, dict):
            answer = str(parsed.get("answer") or "").strip()
            if answer:
                return answer[:280]

        # 非 JSON：去掉思考标签后取有效行
        import re
        text = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("{") and not line.startswith("["):
                return line[:280]
        return text[:280]

    async def _summarize_with_llm(self, persona_messages: list[FocusGroupMessage]) -> dict[str, list[str]]:
        transcript = "\n".join([f"- {m.persona_name}: {m.content}" for m in persona_messages[:30]])
        system_prompt = "你是营销洞察分析师。请汇总焦点小组观点并输出结构化 JSON。"
        user_prompt = (
            "以下是画像用户回答，请归纳：\n"
            f"{transcript}\n"
            "输出 JSON：{\"consensus\":[...],\"divergence\":[...],\"key_insights\":[...],\"recommendations\":[...]}"
        )
        payload = await self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            light=True,
            temperature=0.3,
        )
        if not isinstance(payload, dict):
            raise RuntimeError("LLM 返回总结结构不符合预期")

        return {
            "consensus": self._to_list(payload.get("consensus"), []),
            "divergence": self._to_list(payload.get("divergence"), []),
            "key_insights": self._to_list(payload.get("key_insights"), []),
            "recommendations": self._to_list(payload.get("recommendations"), []),
        }

    async def _save_persona_memories(
        self, session_id: int, persona_messages: list[FocusGroupMessage],
    ) -> None:
        # 按 persona 分组发言
        grouped: dict[int, list[str]] = {}
        names: dict[int, str] = {}
        for m in persona_messages:
            if m.persona_id is None:
                continue
            if m.persona_id not in grouped:
                grouped[m.persona_id] = []
            grouped[m.persona_id].append(m.content)
            names[m.persona_id] = m.persona_name or ""

        semaphore = asyncio.Semaphore(_REPLY_CONCURRENCY)

        async def extract_one(pid: int, contents: list[str]) -> None:
            async with semaphore:
                name = names.get(pid, "")
                content = "; ".join(contents[:5])
                system_prompt = "请用一句话概括该消费者在本次焦点小组中的核心态度。只输出 JSON。"
                user_prompt = (
                    f"画像：{name}\n"
                    f"发言记录：{content}\n"
                    '输出：{"memory":"一句话摘要"}'
                )
                try:
                    result = await self.llm_client.generate_json(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        light=True,
                        temperature=0.3,
                    )
                    memory = result.get("memory", "") if isinstance(result, dict) else ""
                    if memory:
                        await self.persona_memory_repository.save_memory(
                            pid, "focus_group", session_id, memory[:200],
                        )
                except Exception:
                    logger.warning("save memory failed for persona %d", pid)

        tasks = [extract_one(pid, contents) for pid, contents in grouped.items()]
        await asyncio.gather(*tasks)

    def _to_list(self, value: object, default: list[str]) -> list[str]:
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            if cleaned:
                return cleaned[:8]
        return default
