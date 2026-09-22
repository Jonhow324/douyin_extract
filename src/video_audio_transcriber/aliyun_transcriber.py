import base64
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx

from video_audio_transcriber.transcriber import MissingAPIKeyError, _find_ffmpeg_dir, _get_audio_duration

_SENTENCE_ENDINGS = set("。！？；.!?;\n")

_FORMAT_MAP = {
    ".mp3": "mp3",
    ".wav": "wav",
    ".m4a": "mp4",
    ".mp4": "mp4",
    ".aac": "aac",
    ".ogg": "ogg",
    ".flac": "flac",
    ".opus": "opus",
}

_MIME_MAP = {
    "mp3": "mpeg",
    "wav": "wav",
    "mp4": "mp4",
    "aac": "aac",
    "ogg": "ogg",
    "flac": "flac",
    "opus": "opus",
}


class AliyunTranscriber:
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com"
    MODEL = "qwen-audio-3.0-asr-flash"
    MAX_RAW_SIZE = 3_500_000

    def transcribe(self, audio_path: Path, source_url: str = "") -> tuple[dict, str]:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("请设置环境变量 DASHSCOPE_API_KEY")

        base_url = os.environ.get("DASHSCOPE_BASE_URL", self.DEFAULT_BASE_URL)
        parsed = urlparse(base_url)
        api_url = f"{parsed.scheme}://{parsed.netloc}/api/v1/services/aigc/multimodal-generation/generation"

        duration = _get_audio_duration(audio_path)
        audio_b64, audio_format = self._prepare_audio(audio_path)
        mime_type = _MIME_MAP.get(audio_format, audio_format)

        with httpx.Client(timeout=300, trust_env=False) as client:
            response = client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-DashScope-SSE": "disable",
                },
                json={
                    "model": self.MODEL,
                    "input": {
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"audio": f"data:audio/{mime_type};base64,{audio_b64}"}
                                ],
                            }
                        ]
                    },
                    "parameters": {"format": audio_format},
                },
            )

            if response.status_code != 200:
                raise Exception(f"ASR API 请求失败: {response.status_code} {response.text}")

            data = self._parse_response(response.json(), duration, source_url)
            return data, audio_path.stem

    def _prepare_audio(self, audio_path: Path) -> tuple[str, str]:
        if audio_path.stat().st_size <= self.MAX_RAW_SIZE:
            fmt = _FORMAT_MAP.get(audio_path.suffix.lower(), "mp3")
            return base64.b64encode(audio_path.read_bytes()).decode("utf-8"), fmt
        return self._compress_and_encode(audio_path)

    def _compress_and_encode(self, audio_path: Path) -> tuple[str, str]:
        ffmpeg_cmd = "ffmpeg"
        ffmpeg_dir = _find_ffmpeg_dir()
        if ffmpeg_dir:
            ffmpeg_cmd = str(ffmpeg_dir / "ffmpeg.exe")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            compressed_path = Path(f.name)

        try:
            subprocess.run(
                [ffmpeg_cmd, "-y", "-i", str(audio_path),
                 "-acodec", "libmp3lame", "-ab", "48k",
                 "-ar", "16000", "-ac", "1",
                 str(compressed_path)],
                capture_output=True,
                check=True,
            )
            return base64.b64encode(compressed_path.read_bytes()).decode("utf-8"), "mp3"
        finally:
            compressed_path.unlink(missing_ok=True)

    def _parse_response(self, response: dict, duration: float, source_url: str) -> dict:
        output = response.get("output", {})
        text = output.get("text", "")
        words = output.get("sentence", {}).get("words", [])

        return {
            "text": text,
            "duration": duration,
            "segments": self._words_to_segments(words),
            "source_url": source_url,
        }

    def _words_to_segments(self, words: list[dict]) -> list[dict]:
        if not words:
            return []

        segments = []
        current_words: list[dict] = []

        for word in words:
            current_words.append(word)
            if word.get("punctuation", "") in _SENTENCE_ENDINGS:
                segments.append(self._make_segment(current_words))
                current_words = []

        if current_words:
            segments.append(self._make_segment(current_words))

        return segments

    @staticmethod
    def _make_segment(words: list[dict]) -> dict:
        text = "".join(w["text"] + w.get("punctuation", "") for w in words)
        return {
            "text": text,
            "start": words[0]["begin_time"] / 1000.0,
            "end": words[-1]["end_time"] / 1000.0,
            "speaker": "",
        }
