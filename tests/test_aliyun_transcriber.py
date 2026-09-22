import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video_audio_transcriber.aliyun_transcriber import AliyunTranscriber
from video_audio_transcriber.transcriber import MissingAPIKeyError


def _mock_response(output_json: dict) -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = output_json
    return mock


def _mock_client(mock_response: MagicMock) -> MagicMock:
    mock_instance = MagicMock()
    mock_instance.post.return_value = mock_response
    mock_instance.__enter__.return_value = mock_instance
    return mock_instance


WORDS_RESPONSE = {
    "output": {
        "text": "大家好。今天聊一下。",
        "sentence": {
            "sentence_id": 1,
            "begin_time": 0,
            "end_time": 8500,
            "text": "大家好。今天聊一下。",
            "sentence_end": True,
            "words": [
                {"begin_time": 0, "end_time": 500, "text": "大家", "punctuation": "", "fixed": True, "speaker_id": None},
                {"begin_time": 500, "end_time": 1000, "text": "好", "punctuation": "。", "fixed": True, "speaker_id": None},
                {"begin_time": 3000, "end_time": 4000, "text": "今天", "punctuation": "", "fixed": True, "speaker_id": None},
                {"begin_time": 4000, "end_time": 5000, "text": "聊", "punctuation": "", "fixed": True, "speaker_id": None},
                {"begin_time": 5000, "end_time": 6000, "text": "一下", "punctuation": "。", "fixed": True, "speaker_id": None},
            ],
        },
        "request_id": "test-request-id",
    },
}


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
                    mock_client.return_value = _mock_client(_mock_response(WORDS_RESPONSE))

                    transcriber = AliyunTranscriber()
                    audio_path = tmp_path / "douyin_test.mp3"
                    audio_path.write_bytes(b"fake audio content")

                    data, video_id = transcriber.transcribe(audio_path)

                    assert video_id == "douyin_test"
                    assert data["text"] == "大家好。今天聊一下。"
                    assert data["duration"] == 10.0
                    assert len(data["segments"]) == 2

                    assert data["segments"][0]["text"] == "大家好。"
                    assert data["segments"][0]["start"] == 0.0
                    assert data["segments"][0]["end"] == 1.0
                    assert data["segments"][0]["speaker"] == ""

                    assert data["segments"][1]["text"] == "今天聊一下。"
                    assert data["segments"][1]["start"] == 3.0
                    assert data["segments"][1]["end"] == 6.0

    def test_transcribe_api_error_response(self, tmp_path):
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test_key"}):
            with patch("video_audio_transcriber.aliyun_transcriber._get_audio_duration", return_value=10.0):
                with patch("video_audio_transcriber.aliyun_transcriber.httpx.Client") as mock_client:
                    mock_resp = MagicMock()
                    mock_resp.status_code = 400
                    mock_resp.text = "Invalid audio format"

                    mock_client.return_value = _mock_client(mock_resp)

                    transcriber = AliyunTranscriber()
                    audio_path = tmp_path / "test.mp3"
                    audio_path.write_bytes(b"fake audio")

                    with pytest.raises(Exception, match="400"):
                        transcriber.transcribe(audio_path)

    def test_request_format(self, tmp_path):
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test_key_456"}):
            with patch("video_audio_transcriber.aliyun_transcriber._get_audio_duration", return_value=10.0):
                with patch("video_audio_transcriber.aliyun_transcriber.httpx.Client") as mock_client:
                    simple_response = {
                        "output": {
                            "text": "测试文本",
                            "sentence": {
                                "words": [
                                    {"begin_time": 0, "end_time": 2000, "text": "测试", "punctuation": ""},
                                    {"begin_time": 2000, "end_time": 4000, "text": "文本", "punctuation": "。"},
                                ],
                            },
                        },
                    }
                    mock_client.return_value = _mock_client(_mock_response(simple_response))

                    transcriber = AliyunTranscriber()
                    audio_path = tmp_path / "douyin_audio.mp3"
                    audio_path.write_bytes(b"audio data")

                    transcriber.transcribe(audio_path)

                    call_args = mock_client.return_value.post.call_args
                    url = call_args.args[0]
                    assert "aigc/multimodal-generation/generation" in url
                    assert "/compatible-mode/" not in url

                    headers = call_args.kwargs.get("headers", {})
                    assert "Bearer test_key_456" in headers["Authorization"]
                    assert headers.get("X-DashScope-SSE") == "disable"

                    json_body = call_args.kwargs["json"]
                    assert json_body["model"] == "qwen-audio-3.0-asr-flash"
                    assert json_body["parameters"]["format"] == "mp3"

                    content = json_body["input"]["messages"][0]["content"]
                    assert content[0]["audio"].startswith("data:audio/mpeg;base64,")

    def test_url_strips_compatible_mode_suffix(self, tmp_path):
        env = {
            "DASHSCOPE_API_KEY": "test_key",
            "DASHSCOPE_BASE_URL": "https://llm-xxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
        }
        with patch.dict(os.environ, env):
            with patch("video_audio_transcriber.aliyun_transcriber._get_audio_duration", return_value=10.0):
                with patch("video_audio_transcriber.aliyun_transcriber.httpx.Client") as mock_client:
                    mock_client.return_value = _mock_client(_mock_response(WORDS_RESPONSE))

                    transcriber = AliyunTranscriber()
                    audio_path = tmp_path / "test.mp3"
                    audio_path.write_bytes(b"fake audio")

                    transcriber.transcribe(audio_path)

                    url = mock_client.return_value.post.call_args.args[0]
                    assert url == "https://llm-xxx.cn-beijing.maas.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

    def test_words_without_punctuation_form_single_segment(self, tmp_path):
        response = {
            "output": {
                "text": "没有标点的文本",
                "sentence": {
                    "words": [
                        {"begin_time": 0, "end_time": 500, "text": "没有", "punctuation": ""},
                        {"begin_time": 500, "end_time": 1000, "text": "标点", "punctuation": ""},
                        {"begin_time": 1000, "end_time": 1500, "text": "的文本", "punctuation": ""},
                    ],
                },
            },
        }
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test_key"}):
            with patch("video_audio_transcriber.aliyun_transcriber._get_audio_duration", return_value=5.0):
                with patch("video_audio_transcriber.aliyun_transcriber.httpx.Client") as mock_client:
                    mock_client.return_value = _mock_client(_mock_response(response))

                    transcriber = AliyunTranscriber()
                    audio_path = tmp_path / "test.mp3"
                    audio_path.write_bytes(b"fake")

                    data, _ = transcriber.transcribe(audio_path)

                    assert len(data["segments"]) == 1
                    assert data["segments"][0]["text"] == "没有标点的文本"
                    assert data["segments"][0]["start"] == 0.0
                    assert data["segments"][0]["end"] == 1.5
