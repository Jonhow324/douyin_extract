import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video_audio_transcriber.extractor import (
    AudioExtractor,
    BilibiliExtractor,
    DouyinExtractor,
    InvalidURLError,
    detect_platform,
    get_extractor,
)


class TestDetectPlatform:
    def test_detect_douyin_v_domain(self):
        assert detect_platform("https://v.douyin.com/abc123/") == "douyin"

    def test_detect_douyin_www_domain(self):
        assert detect_platform("https://www.douyin.com/video/123") == "douyin"

    def test_detect_douyin_bare_domain(self):
        assert detect_platform("https://douyin.com/video/123") == "douyin"

    def test_detect_bilibili_www_domain(self):
        assert detect_platform("https://www.bilibili.com/video/BV123") == "bilibili"

    def test_detect_bilibili_bare_domain(self):
        assert detect_platform("https://bilibili.com/video/BV123") == "bilibili"

    def test_detect_bilibili_short_domain(self):
        assert detect_platform("https://b23.tv/abc123") == "bilibili"

    def test_detect_bilibili_mobile_domain(self):
        assert detect_platform("https://m.bilibili.com/video/BV123") == "bilibili"

    def test_detect_unsupported_platform(self):
        with pytest.raises(InvalidURLError, match="不支持的平台"):
            detect_platform("https://www.youtube.com/watch?v=abc123")

    def test_detect_random_url(self):
        with pytest.raises(InvalidURLError, match="不支持的平台"):
            detect_platform("https://example.com/video")


class TestGetExtractor:
    def test_get_extractor_douyin(self):
        extractor = get_extractor("https://v.douyin.com/abc/")
        assert isinstance(extractor, DouyinExtractor)

    def test_get_extractor_bilibili(self):
        extractor = get_extractor("https://www.bilibili.com/video/BV123")
        assert isinstance(extractor, BilibiliExtractor)

    def test_get_extractor_unsupported(self):
        with pytest.raises(InvalidURLError):
            get_extractor("https://www.youtube.com/watch?v=abc")


class TestDouyinExtractor:
    def test_extract_valid_url_v_domain(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "test_video_123"}

            extractor = DouyinExtractor()
            result = extractor.extract("https://v.douyin.com/abc123/")

            assert isinstance(result, Path)
            assert "douyin_test_video_123" in result.name
            assert result.suffix == ".mp3"

    def test_extract_valid_url_www_domain(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "video_456"}

            extractor = DouyinExtractor()
            result = extractor.extract("https://www.douyin.com/video/123456")

            assert "douyin_video_456" in result.name

    def test_extract_modal_id_url(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "7683005973090274600"}

            extractor = DouyinExtractor()
            result = extractor.extract(
                "https://www.douyin.com/user/self?modal_id=7683005973090274600&showTab=favorite_collection"
            )

            call_args = mock_instance.extract_info.call_args
            assert call_args[0][0] == "https://www.douyin.com/video/7683005973090274600"

    def test_extract_invalid_url(self):
        extractor = DouyinExtractor()
        with pytest.raises(InvalidURLError):
            extractor.extract("https://www.bilibili.com/video/BV123")

    def test_ytdlp_options(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "test123"}

            extractor = DouyinExtractor()
            extractor.extract("https://v.douyin.com/test/")

            options = mock_ydl.call_args[0][0]
            assert options["format"] == "bestaudio/best"
            assert options["postprocessors"][0]["key"] == "FFmpegExtractAudio"
            assert options["postprocessors"][0]["preferredcodec"] == "mp3"


class TestBilibiliExtractor:
    def test_extract_valid_url(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "BV1xx411c7mD"}

            extractor = BilibiliExtractor()
            result = extractor.extract("https://www.bilibili.com/video/BV1xx411c7mD")

            assert isinstance(result, Path)
            assert "bilibili_BV1xx411c7mD" in result.name
            assert result.suffix == ".mp3"

    def test_extract_short_url(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "BV1xx411c7mD"}

            extractor = BilibiliExtractor()
            result = extractor.extract("https://b23.tv/abc123")

            assert "bilibili_BV1xx411c7mD" in result.name

    def test_extract_invalid_url(self):
        extractor = BilibiliExtractor()
        with pytest.raises(InvalidURLError):
            extractor.extract("https://www.douyin.com/video/123")

    def test_ytdlp_options_has_referer(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "BV123"}

            extractor = BilibiliExtractor()
            extractor.extract("https://www.bilibili.com/video/BV123")

            options = mock_ydl.call_args[0][0]
            assert options["referer"] == "https://www.bilibili.com"
            assert options["format"] == "bestaudio/best"
            assert options["postprocessors"][0]["preferredcodec"] == "mp3"

    def test_extract_with_cookies(self, tmp_path):
        cookies_file = tmp_path / "cookies.txt"
        cookies_file.write_text("# cookies")

        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "BV123"}

            extractor = BilibiliExtractor()
            extractor.extract("https://www.bilibili.com/video/BV123", cookies_path=cookies_file)

            options = mock_ydl.call_args[0][0]
            assert options["cookiefile"] == str(cookies_file)

    def test_extract_with_cookies_from_browser(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "BV123"}

            extractor = BilibiliExtractor()
            extractor.extract("https://www.bilibili.com/video/BV123", cookies_from_browser="chrome")

            options = mock_ydl.call_args[0][0]
            assert options["cookiesfrombrowser"] == ("chrome",)


class TestAudioExtractor:
    def test_extract_douyin_url(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "test123"}

            extractor = AudioExtractor()
            result = extractor.extract("https://v.douyin.com/abc/")

            assert "douyin_test123" in result.name

    def test_extract_bilibili_url(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {"id": "BV123"}

            extractor = AudioExtractor()
            result = extractor.extract("https://www.bilibili.com/video/BV123")

            assert "bilibili_BV123" in result.name

    def test_extract_unsupported_url(self):
        extractor = AudioExtractor()
        with pytest.raises(InvalidURLError, match="不支持的平台"):
            extractor.extract("https://www.youtube.com/watch?v=abc")

    def test_extract_ytdlp_exception_propagates(self):
        with patch("video_audio_transcriber.extractor.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.side_effect = Exception("Video not found")

            extractor = AudioExtractor()
            with pytest.raises(Exception, match="Video not found"):
                extractor.extract("https://v.douyin.com/deleted/")
