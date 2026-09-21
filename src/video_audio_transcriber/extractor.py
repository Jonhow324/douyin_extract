import shutil
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Protocol

import yt_dlp


class InvalidURLError(Exception):
    pass


class Extractor(Protocol):
    def extract(self, url: str, cookies_path: Path | None = None, cookies_from_browser: str | None = None) -> Path:
        ...


FFMPEG_LOCATIONS = [
    Path("C:/Users/92064/AppData/Local/Microsoft/WinGet/Packages")
    / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-9.0.1-full_build" / "bin" / "ffmpeg.exe",
]


def find_ffmpeg() -> Path | None:
    if shutil.which("ffmpeg"):
        return None
    for location in FFMPEG_LOCATIONS:
        if location.exists():
            return location.parent
    return None


class DouyinExtractor:
    DOMAINS = {"v.douyin.com", "www.douyin.com", "douyin.com"}
    PREFIX = "douyin"

    def extract(self, url: str, cookies_path: Path | None = None, cookies_from_browser: str | None = None) -> Path:
        self._validate_url(url)
        url = self._normalize_url(url)
        return self._download(url, cookies_path, cookies_from_browser)

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.hostname not in self.DOMAINS:
            raise InvalidURLError("无效的抖音链接")

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        if "modal_id" in query_params:
            video_id = query_params["modal_id"][0]
            return f"https://www.douyin.com/video/{video_id}"
        return url

    def _download(self, url: str, cookies_path: Path | None, cookies_from_browser: str | None) -> Path:
        output_dir = Path("outputs/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(output_dir / f"{self.PREFIX}_%(id)s.%(ext)s")

        ydl_opts = self._build_ydl_opts(output_template, cookies_path, cookies_from_browser)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info["id"]
            return output_dir / f"{self.PREFIX}_{video_id}.mp3"

    def _build_ydl_opts(self, output_template: str, cookies_path: Path | None, cookies_from_browser: str | None) -> dict:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "proxy": "",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        ffmpeg_location = find_ffmpeg()
        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = str(ffmpeg_location)

        if cookies_path:
            ydl_opts["cookiefile"] = str(cookies_path)
        if cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

        return ydl_opts


class BilibiliExtractor:
    DOMAINS = {"www.bilibili.com", "bilibili.com", "b23.tv", "m.bilibili.com"}
    PREFIX = "bilibili"

    def extract(self, url: str, cookies_path: Path | None = None, cookies_from_browser: str | None = None) -> Path:
        self._validate_url(url)
        url = self._normalize_url(url)
        return self._download(url, cookies_path, cookies_from_browser)

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.hostname not in self.DOMAINS:
            raise InvalidURLError("无效的B站链接")

    def _normalize_url(self, url: str) -> str:
        return url

    def _download(self, url: str, cookies_path: Path | None, cookies_from_browser: str | None) -> Path:
        output_dir = Path("outputs/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(output_dir / f"{self.PREFIX}_%(id)s.%(ext)s")

        ydl_opts = self._build_ydl_opts(output_template, cookies_path, cookies_from_browser)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info["id"]
            return output_dir / f"{self.PREFIX}_{video_id}.mp3"

    def _build_ydl_opts(self, output_template: str, cookies_path: Path | None, cookies_from_browser: str | None) -> dict:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "referer": "https://www.bilibili.com",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        ffmpeg_location = find_ffmpeg()
        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = str(ffmpeg_location)

        if cookies_path:
            ydl_opts["cookiefile"] = str(cookies_path)
        if cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

        return ydl_opts


EXTRACTORS: dict[str, type[DouyinExtractor | BilibiliExtractor]] = {
    "douyin": DouyinExtractor,
    "bilibili": BilibiliExtractor,
}


def detect_platform(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    if hostname in DouyinExtractor.DOMAINS:
        return "douyin"
    if hostname in BilibiliExtractor.DOMAINS:
        return "bilibili"

    raise InvalidURLError(f"不支持的平台: {hostname}")


def get_extractor(url: str) -> DouyinExtractor | BilibiliExtractor:
    platform = detect_platform(url)
    extractor_cls = EXTRACTORS[platform]
    return extractor_cls()


class AudioExtractor:
    def extract(self, url: str, cookies_path: Path | None = None, cookies_from_browser: str | None = None) -> Path:
        extractor = get_extractor(url)
        return extractor.extract(url, cookies_path, cookies_from_browser)
