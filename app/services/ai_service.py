from typing import Any

from openai import OpenAI

from app.config import settings


class AIService:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def _fallback_chat(self, message: str, level: str) -> str:
        return (
            f"[mock] You said: {message}. "
            f"Let's continue in English for level {level}. "
            "Tell me one sentence about your day, and I will help improve it."
        )

    def chat(self, user_message: str, level: str) -> str:
        if self._client is None:
            return self._fallback_chat(user_message, level)

        completion: Any = self._client.responses.create(
            model=settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an English tutor. Keep responses short, practical, and easy to follow."
                    ),
                },
                {"role": "user", "content": f"Level: {level}. Message: {user_message}"},
            ],
        )

        return completion.output_text

    def build_daily_plan(self, level: str, minutes_per_day: int, goals: list[str]) -> list[str]:
        goals_text = ", ".join(goals) if goals else "general speaking and listening"
        return [
            f"5 min warm-up: read 5 sentences at {level} level aloud",
            "10 min listening: one short clip and shadowing",
            f"10 min speaking: answer 3 questions about {goals_text}",
            f"{minutes_per_day - 25} min review: note mistakes and rewrite correct sentences",
        ]


ai_service = AIService()
