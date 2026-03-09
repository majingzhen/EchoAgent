from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class WSConnectionManager:
    def __init__(self) -> None:
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._channels[channel].add(websocket)

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        if channel not in self._channels:
            return
        self._channels[channel].discard(websocket)
        if not self._channels[channel]:
            self._channels.pop(channel, None)

    async def broadcast(self, channel: str, payload: dict[str, Any]) -> None:
        if channel not in self._channels:
            return
        stale_connections: list[WebSocket] = []
        for ws in self._channels[channel]:
            try:
                await ws.send_json(payload)
            except Exception:
                stale_connections.append(ws)
        for ws in stale_connections:
            self.disconnect(channel, ws)

