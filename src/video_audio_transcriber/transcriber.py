import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Protocol

import httpx


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path, source_url: str = "") -> tuple[dict, str]:
        ...


class MissingAPIKeyError(Exception):
    pass


FFMPEG_LOCATIONS = [
    Path("C:/Users/92064/AppData/Local/Microsoft/WinGet/Packages")
    / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-9.0.1-full_build" / "bin",
]


def _find_ffmpeg_dir() -> Path | None:
    if shutil.which("ffmpeg"):
        return None
    for location in FFMPEG_LOCATIONS:
        if location.exists():
            return location
    return None


def _get_audio_duration(audio_path: Path) -> float:
    ffmpeg_dir = _find_ffmpeg_dir()
    ffprobe_cmd = "ffprobe"
    if ffmpeg_dir:
        ffprobe_cmd = str(ffmpeg_dir / "ffprobe.exe")

    result = subprocess.run(
        [ffprobe_cmd, "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


class MiniMaxTranscriber:
    API_URL = "https://api.minimax.cn/v1/speech_to_text"

    def transcribe(self, audio_path: Path, source_url: str = "") -> tuple[dict, str]:
        api_key = os.environ.get("MINIMAX_ASR_KEY")
        if not api_key:
            raise MissingAPIKeyError("请设置环境变量 MINIMAX_ASR_KEY")

        with httpx.Client(timeout=120, trust_env=False) as client:
            with open(audio_path, "rb") as audio_file:
                response = client.post(
                    self.API_URL,
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"file": audio_file},
                    data={
                        "model": "asr-1.0",
                        "response_format": "verbose_json",
                        "timestamp_level": "sentence",
                    },
                )

            if response.status_code != 200:
                raise Exception(f"ASR API 请求失败: {response.status_code} {response.text}")

            data = response.json()
            data["source_url"] = source_url
            video_id = audio_path.stem
            return data, video_id


class LongAudioWrapper:
    def __init__(self, transcriber: Transcriber, max_duration_seconds: int = 480):
        self._transcriber = transcriber
        self._max_duration = max_duration_seconds

    def transcribe(self, audio_path: Path, source_url: str = "") -> tuple[dict, str]:
        duration = _get_audio_duration(audio_path)

        if duration <= self._max_duration:
            return self._transcriber.transcribe(audio_path, source_url)

        return self._transcribe_long(audio_path, source_url, duration)

    def _transcribe_long(self, audio_path: Path, source_url: str, total_duration: float) -> tuple[dict, str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            chunks = self._split_audio(audio_path, Path(temp_dir))

            all_segments = []
            offset = 0.0

            for chunk_path in chunks:
                chunk_data, _ = self._transcriber.transcribe(chunk_path, source_url)

                if "segments" in chunk_data:
                    for seg in chunk_data["segments"]:
                        seg["start"] = seg.get("start", 0) + offset
                        seg["end"] = seg.get("end", 0) + offset
                        seg["id"] = len(all_segments)
                        all_segments.append(seg)

                offset += _get_audio_duration(chunk_path)

            merged_data = {
                "text": "".join(seg["text"] for seg in all_segments),
                "duration": total_duration,
                "segments": all_segments,
                "source_url": source_url,
            }

            video_id = audio_path.stem
            return merged_data, video_id

    def _split_audio(self, audio_path: Path, output_dir: Path) -> list[Path]:
        duration = _get_audio_duration(audio_path)
        num_chunks = int(duration / self._max_duration) + 1
        chunk_duration = duration / num_chunks

        ffmpeg_dir = _find_ffmpeg_dir()
        ffmpeg_cmd = "ffmpeg"
        if ffmpeg_dir:
            ffmpeg_cmd = str(ffmpeg_dir / "ffmpeg.exe")

        chunks = []
        for i in range(num_chunks):
            start_time = i * chunk_duration
            chunk_path = output_dir / f"chunk_{i}.mp3"

            subprocess.run(
                [ffmpeg_cmd, "-i", str(audio_path), "-ss", str(start_time),
                 "-t", str(chunk_duration), "-acodec", "libmp3lame",
                 "-q:a", "2", str(chunk_path), "-y"],
                capture_output=True,
            )
            chunks.append(chunk_path)

        return chunks


def get_transcriber(provider: str) -> LongAudioWrapper:
    if provider == "aliyun":
        from video_audio_transcriber.aliyun_transcriber import AliyunTranscriber
        return LongAudioWrapper(AliyunTranscriber())
    elif provider == "minimax":
        return LongAudioWrapper(MiniMaxTranscriber())
    else:
        raise ValueError(f"不支持的 provider: {provider}（可选: minimax, aliyun）")
