from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.scene import SceneGraph

app = FastAPI(title="VoxSpace Backend")
scene = SceneGraph()
connections: set[WebSocket] = set()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def broadcast_scene_state() -> None:
    payload = {"type": "scene_state", "objects": [obj.model_dump() for obj in scene.list()]}
    for ws in connections:
        await ws.send_json(payload)


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
