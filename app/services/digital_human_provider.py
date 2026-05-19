from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class DigitalHumanRequest:
    job_id: str
    avatar_id: str
    text: str
    audio_url: str
    audio_mime_type: str = "audio/mpeg"


@dataclass(frozen=True)
class DigitalHumanResult:
    job_id: str
    provider: str
    status: str
    video_url: str = ""
    stream_url: str = ""
    message: str = ""


class AvatarProvider(ABC):
    name = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate_from_audio(self, payload: DigitalHumanRequest) -> DigitalHumanResult:
        raise NotImplementedError

    def query(self, job_id: str) -> DigitalHumanResult:
        return DigitalHumanResult(
            job_id=job_id,
            provider=self.name,
            status="unknown",
            message="This provider does not implement job polling yet.",
        )


class MockAvatarProvider(AvatarProvider):
    name = "mock"

    def is_configured(self) -> bool:
        return True

    def generate_from_audio(self, payload: DigitalHumanRequest) -> DigitalHumanResult:
        return DigitalHumanResult(
            job_id=payload.job_id,
            provider=self.name,
            status="mock_ready",
            video_url=settings.digital_human_mock_video_url,
            message=(
                "Mock digital human response. Configure a real provider to generate "
                "a talking avatar video or stream."
            ),
        )


class TencentDigitalHumanProvider(AvatarProvider):
    name = "tencent"

    def is_configured(self) -> bool:
        return bool(
            settings.tencent_secret_id
            and settings.tencent_secret_key
            and settings.tencent_digital_human_app_id
            and settings.tencent_digital_human_avatar_id
        )

    def generate_from_audio(self, payload: DigitalHumanRequest) -> DigitalHumanResult:
        if not self.is_configured():
            return DigitalHumanResult(
                job_id=payload.job_id,
                provider=self.name,
                status="configuration_required",
                message=(
                    "Tencent digital human credentials or avatar id are missing. "
                    "Set TENCENT_SECRET_ID, TENCENT_SECRET_KEY, "
                    "TENCENT_DIGITAL_HUMAN_APP_ID, and TENCENT_DIGITAL_HUMAN_AVATAR_ID."
                ),
            )

        return DigitalHumanResult(
            job_id=payload.job_id,
            provider=self.name,
            status="provider_adapter_required",
            message=(
                "Tencent credentials are present, but the exact product endpoint/signing "
                "adapter is intentionally isolated here. Fill this provider after the "
                "Tencent console confirms your digital human API mode."
            ),
        )


def build_avatar_provider() -> AvatarProvider:
    provider = settings.digital_human_provider.lower().strip()
    if provider == "tencent":
        return TencentDigitalHumanProvider()
    return MockAvatarProvider()
