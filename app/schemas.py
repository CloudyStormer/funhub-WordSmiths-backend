from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    level: str = Field(default="A2", description="English level, e.g. A1-C2")


class ChatResponse(BaseModel):
    reply: str


class DailyPlanRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    level: str = Field(default="A2")
    minutes_per_day: int = Field(default=30, ge=10, le=180)
    goals: list[str] = Field(default_factory=list)


class DailyPlanResponse(BaseModel):
    plan_title: str
    tasks: list[str]
