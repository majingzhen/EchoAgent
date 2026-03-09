from __future__ import annotations

import asyncio
import json
import logging
from statistics import mean
from typing import Any

from app.llm.client import LLMClient
from app.models.simulation import (
    ABTestCreateRequest,
    SimulationActionRecord,
    SimulationCreateRequest,
    SimulationReport,
    SimulationStatus,
)
from app.repositories.persona_repository import PersonaRepository
from app.repositories.persona_memory_repository import PersonaMemoryRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.task_service import TaskService
from app.ws.manager import WSConnectionManager

logger = logging.getLogger(__name__)

_DECISION_CONCURRENCY = 5


class SimulationEngine:
    def __init__(
        self,
        simulation_repository: SimulationRepository,
        persona_repository: PersonaRepository,
        ws_manager: WSConnectionManager,
        task_service: TaskService,
        llm_client: LLMClient,
        persona_memory_repository: PersonaMemoryRepository | None = None,
    ) -> None:
        self.simulation_repository = simulation_repository
        self.persona_repository = persona_repository
        self.ws_manager = ws_manager
        self.task_service = task_service
        self.llm_client = llm_client
        self.persona_memory_repository = persona_memory_repository

    async def create_session(self, request: SimulationCreateRequest) -> SimulationStatus:
        return await self.simulation_repository.create_session(
            tenant_id=1,
            persona_group_id=request.persona_group_id,
            platform=request.platform,
            content_text=request.content_text,
            config=request.config,
            total_rounds=int(request.config.get("max_rounds", 8)),
        )

    async def get_session(self, session_id: int) -> SimulationStatus | None:
        return await self.simulation_repository.get_session(session_id)

    async def get_report(self, session_id: int) -> SimulationReport | None:
        return await self.simulation_repository.get_report(session_id)

    async def start(self, session_id: int) -> str | None:
        raw = await self.simulation_repository.get_session_with_payload(session_id)
        if not raw:
            return None
        task = await self.task_service.create_task(int(raw["tenant_id"]), "simulation", session_id)
        await self.task_service.update_task(task.id, status="running", progress=1, message="simulation started")
        asyncio.create_task(self._run_simulation(session_id, task.id))
        return task.id

    async def _run_simulation(self, session_id: int, task_id: str) -> None:
        raw = await self.simulation_repository.get_session_with_payload(session_id)
        if not raw:
            await self.task_service.update_task(task_id, status="failed", error="session not found")
            return

        session = SimulationStatus(
            id=int(raw["id"]),
            tenant_id=int(raw["tenant_id"]),
            persona_group_id=int(raw["persona_group_id"]),
            platform=raw["platform"],
            status="running",
            total_rounds=int(raw["total_rounds"]),
            current_round=int(raw["current_round"]),
            metrics_timeline=list(raw["metrics_timeline"]),
            created_at=raw["created_at"],
            updated_at=raw["updated_at"],
        )
        content_text = raw["content_text"]
        platform = raw["platform"]
        actions: list[dict[str, Any]] = list(raw["actions"])
        channel = f"simulation:{session_id}"

        try:
            personas = await self.persona_repository.list_personas_by_group(session.persona_group_id)
            # 加载画像历史记忆（失败不阻塞主流程）
            memories_map: dict[int, str] = {}
            if self.persona_memory_repository:
                try:
                    persona_ids = [p.id for p in personas[:12]]
                    memories_map = await self.persona_memory_repository.list_memories_batch(persona_ids)
                except Exception:
                    logger.warning("load persona memories failed, skip", exc_info=True)

            for round_num in range(session.current_round + 1, session.total_rounds + 1):
                # 收集前几轮评论作为社交上下文
                social_context = self._build_social_context(actions)
                round_actions = await self._build_round_actions(
                    personas, round_num, session.total_rounds,
                    content_text, platform, social_context,
                    memories_map=memories_map,
                )
                actions.extend([action.model_dump() for action in round_actions])
                metrics = self._build_metrics(round_actions, round_num)
                session.current_round = round_num
                session.metrics_timeline.append(metrics)
                await self.simulation_repository.update_runtime(
                    session_id,
                    status="running",
                    current_round=session.current_round,
                    metrics_timeline=session.metrics_timeline,
                    actions=actions,
                )
                await self.task_service.update_task(
                    task_id,
                    progress=int(round_num / session.total_rounds * 100),
                    message=f"round {round_num}/{session.total_rounds}",
                )
                await self.ws_manager.broadcast(
                    channel,
                    {"type": "round_progress", "round": round_num, "total": session.total_rounds},
                )
                await self.ws_manager.broadcast(channel, {"type": "metrics_update", **metrics})
                await asyncio.sleep(0.2)

            report = await self._build_report(session_id, session, actions, content_text, platform)
            await self.simulation_repository.save_report(session_id, report.model_dump(mode="json"))

            # 写入画像记忆（失败不影响模拟结果）
            if self.persona_memory_repository:
                try:
                    await self._save_persona_memories(session_id, personas[:12], actions)
                except Exception:
                    logger.warning("save persona memories failed", exc_info=True)

            await self.simulation_repository.update_runtime(
                session_id,
                status="completed",
                current_round=session.current_round,
                metrics_timeline=session.metrics_timeline,
                actions=actions,
            )
            await self.task_service.update_task(
                task_id,
                status="completed",
                progress=100,
                message="simulation completed",
                result={"session_id": session_id, "report_ready": True},
            )
            await self.ws_manager.broadcast(channel, {"type": "simulation_complete", "report_id": session_id})
        except Exception as exc:
            logger.exception("simulation %s failed", session_id)
            await self.simulation_repository.update_runtime(
                session_id,
                status="failed",
                current_round=session.current_round,
                metrics_timeline=session.metrics_timeline,
                actions=actions,
            )
            await self.task_service.update_task(task_id, status="failed", error=str(exc), message="simulation failed")

    async def create_ab_test(self, request: ABTestCreateRequest) -> dict[str, Any]:
        personas = await self.persona_repository.list_personas_by_group(request.persona_group_id)
        jobs = [
            self._simulate_variant(variant=variant, index=idx, personas=personas, platform=request.platform)
            for idx, variant in enumerate(request.variants, start=1)
        ]
        rows = await asyncio.gather(*jobs)
        winner = max(rows, key=lambda x: x["metrics"]["purchase_intent"])
        payload = {
            "name": request.name,
            "status": "completed",
            "variants": rows,
            "winner": winner["label"],
            "summary": (
                f"推荐 {winner['label']}，购买意愿 {winner['metrics']['purchase_intent']}，"
                f"互动率 {winner['metrics']['engagement_rate']}。"
            ),
        }
        return await self.simulation_repository.create_ab_test(
            tenant_id=1,
            name=request.name,
            persona_group_id=request.persona_group_id,
            platform=request.platform,
            payload=payload,
        )

    async def get_ab_test(self, test_id: int) -> dict[str, Any] | None:
        return await self.simulation_repository.get_ab_test(test_id)

    async def list_sessions(self, tenant_id: int) -> list[dict[str, Any]]:
        return await self.simulation_repository.list_sessions(tenant_id)

    async def _simulate_variant(
        self, variant: str, index: int, personas: list[Any], platform: str,
    ) -> dict[str, Any]:
        # LLM 评估每个变体
        persona_summary = ", ".join([
            f"{p.name}({p.age}岁/{p.occupation})"
            for p in personas[:8]
        ])
        system_prompt = "你是社交媒体营销效果评估专家。根据目标人群画像评估内容变体的效果。严格输出 JSON。"
        user_prompt = (
            f"## 平台：{platform}\n"
            f"## 目标人群：{persona_summary}\n"
            f"## 待评估内容：\n{variant}\n\n"
            "请评估并输出：{\"reach_rate\":0.0-1.0,\"engagement_rate\":0.0-1.0,\"purchase_intent\":0.0-1.0,\"reason\":\"简要理由\"}"
        )
        try:
            result = await self.llm_client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                light=True,
                temperature=0.4,
            )
            if isinstance(result, dict):
                return {
                    "label": f"版本{index}",
                    "content": variant,
                    "metrics": {
                        "reach_rate": round(float(result.get("reach_rate", 0.5)), 2),
                        "engagement_rate": round(float(result.get("engagement_rate", 0.3)), 2),
                        "purchase_intent": round(float(result.get("purchase_intent", 0.2)), 2),
                    },
                    "reason": result.get("reason", ""),
                }
        except Exception:
            logger.exception("variant %d LLM eval failed, fallback", index)
        # fallback
        return {
            "label": f"版本{index}",
            "content": variant,
            "metrics": {"reach_rate": 0.5, "engagement_rate": 0.3, "purchase_intent": 0.2},
        }

    def _build_social_context(self, actions: list[dict[str, Any]]) -> str:
        comments = [
            f"{a['persona_name']}: {a['comment_text']}"
            for a in actions
            if a.get("comment_text")
        ]
        if not comments:
            return "暂无前序评论。"
        # 取最近 5 条评论
        recent = comments[-5:]
        return "前序评论：\n" + "\n".join(recent)

    async def _build_round_actions(
        self,
        personas: list[Any],
        round_num: int,
        total_rounds: int,
        content_text: str,
        platform: str,
        social_context: str,
        memories_map: dict[int, str] | None = None,
    ) -> list[SimulationActionRecord]:
        semaphore = asyncio.Semaphore(_DECISION_CONCURRENCY)
        results: list[SimulationActionRecord] = []

        async def decide_one(persona: Any) -> SimulationActionRecord:
            async with semaphore:
                return await self._llm_decide_action(
                    persona, round_num, total_rounds,
                    content_text, platform, social_context,
                    memories_map,
                )

        tasks = [decide_one(p) for p in personas[:min(12, len(personas))]]
        results = await asyncio.gather(*tasks)
        return list(results)

    async def _llm_decide_action(
        self,
        persona: Any,
        round_num: int,
        total_rounds: int,
        content_text: str,
        platform: str,
        social_context: str,
        memories_map: dict[int, str] | None = None,
    ) -> SimulationActionRecord:
        memory_section = ""
        if memories_map and persona.id in memories_map:
            memory_section = f"\n## 历史记忆\n{memories_map[persona.id]}"

        system_prompt = (
            f"你是社交媒体用户行为模拟器。根据用户画像和内容，判断该用户在{platform}上的行为反应。\n"
            "严格输出 JSON。"
        )
        user_prompt = (
            f"## 用户画像\n"
            f"姓名：{persona.name}，{persona.age}岁，{persona.occupation}，{persona.city}\n"
            f"性格：{persona.personality.mbti}，{persona.personality.communication_style}\n"
            f"价格敏感度：{persona.consumer_profile.price_sensitivity}，品牌忠诚度：{persona.consumer_profile.brand_loyalty}\n"
            f"关注点：{'、'.join(persona.consumer_profile.decision_factors)}\n"
            f"广告态度：{persona.social_behavior.stance_on_ads}\n"
            f"从众心理：{persona.agent_config.herd_mentality}，批判思维：{persona.agent_config.critical_thinking}\n"
            f"{memory_section}\n"
            f"## 待测内容（{platform}）\n{content_text}\n\n"
            f"## 当前第{round_num}轮，共{total_rounds}轮\n"
            f"{social_context}\n\n"
            '请输出：{"action":"忽略|点赞|评论|收藏|转发","comment":"评论内容或null","sentiment_score":0-10,"purchase_intent":0.0-1.0}'
        )
        try:
            result = await self.llm_client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                light=True,
                temperature=0.6,
            )
            if isinstance(result, dict):
                action_type = result.get("action", "忽略")
                valid_actions = ["忽略", "点赞", "评论", "收藏", "转发"]
                if action_type not in valid_actions:
                    action_type = "忽略"
                comment = result.get("comment")
                if comment == "null" or comment is None:
                    comment = None
                # 如果行为不是评论但 LLM 给了评论内容，清空
                if action_type != "评论":
                    comment = None
                return SimulationActionRecord(
                    round_num=round_num,
                    persona_id=persona.id,
                    persona_name=persona.name,
                    action_type=action_type,
                    comment_text=comment,
                    sentiment_score=round(min(10, max(0, float(result.get("sentiment_score", 5)))), 2),
                    purchase_intent=round(min(1.0, max(0, float(result.get("purchase_intent", 0.3)))), 2),
                )
        except Exception:
            logger.warning("LLM decide failed for %s round %d, fallback", persona.name, round_num)
        # fallback: 默认忽略
        return SimulationActionRecord(
            round_num=round_num,
            persona_id=persona.id,
            persona_name=persona.name,
            action_type="忽略",
            comment_text=None,
            sentiment_score=5.0,
            purchase_intent=0.3,
        )

    def _build_metrics(self, round_actions: list[SimulationActionRecord], round_num: int) -> dict[str, Any]:
        total = len(round_actions) or 1
        interactions = sum(1 for action in round_actions if action.action_type != "忽略")
        sentiment = round(mean([a.sentiment_score for a in round_actions]), 2) if round_actions else 0
        intent = round(mean([a.purchase_intent for a in round_actions]), 2) if round_actions else 0
        return {
            "round": round_num,
            "reach_rate": round(min(0.95, 0.18 + round_num * 0.08), 2),
            "engagement_rate": round(interactions / total, 2),
            "avg_sentiment": sentiment,
            "avg_purchase_intent": intent,
            "action_counts": {
                "ignore": sum(1 for action in round_actions if action.action_type == "忽略"),
                "like": sum(1 for action in round_actions if action.action_type == "点赞"),
                "comment": sum(1 for action in round_actions if action.action_type == "评论"),
                "collect": sum(1 for action in round_actions if action.action_type == "收藏"),
                "share": sum(1 for action in round_actions if action.action_type == "转发"),
            },
        }

    async def _build_report(
        self,
        session_id: int,
        session: SimulationStatus,
        actions: list[dict[str, Any]],
        content_text: str,
        platform: str,
    ) -> SimulationReport:
        # 采样有评论的行为记录
        commented = [a for a in actions if a.get("comment_text")]
        sampled = commented[:20]
        sampled_text = "\n".join([
            f"第{a['round_num']}轮 {a['persona_name']}({a['action_type']}): {a['comment_text']}"
            for a in sampled
        ]) if sampled else "无评论记录"

        metrics_text = json.dumps(session.metrics_timeline, ensure_ascii=False)
        persona_count = len(set(a.get("persona_id", 0) for a in actions)) if actions else 0

        system_prompt = "你是社交媒体营销分析师，根据模拟数据生成专业的分析报告。严格输出 JSON。"
        user_prompt = (
            f"## 模拟概况\n"
            f"平台：{platform}，{session.total_rounds}轮，{persona_count}个画像\n\n"
            f"## 待测内容\n{content_text}\n\n"
            f"## 指标时间线\n{metrics_text}\n\n"
            f"## 行为记录（采样）\n{sampled_text}\n\n"
            "请输出：\n"
            "{\n"
            '  "executive_summary": "简述整体表现和关键发现",\n'
            '  "segment_insights": [{"segment":"人群标签","reaction":"反应概述","key_concern":"核心关注"}],\n'
            '  "propagation": {"key_spreaders":[],"viral_triggers":[],"bottlenecks":[],"peak_time":N},\n'
            '  "risks": ["风险1"],\n'
            '  "suggestions": ["建议1"]\n'
            "}"
        )
        try:
            result = await self.llm_client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                light=False,
                temperature=0.3,
            )
            if isinstance(result, dict):
                last_metrics = session.metrics_timeline[-1] if session.metrics_timeline else {}
                comments = [a["comment_text"] for a in actions if a.get("comment_text")][:5] or ["暂无代表性评论"]
                return SimulationReport(
                    session_id=session_id,
                    executive_summary=result.get("executive_summary", "分析完成"),
                    metrics=last_metrics,
                    segment_insights=result.get("segment_insights", []),
                    propagation=result.get("propagation", {}),
                    risks=result.get("risks", []),
                    suggestions=result.get("suggestions", []),
                    sample_comments=comments,
                )
        except Exception:
            logger.exception("build report LLM failed for session %d, fallback", session_id)

        # fallback
        last_metrics = session.metrics_timeline[-1] if session.metrics_timeline else {}
        comments = [a["comment_text"] for a in actions if a.get("comment_text")][:5] or ["暂无代表性评论"]
        return SimulationReport(
            session_id=session_id,
            executive_summary="模拟完成，LLM 报告生成失败，请查看原始数据。",
            metrics=last_metrics,
            segment_insights=[],
            propagation={},
            risks=["报告生成异常"],
            suggestions=["请重试或检查 LLM 配置"],
            sample_comments=comments,
        )

    async def _save_persona_memories(
        self, session_id: int, personas: list[Any], actions: list[dict[str, Any]],
    ) -> None:
        # 按 persona_id 分组行为
        grouped: dict[int, list[str]] = {}
        pid_to_name: dict[int, str] = {}
        for a in actions:
            pid = a.get("persona_id", 0)
            pid_to_name[pid] = a.get("persona_name", "")
            if pid not in grouped:
                grouped[pid] = []
            action_desc = a.get("action_type", "忽略")
            if a.get("comment_text"):
                action_desc += f"「{a['comment_text'][:50]}」"
            grouped[pid].append(f"第{a.get('round_num')}轮: {action_desc}")

        semaphore = asyncio.Semaphore(_DECISION_CONCURRENCY)

        async def extract_one(pid: int, records: list[str]) -> None:
            async with semaphore:
                name = pid_to_name.get(pid, "")
                content = "; ".join(records[:8])
                system_prompt = "请用一句话概括该消费者在本次沙盘推演中的核心态度。只输出 JSON。"
                user_prompt = (
                    f"画像：{name}\n"
                    f"行为记录：{content}\n"
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
                            pid, "simulation", session_id, memory[:200],
                        )
                except Exception:
                    logger.warning("save memory failed for persona %d", pid)

        tasks = [extract_one(pid, records) for pid, records in grouped.items()]
        await asyncio.gather(*tasks)
