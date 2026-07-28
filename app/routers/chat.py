from typing import Annotated

from fastapi import APIRouter, Query, status

from app.agent import AgentName, get_agent, run_agent
from app.app_models import SendMessageRequest, SendMessageResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to the agent",
)
async def send_message(
    body: SendMessageRequest,
    agent: Annotated[AgentName, Query(description="Which agent answers.")] = AgentName.DEFAULT,
) -> SendMessageResponse:
    result = await run_agent(body.content, config=get_agent(agent))
    return SendMessageResponse(reply=result.reply, tokens_used=result.tokens_used)
