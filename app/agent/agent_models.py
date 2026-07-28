from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.agent.tools import tool_registry

Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class AgentResult(BaseModel):
    reply: str
    tokens_used: int = Field(description="Summed over every model call in the loop.")
    steps: int = Field(description="Model calls it took to get here.")
    tools_called: tuple[str, ...] = ()


class AgentConfig(BaseModel):
    model_config = {"frozen": True}  # safe to share one instance across requests

    # Model ids: https://tokenfactory.nebius.com/models/catalog
    model: str
    system_prompt: str
    tools: tuple[str, ...] = Field(default=(), description="Names from agent.tools.tool_registry.")
    temperature: float = Field(default=0.6, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1)
    max_steps: int = Field(default=5, ge=1, description="Tool-calling rounds before giving up.")

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
