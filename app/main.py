from fastapi import FastAPI

from app.config import settings
from app.schemas import ChatRequest, ChatResponse, DailyPlanRequest, DailyPlanResponse
from app.services.ai_service import ai_service

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.get("/ai/status")
def ai_status() -> dict[str, str | bool]:
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
