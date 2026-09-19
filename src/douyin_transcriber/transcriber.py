import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx

from douyin_transcriber import TranscriptionResult, TranscriptionSegment


class MissingAPIKeyError(Exception):
    pass


class Transcriber:
    API_URL = "https://api.minimax.cn/v1/speech_to_text"
    MAX_DURATION_SECONDS = 480  # 8 minutes, leave buffer from 500s limit
    MAX_FILE_SIZE_MB = 45  # Leave buffer from 50MB limit
    FFMPEG_LOCATIONS = [
        Path("C:/Users/92064/AppData/Local/Microsoft/WinGet/Packages")
        / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
        / "ffmpeg-9.0.1-full_build" / "bin",
    ]

    def transcribe(self, audio_path: Path) -> tuple[dict, str]:
        api_key = os.environ.get("MINIMAX_ASR_KEY")
        if not api_key:
            raise MissingAPIKeyError("请设置环境变量 MINIMAX_ASR_KEY")

        duration = self._get_audio_duration(audio_path)
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)

        if duration > self.MAX_DURATION_SECONDS or file_size_mb > self.MAX_FILE_SIZE_MB:
            return self._transcribe_long_audio(audio_path, api_key)
        else:
            return self._transcribe_single(audio_path, api_key)

    def _find_ffmpeg_dir(self) -> Path | None:
        if shutil.which("ffmpeg"):
            return None
        for location in self.FFMPEG_LOCATIONS:
            if location.exists():
                return location
        return None

    def _get_audio_duration(self, audio_path: Path) -> float:
        ffmpeg_dir = self._find_ffmpeg_dir()
        ffprobe_cmd = "ffprobe"
        if ffmpeg_dir:
            ffprobe_cmd = str(ffmpeg_dir / "ffprobe.exe")
        
        result = subprocess.run(
            [ffprobe_cmd, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())

    def _transcribe_single(self, audio_path: Path, api_key: str) -> tuple[dict, str]:
        with httpx.Client(timeout=120, trust_env=False) as client:
            with open(audio_path, "rb") as audio_file:
                response = client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                    },
                    files={"file": audio_file},
                    data={
                        "model": "asr-1.0",
                        "response_format": "verbose_json",
                        "timestamp_level": "sentence",
                    },
                )

            if response.status_code != 200:
                raise Exception(f"ASR API 请求失败: {response.status_code} {response.text}")

            data = response.json()
            video_id = audio_path.stem.removeprefix("douyin_")
            return data, video_id

    def _transcribe_long_audio(self, audio_path: Path, api_key: str) -> tuple[dict, str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            chunks = self._split_audio(audio_path, temp_dir)
            
            all_segments = []
            total_duration = 0.0
            
            for i, chunk_path in enumerate(chunks):
                chunk_data, _ = self._transcribe_single(chunk_path, api_key)
                
                if "segments" in chunk_data:
                    for seg in chunk_data["segments"]:
                        seg["start"] = seg.get("start", 0) + total_duration
                        seg["end"] = seg.get("end", 0) + total_duration
                        seg["id"] = len(all_segments)
                        all_segments.append(seg)
                
                total_duration += self._get_audio_duration(chunk_path)
            
            merged_data = {
                "text": " ".join(seg["text"] for seg in all_segments),
                "duration": total_duration,
                "n_speakers": 1,
                "segments": all_segments,
            }
            
            video_id = audio_path.stem.removeprefix("douyin_")
            return merged_data, video_id

    def _split_audio(self, audio_path: Path, output_dir: Path) -> list[Path]:
        duration = self._get_audio_duration(audio_path)
        num_chunks = int(duration / self.MAX_DURATION_SECONDS) + 1
        chunk_duration = duration / num_chunks
        
        ffmpeg_dir = self._find_ffmpeg_dir()
        ffmpeg_cmd = "ffmpeg"
        if ffmpeg_dir:
            ffmpeg_cmd = str(ffmpeg_dir / "ffmpeg.exe")
        
        chunks = []
        for i in range(num_chunks):
            start_time = i * chunk_duration
            chunk_path = output_dir / f"chunk_{i}.mp3"
            
            subprocess.run(
                [ffmpeg_cmd, "-i", str(audio_path), "-ss", str(start_time),
                 "-t", str(chunk_duration), "-acodec", "libmp3lame",
                 "-q:a", "2", str(chunk_path), "-y"],
                capture_output=True,
            )
            chunks.append(chunk_path)
        
        return chunks
