from __future__ import annotations

import json
from typing import Any


class MemoryStore:
    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._hashes: dict[str, dict[str, str]] = {}

    async def incr(self, key: str) -> int:
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]

    async def hset_json(self, key: str, mapping: dict[str, Any]) -> None:
        payload = {k: json.dumps(v, ensure_ascii=False, default=str) for k, v in mapping.items()}
        self._hashes[key] = payload

    async def hgetall_json(self, key: str) -> dict[str, Any]:
        raw = self._hashes.get(key)
        if not raw:
            return {}
        parsed: dict[str, Any] = {}
        for k, v in raw.items():
            try:
                parsed[k] = json.loads(v)
            except json.JSONDecodeError:
                parsed[k] = v
        return parsed

    async def close(self) -> None:
        self._counters.clear()
        self._hashes.clear()
