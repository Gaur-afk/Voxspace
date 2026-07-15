import json
import os

from dotenv import load_dotenv

from app.llm_provider import LLMProvider
from app.providers import AnthropicProvider, OllamaProvider
from app.scene import SceneGraph
from app.tools import CANVAS_HEIGHT, CANVAS_WIDTH, TOOLS, execute_tool

load_dotenv()

SYSTEM_PROMPT = f"""You control a 2D design canvas, {CANVAS_WIDTH}x{CANVAS_HEIGHT} px, origin top-left.
You are given the current scene as a JSON list of objects (each with an id) and a user utterance.
Use the provided tools to carry out the utterance. Reference existing objects by the id shown
in the scene state. If the utterance doesn't require any scene change, don't call a tool."""


PROVIDER_NAMES = ("anthropic", "ollama")
_current_provider_name = os.environ.get("LLM_PROVIDER", "anthropic")


def get_current_provider_name() -> str:
    return _current_provider_name


def set_current_provider_name(name: str) -> None:
    global _current_provider_name
    if name not in PROVIDER_NAMES:
        raise ValueError(f"unknown provider {name!r}, must be one of {PROVIDER_NAMES}")
    _current_provider_name = name


def get_provider() -> LLMProvider:
    if _current_provider_name == "ollama":
        return OllamaProvider()
    return AnthropicProvider()


def run_agent_turn(utterance: str, scene: SceneGraph) -> tuple[list[dict], str | None]:
    scene_json = json.dumps([obj.model_dump() for obj in scene.list()])
    user_message = f'Current scene: {scene_json}\n\nUser said: "{utterance}"'

    provider = get_provider()
    response = provider.generate(SYSTEM_PROMPT, user_message, TOOLS)

    executed = []
    for call in response.tool_calls:
        result = execute_tool(call.name, call.arguments, scene)
        executed.append({"name": call.name, "arguments": call.arguments, "result": result})

    return executed, response.text
