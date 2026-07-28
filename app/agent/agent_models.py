from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from app.agent.tools import tool_registry

Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class AgentResult(BaseModel):
    reply: str
    tokens_used: Annotated[int, Field(description="Summed over every model call in the loop.")]
    steps: Annotated[int, Field(description="Model calls it took to get here.")]
    tools_called: tuple[str, ...] = ()


class AgentConfig(BaseModel):
    model_config = {"frozen": True}  # safe to share one instance across requests

    # Model ids: https://tokenfactory.nebius.com/models/catalog
    model: str
    system_prompt: str
    tools: Annotated[
        tuple[str, ...],
        Field(description="Names from agent.tools.tool_registry."),
    ] = ()
    temperature: Annotated[float, Field(ge=0.0, le=2.0)] = 0.6
    max_tokens: Annotated[int, Field(ge=1)] = 1024
    max_steps: Annotated[int, Field(ge=1, description="Tool-calling rounds before giving up.")] = 5

    @field_validator("tools")
    @classmethod
    def tools_must_exist(cls, names: tuple[str, ...]) -> tuple[str, ...]:
        # A typo here would otherwise only surface when the model asks for the tool.
        unknown = set(names) - set(tool_registry)
        if unknown:
            raise ValueError(f"unknown tools: {sorted(unknown)}")
        return names


class AgentName(StrEnum):
    """The agents the API exposes. FastAPI turns this into a dropdown in /docs."""

    DEFAULT = "default"
    CODER = "coder"
    RESEARCHER = "researcher"
