from __future__ import annotations

import asyncio
from typing import Any

from app.llm.client import LLMClient
from app.models.sentiment_guard import SentimentGuardReport, SentimentGuardRequest, SentimentGuardSession
from app.repositories.sentiment_guard_repository import SentimentGuardRepository
from app.services.task_service import TaskService
from app.ws.manager import WSConnectionManager

_RESPONSE_PLANS = [
    {"label": "方案A", "strategy": "快速回应 + 道歉 + 补偿", "timing_hint": "事件发酵6小时内"},
    {"label": "方案B", "strategy": "冷处理 + 背景说明", "timing_hint": "48小时后视情况发声"},
    {"label": "方案C", "strategy": "正面回应 + 转移焦点", "timing_hint": "同步启动正向话题"},
]


class SentimentGuardService:
    def __init__(
        self,
        repository: SentimentGuardRepository,
        llm_client: LLMClient,
        ws_manager: WSConnectionManager,
        task_service: TaskService,
    ) -> None:
        self.repository = repository
        self.llm_client = llm_client
        self.ws_manager = ws_manager
        self.task_service = task_service

    async def run_async(self, request: SentimentGuardRequest) -> tuple[str, int]:
        """创建会话，后台运行评估，立即返回 (task_id, session_id)。"""
        session = await self.repository.create_session(
            tenant_id=1,
            mode=request.mode,
            event_description=request.event_description,
        )
        task = await self.task_service.create_task(1, "sentiment_guard", session.id)
        asyncio.create_task(self._run_assessment(request, session, task.id))
        return task.id, session.id

    async def get_session(self, session_id: int) -> SentimentGuardSession | None:
        return await self.repository.get_session(session_id)

    async def list_sessions(self, tenant_id: int) -> list[SentimentGuardSession]:
        return await self.repository.list_sessions(tenant_id)

    # ── 后台评估流程 ──────────────────────────────────────────────────────────

    async def _run_assessment(
        self,
        request: SentimentGuardRequest,
        session: SentimentGuardSession,
        task_id: str,
    ) -> None:
        channel = f"sentiment-guard:{session.id}"
        payload: dict[str, Any] = {}
        try:
            # Step 1: 风险评估
            await self.ws_manager.broadcast(channel, {"type": "progress", "step": "risk_assess", "message": "正在评估风险..."})
            risk = await self._risk_assess(request)
            payload["risk_assessment"] = risk
            await self.ws_manager.broadcast(channel, {"type": "step_done", "step": "risk_assess", "data": risk})
            await self.task_service.update_task(task_id, progress=20, message="风险评估完成")

            # Step 2: 传播模拟（规则驱动）
            await self.ws_manager.broadcast(channel, {"type": "progress", "step": "spread", "message": "模拟传播路径..."})
            spread = self._simulate_spread(risk)
            payload["spread_simulation"] = spread
            await self.ws_manager.broadcast(channel, {"type": "step_done", "step": "spread", "data": spread})
            await self.task_service.update_task(task_id, progress=40, message="传播模拟完成")

            # Step 3: 生成3套应对方案
            await self.ws_manager.broadcast(channel, {"type": "progress", "step": "response_gen", "message": "生成应对方案..."})
            plans = await self._generate_plans(request, risk, spread)
            payload["response_plans"] = plans
            await self.ws_manager.broadcast(channel, {"type": "step_done", "step": "response_gen", "data": plans})
            await self.task_service.update_task(task_id, progress=65, message="方案生成完成")

            # Step 4: 并发验证3套方案
            await self.ws_manager.broadcast(channel, {"type": "progress", "step": "validate", "message": "并发验证各方案效果..."})
            validations = await self._validate_plans(request, plans)
            payload["validation_results"] = validations
            await self.ws_manager.broadcast(channel, {"type": "step_done", "step": "validate", "data": validations})
            await self.task_service.update_task(task_id, progress=85, message="方案验证完成")

            # Step 5: 综合报告
            best = max(validations, key=lambda v: v.get("score", 0))
            report_payload = {
                **payload,
                "best_plan": best.get("label", "方案A"),
                "execution_window": best.get("execution_window", "事件发酵12小时内"),
                "summary": (
                    f"风险等级 {risk.get('severity', 5)}/10，"
                    f"预计主要在{risk.get('vulnerable_audiences', ['社交媒体用户'])[0]}群体中扩散。"
                    f"推荐{best.get('label', '方案A')}，预计{best.get('recovery_time', '48小时')}内平息。"
                ),
            }
            await self.repository.update_session(session.id, "completed", report_payload)
            await self.ws_manager.broadcast(channel, {"type": "done", "data": report_payload})
            await self.task_service.update_task(
                task_id, status="completed", progress=100, message="评估完成",
                result={"session_id": session.id},
            )
        except Exception as exc:
            await self.repository.update_session(session.id, "failed", payload)
            await self.ws_manager.broadcast(channel, {"type": "error", "message": str(exc)})
            await self.task_service.update_task(task_id, status="failed", error=str(exc))

    async def _risk_assess(self, request: SentimentGuardRequest) -> dict[str, Any]:
        mode_hint = (
            f"当前舆情状态：{request.current_sentiment}" if request.current_sentiment
            else "请从事前预判角度分析"
        )
        system_prompt = "你是危机公关专家，擅长评估品牌舆情风险。"
        user_prompt = (
            f"风险事件：{request.event_description}\n"
            f"{mode_hint}\n"
            "请输出 JSON：{\"severity\":7,\"trigger_topics\":[],\"vulnerable_audiences\":[],\"estimated_spread_speed\":\"快速\"}"
        )
        payload = await self.llm_client.generate_json(
            system_prompt=system_prompt, user_prompt=user_prompt, light=True, temperature=0.3
        )
        if not isinstance(payload, dict):
            raise RuntimeError("风险评估 LLM 返回格式错误")
        return {
            "severity": min(10, max(1, int(payload.get("severity", 5)))),
            "trigger_topics": payload.get("trigger_topics", [])[:6],
            "vulnerable_audiences": payload.get("vulnerable_audiences", [])[:4],
            "estimated_spread_speed": str(payload.get("estimated_spread_speed", "中速")),
        }

    def _simulate_spread(self, risk: dict[str, Any]) -> dict[str, Any]:
        severity = risk.get("severity", 5)
        speed = risk.get("estimated_spread_speed", "中速")
        if "快" in speed:
            peak_hours = 6
        elif "慢" in speed:
            peak_hours = 48
        else:
            peak_hours = 24
        reach = min(95, 15 + severity * 8)
        neg_ratio = min(90, 20 + severity * 7)
        return {
            "peak_hours": peak_hours,
            "estimated_reach_rate": f"{reach}%",
            "negative_sentiment_ratio": f"{neg_ratio}%",
            "key_spread_nodes": ["意见领袖评论区", "行业媒体转发", "用户话题广场"],
            "inflection_point": f"事件发酵后约 {peak_hours} 小时达到传播峰值",
        }

    async def _generate_plans(
        self,
        request: SentimentGuardRequest,
        risk: dict[str, Any],
        spread: dict[str, Any],
    ) -> list[dict[str, Any]]:
        system_prompt = "你是危机公关策略师，善于制定品牌舆情应对方案。"
        user_prompt = (
            f"事件：{request.event_description}\n"
            f"风险等级：{risk.get('severity')}/10，预计{spread.get('peak_hours')}小时达到峰值\n"
            "请生成3套应对方案，输出 JSON 数组：\n"
            "[{\"label\":\"方案A\",\"strategy\":\"快速回应+道歉+补偿\",\"key_message\":\"\",\"timing\":\"\",\"expected_outcome\":\"\"},"
            "{\"label\":\"方案B\",\"strategy\":\"冷处理+背景说明\",\"key_message\":\"\",\"timing\":\"\",\"expected_outcome\":\"\"},"
            "{\"label\":\"方案C\",\"strategy\":\"正面回应+转移焦点\",\"key_message\":\"\",\"timing\":\"\",\"expected_outcome\":\"\"}]"
        )
        payload = await self.llm_client.generate_json(
            system_prompt=system_prompt, user_prompt=user_prompt, light=False, temperature=0.5
        )
        plans = payload if isinstance(payload, list) else []
        if len(plans) < 3:
            plans = [
                {"label": p["label"], "strategy": p["strategy"], "key_message": "待补充", "timing": p["timing_hint"], "expected_outcome": "待评估"}
                for p in _RESPONSE_PLANS
            ]
        return plans[:3]

    async def _validate_plans(
        self,
        request: SentimentGuardRequest,
        plans: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        async def validate_one(plan: dict[str, Any]) -> dict[str, Any]:
            system_prompt = "你是舆情效果评估专家，擅长预测公关方案的实际效果。"
            user_prompt = (
                f"事件：{request.event_description}\n"
                f"应对方案：{plan.get('label')} — {plan.get('strategy')}\n"
                f"核心信息：{plan.get('key_message', '')}\n"
                "评估此方案效果，输出 JSON：{\"label\":\"方案A\",\"score\":7,\"recovery_time\":\"48小时\",\"execution_window\":\"6小时内发布\",\"effectiveness\":\"较好\",\"risks\":[]}"
            )
            result = await self.llm_client.generate_json(
                system_prompt=system_prompt, user_prompt=user_prompt, light=True, temperature=0.3
            )
            if isinstance(result, dict):
                return {
                    "label": plan.get("label", result.get("label", "")),
                    "score": min(10, max(1, int(result.get("score", 5)))),
                    "recovery_time": str(result.get("recovery_time", "48小时")),
                    "execution_window": str(result.get("execution_window", "尽快")),
                    "effectiveness": str(result.get("effectiveness", "一般")),
                    "risks": result.get("risks", [])[:3],
                }
            return {"label": plan.get("label", ""), "score": 5, "recovery_time": "72小时", "execution_window": "24小时内", "effectiveness": "一般", "risks": []}

        results = await asyncio.gather(*[validate_one(p) for p in plans])
        return list(results)
