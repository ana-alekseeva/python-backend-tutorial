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
    image_url: Annotated[
        str | None,
        Field(description="URL of an image attachment already uploaded to object storage."),
    ] = None
    pdf_url: Annotated[
        str | None,
        Field(description="URL of a PDF attachment already uploaded to object storage."),
    ] = None


class SendMessageResponse(BaseModel):
    reply: Annotated[str, Field(description="The agent's reply.")]
    tokens_used: Annotated[int, Field(description="Total tokens billed for this turn.")]
    image_url: Annotated[
        str | None,
        Field(description="URL of an image the agent produced, in object storage."),
    ] = None
