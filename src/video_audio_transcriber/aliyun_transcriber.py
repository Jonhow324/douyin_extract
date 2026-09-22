import base64
import mimetypes
import os
from pathlib import Path

import httpx

from video_audio_transcriber.transcriber import MissingAPIKeyError, _get_audio_duration


class AliyunTranscriber:
    API_URL = "https://dashscope.aliyuncs.com/api/v1/services/multimodal-generation"
    MODEL = "qwen3-asr-flash"

    def transcribe(self, audio_path: Path, source_url: str = "") -> tuple[dict, str]:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("请设置环境变量 DASHSCOPE_API_KEY")

        duration = _get_audio_duration(audio_path)
        audio_base64 = self._encode_audio(audio_path)

        with httpx.Client(timeout=120, trust_env=False) as client:
            response = client.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.MODEL,
                    "input": {
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"audio": f"data:{self._mime_type(audio_path)};base64,{audio_base64}"}],
                            }
                        ]
                    },
                    "parameters": {
                        "result_format": "message",
                    },
                },
            )

            if response.status_code != 200:
                raise Exception(f"ASR API 请求失败: {response.status_code} {response.text}")

            data = self._parse_response(response.json(), duration, source_url)
            video_id = audio_path.stem
            return data, video_id

    def _encode_audio(self, audio_path: Path) -> str:
        return base64.b64encode(audio_path.read_bytes()).decode("utf-8")

    def _mime_type(self, audio_path: Path) -> str:
        mime, _ = mimetypes.guess_type(str(audio_path))
        return mime or "audio/mpeg"

    def _parse_response(self, response: dict, duration: float, source_url: str) -> dict:
        content = response["output"]["choices"][0]["message"]["content"]

        segments = []
        text_parts = []

        for item in content:
            text = item.get("text", "")
            text_parts.append(text)

            start_time = item.get("start_time")
            end_time = item.get("end_time")

            if start_time is not None and end_time is not None:
                segments.append({
                    "text": text,
                    "start": start_time / 1000.0,
                    "end": end_time / 1000.0,
                    "speaker": "",
                })
            else:
                segments.append({
                    "text": text,
                    "start": 0.0,
                    "end": 0.0,
                    "speaker": "",
                })

        return {
            "text": "".join(text_parts),
            "duration": duration,
            "segments": segments,
            "source_url": source_url,
        }
