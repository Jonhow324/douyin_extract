from dataclasses import dataclass, field


@dataclass
class TranscriptionSegment:
    text: str
    start: float | None = None
    end: float | None = None


@dataclass
class TranscriptionResult:
    segments: list[TranscriptionSegment] = field(default_factory=list)
    video_id: str = ""
