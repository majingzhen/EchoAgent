from __future__ import annotations

import logging
from typing import Any

from app.llm.client import LLMClient
from app.llm.search_client import SearchClient, SearchResult
from app.models.search import SearchEnhanceResponse

logger = logging.getLogger(__name__)

_MODULE_SYSTEM_PROMPTS: dict[str, str] = {
    "workshop": (
        "你是内容营销专家。根据以下网络搜索结果，提炼出可用于内容创作的关键洞察，"
        "包括热门话题角度、消费者痛点、竞品内容风格等。"
    ),
    "market": (
        "你是市场分析师。根据以下搜索结果，提炼市场规模、增长趋势、主要竞争者和"
        "消费者偏好等关键市场洞察。"
    ),
    "persona": (
        "你是用户研究专家。根据以下搜索结果，提炼目标人群的典型特征、消费行为、"
        "痛点和诉求，用于丰富画像描述。"
    ),
    "general": (
        "你是信息分析师。请从以下搜索结果中提炼关键信息，去除噪音，归纳核心事实和趋势。"
    ),
}

_MODULE_SUGGESTED_USE: dict[str, str] = {
    "workshop": "可将这些洞察作为内容工坊的 Brief 背景，或注入为市场洞察增强创作效果。",
    "market": "可将关键词和趋势输入市场智脑，构建更完整的市场知识图谱。",
    "persona": "可将人群特征复制到画像工厂的描述字段，生成更贴近真实的画像组。",
    "general": "可将摘要内容作为焦点小组话题背景或策略参谋的上下文输入。",
}


class SearchService:
    def __init__(self, search_client: SearchClient, llm_client: LLMClient) -> None:
        self.search_client = search_client
        self.llm_client = llm_client

    async def enhance(self, query: str, module: str = "general", max_results: int = 5) -> SearchEnhanceResponse:
        """Search the web and summarize results into structured insights."""
        self.search_client.max_results = max(1, min(max_results, 10))

        try:
            results = await self.search_client.search(query)
        except Exception as e:
            logger.warning("web search failed: %s", e)
            results = []

        if not results:
            return SearchEnhanceResponse(
                query=query,
                module=module,
                results=[],
                summary="未获取到搜索结果，请检查搜索 API 配置或稍后重试。",
                insights=["暂无可用数据"],
                suggested_use=_MODULE_SUGGESTED_USE.get(module, ""),
            )

        transcript = "\n\n".join(
            f"[{i+1}] {r.title}\n{r.snippet}\n来源: {r.url}"
            for i, r in enumerate(results)
        )

        system_prompt = _MODULE_SYSTEM_PROMPTS.get(module, _MODULE_SYSTEM_PROMPTS["general"])
        user_prompt = (
            f"搜索关键词：{query}\n\n"
            f"搜索结果：\n{transcript}\n\n"
            "请输出 JSON：\n"
            '{"summary": "2-3句话的整体摘要", '
            '"insights": ["洞察1", "洞察2", "洞察3", "洞察4", "洞察5"]}'
        )

        try:
            payload = await self.llm_client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                light=True,
                temperature=0.3,
            )
            summary = str(payload.get("summary", "")) if isinstance(payload, dict) else ""
            raw_insights = payload.get("insights", []) if isinstance(payload, dict) else []
            insights = [str(x) for x in raw_insights if str(x).strip()][:8]
        except Exception as e:
            logger.warning("search summarize LLM failed: %s", e)
            summary = "AI 摘要生成失败，以下为原始搜索片段。"
            insights = [r.snippet[:120] for r in results[:5] if r.snippet]

        from app.models.search import SearchResult as SR
        return SearchEnhanceResponse(
            query=query,
            module=module,
            results=[SR(title=r.title, url=r.url, snippet=r.snippet) for r in results],
            summary=summary,
            insights=insights,
            suggested_use=_MODULE_SUGGESTED_USE.get(module, ""),
        )
