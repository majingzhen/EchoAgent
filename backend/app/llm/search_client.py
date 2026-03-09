from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchClient:
    """Web search client supporting anspire, bing, serper, and duckduckgo providers."""

    def __init__(self, provider: str, api_key: str, max_results: int = 5) -> None:
        self.provider = provider
        self.api_key = api_key
        self.max_results = max_results

    async def search(self, query: str) -> list[SearchResult]:
        provider = self.provider
        if provider == "anspire":
            return await self._search_anspire(query)
        elif provider == "bing":
            return await self._search_bing(query)
        elif provider == "serper":
            return await self._search_serper(query)
        elif provider == "duckduckgo":
            return await self._search_duckduckgo(query)
        else:
            logger.warning("search provider '%s' unknown, returning empty results", provider)
            return []

    async def _search_anspire(self, query: str) -> list[SearchResult]:
        import httpx
        url = "https://plugin.anspire.cn/api/ntsearch/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "Accept": "*/*",
        }
        params = {"query": query, "top_k": str(self.max_results)}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
        data = resp.json()
        results = []
        for item in (data.get("results") or []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
            ))
        return results[:self.max_results]

    async def _search_bing(self, query: str) -> list[SearchResult]:
        import httpx
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": self.max_results, "mkt": "zh-CN", "setLang": "zh-hans"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
        data = resp.json()
        results = []
        for item in (data.get("webPages", {}).get("value") or []):
            results.append(SearchResult(
                title=item.get("name", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
            ))
        return results[:self.max_results]

    async def _search_serper(self, query: str) -> list[SearchResult]:
        import httpx
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        body = {"q": query, "num": self.max_results, "gl": "cn", "hl": "zh-cn"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
        data = resp.json()
        results = []
        for item in (data.get("organic") or []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
            ))
        return results[:self.max_results]

    async def _search_duckduckgo(self, query: str) -> list[SearchResult]:
        import asyncio
        try:
            from duckduckgo_search import DDGS

            def _sync_search() -> list[SearchResult]:
                with DDGS() as ddgs:
                    raw = ddgs.text(query, max_results=self.max_results, region="cn-zh")
                return [
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                    )
                    for r in (raw or [])
                ]

            return await asyncio.to_thread(_sync_search)
        except ImportError:
            logger.warning("duckduckgo_search not installed, returning empty results")
            return []
        except Exception as e:
            logger.warning("duckduckgo search failed: %s", e)
            return []


    async def _search_bing(self, query: str) -> list[SearchResult]:
        import httpx
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": self.max_results, "mkt": "zh-CN", "setLang": "zh-hans"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
        data = resp.json()
        results = []
        for item in (data.get("webPages", {}).get("value") or []):
            results.append(SearchResult(
                title=item.get("name", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
            ))
        return results[:self.max_results]

    async def _search_serper(self, query: str) -> list[SearchResult]:
        import httpx
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        body = {"q": query, "num": self.max_results, "gl": "cn", "hl": "zh-cn"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
        data = resp.json()
        results = []
        for item in (data.get("organic") or []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
            ))
        return results[:self.max_results]

    async def _search_duckduckgo(self, query: str) -> list[SearchResult]:
        import asyncio
        try:
            from duckduckgo_search import DDGS

            def _sync_search() -> list[SearchResult]:
                with DDGS() as ddgs:
                    raw = ddgs.text(query, max_results=self.max_results, region="cn-zh")
                return [
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                    )
                    for r in (raw or [])
                ]

            return await asyncio.to_thread(_sync_search)
        except ImportError:
            logger.warning("duckduckgo_search not installed, returning empty results")
            return []
        except Exception as e:
            logger.warning("duckduckgo search failed: %s", e)
            return []
