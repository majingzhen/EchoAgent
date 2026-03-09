from __future__ import annotations

import re
from collections import Counter
from typing import Any

from fastapi import UploadFile

from app.llm.client import LLMClient
from app.models.market import MarketGraph, MarketGraphBuildRequest, MarketReport
from app.repositories.market_repository import MarketRepository
from app.utils.file_utils import decode_file, extract_pdf_text


class MarketService:
    def __init__(self, market_repository: MarketRepository, llm_client: LLMClient) -> None:
        self.market_repository = market_repository
        self.llm_client = llm_client

    async def build_graph(self, request: MarketGraphBuildRequest) -> MarketGraph:
        entities = self._extract_entities(request.source_text)
        relations = self._extract_relations(request.source_text, entities)
        graph = await self.market_repository.create_graph(
            tenant_id=1,
            name=request.name,
            source_text=request.source_text,
            entities=entities,
            relations=relations,
        )
        return graph

    async def build_graph_from_upload(self, tenant_id: int, name: str, file: UploadFile) -> MarketGraph:
        raw = await file.read()
        filename = (file.filename or "").lower()
        if filename.endswith(".pdf") or raw[:4] == b"%PDF":
            text = extract_pdf_text(raw)
        else:
            text = decode_file(raw)
        request = MarketGraphBuildRequest(name=name, source_text=text)
        return await self.build_graph(request)

    async def get_graph(self, graph_id: int) -> MarketGraph | None:
        return await self.market_repository.get_graph(graph_id)

    async def get_report(self, graph_id: int) -> MarketReport | None:
        report = await self.market_repository.get_report(graph_id)
        if report:
            return report
        graph = await self.market_repository.get_graph(graph_id)
        if not graph:
            return None
        payload = await self._build_report_with_llm(graph)
        await self.market_repository.save_report(graph_id, payload)
        return MarketReport(**payload)

    def _extract_entities(self, text: str) -> list[dict[str, Any]]:
        tokens = re.findall(r"[\u4e00-\u9fff]{2,8}|[A-Za-z][A-Za-z0-9_-]{2,}", text)
        stopwords = {
            "我们",
            "你们",
            "他们",
            "用户",
            "产品",
            "平台",
            "内容",
            "这个",
            "那个",
            "以及",
            "进行",
            "通过",
            "可以",
        }
        filtered = [tok for tok in tokens if tok not in stopwords]
        counter = Counter(filtered)
        if not counter:
            counter = Counter(["市场反馈", "价格", "竞品"])

        max_count = max(counter.values())
        entities: list[dict[str, Any]] = []
        for idx, (name, count) in enumerate(counter.most_common(18), start=1):
            entities.append(
                {
                    "entity_id": f"E{idx}",
                    "name": name,
                    "entity_type": self._classify_entity(name),
                    "score": round(0.25 + count / max_count * 0.75, 2),
                }
            )
        return entities

    def _extract_relations(self, text: str, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(entities) < 2:
            return []

        entity_map = {entity["name"]: entity["entity_id"] for entity in entities}
        pair_counter: Counter[tuple[str, str]] = Counter()
        sentences = [s.strip() for s in re.split(r"[。！？!\n]", text) if s.strip()]
        for sentence in sentences:
            hits = [name for name in entity_map.keys() if name in sentence]
            unique_hits = list(dict.fromkeys(hits))
            for idx in range(len(unique_hits) - 1):
                pair = (unique_hits[idx], unique_hits[idx + 1])
                pair_counter[pair] += 1

        if not pair_counter:
            first = entities[0]["name"]
            for other in entities[1:4]:
                pair_counter[(first, other["name"])] += 1

        max_count = max(pair_counter.values())
        relations: list[dict[str, Any]] = []
        for (source_name, target_name), count in pair_counter.most_common(30):
            relations.append(
                {
                    "source": entity_map[source_name],
                    "target": entity_map[target_name],
                    "relation_type": self._classify_relation(source_name, target_name),
                    "weight": round(0.2 + count / max_count * 0.8, 2),
                }
            )
        return relations

    def _build_report_payload(self, graph: MarketGraph) -> dict[str, Any]:
        brands = [item.name for item in graph.entities if item.entity_type == "brand"]
        attributes = [item.name for item in graph.entities if item.entity_type == "attribute"]

        top_entities = ", ".join([item.name for item in graph.entities[:4]])
        summary = f"图谱显示高频关注点集中在 {top_entities}，竞品讨论与价格话题耦合明显。"

        key_insights = [
            f"高频竞品：{', '.join(brands[:3]) or '未显著提及'}",
            f"强关联属性：{', '.join(attributes[:3]) or '价格/口碑'}",
            f"关系边数量 {len(graph.relations)}，说明讨论扩散路径已形成。",
        ]
        opportunities = [
            "在内容首屏优先回应价格与体验对比，提升停留与转评。",
            "将高频属性拆分成系列化选题，形成持续内容节奏。",
        ]
        risks = [
            "竞品对比语义过强时，易引发品牌对立评论。",
            "价格表达不清晰会放大负向口碑扩散。",
        ]
        actions = [
            "工坊创作时注入市场高频实体作为选题锚点。",
            "A/B 版本至少保留一个理性证据链方向。",
            "评论区准备 FAQ，优先处理价格与功效边界问题。",
        ]
        return {
            "graph_id": graph.id,
            "summary": summary,
            "competitor_landscape": brands[:5],
            "key_insights": key_insights,
            "opportunities": opportunities,
            "risks": risks,
            "recommended_actions": actions,
        }

    async def _build_report_with_llm(self, graph: MarketGraph) -> dict[str, Any]:
        entity_summary = [
            f"{e.name}（{e.entity_type}，热度{e.score}）"
            for e in graph.entities[:12]
        ]
        top_entities_text = "；".join(entity_summary)
        source_preview = (graph.source_text or "")[:800]

        system_prompt = "你是资深市场竞品分析师。请基于实体图谱数据输出结构化竞品分析报告，仅返回 JSON。"
        user_prompt = (
            f"图谱名称：{graph.name}\n"
            f"高频实体（{len(graph.entities)} 个）：{top_entities_text}\n"
            f"关系条数：{len(graph.relations)}\n"
            f"原始文本摘要：{source_preview}\n"
            "输出 JSON：{"
            '"summary":"总体态势1-2句",'
            '"competitor_landscape":["竞品1","竞品2"],'
            '"key_insights":["洞察1","洞察2","洞察3"],'
            '"opportunities":["机会1","机会2"],'
            '"risks":["风险1","风险2"],'
            '"recommended_actions":["行动1","行动2","行动3"]'
            "}"
        )
        try:
            payload = await self.llm_client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4,
            )
            if not isinstance(payload, dict):
                raise ValueError("not dict")
            return {
                "graph_id": graph.id,
                "summary": str(payload.get("summary") or ""),
                "competitor_landscape": self._to_str_list(payload.get("competitor_landscape"), []),
                "key_insights": self._to_str_list(payload.get("key_insights"), []),
                "opportunities": self._to_str_list(payload.get("opportunities"), []),
                "risks": self._to_str_list(payload.get("risks"), []),
                "recommended_actions": self._to_str_list(payload.get("recommended_actions"), []),
            }
        except Exception:
            return self._build_report_payload(graph)

    def _to_str_list(self, value: object, default: list[str]) -> list[str]:
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            if cleaned:
                return cleaned
        return default

    def _classify_entity(self, name: str) -> str:
        if any(key in name for key in ["品牌", "竞品", "官方", "旗舰", "公司"]):
            return "brand"
        if any(key in name for key in ["价格", "口碑", "成分", "功效", "渠道", "售后"]):
            return "attribute"
        return "topic"

    def _classify_relation(self, source_name: str, target_name: str) -> str:
        combo = source_name + target_name
        if "竞品" in combo or "品牌" in combo:
            return "competition"
        if "价格" in combo or "口碑" in combo:
            return "impact"
        return "association"

