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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
