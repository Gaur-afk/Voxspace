from dataclasses import dataclass
from typing import NamedTuple, Protocol


class ToolCall(NamedTuple):
    name: str
    arguments: dict


@dataclass
class ProviderResponse:
    text: str | None
    tool_calls: list[ToolCall]


class LLMProvider(Protocol):
    def generate(self, system: str, user_message: str, tools: list[dict]) -> ProviderResponse: ...
