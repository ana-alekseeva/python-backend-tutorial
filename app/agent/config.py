from functools import lru_cache
from pathlib import Path

from app.agent.agent_models import AgentConfig, AgentName

PROMPT_DIR = Path(__file__).parent / "prompts"


@lru_cache
def load_prompt(name: str) -> str:
    """Read prompts/<name>.txt. Cached, so each file is read once per process."""
    return (PROMPT_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()


AGENTS: dict[AgentName, AgentConfig] = {
    AgentName.DEFAULT: AgentConfig(
        model="meta-llama/Llama-3.3-70B-Instruct",
        system_prompt=load_prompt("default"),
        tools=("get_weather", "current_time"),
    ),
    AgentName.CODER: AgentConfig(
        model="Qwen/Qwen3-235B-A22B-Instruct-2507",
        system_prompt=load_prompt("coder"),
        tools=("search_docs",),
        temperature=0.2,
        max_tokens=4096,
    ),
    AgentName.RESEARCHER: AgentConfig(
        model="Qwen/Qwen3-Next-80B-A3B-Thinking",
        system_prompt=load_prompt("researcher"),
        tools=("search_docs", "get_weather", "current_time"),
        temperature=0.3,
        max_tokens=8192,
        max_steps=10,
    ),
}


def get_agent(name: AgentName = AgentName.DEFAULT) -> AgentConfig:
    return AGENTS[name]
