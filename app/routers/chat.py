import json
from typing import Annotated

from fastapi import APIRouter, Path, Query, status
from fastapi.responses import StreamingResponse

from app.agent import AgentConfig, AgentName, get_agent, run_agent, stream_agent
from app.app_models import SendMessageRequest, SendMessageResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/{agent}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to the agent",
)
async def send_message(
    agent: Annotated[AgentName, Path(title="Which agent answers")],
    body: SendMessageRequest,
    stream: Annotated[bool, Query(description="Stream the reply as it is generated.")] = False,
) -> SendMessageResponse:
    config = get_agent(agent)

    if stream:
        # Returning a Response subclass bypasses FastAPI's serialization: the reply
        # leaves as server-sent events instead of one JSON body.
        return StreamingResponse(
            _events(body.content, config),
            media_type="text/event-stream",
            status_code=status.HTTP_201_CREATED,
        )

    result = await run_agent(body.content, config=config)
    return SendMessageResponse(reply=result.reply, tokens_used=result.tokens_used)


async def _events(content: str, config: AgentConfig):
    # JSON-encode every chunk: model output contains newlines, which would
    # otherwise break the "data: ...\n\n" framing of server-sent events.
    async for chunk in stream_agent(content, config):
        yield f"data: {json.dumps({'delta': chunk})}\n\n"
    yield "data: [DONE]\n\n"
