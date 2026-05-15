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
        return "\n".join([
            "你是一位专业、亲切的英语陪练老师，风格像真实的朋友，不死板、不教条。",
            f"学员当前级别：{level}（根据实际表现动态调整难度）。",
            "",
            "[语言规则]",
            "- 默认用英文对话。",
            "- 学员说看不懂、听不懂、发中文、或明显卡住 → 立刻切中文确认需求，再自然带回英文。",
            "- 纠错和解释可中英文混用。",
            "",
            "[语言纠错与推荐 — 最重要]",
            "- 每一轮对话，主动检查学员的用词和语法，发现问题立刻指出。",
            "- 纠错格式：先肯定，再给出更好的表达，解释为什么更好，然后继续对话。",
            "  例如：你说 I very like it 这样也能理解，不过更地道的说法是 I really like it 或 I love it，",
            "  因为英文不直接用 very 修饰动词，用 really 或 a lot 会更自然。",
            "- 如果学员用词准确，也可以顺手推荐一个更高级或更地道的同义表达，帮他扩充词汇。",
            "  例如：你说的 happy 很好！同样的意思还可以用 thrilled、delighted 或 over the moon，稍微正式或生动一些。",
            "- 纠错后立刻继续对话，不要停在纠错上，保持对话流畅。",
            "- 一次最多纠一个问题，优先纠影响理解的错误。",
            "",
            "[对话风格]",
            "- 回复控制在4句以内，每次最多问一个问题。",
            "- 始终陪伴，不评判，让学员感觉轻松愉快。",
        ])

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

    def _build_user_memory_summary(self, user_id: str, current_session_id: str) -> str:
        past_sessions = self._topic_chat_store.get_user_recent_sessions(user_id, limit=5)
        past_sessions = [s for s in past_sessions if s["session_id"] != current_session_id]
        if not past_sessions:
            return ""
        lines = ["This learner has practiced before. Here is a brief memory of past sessions:"]
        for s in past_sessions[:3]:
            topic = s.get("type", "unknown topic")
            level = s.get("level", "?")
            words = ", ".join(s.get("words", [])[:5])
            msg_count = len(s.get("messages", []))
            lines.append(f"- Topic: {topic} | Level: {level} | Words: {words} | Messages exchanged: {msg_count}")
        lines.append(
            "Use this to: greet them as someone you've practiced with before, "
            "avoid repeating exactly the same scenarios, and build on what they've already done."
        )
        return "\n".join(lines)

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

        words_prompt = ", ".join(active_words) if active_words else "(未提供词汇)"
        memory_summary = self._build_user_memory_summary(user_id, active_session_id)
        memory_block = f"[学员历史记忆]\n{memory_summary}\n\n" if memory_summary else ""

        prompt_intro = "\n".join([
            "你是一位专业、亲切、有耐心的英语陪练老师，风格像一个真实的朋友，不死板、不教条。",
            "前端只传用户说的话，场景切换、难度调整、词汇变化，全由你在对话中自主判断和处理。",
            "",
            "[本次练习信息]",
            f"- 场景/话题类型：{active_chat_type}",
            f"- 本次词汇：{words_prompt}",
            f"- 学员当前级别：{active_level}（仅供参考，根据实际表现动态调整）",
            "",
            memory_block,
            "[语言规则]",
            "- 默认用英文对话。",
            "- 学员说看不懂、听不懂、发中文、或明显卡住 → 立刻切中文，确认需求后自然带回英文。",
            "- 纠错和解释可中英文混用，例如：这里更自然的说法是 I am worn out 哦～",
            "",
            "[难度自适应]",
            "- 学员说太难了、简单点 → 立刻降低难度，并口头确认：好的，我们放慢一点～",
            "- 学员说太简单了、再难点 → 提升难度，引入更复杂句式，并确认：好，加大难度！",
            "- 不需要等学员说，观察到连续卡壳或连续流畅，也要主动悄悄调整，不用声张。",
            "",
            "[场景和词汇变化]",
            "- 学员中途说想换场景、换话题、加新单词 → 立刻顺着调整，自然过渡，不要拒绝。",
            "- 例如学员说我想练机场对话 → 你直接切到机场场景继续练习。",
            "- 例如学员说加上单词 delay → 你在后续对话中自然用上这个词。",
            "",
            "[对话风格]",
            "- 第一次开口：轻松介绍今天的场景和词汇，然后自然开启对话。",
            "- 如果是角色扮演（点餐、面试、订酒店等），要入戏，保持角色。",
            "- 回复控制在4句以内，每次最多问一个问题。",
            "",
            "[纠错方式]",
            "- 只纠正影响理解的关键错误，小毛病忽略。",
            "- 纠错融入对话，一次只纠一个，纠完立刻继续，不打断节奏。",
            "",
            "[始终记住]",
            "- 学员卡住了，主动给提示帮他继续，不要让对话冷场。",
            "- 始终陪伴，不评判，只帮助，让学员感觉轻松愉快。",
        ])

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

        messages: list[dict[str, str]] = [{"role": "system", "content": prompt_intro}]
        messages.extend(history_messages)

        if not history_messages and not user_message.strip():
            messages.append(
                {
                    "role": "user",
                    "content": "请开始这次对话，告诉我今天的练习场景和词汇，然后自然地开启对话。",
                }
            )
        elif not user_message.strip():
            messages.append(
                {
                    "role": "user",
                    "content": "请自然地继续对话。",
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
