from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "WordSmiths AI Backend"
    app_env: str = "dev"
    langchain_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("LANGCHAIN_ENABLED"),
    )
    llm_provider: str = Field(default="mock", validation_alias=AliasChoices("LLM_PROVIDER"))
    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_API_KEY", "OPENAI_API_KEY"),
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("LLM_MODEL", "OPENAI_MODEL"),
    )
    llm_base_url: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_BASE_URL", "OPENAI_BASE_URL"),
    )
    hunyuan_api_key: str = Field(default="", validation_alias=AliasChoices("HUNYUAN_API_KEY"))
    hunyuan_model: str = Field(default="", validation_alias=AliasChoices("HUNYUAN_MODEL"))
    hunyuan_base_url: str = Field(default="", validation_alias=AliasChoices("HUNYUAN_BASE_URL"))
    deepseek_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("DEEPSEEK_API_KEY"),
    )
    deepseek_model: str = Field(
        default="deepseek-v4-flash",
        validation_alias=AliasChoices("DEEPSEEK_MODEL"),
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        validation_alias=AliasChoices("DEEPSEEK_BASE_URL"),
    )
    topic_chat_store_path: str = Field(
        default="app/data/topic_chat_sessions.json",
        validation_alias=AliasChoices("TOPIC_CHAT_STORE_PATH"),
    )
    topic_chat_max_history_messages: int = Field(
        default=100,
        ge=20,
        le=1000,
        validation_alias=AliasChoices("TOPIC_CHAT_MAX_HISTORY_MESSAGES"),
    )
    xfyun_app_id: str = Field(default="", validation_alias=AliasChoices("XFYUN_APP_ID"))
    xfyun_api_key: str = Field(default="", validation_alias=AliasChoices("XFYUN_API_KEY"))
    xfyun_api_secret: str = Field(default="", validation_alias=AliasChoices("XFYUN_API_SECRET"))
    digital_human_provider: str = Field(
        default="mock",
        validation_alias=AliasChoices("DIGITAL_HUMAN_PROVIDER"),
    )
    digital_human_media_dir: str = Field(
        default="app/data/digital_human_media",
        validation_alias=AliasChoices("DIGITAL_HUMAN_MEDIA_DIR"),
    )
    digital_human_public_base_url: str = Field(
        default="http://127.0.0.1:8000",
        validation_alias=AliasChoices("DIGITAL_HUMAN_PUBLIC_BASE_URL"),
    )
    digital_human_mock_video_url: str = Field(
        default="",
        validation_alias=AliasChoices("DIGITAL_HUMAN_MOCK_VIDEO_URL"),
    )
    tencent_secret_id: str = Field(default="", validation_alias=AliasChoices("TENCENT_SECRET_ID"))
    tencent_secret_key: str = Field(default="", validation_alias=AliasChoices("TENCENT_SECRET_KEY"))
    tencent_digital_human_app_id: str = Field(
        default="",
        validation_alias=AliasChoices("TENCENT_DIGITAL_HUMAN_APP_ID"),
    )
    tencent_digital_human_project_id: str = Field(
        default="",
        validation_alias=AliasChoices("TENCENT_DIGITAL_HUMAN_PROJECT_ID"),
    )
    tencent_digital_human_avatar_id: str = Field(
        default="",
        validation_alias=AliasChoices("TENCENT_DIGITAL_HUMAN_AVATAR_ID"),
    )
    tencent_digital_human_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices("TENCENT_DIGITAL_HUMAN_ENDPOINT"),
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
