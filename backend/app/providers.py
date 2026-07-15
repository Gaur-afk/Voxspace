import httpx
from anthropic import Anthropic

from app.llm_provider import ProviderResponse, ToolCall

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"


class AnthropicProvider:
    def __init__(self) -> None:
        self._client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    def generate(self, system: str, user_message: str, tools: list[dict]) -> ProviderResponse:
        response = self._client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            system=system,
            tools=tools,
            messages=[{"role": "user", "content": user_message}],
        )

        text = None
        tool_calls = []
        for block in response.content:
            if block.type == "text" and block.text:
                text = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(name=block.name, arguments=block.input))

        return ProviderResponse(text=text, tool_calls=tool_calls)


class OllamaProvider:
    def generate(self, system: str, user_message: str, tools: list[dict]) -> ProviderResponse:
        ollama_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in tools
        ]

        response = httpx.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
                "tools": ollama_tools,
            },
            timeout=60,
        )
        response.raise_for_status()
        message = response.json()["message"]

        tool_calls = [
            ToolCall(name=call["function"]["name"], arguments=call["function"]["arguments"])
            for call in message.get("tool_calls", [])
        ]
        text = message.get("content") or None

        return ProviderResponse(text=text, tool_calls=tool_calls)
