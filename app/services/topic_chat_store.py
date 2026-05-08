import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4


class TopicChatStore:
    def __init__(self, file_path: str, max_history_messages: int) -> None:
        self._file_path = Path(file_path)
        self._max_history_messages = max_history_messages
        self._lock = Lock()
        self._sessions: dict[str, dict] = {}
        self._load()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _load(self) -> None:
        if not self._file_path.exists():
            return
        try:
            content = json.loads(self._file_path.read_text(encoding="utf-8"))
            sessions = content.get("sessions", {})
            if isinstance(sessions, dict):
                self._sessions = sessions
        except Exception:
            self._sessions = {}

    def _save(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"sessions": self._sessions}
        self._file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_or_create_session(
        self,
        user_id: str,
        session_id: str,
        chat_type: str,
        level: str,
        parsed_words: list[str],
    ) -> dict:
        with self._lock:
            normalized_session_id = session_id.strip()
            if normalized_session_id and normalized_session_id in self._sessions:
                session = self._sessions[normalized_session_id]
                if session.get("user_id") != user_id:
                    raise PermissionError("session does not belong to this user")
                if chat_type.strip():
                    session["type"] = chat_type.strip()
                if level.strip():
                    session["level"] = level.strip()
                if parsed_words:
                    session["words"] = parsed_words
                session["updated_at"] = self._now_iso()
                self._save()
                return {"session_id": normalized_session_id, **session}

            if not chat_type.strip():
                raise ValueError("type is required when creating a new session")
            if not parsed_words:
                raise ValueError("words is required when creating a new session")

            new_session_id = normalized_session_id or uuid4().hex
            now_iso = self._now_iso()
            session = {
                "user_id": user_id,
                "type": chat_type.strip(),
                "level": level.strip() or "A2",
                "words": parsed_words,
                "messages": [],
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            self._sessions[new_session_id] = session
            self._save()
            return {"session_id": new_session_id, **session}

    def append_message(self, session_id: str, role: str, content: str) -> list[dict[str, str]]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError("session not found")
            message = {
                "role": role,
                "content": content,
                "created_at": self._now_iso(),
            }
            session_messages = session.setdefault("messages", [])
            session_messages.append(message)
            if len(session_messages) > self._max_history_messages:
                session["messages"] = session_messages[-self._max_history_messages :]
            session["updated_at"] = self._now_iso()
            self._save()
            return list(session["messages"])

    def get_session(self, session_id: str) -> dict:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError("session not found")
            return {
                "session_id": session_id,
                "user_id": session["user_id"],
                "type": session["type"],
                "level": session["level"],
                "words": list(session.get("words", [])),
                "messages": list(session.get("messages", [])),
            }

    def get_user_recent_sessions(self, user_id: str, limit: int = 5) -> list[dict]:
        with self._lock:
            user_sessions = [
                {"session_id": sid, **s}
                for sid, s in self._sessions.items()
                if s.get("user_id") == user_id
            ]
            user_sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
            return user_sessions[:limit]
