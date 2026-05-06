from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    level: str = Field(default="A2", description="English level, e.g. A1-C2")


class ChatResponse(BaseModel):
    reply: str


class TopicAgentChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    session_id: str = Field(
        default="",
        description="Existing conversation session id. Leave empty to create a new one.",
    )
    words: str = Field(
        default="",
        description="Comma-separated English words. Required when creating a new session.",
    )
    type: str = Field(
        default="",
        description="Conversation topic or scenario. Required when creating a new session.",
    )
    message: str = Field(
        default="",
        description="Latest user message. Leave empty to let the agent open the conversation.",
    )
    level: str = Field(default="A2", description="English level, e.g. A1-C2")


class TopicAgentChatResponse(BaseModel):
    session_id: str
    type: str
    parsed_words: list[str]
    history: list[dict[str, str]]
    reply: str


class TopicAgentSessionHistoryResponse(BaseModel):
    session_id: str
    user_id: str
    type: str
    level: str
    parsed_words: list[str]
    history: list[dict[str, str]]


class DailyPlanRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    level: str = Field(default="A2")
    minutes_per_day: int = Field(default=30, ge=10, le=180)
    goals: list[str] = Field(default_factory=list)


class DailyPlanResponse(BaseModel):
    plan_title: str
    tasks: list[str]
