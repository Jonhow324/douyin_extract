import base64
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video_audio_transcriber.aliyun_transcriber import AliyunTranscriber
from video_audio_transcriber.transcriber import MissingAPIKeyError


class TestAliyunTranscriber:
    def test_transcribe_missing_api_key(self, tmp_path):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("DASHSCOPE_API_KEY", None)

            transcriber = AliyunTranscriber()
            audio_path = tmp_path / "test.mp3"
            audio_path.write_bytes(b"fake audio content")

            with pytest.raises(MissingAPIKeyError, match="DASHSCOPE_API_KEY"):
                transcriber.transcribe(audio_path)

    def test_transcribe_success_with_segments(self, tmp_path):
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test_dashscope_key"}):
            with patch("video_audio_transcriber.aliyun_transcriber._get_audio_duration", return_value=10.0):
                with patch("video_audio_transcriber.aliyun_transcriber.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "output": {
                            "choices": [{
                                "message": {
                                    "role": "assistant",
                                    "content": [
                                        {"text": "大家好"},
                                        {"text": "今天聊一下", "start_time": 3000, "end_time": 8500}
                                    ]
                                }
                            }]
                        },
                        "usage": {"duration": 10}
                    }

                    mock_instance = MagicMock()
                    mock_instance.post.return_value = mock_response
                    mock_instance.__enter__.return_value = mock_instance
                    mock_client.return_value = mock_instance

                    transcriber = AliyunTranscriber()
                    audio_path = tmp_path / "douyin_test.mp3"
                    audio_path.write_bytes(b"fake audio content")

                    data, video_id = transcriber.transcribe(audio_path)

                    assert video_id == "douyin_test"
                    assert data["text"] == "大家好今天聊一下"
                    assert data["duration"] == 10.0
                    assert len(data["segments"]) == 2
                    assert data["segments"][0]["text"] == "大家好"
                    assert data["segments"][0]["start"] == 0.0
                    assert data["segments"][0]["speaker"] == ""
                    assert data["segments"][1]["text"] == "今天聊一下"
                    assert data["segments"][1]["start"] == 3.0
                    assert data["segments"][1]["end"] == 8.5

                    mock_instance.post.assert_called_once()

    def test_transcribe_api_error_response(self, tmp_path):
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test_key"}):
            with patch("video_audio_transcriber.aliyun_transcriber._get_audio_duration", return_value=10.0):
                with patch("video_audio_transcriber.aliyun_transcriber.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 400
                    mock_response.text = "Invalid audio format"

                    mock_instance = MagicMock()
                    mock_instance.post.return_value = mock_response
                    mock_instance.__enter__.return_value = mock_instance
                    mock_client.return_value = mock_instance

                    transcriber = AliyunTranscriber()
                    audio_path = tmp_path / "test.mp3"
                    audio_path.write_bytes(b"fake audio")

                    with pytest.raises(Exception, match="400"):
                        transcriber.transcribe(audio_path)

    def test_request_format(self, tmp_path):
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test_key_456"}):
            with patch("video_audio_transcriber.aliyun_transcriber._get_audio_duration", return_value=10.0):
                with patch("video_audio_transcriber.aliyun_transcriber.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "output": {
                            "choices": [{
                                "message": {
                                    "content": [{"text": "test"}]
                                }
                            }]
                        },
                        "usage": {"duration": 10}
                    }

                    mock_instance = MagicMock()
                    mock_instance.post.return_value = mock_response
                    mock_instance.__enter__.return_value = mock_instance
                    mock_client.return_value = mock_instance

                    transcriber = AliyunTranscriber()
                    audio_path = tmp_path / "douyin_audio.mp3"
                    audio_path.write_bytes(b"audio data")

                    transcriber.transcribe(audio_path)

                    call_args = mock_instance.post.call_args
                    assert call_args.args[0] == "https://dashscope.aliyuncs.com/api/v1/services/multimodal-generation"
                    assert "Authorization" in call_args.kwargs.get("headers", {})
                    assert "Bearer test_key_456" in call_args.kwargs["headers"]["Authorization"]

                    json_body = call_args.kwargs["json"]
                    assert json_body["model"] == "qwen3-asr-flash"
                    assert "input" in json_body
                    assert "messages" in json_body["input"]
                    assert json_body["input"]["messages"][0]["role"] == "user"

                    content = json_body["input"]["messages"][0]["content"]
                    assert len(content) == 1
                    assert "audio" in content[0]
                    audio_data = content[0]["audio"]
                    assert audio_data.startswith("data:audio/mpeg;base64,")
