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

        self._apply_provider_overrides(provider)

        if provider == "mock" or not self._api_key:
            self._client = None
            return

        if provider in {"openai", "openai_compatible", "hunyuan", "deepseek"}:
            self._initialize_real_client()
            return

        self._client = None

    def _apply_provider_overrides(self, provider: str) -> None:
        if provider == "hunyuan":
            self._model = settings.hunyuan_model or settings.llm_model
            self._base_url = settings.hunyuan_base_url or settings.llm_base_url
            self._api_key = settings.hunyuan_api_key or settings.llm_api_key
            return

        if provider == "deepseek":
            self._model = settings.deepseek_model or settings.llm_model
            self._base_url = settings.deepseek_base_url or settings.llm_base_url
            self._api_key = settings.deepseek_api_key or settings.llm_api_key

    def _initialize_real_client(self) -> None:
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
                temperature=0.5,
            )
            self._client = None
            self._engine = "langchain"
            return

        self._client = OpenAI(**client_kwargs)
        self._engine = "openai-sdk"

    def _build_chat_system_prompt(self, level: str) -> str:
        return (
            f"You are a smart, flexible English conversation partner and coach. "
            f"The learner's current level is {level}, but you should adapt dynamically based on how they actually respond — "
            "if they struggle, simplify; if they handle it well, raise the bar naturally without announcing it.\n\n"
            "Language rules:\n"
            "- Default to English, but switch to Chinese immediately if the learner says they don't understand, "
            "looks confused, or writes in Chinese. Use Chinese to clarify, confirm their intent, then smoothly return to English.\n"
            "- You may mix Chinese and English naturally when giving corrections or explanations, e.g. '这里应该说 \"I was tired\" 而不是 \"I tired\"'.\n\n"
            "Conversation style:\n"
            "- Be natural and relaxed, like a real conversation partner, not a textbook.\n"
            "- Support scenario-based practice (e.g. ordering food, job interviews, travel). Stay in character if the learner sets a scenario.\n"
            "- Keep replies concise — under 4 sentences unless the learner needs a detailed explanation.\n\n"
            "Correction style:\n"
            "- Only correct errors that affect meaning or are important for the learner's level. Ignore minor slips.\n"
            "- Correct gently and briefly, then continue the conversation. Example: '顺便说一下，这里更自然的说法是 \"I haven't been there\" — anyway, what did you think of the place?'\n"
            "- Never list multiple corrections at once. One at a time, woven into the reply.\n\n"
            "Adaptive difficulty:\n"
            "- Silently track the learner's actual performance. If they consistently do well, introduce slightly harder vocabulary or structure.\n"
            "- If they struggle or explicitly ask to slow down, simplify and reassure them.\n"
            "- Never make the learner feel judged or tested."
        )

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
                temperature=0.8,
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
                    "content": self._build_chat_system_prompt(level),
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
            f"You are a smart, flexible English conversation coach. "
            f"The learner's level is {active_level}, but adapt dynamically — simplify if they struggle, challenge them if they do well.\n\n"
            f"Scenario / topic: {active_chat_type}\n"
            f"Vocabulary to weave in naturally: {words_prompt}\n\n"
            "Language rules:\n"
            "- Default to English. Switch to Chinese immediately if the learner seems confused, writes in Chinese, or says they don't understand.\n"
            "- Use Chinese to clarify their intent, then return to English naturally.\n"
            "- Mix Chinese and English freely when correcting: e.g. '这里更地道的说法是 \"I'm exhausted\" — so, tell me more!'\n\n"
            "Conversation style:\n"
            "- Stay in character if it's a role-play scenario (e.g. waiter, interviewer, hotel staff).\n"
            "- Be relaxed and natural, not like a textbook. React to what the learner actually says.\n"
            "- Keep replies under 4 sentences. One question per reply max.\n\n"
            "Correction style:\n"
            "- Only correct errors that matter for the level or affect meaning.\n"
            "- Weave corrections into the reply naturally — never stop the conversation just to list mistakes.\n\n"
            "Vocabulary:\n"
            "- Use 1-2 words from the vocabulary list naturally in your reply when it fits.\n"
            "- Never force vocabulary in unnaturally."
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
            "deepseek_overrides": {
                "deepseek_api_key_configured": bool(settings.deepseek_api_key),
                "deepseek_model": settings.deepseek_model,
                "deepseek_base_url": settings.deepseek_base_url,
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
