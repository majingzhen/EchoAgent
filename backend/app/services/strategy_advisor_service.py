from __future__ import annotations

import asyncio
from typing import Any

from app.llm.client import LLMClient
from app.models.strategy_advisor import StrategyAdvisorRequest, StrategyAdvisorSession
from app.repositories.strategy_advisor_repository import StrategyAdvisorRepository
from app.services.task_service import TaskService
from app.ws.manager import WSConnectionManager

THINKING_MODELS = {
    "first_principles": {
        "name": "第一性原理",
        "approach": "剥离表象回到本质，从基本事实出发推理",
        "question": "这个问题的本质是什么？哪些是不可简化的基本事实？",
    },
    "game_theory": {
        "name": "博弈论",
        "approach": "分析各方利益和策略互动",
        "question": "各方的利益是什么？他们会怎么反应？纳什均衡在哪？",
    },
    "systems_thinking": {
        "name": "系统思维",
        "approach": "看整体结构和反馈回路",
        "question": "这个系统的关键反馈回路是什么？改变一处会如何影响全局？",
    },
    "inversion": {
        "name": "逆向思维",
        "approach": "反过来想，怎样才能失败",
        "question": "要让这件事彻底失败，需要怎么做？避免这些就是正确方向。",
    },
    "customer_lens": {
        "name": "用户视角",
        "approach": "站在客户角度思考",
        "question": "如果我是客户，我真正需要什么？我会怎么选择？",
    },
}


