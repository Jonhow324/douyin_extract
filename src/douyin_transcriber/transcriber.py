import os
from pathlib import Path

import httpx

from douyin_transcriber import TranscriptionResult, TranscriptionSegment


class MissingAPIKeyError(Exception):
    pass


class Transcriber:
    API_URL = "https://api.minimax.cn/v1/speech_to_text"

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        api_key = os.environ.get("MINIMAX_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("请设置环境变量 MINIMAX_API_KEY")

        with httpx.Client(timeout=120, trust_env=False) as client:
            with open(audio_path, "rb") as audio_file:
                response = client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                    },
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
            video_id = audio_path.stem.removeprefix("douyin_")
            return self._parse_response(data, video_id)

    def _parse_response(self, data: dict, video_id: str = "") -> TranscriptionResult:
        if "segments" in data and data["segments"]:
            segments = [
                TranscriptionSegment(
                    text=seg["text"],
                    start=seg.get("start"),
                    end=seg.get("end"),
                )
                for seg in data["segments"]
            ]
        else:
            segments = [TranscriptionSegment(text=data.get("text", ""))]

        return TranscriptionResult(segments=segments, video_id=video_id)
