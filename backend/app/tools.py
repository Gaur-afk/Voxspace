import random

from app.scene import SceneGraph

CANVAS_WIDTH = 900
CANVAS_HEIGHT = 600
DEFAULT_SIZE = 80
DEFAULT_FILL = "#4287f5"

# Tool schemas passed to the LLM. Target objects are referenced by `id` —
# the LLM picks the id itself from the scene state given as context, since
# there's no dedicated resolver yet (that's Phase 4). This is why Phase 3's
# checkpoint only covers unambiguous commands.
TOOLS = [
    {
        "name": "create_shape",
        "description": "Create a new shape in the scene. Position and size are optional — omit them to let the system place the shape with a sensible default.",
        "input_schema": {
            "type": "object",
            "properties": {
                "shape_type": {"type": "string", "enum": ["circle", "rectangle"]},
                "fill": {"type": "string", "description": "CSS color name or hex code, e.g. 'red' or '#ff0000'"},
                "x": {"type": "number", "description": "Top-left x of the bounding box"},
                "y": {"type": "number", "description": "Top-left y of the bounding box"},
                "w": {"type": "number"},
                "h": {"type": "number"},
            },
            "required": ["shape_type"],
        },
    },
    {
        "name": "update_shape",
        "description": "Change the color, size, or rotation of an existing shape. Provide only the fields that should change. To resize, use the object's current w/h (given in the scene state) to compute new absolute values.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "id of the target object from the current scene state"},
                "fill": {"type": "string"},
                "w": {"type": "number"},
                "h": {"type": "number"},
                "rotation": {"type": "number"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "move_shape",
        "description": f"Move an existing shape to an absolute position. The canvas is {CANVAS_WIDTH}x{CANVAS_HEIGHT} px, origin top-left, so translate relative phrases ('top left', 'center') into coordinates within those bounds.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "id of the target object from the current scene state"},
                "x": {"type": "number"},
                "y": {"type": "number"},
            },
            "required": ["id", "x", "y"],
        },
    },
    {
        "name": "delete_shape",
        "description": "Remove a shape from the scene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "id of the target object from the current scene state"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "select_shape",
        "description": "Mark a shape as selected in the UI (highlights it). Does not change any of its properties.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "id of the target object from the current scene state"},
            },
            "required": ["id"],
        },
    },
]


def execute_tool(name: str, arguments: dict, scene: SceneGraph) -> dict:
    if name == "create_shape":
        obj = scene.create(
            type=arguments["shape_type"],
            x=arguments.get("x", random.uniform(50, CANVAS_WIDTH - DEFAULT_SIZE - 50)),
            y=arguments.get("y", random.uniform(50, CANVAS_HEIGHT - DEFAULT_SIZE - 50)),
            w=arguments.get("w", DEFAULT_SIZE),
            h=arguments.get("h", DEFAULT_SIZE),
            fill=arguments.get("fill", DEFAULT_FILL),
        )
        return {"status": "ok", "object": obj.model_dump()}

    if name == "update_shape":
        fields = {k: v for k, v in arguments.items() if k != "id"}
        obj = scene.update(arguments["id"], fields)
        if obj is None:
            return {"status": "error", "message": f"no object with id {arguments['id']}"}
        return {"status": "ok", "object": obj.model_dump()}

    if name == "move_shape":
        obj = scene.update(arguments["id"], {"x": arguments["x"], "y": arguments["y"]})
        if obj is None:
            return {"status": "error", "message": f"no object with id {arguments['id']}"}
        return {"status": "ok", "object": obj.model_dump()}

    if name == "delete_shape":
        ok = scene.delete(arguments["id"])
        if not ok:
            return {"status": "error", "message": f"no object with id {arguments['id']}"}
        return {"status": "ok"}

    if name == "select_shape":
        return {"status": "ok", "selected_id": arguments["id"]}

    return {"status": "error", "message": f"unknown tool {name}"}
