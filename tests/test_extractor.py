import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from douyin_transcriber.extractor import AudioExtractor, InvalidURLError


class TestAudioExtractor:
    def test_extract_valid_douyin_url_v_domain(self):
        with patch("douyin_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance

            mock_instance.extract_info.return_value = {
                "id": "test_video_123",
                "title": "测试视频"
            }

            extractor = AudioExtractor()
            result = extractor.extract("https://v.douyin.com/abc123/")

            assert isinstance(result, Path)
            assert "test_video_123" in result.name
            assert result.suffix == ".mp3"

            mock_instance.extract_info.assert_called_once()
            call_args = mock_instance.extract_info.call_args
            assert call_args[0][0] == "https://v.douyin.com/abc123/"

    def test_extract_valid_douyin_url_www_domain(self):
        with patch("douyin_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance

            mock_instance.extract_info.return_value = {
                "id": "video_456",
                "title": "另一个测试"
            }

            extractor = AudioExtractor()
            result = extractor.extract("https://www.douyin.com/video/123456")

            assert isinstance(result, Path)
            assert "video_456" in result.name

    def test_extract_invalid_url_not_douyin(self):
        extractor = AudioExtractor()

        with pytest.raises(InvalidURLError, match="仅支持抖音链接"):
            extractor.extract("https://www.bilibili.com/video/BV123")

    def test_extract_invalid_url_other_platform(self):
        extractor = AudioExtractor()

        with pytest.raises(InvalidURLError, match="仅支持抖音链接"):
            extractor.extract("https://www.youtube.com/watch?v=abc123")

    def test_extract_invalid_url_random(self):
        extractor = AudioExtractor()

        with pytest.raises(InvalidURLError, match="仅支持抖音链接"):
            extractor.extract("https://example.com/video")

    def test_ytdlp_options_correct(self):
        with patch("douyin_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance

            mock_instance.extract_info.return_value = {
                "id": "test123",
                "title": "测试"
            }

            extractor = AudioExtractor()
            extractor.extract("https://v.douyin.com/test/")

            mock_ydl.assert_called_once()
            options = mock_ydl.call_args[0][0]

            assert options.get("format") == "bestaudio/best"
            assert "postprocessors" in options
            assert options["postprocessors"][0]["key"] == "FFmpegExtractAudio"
            assert options["postprocessors"][0]["preferredcodec"] == "mp3"
            assert "outtmpl" in options

    def test_extract_ytdlp_exception_propagates(self):
        with patch("douyin_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance

            mock_instance.extract_info.side_effect = Exception("Video not found")

            extractor = AudioExtractor()

            with pytest.raises(Exception, match="Video not found"):
                extractor.extract("https://v.douyin.com/deleted/")
