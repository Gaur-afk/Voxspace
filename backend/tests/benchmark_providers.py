"""Side-by-side accuracy/latency benchmark for Phase 3b — run with:
    python tests/benchmark_providers.py
from the backend/ directory (voxspace conda env active).
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import SYSTEM_PROMPT
from app.providers import AnthropicProvider, OllamaProvider
from app.scene import SceneGraph
from app.tools import TOOLS


def make_scene(seed_objects: list[dict]) -> SceneGraph:
    scene = SceneGraph()
    for obj in seed_objects:
        scene.create(**obj)
    return scene


CASES = [
    {
        "name": "create circle",
        "seed": [],
        "utterance": "add a blue circle",
        "expect_tool": "create_shape",
        "check": lambda args, scene: args.get("shape_type") == "circle",
    },
    {
        "name": "create rectangle",
        "seed": [],
        "utterance": "add a red rectangle",
        "expect_tool": "create_shape",
        "check": lambda args, scene: args.get("shape_type") == "rectangle",
    },
    {
        "name": "update (resize)",
        "seed": [{"type": "rectangle", "x": 100, "y": 100, "w": 80, "h": 80, "fill": "gray"}],
        "utterance": "make the rectangle bigger",
        "expect_tool": "update_shape",
        "check": lambda args, scene: args.get("id") == 1 and (args.get("w", 80) > 80 or args.get("h", 80) > 80),
    },
    {
        "name": "move",
        "seed": [{"type": "circle", "x": 400, "y": 300, "w": 80, "h": 80, "fill": "blue"}],
        "utterance": "move the circle to the top left",
        "expect_tool": "move_shape",
        "check": lambda args, scene: args.get("id") == 1 and args.get("x", 999) < 300 and args.get("y", 999) < 300,
    },
    {
        "name": "select",
        "seed": [{"type": "circle", "x": 100, "y": 100, "w": 80, "h": 80, "fill": "blue"}],
        "utterance": "select the circle",
        "expect_tool": "select_shape",
        "check": lambda args, scene: args.get("id") == 1,
    },
    {
        "name": "delete",
        "seed": [{"type": "rectangle", "x": 100, "y": 100, "w": 80, "h": 80, "fill": "gray"}],
        "utterance": "delete the rectangle",
        "expect_tool": "delete_shape",
        "check": lambda args, scene: args.get("id") == 1,
    },
]

PROVIDERS = {"anthropic": AnthropicProvider, "ollama": OllamaProvider}


def run_case(provider, case: dict) -> tuple[bool, float, str]:
    scene = make_scene(case["seed"])
    scene_json = str([obj.model_dump() for obj in scene.list()])
    user_message = f'Current scene: {scene_json}\n\nUser said: "{case["utterance"]}"'

    start = time.perf_counter()
    response = provider.generate(SYSTEM_PROMPT, user_message, TOOLS)
    elapsed = time.perf_counter() - start

    if len(response.tool_calls) != 1:
        return False, elapsed, f"expected 1 tool call, got {len(response.tool_calls)}"
    call = response.tool_calls[0]
    if call.name != case["expect_tool"]:
        return False, elapsed, f"expected {case['expect_tool']}, got {call.name}({call.arguments})"
    if not case["check"](call.arguments, scene):
        return False, elapsed, f"wrong arguments: {call.name}({call.arguments})"
    return True, elapsed, f"{call.name}({call.arguments})"


def main() -> None:
    results: dict[str, list[tuple[bool, float]]] = {name: [] for name in PROVIDERS}

    for provider_name, provider_cls in PROVIDERS.items():
        provider = provider_cls()
        print(f"\n=== {provider_name} ===")
        for case in CASES:
            correct, elapsed, detail = run_case(provider, case)
            results[provider_name].append((correct, elapsed))
            mark = "PASS" if correct else "FAIL"
            print(f"[{mark}] {case['name']:20s} {elapsed:5.2f}s  {detail}")

    print("\n=== Summary ===")
    for provider_name, rows in results.items():
        accuracy = sum(1 for correct, _ in rows if correct) / len(rows)
        avg_latency = sum(elapsed for _, elapsed in rows) / len(rows)
        print(f"{provider_name:10s} accuracy={accuracy:.0%}  avg_latency={avg_latency:.2f}s")


if __name__ == "__main__":
    main()
