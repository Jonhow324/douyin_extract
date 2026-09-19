import shutil
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp


class InvalidURLError(Exception):
    pass


class AudioExtractor:
    DOUYIN_DOMAINS = {"v.douyin.com", "www.douyin.com", "douyin.com"}
    FFMPEG_LOCATIONS = [
        Path("C:/Users/92064/AppData/Local/Microsoft/WinGet/Packages")
        / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
        / "ffmpeg-9.0.1-full_build" / "bin" / "ffmpeg.exe",
    ]

    def extract(self, url: str, cookies_path: Path | None = None, cookies_from_browser: str | None = None) -> Path:
        self._validate_url(url)

        output_dir = Path("outputs/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(output_dir / "douyin_%(id)s.%(ext)s")

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

        ffmpeg_location = self._find_ffmpeg()
        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = str(ffmpeg_location)

        if cookies_path:
            ydl_opts["cookiefile"] = str(cookies_path)
        if cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info["id"]
            audio_path = output_dir / f"douyin_{video_id}.mp3"
            return audio_path

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.hostname not in self.DOUYIN_DOMAINS:
            raise InvalidURLError("仅支持抖音链接")

    def _find_ffmpeg(self) -> Path | None:
        if shutil.which("ffmpeg"):
            return None
        for location in self.FFMPEG_LOCATIONS:
            if location.exists():
                return location.parent
        return None
