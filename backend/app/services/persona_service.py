from __future__ import annotations

import asyncio
from typing import Any

from app.llm.client import LLMClient
from app.models.persona import (
    PersonaAgentConfig,
    PersonaConsumerProfile,
    PersonaGenerateRequest,
    PersonaGroupDetail,
    PersonaGroupSummary,
    PersonaMediaBehavior,
    PersonaPersonality,
    PersonaProfile,
    PersonaSocialBehavior,
)
from app.repositories.persona_repository import PersonaRepository
from app.services.task_service import TaskService
from app.ws.manager import WSConnectionManager

# 并发限制：最多同时发 5 个 LLM 请求，避免触发限流
_PERSONA_CONCURRENCY = 5

# 差异化方向，循环分配给每个画像，引导 LLM 生成不同类型的人
_VARIETY_HINTS = [
    "价格敏感型，注重性价比，消费前会大量比价",
    "品质导向型，愿意为品牌和成分溢价，追求可靠感",
    "尝鲜探索型，喜欢尝试新品，受社交媒体影响大",
    "务实复购型，认准好用的就反复购买，不爱折腾",
    "社交驱动型，因朋友推荐或热搜种草，重视晒单",
]

_SINGLE_PERSONA_SCHEMA = (
    '{"name":"","age":30,"gender":"男/女","city":"","occupation":"",'
    '"monthly_income":12000,'
    '"personality":{"mbti":"","communication_style":"","description":""},'
    '"consumer_profile":{"price_sensitivity":0.5,"brand_loyalty":0.5,'
    '"decision_factors":[""],"purchase_frequency":"计划型","monthly_disposable":3000},'
    '"media_behavior":{"platforms":["小红书","抖音"],"content_preference":["测评"],'
    '"influence_susceptibility":0.5,"influence_power":0.5},'
    '"social_behavior":{"post_frequency":"低频","interaction_style":"评论派","stance_on_ads":"中立"},'
    '"agent_config":{"activity_level":0.5,"sentiment_bias":0.0,"critical_thinking":0.5,"herd_mentality":0.5},'
    '"backstory":""}'
)


