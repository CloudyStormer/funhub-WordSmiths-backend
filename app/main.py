from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import (
    ChatRequest,
    ChatResponse,
    DailyPlanRequest,
    DailyPlanResponse,
    TopicAgentChatRequest,
    TopicAgentChatResponse,
    TopicAgentSessionHistoryResponse,
)
from app.services.ai_service import ai_service

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.get("/ai/status")
def ai_status() -> dict[str, Any]:
    return ai_service.runtime_status()


@app.post("/ai/chat")
def ai_chat(payload: ChatRequest) -> ChatResponse:
    reply = ai_service.chat(user_message=payload.message, level=payload.level)
    return ChatResponse(reply=reply)


@app.post("/ai/daily-plan")
def ai_daily_plan(payload: DailyPlanRequest) -> DailyPlanResponse:
    tasks = ai_service.build_daily_plan(
        level=payload.level,
        minutes_per_day=payload.minutes_per_day,
        goals=payload.goals,
    )
    return DailyPlanResponse(plan_title="Your daily English plan", tasks=tasks)


@app.post(
    "/ai/topic-agent-chat",
    responses={
        400: {"description": "Invalid request for creating or continuing session"},
        403: {"description": "Session does not belong to this user"},
    },
)
def ai_topic_agent_chat(payload: TopicAgentChatRequest) -> TopicAgentChatResponse:
    try:
        session_id, active_type, parsed_words, history, reply = ai_service.topic_agent_chat(
            user_id=payload.user_id,
            session_id=payload.session_id,
            words_text=payload.words,
            chat_type=payload.type,
            user_message=payload.message,
            level=payload.level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return TopicAgentChatResponse(
        session_id=session_id,
        type=active_type,
        parsed_words=parsed_words,
        history=history,
        reply=reply,
    )


@app.get(
    "/ai/topic-agent-chat/history/{session_id}",
    responses={
        403: {"description": "Session does not belong to this user"},
        404: {"description": "Session not found"},
    },
)
def ai_topic_agent_chat_history(session_id: str, user_id: str) -> TopicAgentSessionHistoryResponse:
    try:
        session = ai_service.topic_agent_history(user_id=user_id, session_id=session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return TopicAgentSessionHistoryResponse(
        session_id=session["session_id"],
        user_id=session["user_id"],
        type=session["type"],
        level=session["level"],
        parsed_words=session["words"],
        history=session["messages"],
    )
