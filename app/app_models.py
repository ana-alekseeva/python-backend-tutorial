from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    model_config = {"extra": "forbid"}  # reject unknown fields

    content: str = Field(
        min_length=1,
        max_length=8000,
        description="The user's message to the agent.",
        examples=["Explain FastAPI routing in two sentences."],
    )


class SendMessageResponse(BaseModel):
    reply: str = Field(description="The agent's reply.")
    tokens_used: int = Field(description="Total tokens billed for this turn.")