class StrategyAdvisorService:
    def __init__(
        self,
        repository: StrategyAdvisorRepository,
        llm_client: LLMClient,
        ws_manager: WSConnectionManager,
        task_service: TaskService,
    ) -> None:
        self.repository = repository
        self.llm_client = llm_client
        self.ws_manager = ws_manager
        self.task_service = task_service

    async def run_async(self, request: StrategyAdvisorRequest) -> tuple[str, int]:
        session = await self.repository.create_session(
            tenant_id=1,
            question=request.question,
            context_info=request.context_info,
        )
        task = await self.task_service.create_task(1, "strategy_advisor", session.id)
        asyncio.create_task(self._run_analysis(request, session, task.id))
        return task.id, session.id

    async def get_session(self, session_id: int) -> StrategyAdvisorSession | None:
        return await self.repository.get_session(session_id)

    async def list_sessions(self, tenant_id: int) -> list[StrategyAdvisorSession]:
        return await self.repository.list_sessions(tenant_id)

    # ── 后台分析流程 ──────────────────────────────────────────────────────────

    async def _run_analysis(
        self,
        request: StrategyAdvisorRequest,
        session: StrategyAdvisorSession,
        task_id: str,
    ) -> None:
        channel = f"strategy-advisor:{session.id}"
        payload: dict[str, Any] = {"question": request.question}
        try:
            # Phase 1: 5个模型并发独立分析，每完成一个立即推送
            await self.ws_manager.broadcast(channel, {"type": "progress", "step": "phase1", "message": "5个思维模型并发分析中..."})
            model_analyses: list[dict[str, Any]] = []
            semaphore = asyncio.Semaphore(5)

            async def analyze_one(model_key: str, model_cfg: dict[str, Any]) -> None:
                async with semaphore:
                    result = await self._single_model_analyze(request, model_key, model_cfg)
                model_analyses.append(result)
                await self.ws_manager.broadcast(channel, {
                    "type": "model_done",
                    "model_key": model_key,
                    "model_name": model_cfg["name"],
                    "data": result,
                })

            await asyncio.gather(*[
                analyze_one(key, cfg) for key, cfg in THINKING_MODELS.items()
            ])
            payload["model_analyses"] = model_analyses
            await self.task_service.update_task(task_id, progress=50, message="独立分析完成")

            # Phase 2: 找分歧最大的两个模型，进行交叉辩论
            await self.ws_manager.broadcast(channel, {"type": "progress", "step": "phase2", "message": "识别分歧，交叉质疑中..."})
            debate = await self._cross_debate(request, model_analyses)
            payload["debate"] = debate
            await self.ws_manager.broadcast(channel, {"type": "step_done", "step": "debate", "data": debate})
            await self.task_service.update_task(task_id, progress=75, message="交叉辩论完成")

            # Phase 3: 综合报告
            await self.ws_manager.broadcast(channel, {"type": "progress", "step": "phase3", "message": "生成综合报告..."})
            synthesis = await self._synthesize(request, model_analyses, debate)
            payload.update(synthesis)
            await self.repository.update_session(session.id, "completed", payload)
            await self.ws_manager.broadcast(channel, {"type": "done", "data": payload})
            await self.task_service.update_task(
                task_id, status="completed", progress=100, message="分析完成",
                result={"session_id": session.id},
            )
        except Exception as exc:
            await self.repository.update_session(session.id, "failed", payload)
            await self.ws_manager.broadcast(channel, {"type": "error", "message": str(exc)})
            await self.task_service.update_task(task_id, status="failed", error=str(exc))

    async def _single_model_analyze(
        self,
        request: StrategyAdvisorRequest,
        model_key: str,
        model_cfg: dict[str, Any],
    ) -> dict[str, Any]:
        ctx = f"\n背景信息：{request.context_info}" if request.context_info else ""
        system_prompt = (
            f"你是一位专精于{model_cfg['name']}的战略分析师。"
            f"你的分析方法：{model_cfg['approach']}"
        )
        user_prompt = (
            f"业务问题：{request.question}{ctx}\n"
            f"请用{model_cfg['name']}回答：{model_cfg['question']}\n"
            "输出 JSON：{\"conclusion\":\"\",\"reasoning\":\"\",\"key_assumptions\":[]}"
        )
        result = await self.llm_client.generate_json(
            system_prompt=system_prompt, user_prompt=user_prompt, light=True, temperature=0.5
        )
        if not isinstance(result, dict):
            raise RuntimeError(f"{model_cfg['name']} 模型分析返回格式错误")
        return {
            "model_key": model_key,
            "model_name": model_cfg["name"],
            "conclusion": str(result.get("conclusion", "")),
            "reasoning": str(result.get("reasoning", "")),
            "key_assumptions": result.get("key_assumptions", [])[:5],
        }

    async def _cross_debate(
        self,
        request: StrategyAdvisorRequest,
        analyses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if len(analyses) < 2:
            return {"skipped": True, "reason": "分析数量不足"}

        # 简单策略：取第一个和最后一个分析进行辩论（通常差异较大）
        sorted_analyses = sorted(analyses, key=lambda a: a.get("model_key", ""))
        model_a = sorted_analyses[0]
        model_b = sorted_analyses[-1]

        system_prompt = "你是中立的战略辩论评审，负责主持两种思维模型的观点碰撞并给出评判。"
        user_prompt = (
            f"问题：{request.question}\n"
            f"{model_a['model_name']}观点：{model_a['conclusion']}\n"
            f"推理：{model_a['reasoning']}\n\n"
            f"{model_b['model_name']}观点：{model_b['conclusion']}\n"
            f"推理：{model_b['reasoning']}\n\n"
            "请识别核心分歧，模拟双方争辩，给出评审结论。\n"
            "输出 JSON：{\"core_disagreement\":\"\",\"model_a_argument\":\"\",\"model_b_argument\":\"\","
            "\"judge_verdict\":\"\",\"winner\":\"\"}"
        )
        result = await self.llm_client.generate_json(
            system_prompt=system_prompt, user_prompt=user_prompt, light=False, temperature=0.4
        )
        if not isinstance(result, dict):
            return {"skipped": True, "reason": "辩论生成失败"}
        return {
            "model_a": model_a["model_name"],
            "model_b": model_b["model_name"],
            "core_disagreement": str(result.get("core_disagreement", "")),
            "model_a_argument": str(result.get("model_a_argument", "")),
            "model_b_argument": str(result.get("model_b_argument", "")),
            "judge_verdict": str(result.get("judge_verdict", "")),
            "winner": str(result.get("winner", "平局")),
        }

    async def _synthesize(
        self,
        request: StrategyAdvisorRequest,
        analyses: list[dict[str, Any]],
        debate: dict[str, Any],
    ) -> dict[str, Any]:
        analyses_text = "\n".join([
            f"- {a['model_name']}：{a['conclusion']}" for a in analyses
        ])
        debate_text = (
            f"核心分歧：{debate.get('core_disagreement', '')}，评审结论：{debate.get('judge_verdict', '')}"
            if not debate.get("skipped") else ""
        )
        system_prompt = "你是综合战略顾问，善于整合多种分析视角形成平衡建议。"
        user_prompt = (
            f"问题：{request.question}\n"
            f"各模型分析：\n{analyses_text}\n"
            f"{debate_text}\n"
            "请综合输出 JSON：{\"consensus\":[],\"divergences\":[],\"key_assumptions\":[],\"blind_spots\":[],\"recommendation\":\"\"}"
        )
        result = await self.llm_client.generate_json(
            system_prompt=system_prompt, user_prompt=user_prompt, light=False, temperature=0.3
        )
        if not isinstance(result, dict):
            return {
                "consensus": [], "divergences": [], "key_assumptions": [],
                "blind_spots": [], "recommendation": "综合报告生成失败，请重试"
            }
        return {
            "consensus": result.get("consensus", [])[:6],
            "divergences": result.get("divergences", [])[:6],
            "key_assumptions": result.get("key_assumptions", [])[:6],
            "blind_spots": result.get("blind_spots", [])[:4],
            "recommendation": str(result.get("recommendation", "")),
        }
