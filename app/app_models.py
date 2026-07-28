from typing import Annotated

from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    model_config = {"extra": "forbid"}  # reject unknown fields

    content: Annotated[
        str,
        Field(
            min_length=1,
            max_length=8000,
            description="The user's message to the agent.",
            examples=["Explain FastAPI routing in two sentences."],
        ),
    ]


class SendMessageResponse(BaseModel):
    reply: Annotated[str, Field(description="The agent's reply.")]
    tokens_used: Annotated[int, Field(description="Total tokens billed for this turn.")]

    # Only filled in when the caller asks with ?details=true.
    steps: Annotated[int | None, Field(description="Model calls the reply took.")] = None
    tools_called: Annotated[tuple[str, ...] | None, Field(description="In call order.")] = None
