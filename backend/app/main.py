from fastapi import FastAPI, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.agent import (
    PROVIDER_NAMES,
    get_current_provider_name,
    run_agent_turn,
    set_current_provider_name,
)
from app.scene import SceneGraph
from app.stt import transcribe

app = FastAPI(title="VoxSpace Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
scene = SceneGraph()
connections: set[WebSocket] = set()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile) -> dict[str, str]:
    audio_bytes = await audio.read()
    return {"text": transcribe(audio_bytes)}


async def broadcast_scene_state() -> None:
    payload = {"type": "scene_state", "objects": [obj.model_dump() for obj in scene.list()]}
    for ws in connections:
        await ws.send_json(payload)


@app.post("/agent")
async def agent_turn(payload: dict) -> dict:
    executed, message = run_agent_turn(payload["utterance"], scene)
    await broadcast_scene_state()
    return {"executed": executed, "message": message}


@app.get("/provider")
async def get_provider_setting() -> dict:
    return {"provider": get_current_provider_name(), "options": list(PROVIDER_NAMES)}


@app.post("/provider")
async def set_provider_setting(payload: dict) -> dict[str, str]:
    try:
        set_current_provider_name(payload["provider"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"provider": get_current_provider_name()}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    connections.add(websocket)
    try:
        await broadcast_scene_state()
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "create_object":
                payload = message["payload"]
                scene.create(
                    type=payload["type"],
                    x=payload["x"],
                    y=payload["y"],
                    w=payload["w"],
                    h=payload["h"],
                    fill=payload["fill"],
                )
            elif msg_type == "update_object":
                scene.update(message["id"], message["payload"])
            elif msg_type == "delete_object":
                scene.delete(message["id"])

            await broadcast_scene_state()
    except WebSocketDisconnect:
        connections.discard(websocket)
