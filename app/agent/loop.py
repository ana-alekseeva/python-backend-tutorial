import json

from openai import AsyncOpenAI

from app.agent.agent_models import AgentConfig, AgentResult, ChatMessage
from app.agent.config import get_agent
from app.agent.tools import tool_registry
from app.config import get_settings

settings = get_settings()

client = AsyncOpenAI(api_key=settings.nebius_api_key, base_url=settings.nebius_base_url)


async def run_agent(content: str, config: AgentConfig | None = None) -> AgentResult:
    config = config or get_agent()
    tools = [tool_registry[name].schema for name in config.tools]
    messages = [
        ChatMessage(role="system", content=config.system_prompt).model_dump(),
        ChatMessage(role="user", content=content).model_dump(),
    ]
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
            result = tool_registry[call.function.name].run(**json.loads(call.function.arguments))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})

    return AgentResult(
        reply="Gave up: too many tool steps.",
        tokens_used=tokens_used,
        steps=config.max_steps,
        tools_called=tuple(tools_called),
    )
