from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.deps import ws_manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws/sentiment-guard/{session_id}")
async def sentiment_guard_ws(websocket: WebSocket, session_id: int) -> None:
    channel = f"sentiment-guard:{session_id}"
    await ws_manager.connect(channel, websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)


@router.websocket("/ws/strategy-advisor/{session_id}")
async def strategy_advisor_ws(websocket: WebSocket, session_id: int) -> None:
    channel = f"strategy-advisor:{session_id}"
    await ws_manager.connect(channel, websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)


@router.websocket("/ws/persona/{group_id}")
async def persona_gen_ws(websocket: WebSocket, group_id: int) -> None:
    channel = f"persona-gen:{group_id}"
    await ws_manager.connect(channel, websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)


@router.websocket("/ws/simulation/{session_id}")
async def simulation_ws(websocket: WebSocket, session_id: int) -> None:
    channel = f"simulation:{session_id}"
    await ws_manager.connect(channel, websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)


@router.websocket("/ws/focus-group/{session_id}")
async def focus_group_ws(websocket: WebSocket, session_id: int) -> None:
    channel = f"focus-group:{session_id}"
    await ws_manager.connect(channel, websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)


@router.websocket("/ws/workshop/{session_id}")
async def workshop_ws(websocket: WebSocket, session_id: int) -> None:
    channel = f"workshop:{session_id}"
    await ws_manager.connect(channel, websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)


@router.websocket("/ws/workflow/{workflow_id}")
async def workflow_ws(websocket: WebSocket, workflow_id: int) -> None:
    channel = f"workflow:{workflow_id}"
    await ws_manager.connect(channel, websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)
