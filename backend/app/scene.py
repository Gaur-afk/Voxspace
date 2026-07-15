from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel


class SceneObject(BaseModel):
    id: int
    type: Literal["circle", "rectangle"]
    x: float
    y: float
    w: float
    h: float
    rotation: float = 0
    fill: str = "#4287f5"
    z_index: int
    created_at: str


class SceneGraph:
    """In-memory, single-process store. The one source of truth the
    renderer and (later) the agent loop both read/mutate through."""

    def __init__(self) -> None:
        self._objects: dict[int, SceneObject] = {}
        self._next_id = 1

    def list(self) -> list[SceneObject]:
        return sorted(self._objects.values(), key=lambda obj: obj.z_index)

    def create(self, type: Literal["circle", "rectangle"], x: float, y: float, w: float, h: float, fill: str) -> SceneObject:
        obj_id = self._next_id
        self._next_id += 1
        obj = SceneObject(
            id=obj_id,
            type=type,
            x=x,
            y=y,
            w=w,
            h=h,
            fill=fill,
            z_index=obj_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._objects[obj_id] = obj
        return obj

    def update(self, obj_id: int, fields: dict) -> SceneObject | None:
        obj = self._objects.get(obj_id)
        if obj is None:
            return None
        updated = obj.model_copy(update=fields)
        self._objects[obj_id] = updated
        return updated

    def delete(self, obj_id: int) -> bool:
        return self._objects.pop(obj_id, None) is not None
