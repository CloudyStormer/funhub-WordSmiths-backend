from typing import Any

from openai import OpenAI

try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
except Exception:
    AIMessage = None
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None

from app.config import settings
from app.services.topic_chat_store import TopicChatStore


class AIService:
    def __init__(self) -> None:
        provider = settings.llm_provider.lower().strip()
        self._provider = provider
        self._engine = "mock"
        self._lc_client = None
        self._init_error = ""
        self._model = settings.llm_model
        self._base_url = settings.llm_base_url
        self._api_key = settings.llm_api_key
        self._topic_chat_store = TopicChatStore(
            file_path=settings.topic_chat_store_path,
            max_history_messages=settings.topic_chat_max_history_messages,
        )

        if provider == "hunyuan":
            self._model = settings.hunyuan_model or settings.llm_model
            self._base_url = settings.hunyuan_base_url or settings.llm_base_url
            self._api_key = settings.hunyuan_api_key or settings.llm_api_key

        if provider == "mock" or not self._api_key:
            self._client = None
            return

        if provider in {"openai", "openai_compatible", "hunyuan"}:
            client_kwargs: dict[str, str] = {"api_key": self._api_key}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url

            if settings.langchain_enabled:
                if ChatOpenAI is None:
                    self._client = None
                    self._engine = "langchain-unavailable"
                    self._init_error = "langchain_openai is not installed"
                    return

                self._lc_client = ChatOpenAI(
                    api_key=self._api_key,
                    model=self._model,
                    base_url=self._base_url or None,
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

    def _extract_content(self, response: Any) -> str:
        if isinstance(response, str):
            return response
        content = getattr(response, "content", None)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return " ".join(str(item) for item in content)
        return ""

    def _to_langchain_messages(self, messages: list[dict[str, str]]) -> list[Any]:
        lc_messages: list[Any] = []
        for message in messages:
            if message["role"] == "system":
                lc_messages.append(SystemMessage(content=message["content"]))
            elif message["role"] == "assistant":
                lc_messages.append(AIMessage(content=message["content"]))
            else:
                lc_messages.append(HumanMessage(content=message["content"]))
        return lc_messages

    def _invoke_messages(self, messages: list[dict[str, str]], fallback_text: str) -> str:
        if self._init_error:
            return f"[mock] AI init error: {self._init_error}"

        if self._lc_client is not None and HumanMessage is not None and SystemMessage is not None and AIMessage is not None:
            try:
                lc_messages = self._to_langchain_messages(messages)
                response = self._lc_client.invoke(lc_messages)
                content = self._extract_content(response)
                return content or fallback_text
            except Exception:
                return fallback_text

        if self._client is None:
            return fallback_text

        try:
            completion: Any = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.7,
            )
            content = completion.choices[0].message.content
            return content or fallback_text
        except Exception:
            return fallback_text

    def _parse_words(self, words_text: str) -> list[str]:
        parsed_words: list[str] = []
        seen: set[str] = set()
        for raw_word in words_text.split(","):
            normalized_word = raw_word.strip()
            if not normalized_word:
                continue
            dedupe_key = normalized_word.lower()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            parsed_words.append(normalized_word)
        return parsed_words

    def _fallback_topic_agent_chat(
        self,
        words: list[str],
        chat_type: str,
        user_message: str,
        level: str,
    ) -> str:
        words_hint = ", ".join(words[:5]) if words else "the given words"
        if user_message.strip():
            return (
                f"[mock] Let's keep talking about {chat_type}. "
                f"Try to use these words naturally: {words_hint}. "
                f"You said: {user_message}. "
                f"My question for level {level}: what is your opinion about {chat_type}?"
            )
        return (
            f"[mock] We will practice English about {chat_type}. "
            f"Please try to use these words: {words_hint}. "
            f"For level {level}, here is my first question: what comes to your mind when you think about {chat_type}?"
        )

    def chat(self, user_message: str, level: str) -> str:
        return self._invoke_messages(
            messages=[
                {
                    "role": "system",
                    "content": "You are an English tutor. Keep responses short, practical, and easy to follow.",
                },
                {"role": "user", "content": f"Level: {level}. Message: {user_message}"},
            ],
            fallback_text=self._fallback_chat(user_message, level),
        )

    def topic_agent_chat(
        self,
        user_id: str,
        session_id: str,
        words_text: str,
        chat_type: str,
        user_message: str,
        level: str,
    ) -> tuple[str, str, list[str], list[dict[str, str]], str]:
        parsed_words = self._parse_words(words_text)
        session = self._topic_chat_store.get_or_create_session(
            user_id=user_id,
            session_id=session_id,
            chat_type=chat_type,
            level=level,
            parsed_words=parsed_words,
        )
        active_session_id = session["session_id"]
        active_chat_type = session["type"]
        active_level = session["level"]
        active_words = list(session.get("words", []))
        active_messages = list(session.get("messages", []))
        fallback_text = self._fallback_topic_agent_chat(
            words=active_words,
            chat_type=active_chat_type,
            user_message=user_message,
            level=active_level,
        )
        words_prompt = ", ".join(active_words) if active_words else "No vocabulary words were provided"
        prompt_intro = (
            "You are an English conversation agent. "
            "Lead a natural, short, interactive conversation. "
            "Stay focused on the given topic type. "
            "Encourage the learner to answer in English and naturally reuse the provided vocabulary when suitable. "
            "Ask at most one follow-up question in each reply."
        )

        if user_message.strip():
            active_messages = self._topic_chat_store.append_message(
                session_id=active_session_id,
                role="user",
                content=user_message,
            )

        history_messages = [
            {"role": item["role"], "content": item["content"]}
            for item in active_messages
            if item.get("role") in {"user", "assistant"} and item.get("content")
        ]

        messages = [
            {"role": "system", "content": prompt_intro},
            {
                "role": "user",
                "content": (
                    f"Context for this conversation:\n"
                    f"Level: {active_level}\n"
                    f"Topic type: {active_chat_type}\n"
                    f"Vocabulary words: {words_prompt}"
                ),
            },
        ]
        messages.extend(history_messages)

        if not history_messages and not user_message.strip():
            messages.append(
                {
                    "role": "user",
                    "content": "Start the conversation with a short opening and ask one question.",
                }
            )
        elif not user_message.strip():
            messages.append(
                {
                    "role": "user",
                    "content": "Continue the conversation naturally with one brief follow-up question.",
                }
            )

        reply = self._invoke_messages(
            messages=messages,
            fallback_text=fallback_text,
        )
        final_messages = self._topic_chat_store.append_message(
            session_id=active_session_id,
            role="assistant",
            content=reply,
        )
        return active_session_id, active_chat_type, active_words, final_messages, reply

    def topic_agent_history(self, user_id: str, session_id: str) -> dict[str, Any]:
        session = self._topic_chat_store.get_session(session_id=session_id)
        if session["user_id"] != user_id:
            raise PermissionError("session does not belong to this user")
        return session

    def runtime_status(self) -> dict[str, Any]:
        return {
            "provider": self._provider,
            "mode": "real" if (self._client is not None or self._lc_client is not None) else "mock",
            "engine": self._engine,
            "langchain_enabled": settings.langchain_enabled,
            "init_error": self._init_error,
            "model": self._model,
            "base_url": self._base_url or "",
            "api_key_configured": bool(self._api_key),
            "hunyuan_overrides": {
                "hunyuan_api_key_configured": bool(settings.hunyuan_api_key),
                "hunyuan_model": settings.hunyuan_model,
                "hunyuan_base_url": settings.hunyuan_base_url,
            },
            "topic_chat_store_path": settings.topic_chat_store_path,
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