class PersonaService:
    def __init__(
        self,
        repository: PersonaRepository,
        llm_client: LLMClient,
        ws_manager: WSConnectionManager,
        task_service: TaskService,
    ) -> None:
        self.repository = repository
        self.llm_client = llm_client
        self.ws_manager = ws_manager
        self.task_service = task_service

    async def generate_group_async(self, request: PersonaGenerateRequest) -> tuple[str, int]:
        group_summary = await self.repository.create_group(
            tenant_id=1,
            name=request.group_name,
            description=request.description,
            source="description",
            persona_count=request.count,
        )
        task = await self.task_service.create_task(1, "persona_generate", group_summary.id)
        asyncio.create_task(self._run_generate(request, group_summary, task.id))
        return task.id, group_summary.id

    async def _run_generate(
        self,
        request: PersonaGenerateRequest,
        group_summary: PersonaGroupSummary,
        task_id: str,
    ) -> None:
        channel = f"persona-gen:{group_summary.id}"
        semaphore = asyncio.Semaphore(_PERSONA_CONCURRENCY)
        used_names: set[str] = set()
        name_lock = asyncio.Lock()
        total = request.count
        completed = 0

        async def build_and_save(idx: int) -> None:
            nonlocal completed
            hint = _VARIETY_HINTS[idx % len(_VARIETY_HINTS)]
            async with semaphore:
                raw = await self._fetch_single_persona(request, idx, hint)
            async with name_lock:
                persona = self._parse_single_persona(raw, request, group_summary.id, idx, used_names)
            db_id = await self.repository.save_single_persona(persona)
            persona.id = db_id
            completed += 1
            await self.ws_manager.broadcast(channel, {
                "type": "persona_ready",
                "index": idx,
                "completed": completed,
                "total": total,
                "persona": persona.model_dump(),
            })
            await self.task_service.update_task(
                task_id,
                progress=int(completed / total * 100),
                message=f"{completed}/{total} 画像已生成",
            )

        try:
            await asyncio.gather(*[build_and_save(i) for i in range(total)])
            await self.ws_manager.broadcast(channel, {
                "type": "done",
                "group": group_summary.model_dump(mode="json"),
                "total": total,
            })
            await self.task_service.update_task(
                task_id,
                status="completed",
                progress=100,
                message="画像生成完成",
                result={"group_id": group_summary.id},
            )
        except Exception as exc:
            await self.ws_manager.broadcast(channel, {"type": "error", "message": str(exc)})
            await self.task_service.update_task(task_id, status="failed", error=str(exc))

    async def list_groups(self, tenant_id: int) -> list[PersonaGroupSummary]:
        return await self.repository.list_groups(tenant_id)

    async def get_group_detail(self, group_id: int) -> PersonaGroupDetail | None:
        group = await self.repository.get_group(group_id)
        if not group:
            return None
        personas = await self.repository.list_personas_by_group(group_id)
        return PersonaGroupDetail(**group.model_dump(), personas=personas)

    async def list_group_personas(self, group_id: int) -> list[PersonaProfile]:
        return await self.repository.list_personas_by_group(group_id)

    async def get_persona(self, persona_id: int) -> PersonaProfile | None:
        return await self.repository.get_persona(persona_id)

    async def recommend_combination(self, tenant_id: int, scenario: str) -> dict[str, Any]:
        """Given a marketing scenario, recommend the best persona group and suggest complementary types."""
        groups = await self.repository.list_groups(tenant_id)
        if not groups:
            return {
                "recommended_group_id": None,
                "recommended_group_name": None,
                "reasoning": "当前没有可用的画像组，请先创建画像组。",
                "match_scores": [],
                "complementary_types": [],
            }

        # Collect group summaries (name + persona count + description)
        group_lines = [
            f"- ID={g.id} 名称={g.name} 画像数={g.persona_count} 描述={g.description or '无'}"
            for g in groups
        ]
        groups_text = "\n".join(group_lines)

        system_prompt = (
            "你是用户研究专家，根据给定的营销场景推荐最合适的画像组。"
            "严格输出 JSON，不要输出任何解释文字。"
        )
        user_prompt = (
            f"营销场景：{scenario}\n\n"
            f"可用画像组：\n{groups_text}\n\n"
            "请分析每个画像组与该场景的匹配度，并输出以下 JSON：\n"
            '{"recommended_group_id": 数字, "recommended_group_name": "名称", '
            '"reasoning": "推荐理由（2-3句话）", '
            '"match_scores": [{"group_id": 数字, "group_name": "名称", "score": 0-100, "reason": "简短理由"}], '
            '"complementary_types": ["补充画像类型描述1", "补充画像类型描述2"]}'
        )

        payload = await self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            light=True,
            temperature=0.4,
        )
        if not isinstance(payload, dict):
            raise RuntimeError("LLM 推荐结果格式不符合预期")

        return {
            "recommended_group_id": payload.get("recommended_group_id"),
            "recommended_group_name": payload.get("recommended_group_name", ""),
            "reasoning": str(payload.get("reasoning", "")),
            "match_scores": payload.get("match_scores") if isinstance(payload.get("match_scores"), list) else [],
            "complementary_types": payload.get("complementary_types") if isinstance(payload.get("complementary_types"), list) else [],
        }

    async def _fetch_single_persona(
        self,
        request: PersonaGenerateRequest,
        idx: int,
        variety_hint: str,
    ) -> dict[str, Any]:
        system_prompt = (
            "你是用户研究专家，请生成一个真实的虚拟消费者画像。"
            "严格输出单个 JSON 对象，不要输出解释文字。"
        )
        user_prompt = (
            f"目标人群：{request.description}\n"
            f"画像类型提示：{variety_hint}\n"
            f"（这是第 {idx + 1} 个画像，共 {request.count} 个，请保持独特性）\n"
            f"输出 JSON：{_SINGLE_PERSONA_SCHEMA}"
        )
        payload = await self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            light=True,
            temperature=0.7,
        )
        if not isinstance(payload, dict):
            raise RuntimeError(f"画像 #{idx + 1} LLM 返回格式错误")
        return payload

    def _parse_single_persona(
        self,
        raw: dict[str, Any],
        request: PersonaGenerateRequest,
        group_id: int,
        idx: int,
        used_names: set[str],
    ) -> PersonaProfile:
        persona_id = idx + 1

        name = str(raw.get("name") or f"虚拟用户{persona_id}").strip() or f"虚拟用户{persona_id}"
        if name in used_names:
            name = f"{name}{persona_id}"
        used_names.add(name)

        age = self._clamp_int(raw.get("age"), 18, 65, 28 + (idx % 10))
        monthly_income = self._clamp_int(raw.get("monthly_income"), 3000, 60000, 10000 + idx * 500)

        personality_raw = self._as_dict(raw.get("personality"))
        consumer_raw = self._as_dict(raw.get("consumer_profile"))
        media_raw = self._as_dict(raw.get("media_behavior"))
        social_raw = self._as_dict(raw.get("social_behavior"))
        agent_raw = self._as_dict(raw.get("agent_config"))

        monthly_disposable = self._clamp_int(
            consumer_raw.get("monthly_disposable"),
            800,
            30000,
            max(1200, monthly_income // 3),
        )

        return PersonaProfile(
            id=persona_id,
            group_id=group_id,
            tenant_id=1,
            name=name,
            age=age,
            gender=str(raw.get("gender") or ("女" if idx % 2 == 0 else "男")),
            city=str(raw.get("city") or ["上海", "北京", "广州", "深圳", "杭州", "成都"][idx % 6]),
            occupation=str(raw.get("occupation") or ["产品经理", "设计师", "运营", "程序员", "教师"][idx % 5]),
            monthly_income=monthly_income,
            personality=PersonaPersonality(
                mbti=str(personality_raw.get("mbti") or ["ENFP", "ISTJ", "ENTJ", "ISFJ", "INFJ"][idx % 5]),
                communication_style=str(personality_raw.get("communication_style") or "分析型"),
                description=str(personality_raw.get("description") or "对内容有自己的判断，愿意为真实体验买单。"),
            ),
            consumer_profile=PersonaConsumerProfile(
                price_sensitivity=self._clamp_float(consumer_raw.get("price_sensitivity"), 0.0, 1.0, 0.5),
                brand_loyalty=self._clamp_float(consumer_raw.get("brand_loyalty"), 0.0, 1.0, 0.5),
                decision_factors=self._as_str_list(consumer_raw.get("decision_factors"), ["价格", "口碑", "功效"]),
                purchase_frequency=str(consumer_raw.get("purchase_frequency") or "计划型"),
                monthly_disposable=monthly_disposable,
            ),
            media_behavior=PersonaMediaBehavior(
                platforms=self._as_str_list(media_raw.get("platforms"), ["小红书", "抖音", "微信"]),
                content_preference=self._as_str_list(media_raw.get("content_preference"), ["测评", "种草"]),
                influence_susceptibility=self._clamp_float(media_raw.get("influence_susceptibility"), 0.0, 1.0, 0.5),
                influence_power=self._clamp_float(media_raw.get("influence_power"), 0.0, 1.0, 0.45),
            ),
            social_behavior=PersonaSocialBehavior(
                post_frequency=str(social_raw.get("post_frequency") or "低频"),
                interaction_style=str(social_raw.get("interaction_style") or "评论派"),
                stance_on_ads=str(social_raw.get("stance_on_ads") or "中立"),
            ),
            agent_config=PersonaAgentConfig(
                activity_level=self._clamp_float(agent_raw.get("activity_level"), 0.0, 1.0, 0.55),
                sentiment_bias=self._clamp_float(agent_raw.get("sentiment_bias"), -1.0, 1.0, 0.0),
                critical_thinking=self._clamp_float(agent_raw.get("critical_thinking"), 0.0, 1.0, 0.6),
                herd_mentality=self._clamp_float(agent_raw.get("herd_mentality"), 0.0, 1.0, 0.35),
            ),
            backstory=str(raw.get("backstory") or f"来自{request.description}，近期持续关注同类产品真实评价。"),
        )

    def _as_dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _as_str_list(self, value: Any, default: list[str]) -> list[str]:
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            if cleaned:
                return cleaned[:8]
        return default

    def _clamp_int(self, value: Any, min_value: int, max_value: int, default: int) -> int:
        try:
            num = int(value)
        except (TypeError, ValueError):
            return default
        return max(min_value, min(max_value, num))

    def _clamp_float(self, value: Any, min_value: float, max_value: float, default: float) -> float:
        try:
            num = float(value)
        except (TypeError, ValueError):
            return default
        num = max(min_value, min(max_value, num))
        return round(num, 2)
