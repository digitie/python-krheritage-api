from __future__ import annotations

from krheritage.codes import KoglLicense, Lang
from krheritage.models.base import KrHeritageModel


class MediaImage(KrHeritageModel):
    image_url: str
    description: str | None = None
    license: KoglLicense | None = None


class MediaVideo(KrHeritageModel):
    title: str
    video_url: str
    duration_sec: int | None = None
    license: KoglLicense | None = None


class Narration(KrHeritageModel):
    lang: Lang
    audio_url: str
    transcript: str | None = None

