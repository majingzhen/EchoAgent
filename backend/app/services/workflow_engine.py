from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.models.simulation import SimulationCreateRequest
from app.models.workflow import WORKFLOW_TEMPLATES, WorkflowCreateRequest, WorkflowSession, WorkflowStepRecord
from app.repositories.workflow_repository import WorkflowRepository
from app.services.market_service import MarketService
from app.services.sentiment_guard_service import SentimentGuardService
from app.services.simulation_engine import SimulationEngine
from app.services.strategy_advisor_service import StrategyAdvisorService
from app.services.task_service import TaskService
from app.services.workshop_service import WorkshopService
from app.ws.manager import WSConnectionManager

logger = logging.getLogger(__name__)


class WorkflowEngine:
    def __init__(
        self,
        repository: WorkflowRepository,
        workshop_service: WorkshopService,
        simulation_engine: SimulationEngine,
        sentiment_guard_service: SentimentGuardService,
        strategy_advisor_service: StrategyAdvisorService,
        market_service: MarketService,
        task_service: TaskService,
        ws_manager: WSConnectionManager,
    ) -> None:
        self.repository = repository
        self.workshop_service = workshop_service
        self.simulation_engine = simulation_engine
        self.sentiment_guard_service = sentiment_guard_service
        self.strategy_advisor_service = strategy_advisor_service
        self.market_service = market_service
        self.task_service = task_service
        self.ws_manager = ws_manager

    async def create_workflow(self, request: WorkflowCreateRequest) -> WorkflowSession:
        template = WORKFLOW_TEMPLATES.get(request.workflow_type)
        if not template:
            raise ValueError(f"未知工作流类型: {request.workflow_type}")

        steps: list[dict[str, Any]] = []
        for step_def in template["steps"]:
            skip = step_def["name"] in request.disabled_steps and not step_def["required"]
            steps.append({
                "name": step_def["name"],
                "label": step_def["label"],
                "required": step_def["required"],
                "status": "skipped" if skip else "pending",
                "result": {},
                "session_id": None,
                "error": None,
            })

        config = {
            "persona_group_id": request.persona_group_id,
            "platform": request.platform,
            "brand_tone": request.brand_tone,
            "brief": request.brief,
            "market_source_text": request.market_source_text,
            "disabled_steps": request.disabled_steps,
        }
        return await self.repository.create(
            tenant_id=1,
            workflow_type=request.workflow_type,
            config=config,
            steps=steps,
        )

    async def start_async(self, workflow_id: int) -> str:
        ws = await self.repository.get(workflow_id)
        if not ws:
            raise ValueError("workflow session not found")
        task = await self.task_service.create_task(ws.tenant_id, "workflow", workflow_id)
        await self.repository.update_status(workflow_id, "running")
        asyncio.create_task(self._run_workflow(workflow_id, task.id))
        return task.id

    async def get(self, workflow_id: int) -> WorkflowSession | None:
        return await self.repository.get(workflow_id)

    async def list(self, tenant_id: int) -> list[WorkflowSession]:
        return await self.repository.list(tenant_id)

    async def complete_step(self, workflow_id: int, step_name: str, notes: str = "") -> WorkflowSession | None:
        ws = await self.repository.get(workflow_id)
        if not ws:
            return None
        step = next((s for s in ws.steps if s.name == step_name), None)
        if not step or step.status == "skipped":
            return None
        await self.repository.save_step(
            workflow_id, step_name, "completed",
            result={"notes": notes} if notes else {},
        )
        # 若所有非跳过步骤都已完成，更新工作流状态
        updated = await self.repository.get(workflow_id)
        if updated and all(s.status in ("completed", "skipped") for s in updated.steps):
            await self.repository.update_status(workflow_id, "completed")
            updated = await self.repository.get(workflow_id)
        return updated

    # ── 后台执行 ──────────────────────────────────────────────────────────────

    async def _run_workflow(self, workflow_id: int, task_id: str) -> None:
        channel = f"workflow:{workflow_id}"
        try:
            ws = await self.repository.get(workflow_id)
            if not ws:
                return

            prev_results: dict[str, Any] = {}
            enabled_steps = [s for s in ws.steps if s.status != "skipped"]

            for step in enabled_steps:
                await self.repository.update_current_step(workflow_id, step.name)
                await self.ws_manager.broadcast(channel, {
                    "type": "step_start",
                    "step": step.name,
                    "label": step.label,
                })
                try:
                    result, sub_session_id = await self._execute_step(step, ws.config, prev_results, ws.tenant_id)
                    prev_results[step.name] = result
                    await self.repository.save_step(
                        workflow_id, step.name, "completed", result, sub_session_id,
                    )
                    await self.ws_manager.broadcast(channel, {
                        "type": "step_done",
                        "step": step.name,
                        "session_id": sub_session_id,
                        "result": result,
                    })
                except Exception as exc:
                    logger.exception("workflow %d step %s failed", workflow_id, step.name)
                    await self.repository.save_step(
                        workflow_id, step.name, "failed", {}, None, str(exc),
                    )
                    await self.ws_manager.broadcast(channel, {
                        "type": "step_failed",
                        "step": step.name,
                        "error": str(exc),
                    })
                    if step.required:
                        await self.repository.update_status(workflow_id, "failed")
                        await self.task_service.update_task(task_id, status="failed", error=str(exc))
                        await self.ws_manager.broadcast(channel, {"type": "error", "message": str(exc)})
                        return

            await self.repository.update_current_step(workflow_id, None)
            await self.repository.update_status(workflow_id, "completed")
            await self.task_service.update_task(task_id, status="completed", progress=100)
            await self.ws_manager.broadcast(channel, {"type": "done"})

        except Exception as exc:
            logger.exception("workflow %d crashed", workflow_id)
            await self.repository.update_status(workflow_id, "failed")
            await self.task_service.update_task(task_id, status="failed", error=str(exc))
            await self.ws_manager.broadcast(channel, {"type": "error", "message": str(exc)})

    async def _execute_step(
        self,
        step: WorkflowStepRecord,
        config: dict[str, Any],
        prev: dict[str, Any],
        tenant_id: int = 1,
    ) -> tuple[dict[str, Any], int | None]:
        name = step.name
        if name == "market":
            return await self._run_market(config, tenant_id)
        if name == "workshop":
            return await self._run_workshop(config, prev, tenant_id)
        if name == "simulation":
            return await self._run_simulation(config, prev, tenant_id)
        if name == "sentiment_guard":
            return await self._run_sentiment_guard(config, prev, tenant_id)
        if name == "strategy_advisor":
            return await self._run_strategy_advisor(config, prev, tenant_id)
        raise ValueError(f"未知步骤: {name}")

    async def _run_market(self, config: dict[str, Any], tenant_id: int = 1) -> tuple[dict[str, Any], int | None]:
        from app.models.market import MarketGraphBuildRequest
        source_text = config.get("market_source_text", "").strip()
        if not source_text:
            source_text = f"品牌关键词：{config.get('brief', '')}"
        request = MarketGraphBuildRequest(
            name="工作流-市场分析",
            source_text=source_text,
        )
        graph = await self.market_service.build_graph(request)
        return {"graph_id": graph.id, "entity_count": len(graph.entities)}, graph.id

    async def _run_workshop(
        self, config: dict[str, Any], prev: dict[str, Any], tenant_id: int = 1,
    ) -> tuple[dict[str, Any], int | None]:
        from app.models.workshop import WorkshopCreateRequest
        market_graph_id = prev.get("market", {}).get("graph_id") if "market" in prev else None
        request = WorkshopCreateRequest(
            persona_group_id=config["persona_group_id"],
            platform=config["platform"],
            brand_tone=config["brand_tone"],
            brief=config.get("brief", ""),
            goal="完成营销内容创作",
            product="营销产品",
        )
        session = await self.workshop_service.create_session(request)
        task_id = await self.workshop_service.run_session_async(
            session.id, tenant_id, market_graph_id=market_graph_id,
        )
        task = await self._wait_task(task_id)
        result_data = task.result or {}
        return {"session_id": session.id, "task_id": task_id, **result_data}, session.id

    async def _run_simulation(
        self, config: dict[str, Any], prev: dict[str, Any], tenant_id: int = 1,
    ) -> tuple[dict[str, Any], int | None]:
        content_text = config.get("brief", "")
        workshop_prev = prev.get("workshop", {})
        if workshop_prev.get("final_content"):
            content_text = workshop_prev["final_content"]

        request = SimulationCreateRequest(
            persona_group_id=config["persona_group_id"],
            platform=config["platform"],
            content_text=content_text,
            config={"max_rounds": 5},
        )
        sim_session = await self.simulation_engine.create_session(request)
        task_id = await self.simulation_engine.start(sim_session.id)
        task = await self._wait_task(task_id)
        result_data = task.result or {}
        return {"session_id": sim_session.id, "task_id": task_id, **result_data}, sim_session.id

    async def _run_sentiment_guard(
        self, config: dict[str, Any], prev: dict[str, Any], tenant_id: int = 1,
    ) -> tuple[dict[str, Any], int | None]:
        from app.models.sentiment_guard import SentimentGuardRequest
        event_desc = (
            f"针对品牌内容「{config.get('brief', '')[:100]}」的传播风险预评估"
        )
        request = SentimentGuardRequest(
            mode="proactive",
            event_description=event_desc,
        )
        task_id, session_id = await self.sentiment_guard_service.run_async(request)
        task = await self._wait_task(task_id)
        result_data = task.result or {}
        return {"session_id": session_id, "task_id": task_id, **result_data}, session_id

    async def _run_strategy_advisor(
        self, config: dict[str, Any], prev: dict[str, Any], tenant_id: int = 1,
    ) -> tuple[dict[str, Any], int | None]:
        from app.models.strategy_advisor import StrategyAdvisorRequest
        context_parts = []
        if "workshop" in prev:
            context_parts.append(f"内容工坊完成，session_id={prev['workshop'].get('session_id')}")
        if "simulation" in prev:
            context_parts.append(f"沙盘推演完成，session_id={prev['simulation'].get('session_id')}")
        context_info = "；".join(context_parts) if context_parts else ""

        request = StrategyAdvisorRequest(
            question=f"如何优化「{config.get('brief', '')[:80]}」这个营销内容的传播效果？",
            context_info=context_info,
        )
        task_id, session_id = await self.strategy_advisor_service.run_async(request)
        task = await self._wait_task(task_id)
        result_data = task.result or {}
        return {"session_id": session_id, "task_id": task_id, **result_data}, session_id

    async def _wait_task(self, task_id: str, timeout: int = 300) -> Any:
        for _ in range(timeout * 2):
            task = await self.task_service.get_task(task_id)
            if task and task.status == "completed":
                return task
            if task and task.status == "failed":
                raise RuntimeError(task.error or "task failed")
            await asyncio.sleep(0.5)
        raise TimeoutError(f"task {task_id} timeout after {timeout}s")
