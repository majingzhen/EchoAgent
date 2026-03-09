from __future__ import annotations

import asyncio
from typing import Any

from app.llm.client import LLMClient
from app.models.simulation import ABTestCreateRequest
from app.models.workshop import WorkshopCreateRequest, WorkshopSession
from app.repositories.market_repository import MarketRepository
from app.repositories.persona_repository import PersonaRepository
from app.repositories.workshop_repository import WorkshopRepository
from app.services.simulation_engine import SimulationEngine
from app.services.task_service import TaskService
from app.ws.manager import WSConnectionManager


class WorkshopService:
    def __init__(
        self,
        workshop_repository: WorkshopRepository,
        persona_repository: PersonaRepository,
        simulation_engine: SimulationEngine,
        market_repository: MarketRepository,
        llm_client: LLMClient,
        ws_manager: WSConnectionManager,
        task_service: TaskService,
    ) -> None:
        self.workshop_repository = workshop_repository
        self.persona_repository = persona_repository
        self.simulation_engine = simulation_engine
        self.market_repository = market_repository
        self.llm_client = llm_client
        self.ws_manager = ws_manager
        self.task_service = task_service

    async def create_session(self, request: WorkshopCreateRequest) -> WorkshopSession:
        brief_payload = {
            "brief": request.brief,
            "goal": request.goal,
            "product": request.product,
        }
        return await self.workshop_repository.create_session(
            tenant_id=1,
            persona_group_id=request.persona_group_id,
            platform=request.platform,
            brand_tone=request.brand_tone,
            brief=brief_payload,
        )

    async def get_session(self, session_id: int) -> WorkshopSession | None:
        return await self.workshop_repository.get_session(session_id)

    async def list_sessions(self, tenant_id: int) -> list[dict]:
        return await self.workshop_repository.list_sessions(tenant_id)

    async def run_session_async(
        self,
        session_id: int,
        tenant_id: int,
        market_graph_id: int | None = None,
    ) -> str:
        """立即返回 task_id，后台运行 pipeline 并逐步推送 WS 进度。"""
        task = await self.task_service.create_task(tenant_id, "workshop_run", session_id)
        asyncio.create_task(self._run_pipeline(session_id, market_graph_id, task.id))
        return task.id

    async def _run_pipeline(
        self,
        session_id: int,
        market_graph_id: int | None,
        task_id: str,
    ) -> None:
        channel = f"workshop:{session_id}"

        async def push(event: dict[str, Any]) -> None:
            await self.ws_manager.broadcast(channel, event)

        try:
            session = await self.workshop_repository.get_session(session_id)
            if not session:
                await push({"type": "error", "message": "workshop session not found"})
                return

            # 洞察注入
            insights = list(session.insights)
            if market_graph_id:
                graph = await self.market_repository.get_graph(market_graph_id)
                if graph:
                    insights = self._graph_to_insights(graph.entities, graph.relations)

            # Step 1: 策略方向
            await push({"type": "progress", "step": "angles", "message": "策略方向生成中..."})
            strategist_angles = await self._build_angles_with_llm(session, insights)
            await push({"type": "step_done", "step": "angles", "data": strategist_angles})

            # Step 2: 文案草稿 + 加载画像（并行）
            await push({"type": "progress", "step": "drafts", "message": "文案草稿生成中..."})
            drafts, personas = await asyncio.gather(
                self._build_drafts_with_llm(session, strategist_angles),
                self.persona_repository.list_personas_by_group(session.persona_group_id),
            )
            await push({"type": "step_done", "step": "drafts", "data": drafts})

            # Step 3: 消费者评分
            await push({"type": "progress", "step": "feedback", "message": "消费者评分中..."})
            feedback = await self._build_consumer_feedback_with_llm(drafts, personas)
            await push({"type": "step_done", "step": "feedback", "data": feedback})

            # Step 4: 品牌审核
            winner_index = max(range(len(feedback)), key=lambda i: float(feedback[i]["avg_score"]))
            winner = drafts[winner_index]
            await push({"type": "progress", "step": "brand_guard", "message": "品牌合规审核中..."})
            brand_review = await self._brand_guard_with_llm(winner["content"], session.brand_tone)
            await push({"type": "step_done", "step": "brand_guard", "data": brand_review})

            final_content = winner["content"]
            if brand_review["needs_fix"]:
                final_content = f"{winner['content']}\n\n补充：表达克制，避免绝对化承诺，强调真实体验边界。"

            payload = {
                "strategist_angles": strategist_angles,
                "drafts": drafts,
                "consumer_feedback": feedback,
                "winner_variant": winner["variant"],
                "brand_review": brand_review,
                "final_content": final_content,
            }
            await self.workshop_repository.update_runtime(
                session_id,
                status="completed",
                payload=payload,
                insights=insights,
            )
            await push({"type": "done", "data": payload})
            await self.task_service.update_task(task_id, status="completed", progress=100)

        except Exception as exc:
            await push({"type": "error", "message": str(exc)})
            await self.task_service.update_task(task_id, status="failed", error=str(exc))
            await self.workshop_repository.update_runtime(
                session_id, status="failed", payload={}, insights=[]
            )

    async def inject_insights(self, session_id: int, graph_id: int) -> list[str] | None:
        session = await self.workshop_repository.get_session(session_id)
        if not session:
            return None
        graph = await self.market_repository.get_graph(graph_id)
        if not graph:
            return None
        insights = self._graph_to_insights(graph.entities, graph.relations)
        await self.workshop_repository.update_insights(session_id, insights)
        return insights

    async def create_ab_test(self, session_id: int) -> dict | None:
        session = await self.workshop_repository.get_session(session_id)
        if not session:
            return None
        drafts = session.payload.get("drafts", [])
        variants = [draft["content"] for draft in drafts if draft.get("content")]
        if len(variants) < 2:
            final_content = session.payload.get("final_content")
            if not final_content:
                return None
            variants = [final_content, f"{final_content}\n\n补充：增加场景化描述与价格锚点。"]

        request = ABTestCreateRequest(
            tenant_id=session.tenant_id,
            name=f"Workshop-{session_id}-AB",
            persona_group_id=session.persona_group_id,
            platform=session.platform,
            variants=variants[:5],
        )
        result = await self.simulation_engine.create_ab_test(request)
        await self.workshop_repository.update_ab_test(session_id, int(result["id"]))
        return result

    async def _build_angles_with_llm(self, session: WorkshopSession, insights: list[str]) -> list[dict[str, str]]:
        system_prompt = "你是资深内容策略专家。请输出 3 个差异化创意方向，仅返回 JSON。"
        user_prompt = (
            f"平台：{session.platform}\n"
            f"品牌调性：{session.brand_tone}\n"
            f"Brief：{session.brief.get('brief', '')}\n"
            f"目标：{session.brief.get('goal', '')}\n"
            f"洞察：{'；'.join(insights) if insights else '暂无额外洞察'}\n"
            "输出 JSON：{\"angles\":[{\"title\":\"\",\"core_message\":\"\",\"audience\":\"\",\"hook\":\"\",\"reason\":\"\"}]}"
        )
        payload = await self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
        )
        if not isinstance(payload, dict):
            raise RuntimeError("LLM 返回策略方向结构不符合预期")

        raw = payload.get("angles")
        if not isinstance(raw, list) or not raw:
            raise RuntimeError("LLM 未返回有效的策略方向列表")

        angles: list[dict[str, str]] = []
        for item in raw[:3]:
            if not isinstance(item, dict):
                continue
            angles.append(
                {
                    "title": str(item.get("title") or "策略方向").strip(),
                    "core_message": str(item.get("core_message") or "突出价值点与真实证据").strip(),
                    "audience": str(item.get("audience") or "核心人群").strip(),
                    "hook": str(item.get("hook") or "这个点为什么值得关注").strip(),
                    "reason": str(item.get("reason") or "与用户关注点匹配").strip(),
                }
            )

        if not angles:
            raise RuntimeError("LLM 返回的策略方向无法解析")
        return angles

    async def _build_drafts_with_llm(
        self,
        session: WorkshopSession,
        angles: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        system_prompt = "你是资深营销文案，按给定方向产出多版本内容。仅返回 JSON。"
        angles_desc = "\n".join(
            [
                f"{idx + 1}. {item['title']} | {item['core_message']} | {item['audience']} | {item['hook']}"
                for idx, item in enumerate(angles)
            ]
        )
        user_prompt = (
            f"平台：{session.platform}\n"
            f"品牌调性：{session.brand_tone}\n"
            f"Brief：{session.brief.get('brief', '')}\n"
            f"创意方向：\n{angles_desc}\n"
            "输出 JSON：{\"drafts\":[{\"variant\":\"V1\",\"angle\":\"方向名\",\"content\":\"完整文案\"}]}"
        )
        payload = await self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        )
        if not isinstance(payload, dict):
            raise RuntimeError("LLM 返回文案草稿结构不符合预期")

        raw = payload.get("drafts")
        if not isinstance(raw, list) or not raw:
            raise RuntimeError("LLM 未返回有效的文案草稿列表")

        drafts: list[dict[str, str]] = []
        for idx, item in enumerate(raw[: max(2, len(angles))], start=1):
            if not isinstance(item, dict):
                continue
            content = str(item.get("content") or "").strip()
            if not content:
                continue
            drafts.append(
                {
                    "variant": str(item.get("variant") or f"V{idx}"),
                    "angle": str(item.get("angle") or angles[min(idx - 1, len(angles) - 1)]["title"]),
                    "content": content,
                }
            )

        if len(drafts) < 2:
            raise RuntimeError(f"LLM 只生成了 {len(drafts)} 个文案版本，至少需要 2 个")
        return drafts

    async def _build_consumer_feedback_with_llm(
        self, drafts: list[dict[str, str]], personas: list
    ) -> list[dict[str, Any]]:
        if not drafts:
            raise RuntimeError("没有可评分的文案草稿")

        persona_summary = [
            {
                "name": persona.name,
                "price_sensitivity": persona.consumer_profile.price_sensitivity,
                "brand_loyalty": persona.consumer_profile.brand_loyalty,
                "decision_factors": persona.consumer_profile.decision_factors,
            }
            for persona in personas[:8]
        ]
        draft_summary = [
            {
                "variant": draft["variant"],
                "angle": draft["angle"],
                "content_preview": draft["content"][:160],
            }
            for draft in drafts
        ]

        system_prompt = "你是消费者研究分析师。请基于画像和文案版本打分并给出解释。仅返回 JSON。"
        user_prompt = (
            f"画像摘要：{persona_summary}\n"
            f"版本摘要：{draft_summary}\n"
            "输出 JSON：{\"feedback\":[{\"variant\":\"V1\",\"avg_score\":7.8,\"highlights\":[\"原因1\",\"原因2\"]}]}"
        )

        payload = await self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )
        if not isinstance(payload, dict):
            raise RuntimeError("LLM 返回消费者评分结构不符合预期")

        raw = payload.get("feedback")
        if not isinstance(raw, list) or not raw:
            raise RuntimeError("LLM 未返回有效的消费者评分列表")

        feedback: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            variant = str(item.get("variant") or "").strip()
            if not variant:
                continue
            score = self._clamp_score(item.get("avg_score"), 6.5)
            highlights = self._to_list(item.get("highlights"), [])
            feedback.append({"variant": variant, "avg_score": score, "highlights": highlights})

        if not feedback:
            raise RuntimeError("LLM 返回的消费者评分无法解析")
        return feedback

    async def _brand_guard_with_llm(self, content: str, brand_tone: str) -> dict[str, Any]:
        system_prompt = "你是品牌与合规审核专家。仅输出 JSON。"
        user_prompt = (
            f"品牌调性：{brand_tone}\n"
            f"待审核文案：\n{content}\n"
            "输出 JSON：{\"score\":8,\"needs_fix\":false,\"risk_hits\":[\"风险词\"],\"suggestions\":[\"建议1\"]}"
        )
        payload = await self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )
        if not isinstance(payload, dict):
            raise RuntimeError("LLM 返回品牌审核结构不符合预期")

        return {
            "score": int(self._clamp_score(payload.get("score"), 8.0)),
            "needs_fix": bool(payload.get("needs_fix")),
            "risk_hits": self._to_list(payload.get("risk_hits"), []),
            "suggestions": self._to_list(payload.get("suggestions"), []),
        }

    def _graph_to_insights(self, entities: list, relations: list) -> list[str]:
        entity_names = [str(item.get("name", "")) for item in entities[:5] if isinstance(item, dict)]
        relation_count = len(relations)
        insights = []
        if entity_names:
            insights.append("高频实体：" + "、".join(entity_names))
        insights.append(f"图谱关系数 {relation_count}，说明讨论点之间存在联动传播。")
        insights.append("建议在内容工坊优先回应高频竞品与价格敏感话题。")
        return insights

    async def save_result(
        self,
        session_id: int,
        variant: str,
        went_live: bool,
        actual_engagement_rate: float | None,
        actual_conversion_rate: float | None,
        notes: str,
    ) -> int:
        return await self.workshop_repository.save_result(
            session_id, variant, went_live,
            actual_engagement_rate, actual_conversion_rate, notes,
        )

    async def get_results(self, session_id: int) -> list[dict]:
        return await self.workshop_repository.get_results(session_id)

    def _to_list(self, value: object, default: list[str]) -> list[str]:
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            if cleaned:
                return cleaned[:8]
        return default

    def _clamp_score(self, value: object, default: float) -> float:
        try:
            score = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            score = default
        score = max(0.0, min(10.0, score))
        return round(score, 2)
