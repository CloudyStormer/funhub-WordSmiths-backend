import json
import uuid
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.ai_service import ai_service
from app.services.digital_human_provider import DigitalHumanRequest, build_avatar_provider
from app.services.tts_service import synthesize_audio


class DigitalHumanService:
    def __init__(self) -> None:
        self._provider = build_avatar_provider()
        self._media_dir = Path(settings.digital_human_media_dir)
        self._jobs_path = self._media_dir / "jobs.json"

    def status(self) -> dict[str, Any]:
        return {
            "provider": self._provider.name,
            "provider_configured": self._provider.is_configured(),
            "media_dir": str(self._media_dir),
            "public_base_url": settings.digital_human_public_base_url,
            "supports": {
                "text_chat": True,
                "xfyun_tts": True,
                "audio_driven_avatar": self._provider.name != "mock",
                "browser_asr_recommended_for_mvp": True,
            },
        }

    def _ensure_media_dir(self) -> None:
        self._media_dir.mkdir(parents=True, exist_ok=True)

    def _audio_url(self, job_id: str) -> str:
        base_url = settings.digital_human_public_base_url.rstrip("/")
        return f"{base_url}/digital-human/media/{job_id}.mp3"

    def _write_audio(self, job_id: str, audio_bytes: bytes) -> str:
        self._ensure_media_dir()
        audio_path = self._media_dir / f"{job_id}.mp3"
        audio_path.write_bytes(audio_bytes)
        return self._audio_url(job_id)

    def _read_jobs(self) -> dict[str, Any]:
        if not self._jobs_path.exists():
            return {}
        try:
            return json.loads(self._jobs_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write_job(self, job_id: str, payload: dict[str, Any]) -> None:
        self._ensure_media_dir()
        jobs = self._read_jobs()
        jobs[job_id] = payload
        self._jobs_path.write_text(
            json.dumps(jobs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        local_job = self._read_jobs().get(job_id)
        if not local_job:
            return None

        provider_result = self._provider.query(job_id)
        local_job["provider_query"] = {
            "status": provider_result.status,
            "video_url": provider_result.video_url,
            "stream_url": provider_result.stream_url,
            "message": provider_result.message,
        }
        return local_job

    async def chat(
        self,
        user_id: str,
        message: str,
        level: str,
        avatar_id: str,
        voice: str,
    ) -> dict[str, Any]:
        user_message = message.strip()
        job_id = uuid.uuid4().hex
        reply_text = ai_service.chat(user_message=user_message, level=level)
        audio_bytes = await synthesize_audio(reply_text, voice=voice)
        audio_url = self._write_audio(job_id, audio_bytes)
        active_avatar_id = avatar_id or settings.tencent_digital_human_avatar_id or "default"

        avatar_result = self._provider.generate_from_audio(
            DigitalHumanRequest(
                job_id=job_id,
                avatar_id=active_avatar_id,
                text=reply_text,
                audio_url=audio_url,
            )
        )
        response = {
            "job_id": job_id,
            "user_id": user_id,
            "user_text": user_message,
            "reply_text": reply_text,
            "audio_url": audio_url,
            "avatar": {
                "provider": avatar_result.provider,
                "avatar_id": active_avatar_id,
                "status": avatar_result.status,
                "video_url": avatar_result.video_url,
                "stream_url": avatar_result.stream_url,
                "message": avatar_result.message,
            },
        }
        self._write_job(job_id, response)
        return response


digital_human_service = DigitalHumanService()
