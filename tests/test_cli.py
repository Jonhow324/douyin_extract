import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from douyin_transcriber import TranscriptionResult, TranscriptionSegment
from douyin_transcriber.cli import main
from douyin_transcriber.extractor import InvalidURLError
from douyin_transcriber.transcriber import MissingAPIKeyError


class TestCLI:
    def test_main_pipeline_success(self, tmp_path, capsys):
        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.Transcriber") as mock_transcriber_cls, \
             patch("douyin_transcriber.cli.sys.argv", ["douyin-transcriber", "https://v.douyin.com/test123/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_video_abc.mp3"
            audio_path.write_bytes(b"fake audio")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber

            result = TranscriptionResult(
                segments=[
                    TranscriptionSegment(text="大家好"),
                    TranscriptionSegment(text="今天聊一下"),
                ],
                video_id="video_abc"
            )
            mock_transcriber.transcribe.return_value = result

            with patch("douyin_transcriber.cli.Path.cwd", return_value=tmp_path):
                main()

            output_file = tmp_path / "douyin_video_abc.txt"
            assert output_file.exists()
            content = output_file.read_text(encoding="utf-8")
            assert "大家好" in content
            assert "今天聊一下" in content

            assert not audio_path.exists()

    def test_main_pipeline_cleans_up_on_error(self, tmp_path):
        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.Transcriber") as mock_transcriber_cls, \
             patch("douyin_transcriber.cli.sys.argv", ["douyin-transcriber", "https://v.douyin.com/test/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_video_xyz.mp3"
            audio_path.write_bytes(b"fake audio")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber
            mock_transcriber.transcribe.side_effect = Exception("API Error")

            with patch("douyin_transcriber.cli.Path.cwd", return_value=tmp_path):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

            assert not audio_path.exists()

    def test_main_output_filename_format(self, tmp_path):
        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.Transcriber") as mock_transcriber_cls, \
             patch("douyin_transcriber.cli.sys.argv", ["douyin-transcriber", "https://v.douyin.com/abc/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_test_id_123.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber

            result = TranscriptionResult(
                segments=[TranscriptionSegment(text="测试")],
                video_id="test_id_123"
            )
            mock_transcriber.transcribe.return_value = result

            with patch("douyin_transcriber.cli.Path.cwd", return_value=tmp_path):
                main()

            output_file = tmp_path / "douyin_test_id_123.txt"
            assert output_file.exists()

    def test_main_plain_text_no_timestamps(self, tmp_path):
        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.Transcriber") as mock_transcriber_cls, \
             patch("douyin_transcriber.cli.sys.argv", ["douyin-transcriber", "https://v.douyin.com/test/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_vid.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber

            result = TranscriptionResult(
                segments=[
                    TranscriptionSegment(text="有时间戳的文字", start=10.0, end=15.0),
                ],
                video_id="vid"
            )
            mock_transcriber.transcribe.return_value = result

            with patch("douyin_transcriber.cli.Path.cwd", return_value=tmp_path):
                main()

            output_file = tmp_path / "douyin_vid.txt"
            content = output_file.read_text(encoding="utf-8")
            assert "有时间戳的文字" in content
            assert "[" not in content

    def test_main_missing_api_key(self, tmp_path, capsys):
        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.sys.argv", ["douyin-transcriber", "https://v.douyin.com/test/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor
            mock_extractor.extract.side_effect = MissingAPIKeyError("请设置环境变量 MINIMAX_API_KEY")

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "MINIMAX_API_KEY" in captured.err

    def test_main_invalid_url(self, tmp_path, capsys):
        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.sys.argv", ["douyin-transcriber", "https://www.bilibili.com/video/BV123"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor
            mock_extractor.extract.side_effect = InvalidURLError("仅支持抖音链接")

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "仅支持抖音链接" in captured.err

    def test_main_video_unavailable(self, tmp_path, capsys):
        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.sys.argv", ["douyin-transcriber", "https://v.douyin.com/deleted/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor
            mock_extractor.extract.side_effect = Exception("Video not found")

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "视频不可用" in captured.err

    def test_main_progress_feedback_to_stderr(self, tmp_path, capsys):
        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.Transcriber") as mock_transcriber_cls, \
             patch("douyin_transcriber.cli.sys.argv", ["douyin-transcriber", "https://v.douyin.com/test/"]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_prog_test.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber

            result = TranscriptionResult(
                segments=[TranscriptionSegment(text="测试内容")],
                video_id="prog_test"
            )
            mock_transcriber.transcribe.return_value = result

            with patch("douyin_transcriber.cli.Path.cwd", return_value=tmp_path):
                main()

            captured = capsys.readouterr()
            assert "正在提取音频" in captured.err
            assert "正在转录" in captured.err
            assert "已保存" in captured.err
            assert captured.out == ""

    def test_main_timestamps_flag(self, tmp_path):
        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.Transcriber") as mock_transcriber_cls, \
             patch("douyin_transcriber.cli.sys.argv", [
                 "douyin-transcriber", "--timestamps", "https://v.douyin.com/test/"
             ]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_ts_test.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber

            result = TranscriptionResult(
                segments=[
                    TranscriptionSegment(text="大家好", start=0.0, end=2.5),
                    TranscriptionSegment(text="今天聊一下", start=3.0, end=8.5),
                ],
                video_id="ts_test"
            )
            mock_transcriber.transcribe.return_value = result

            with patch("douyin_transcriber.cli.Path.cwd", return_value=tmp_path):
                main()

            output_file = tmp_path / "douyin_ts_test.txt"
            content = output_file.read_text(encoding="utf-8")
            assert "[00:00] 大家好" in content
            assert "[00:03] 今天聊一下" in content

    def test_main_custom_output_path(self, tmp_path):
        custom_path = tmp_path / "my_custom_output.txt"

        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.Transcriber") as mock_transcriber_cls, \
             patch("douyin_transcriber.cli.sys.argv", [
                 "douyin-transcriber", "-o", str(custom_path), "https://v.douyin.com/test/"
             ]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_custom_test.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber

            result = TranscriptionResult(
                segments=[TranscriptionSegment(text="自定义路径测试")],
                video_id="custom_test"
            )
            mock_transcriber.transcribe.return_value = result

            main()

            assert custom_path.exists()
            content = custom_path.read_text(encoding="utf-8")
            assert "自定义路径测试" in content

    def test_main_output_file_exists_error(self, tmp_path, capsys):
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("already exists", encoding="utf-8")

        with patch("douyin_transcriber.cli.AudioExtractor") as mock_extractor_cls, \
             patch("douyin_transcriber.cli.Transcriber") as mock_transcriber_cls, \
             patch("douyin_transcriber.cli.sys.argv", [
                 "douyin-transcriber", "-o", str(existing_file), "https://v.douyin.com/test/"
             ]):

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            audio_path = tmp_path / "douyin_exist_test.mp3"
            audio_path.write_bytes(b"fake")
            mock_extractor.extract.return_value = audio_path

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber

            result = TranscriptionResult(
                segments=[TranscriptionSegment(text="测试")],
                video_id="exist_test"
            )
            mock_transcriber.transcribe.return_value = result

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "文件已存在" in captured.err

            assert not audio_path.exists()
