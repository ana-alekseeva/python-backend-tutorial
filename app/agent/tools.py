from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class Tool:
    schema: dict
    run: Callable[..., str]


tool_registry: dict[str, Tool] = {}


def tool(description: str, parameters: dict) -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Register a function as a tool. `parameters` is a JSON Schema of its arguments."""

    def decorator(fn: Callable[..., str]) -> Callable[..., str]:
        tool_registry[fn.__name__] = Tool(
            schema={
                "type": "function",
                "function": {
                    "name": fn.__name__,
                    "description": description,
                    "parameters": parameters,
                },
            },
            run=fn,
        )
        return fn

    return decorator


@tool(
    description="Look up the current weather in a city.",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string", "description": "City name, e.g. 'Amsterdam'."}},
        "required": ["city"],
    },
)
def get_weather(city: str) -> str:
    """Stub. Replace the body with a real API call."""
    return f"It is 18 degrees and sunny in {city}."


@tool(
    description="Get the current date and time in a timezone.",
    parameters={
        "type": "object",
        "properties": {"timezone": {"type": "string", "description": "IANA name, e.g. 'Europe/Amsterdam'."}},
        "required": ["timezone"],
    },
)
def current_time(timezone: str) -> str:
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        return f"Unknown timezone: {timezone}."
    return datetime.now(zone).strftime("%Y-%m-%d %H:%M %Z")


@tool(
    description="Search the project documentation.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "What to look for."}},
        "required": ["query"],
    },
)
def search_docs(query: str) -> str:
    """Stub. Replace the body with a real search over your docs."""
    return f"No documentation matched {query!r}."
