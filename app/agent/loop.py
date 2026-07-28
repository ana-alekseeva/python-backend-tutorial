import json
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.agent.agent_models import AgentConfig, AgentResult, ChatMessage
from app.agent.config import get_agent
from app.agent.tools import tool_registry
from app.config import get_settings

settings = get_settings()

client = AsyncOpenAI(api_key=settings.nebius_api_key, base_url=settings.nebius_base_url)


def build_messages(content: str, config: AgentConfig) -> list[dict]:
    return [
        ChatMessage(role="system", content=config.system_prompt).model_dump(),
        ChatMessage(role="user", content=content).model_dump(),
    ]


def run_tool(name: str, arguments: str) -> str:
    return str(tool_registry[name].run(**json.loads(arguments)))


async def run_agent(content: str, config: AgentConfig | None = None) -> AgentResult:
    config = config or get_agent()
    tools = [tool_registry[name].schema for name in config.tools]
    messages = build_messages(content, config)
    tokens_used = 0
    tools_called: list[str] = []

    for step in range(1, config.max_steps + 1):
        completion = await client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            tools=tools or None,
        )
        tokens_used += completion.usage.total_tokens if completion.usage else 0
        message = completion.choices[0].message

        if not message.tool_calls:
            return AgentResult(
                reply=message.content or "",
                tokens_used=tokens_used,
                steps=step,
                tools_called=tuple(tools_called),
            )

        messages.append(message.model_dump(exclude_none=True))
        for call in message.tool_calls:
            tools_called.append(call.function.name)
            result = run_tool(call.function.name, call.function.arguments)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return AgentResult(
        reply="Gave up: too many tool steps.",
        tokens_used=tokens_used,
        steps=config.max_steps,
        tools_called=tuple(tools_called),
    )


async def stream_agent(content: str, config: AgentConfig | None = None) -> AsyncIterator[str]:
    """Same loop, but text is yielded as it arrives instead of returned at the end."""
    config = config or get_agent()
    tools = [tool_registry[name].schema for name in config.tools]
    messages = build_messages(content, config)

    for _ in range(config.max_steps):
        stream = await client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            tools=tools or None,
            stream=True,
        )

        text: list[str] = []
        # A tool call arrives in pieces too: the name in one chunk, the arguments
        # split across the next few. Reassemble them by index before running anything.
        calls: dict[int, dict[str, str]] = {}

        async for event in stream:
            if not event.choices:
                continue
            delta = event.choices[0].delta

            if delta.content:
                text.append(delta.content)
                yield delta.content

            for part in delta.tool_calls or []:
                call = calls.setdefault(part.index, {"id": "", "name": "", "arguments": ""})
                call["id"] += part.id or ""
                call["name"] += part.function.name or "" if part.function else ""
                call["arguments"] += part.function.arguments or "" if part.function else ""

        if not calls:
            return

        messages.append(
            {
                "role": "assistant",
                "content": "".join(text) or None,
                "tool_calls": [
                    {
                        "id": call["id"],
                        "type": "function",
                        "function": {"name": call["name"], "arguments": call["arguments"]},
                    }
                    for call in calls.values()
                ],
            }
        )
        for call in calls.values():
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": run_tool(call["name"], call["arguments"]),
                }
            )

    yield "\n\n[Gave up: too many tool steps.]"
