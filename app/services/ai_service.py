from typing import Any

from openai import OpenAI

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None

from app.config import settings


class AIService:
    def __init__(self) -> None:
        provider = settings.llm_provider.lower().strip()
        self._provider = provider
        self._engine = "mock"
        self._lc_client = None
        self._init_error = ""

        if provider == "mock" or not settings.llm_api_key:
            self._client = None
            return

        if provider in {"openai", "openai_compatible", "hunyuan"}:
            client_kwargs: dict[str, str] = {"api_key": settings.llm_api_key}
            if settings.llm_base_url:
                client_kwargs["base_url"] = settings.llm_base_url

            if settings.langchain_enabled:
                if ChatOpenAI is None:
                    self._client = None
                    self._engine = "langchain-unavailable"
                    self._init_error = "langchain_openai is not installed"
                    return

                self._lc_client = ChatOpenAI(
                    api_key=settings.llm_api_key,
                    model=settings.llm_model,
                    base_url=settings.llm_base_url or None,
                    temperature=0.7,
                )
                self._client = None
                self._engine = "langchain"
                return

            self._client = OpenAI(**client_kwargs)
            self._engine = "openai-sdk"
            return

        self._client = None

    def _fallback_chat(self, message: str, level: str) -> str:
        return (
            f"[mock] You said: {message}. "
            f"Let's continue in English for level {level}. "
            "Tell me one sentence about your day, and I will help improve it."
        )

    def chat(self, user_message: str, level: str) -> str:
        if self._init_error:
            return f"[mock] AI init error: {self._init_error}"

        if self._lc_client is not None and HumanMessage is not None and SystemMessage is not None:
            try:
                response = self._lc_client.invoke(
                    [
                        SystemMessage(
                            content=(
                                "You are an English tutor. Keep responses short, practical, and easy to follow."
                            )
                        ),
                        HumanMessage(content=f"Level: {level}. Message: {user_message}"),
                    ]
                )
                if isinstance(response.content, str):
                    return response.content
                if isinstance(response.content, list):
                    return " ".join(str(item) for item in response.content)
            except Exception:
                return self._fallback_chat(user_message, level)

        if self._client is None:
            return self._fallback_chat(user_message, level)

        try:
            completion: Any = self._client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an English tutor. Keep responses short, practical, and easy to follow."
                        ),
                    },
                    {"role": "user", "content": f"Level: {level}. Message: {user_message}"},
                ],
                temperature=0.7,
            )
            content = completion.choices[0].message.content
            return content or self._fallback_chat(user_message, level)
        except Exception:
            return self._fallback_chat(user_message, level)

    def runtime_status(self) -> dict[str, Any]:
        return {
            "provider": self._provider,
            "mode": "real" if (self._client is not None or self._lc_client is not None) else "mock",
            "engine": self._engine,
            "langchain_enabled": settings.langchain_enabled,
            "init_error": self._init_error,
            "model": settings.llm_model,
            "base_url": settings.llm_base_url or "",
            "api_key_configured": bool(settings.llm_api_key),
        }

    def build_daily_plan(self, level: str, minutes_per_day: int, goals: list[str]) -> list[str]:
        goals_text = ", ".join(goals) if goals else "general speaking and listening"
        return [
            f"5 min warm-up: read 5 sentences at {level} level aloud",
            "10 min listening: one short clip and shadowing",
            f"10 min speaking: answer 3 questions about {goals_text}",
            f"{minutes_per_day - 25} min review: note mistakes and rewrite correct sentences",
        ]


ai_service = AIService()
