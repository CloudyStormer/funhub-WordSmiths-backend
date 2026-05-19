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


class DigitalHumanChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, description="ASR transcript or typed text")
    level: str = Field(default="A2", description="English level, e.g. A1-C2")
    avatar_id: str = Field(default="", description="Digital human avatar id")
    voice: str = Field(default="x4_yezi", description="XFYUN voice name")


class DigitalHumanAvatarResponse(BaseModel):
    provider: str
    avatar_id: str
    status: str
    video_url: str = ""
    stream_url: str = ""
    message: str = ""


class DigitalHumanChatResponse(BaseModel):
    job_id: str
    user_id: str
    user_text: str
    reply_text: str
    audio_url: str
    avatar: DigitalHumanAvatarResponse


class DigitalHumanJobResponse(DigitalHumanChatResponse):
    provider_query: dict = Field(default_factory=dict)


class DigitalHumanStatusResponse(BaseModel):
    provider: str
    provider_configured: bool
    media_dir: str
    public_base_url: str
    supports: dict
