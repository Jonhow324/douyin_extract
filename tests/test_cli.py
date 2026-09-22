import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video_audio_transcriber.cli import main
from video_audio_transcriber.extractor import InvalidURLError
from video_audio_transcriber.transcriber import MissingAPIKeyError


class TestCLI:
    def test_main_pipeline_success(self, tmp_path, capsys):
        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.get_transcriber") as mock_get_transcriber, \
             patch("video_audio_transcriber.cli.sys.argv", ["video-audio-transcribe", "https://v.douyin.com/test123/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_video_abc.mp3"
            audio_path.write_bytes(b"fake audio")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_get_transcriber.return_value = mock_transcriber

            api_response = {
                "text": "大家好今天聊一下",
                "duration": 10.5,
                "segments": [
                    {"text": "大家好", "start": 0.0, "end": 2.5, "speaker": "S1"},
                    {"text": "今天聊一下", "start": 3.0, "end": 8.5, "speaker": "S1"},
                ]
            }
            mock_transcriber.transcribe.return_value = (api_response, "douyin_video_abc")

            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)
                main()
            finally:
                os.chdir(old_cwd)

            output_file = tmp_path / "outputs" / "json" / "douyin_video_abc.json"
            assert output_file.exists()
            content = json.loads(output_file.read_text(encoding="utf-8"))
            assert content["text"] == "大家好今天聊一下"
            assert len(content["segments"]) == 2
            assert content["segments"][0]["text"] == "大家好"

    def test_main_pipeline_cleans_up_on_error(self, tmp_path):
        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.get_transcriber") as mock_get_transcriber, \
             patch("video_audio_transcriber.cli.sys.argv", ["video-audio-transcribe", "https://v.douyin.com/test/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_video_xyz.mp3"
            audio_path.write_bytes(b"fake audio")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_get_transcriber.return_value = mock_transcriber
            mock_transcriber.transcribe.side_effect = Exception("API Error")

            with patch("video_audio_transcriber.cli.Path.cwd", return_value=tmp_path):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

    def test_main_output_filename_format(self, tmp_path):
        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.get_transcriber") as mock_get_transcriber, \
             patch("video_audio_transcriber.cli.sys.argv", ["video-audio-transcribe", "https://v.douyin.com/abc/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_test_id_123.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_get_transcriber.return_value = mock_transcriber

            api_response = {"text": "测试", "segments": []}
            mock_transcriber.transcribe.return_value = (api_response, "douyin_test_id_123")

            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)
                main()
            finally:
                os.chdir(old_cwd)

            output_file = tmp_path / "outputs" / "json" / "douyin_test_id_123.json"
            assert output_file.exists()

    def test_main_json_output_format(self, tmp_path):
        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.get_transcriber") as mock_get_transcriber, \
             patch("video_audio_transcriber.cli.sys.argv", ["video-audio-transcribe", "https://v.douyin.com/test/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_vid.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_get_transcriber.return_value = mock_transcriber

            api_response = {
                "text": "有时间戳的文字",
                "duration": 15.0,
                "n_speakers": 1,
                "segments": [
                    {"text": "有时间戳的文字", "start": 10.0, "end": 15.0, "speaker": "S1"},
                ]
            }
            mock_transcriber.transcribe.return_value = (api_response, "douyin_vid")

            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)
                main()
            finally:
                os.chdir(old_cwd)

            output_file = tmp_path / "outputs" / "json" / "douyin_vid.json"
            content = json.loads(output_file.read_text(encoding="utf-8"))
            assert content["text"] == "有时间戳的文字"
            assert content["duration"] == 15.0
            assert content["segments"][0]["start"] == 10.0
            assert content["segments"][0]["speaker"] == "S1"

    def test_main_missing_api_key(self, tmp_path, capsys):
        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.sys.argv", ["video-audio-transcribe", "https://v.douyin.com/test/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor
            mock_extractor.extract.side_effect = MissingAPIKeyError("请设置环境变量 MINIMAX_ASR_KEY")

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "MINIMAX_ASR_KEY" in captured.err

    def test_main_invalid_url(self, tmp_path, capsys):
        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.sys.argv", ["video-audio-transcribe", "https://www.youtube.com/watch?v=abc"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor
            mock_extractor.extract.side_effect = InvalidURLError("不支持的平台: www.youtube.com")

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "不支持的平台" in captured.err

    def test_main_video_unavailable(self, tmp_path, capsys):
        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.sys.argv", ["video-audio-transcribe", "https://v.douyin.com/deleted/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor
            mock_extractor.extract.side_effect = Exception("Video not found")

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "视频不可用" in captured.err

    def test_main_progress_feedback_to_stderr(self, tmp_path, capsys):
        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.get_transcriber") as mock_get_transcriber, \
             patch("video_audio_transcriber.cli.sys.argv", ["video-audio-transcribe", "https://v.douyin.com/test/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_prog_test.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_get_transcriber.return_value = mock_transcriber

            api_response = {"text": "测试内容", "segments": []}
            mock_transcriber.transcribe.return_value = (api_response, "douyin_prog_test")

            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)
                main()
            finally:
                os.chdir(old_cwd)

            captured = capsys.readouterr()
            assert "正在提取音频" in captured.err
            assert "正在转录" in captured.err
            assert "已保存" in captured.err
            assert captured.out == ""

    def test_main_custom_output_path(self, tmp_path):
        custom_path = tmp_path / "my_custom_output.json"

        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.get_transcriber") as mock_get_transcriber, \
             patch("video_audio_transcriber.cli.sys.argv", [
                 "video-audio-transcribe", "-o", str(custom_path), "https://v.douyin.com/test/"
             ]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_custom_test.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_get_transcriber.return_value = mock_transcriber

            api_response = {"text": "自定义路径测试", "segments": []}
            mock_transcriber.transcribe.return_value = (api_response, "douyin_custom_test")

            main()

            assert custom_path.exists()
            content = json.loads(custom_path.read_text(encoding="utf-8"))
            assert content["text"] == "自定义路径测试"

    def test_main_output_file_exists_error(self, tmp_path, capsys):
        existing_file = tmp_path / "existing.json"
        existing_file.write_text("already exists", encoding="utf-8")

        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.get_transcriber") as mock_get_transcriber, \
             patch("video_audio_transcriber.cli.sys.argv", [
                 "video-audio-transcribe", "-o", str(existing_file), "https://v.douyin.com/test/"
             ]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_exist_test.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_get_transcriber.return_value = mock_transcriber

            api_response = {"text": "测试", "segments": []}
            mock_transcriber.transcribe.return_value = (api_response, "douyin_exist_test")

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "文件已存在" in captured.err

    def test_main_provider_aliyun(self, tmp_path):
        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.get_transcriber") as mock_get_transcriber, \
             patch("video_audio_transcriber.cli.sys.argv", [
                 "video-audio-transcribe", "--provider", "aliyun", "https://v.douyin.com/test/"
             ]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_aliyun_test.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_get_transcriber.return_value = mock_transcriber

            api_response = {"text": "阿里云测试", "segments": []}
            mock_transcriber.transcribe.return_value = (api_response, "douyin_aliyun_test")

            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)
                main()
            finally:
                os.chdir(old_cwd)

            mock_get_transcriber.assert_called_once_with("aliyun")

    def test_main_invalid_provider(self, tmp_path, capsys):
        with patch("video_audio_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("video_audio_transcriber.cli.sys.argv", [
                 "video-audio-transcribe", "--provider", "foo", "https://v.douyin.com/test/"
             ]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "不支持的 provider: foo" in captured.err
