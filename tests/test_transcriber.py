import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from douyin_transcriber.transcriber import MissingAPIKeyError, Transcriber


class TestTranscriber:
    def test_transcribe_missing_api_key(self, tmp_path):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MINIMAX_API_KEY", None)

            transcriber = Transcriber()
            audio_path = tmp_path / "test.mp3"
            audio_path.write_bytes(b"fake audio content")

            with pytest.raises(MissingAPIKeyError, match="MINIMAX_API_KEY"):
                transcriber.transcribe(audio_path)

    def test_transcribe_success_with_segments(self, tmp_path):
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test_key_123"}):
            with patch("douyin_transcriber.transcriber.httpx.Client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "text": "大家好今天聊一下",
                    "duration": 10.5,
                    "segments": [
                        {"text": "大家好", "start": 0.0, "end": 2.5, "speaker": "S1"},
                        {"text": "今天聊一下", "start": 3.0, "end": 8.5, "speaker": "S1"},
                    ]
                }

                mock_instance = MagicMock()
                mock_instance.post.return_value = mock_response
                mock_instance.__enter__.return_value = mock_instance
                mock_client.return_value = mock_instance

                transcriber = Transcriber()
                audio_path = tmp_path / "douyin_test.mp3"
                audio_path.write_bytes(b"fake audio content")

                data, video_id = transcriber.transcribe(audio_path)

                assert video_id == "test"
                assert data["text"] == "大家好今天聊一下"
                assert data["duration"] == 10.5
                assert len(data["segments"]) == 2
                assert data["segments"][0]["text"] == "大家好"
                assert data["segments"][0]["start"] == 0.0
                assert data["segments"][0]["speaker"] == "S1"

                mock_instance.post.assert_called_once()

    def test_transcribe_success_without_segments(self, tmp_path):
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test_key"}):
            with patch("douyin_transcriber.transcriber.httpx.Client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "text": "完整的转录文本"
                }

                mock_instance = MagicMock()
                mock_instance.post.return_value = mock_response
                mock_instance.__enter__.return_value = mock_instance
                mock_client.return_value = mock_instance

                transcriber = Transcriber()
                audio_path = tmp_path / "douyin_test.mp3"
                audio_path.write_bytes(b"fake audio")

                data, video_id = transcriber.transcribe(audio_path)

                assert video_id == "test"
                assert data["text"] == "完整的转录文本"

    def test_transcribe_api_error_response(self, tmp_path):
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test_key"}):
            with patch("douyin_transcriber.transcriber.httpx.Client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 400
                mock_response.text = "Invalid audio format"

                mock_instance = MagicMock()
                mock_instance.post.return_value = mock_response
                mock_instance.__enter__.return_value = mock_instance
                mock_client.return_value = mock_instance

                transcriber = Transcriber()
                audio_path = tmp_path / "test.mp3"
                audio_path.write_bytes(b"fake audio")

                with pytest.raises(Exception, match="400"):
                    transcriber.transcribe(audio_path)

    def test_transcribe_request_format(self, tmp_path):
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test_key_456"}):
            with patch("douyin_transcriber.transcriber.httpx.Client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"text": "test"}

                mock_instance = MagicMock()
                mock_instance.post.return_value = mock_response
                mock_instance.__enter__.return_value = mock_instance
                mock_client.return_value = mock_instance

                transcriber = Transcriber()
                audio_path = tmp_path / "douyin_audio.mp3"
                audio_path.write_bytes(b"audio data")

                transcriber.transcribe(audio_path)

                call_args = mock_instance.post.call_args
                assert call_args.args[0] == "https://api.minimax.cn/v1/speech_to_text"
                assert "Authorization" in call_args.kwargs.get("headers", {})
                assert "Bearer test_key_456" in call_args.kwargs["headers"]["Authorization"]
                assert call_args.kwargs["data"]["model"] == "asr-1.0"
                assert call_args.kwargs["data"]["response_format"] == "verbose_json"
                assert call_args.kwargs["data"]["timestamp_level"] == "sentence"
