from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas import (
    DigitalHumanChatRequest,
    DigitalHumanChatResponse,
    DigitalHumanJobResponse,
    DigitalHumanStatusResponse,
)
from app.services.digital_human_service import digital_human_service

router = APIRouter(prefix="/digital-human", tags=["digital-human"])


@router.get("/status")
def digital_human_status() -> DigitalHumanStatusResponse:
    return DigitalHumanStatusResponse(**digital_human_service.status())


@router.post("/chat")
async def digital_human_chat(payload: DigitalHumanChatRequest) -> DigitalHumanChatResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message is empty")

    try:
        result = await digital_human_service.chat(
            user_id=payload.user_id,
            message=payload.message,
            level=payload.level,
            avatar_id=payload.avatar_id,
            voice=payload.voice,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return DigitalHumanChatResponse(**result)


@router.get("/jobs/{job_id}")
def digital_human_job(job_id: str) -> DigitalHumanJobResponse:
    result = digital_human_service.get_job(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="job not found")
    return DigitalHumanJobResponse(**result)


@router.get("/media/{filename}")
def digital_human_media(filename: str) -> FileResponse:
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="invalid filename")
    media_path = Path(settings.digital_human_media_dir) / filename
    if not media_path.exists() or media_path.suffix != ".mp3":
        raise HTTPException(status_code=404, detail="media not found")
    return FileResponse(path=media_path, media_type="audio/mpeg")
