from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.agent import AgentName, get_agent, run_agent
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
    details: Annotated[bool, Query(description="Report how the reply was produced.")] = False,
) -> SendMessageResponse:
    result = await run_agent(body.content, config=get_agent(agent))
    extra = {"steps": result.steps, "tools_called": result.tools_called} if details else {}
    return SendMessageResponse(reply=result.reply, tokens_used=result.tokens_used, **extra)
