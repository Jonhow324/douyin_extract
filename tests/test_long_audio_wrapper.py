from pathlib import Path
from unittest.mock import MagicMock, patch

from video_audio_transcriber.transcriber import LongAudioWrapper


class TestLongAudioWrapper:
    def test_short_audio_delegates_to_inner_transcriber(self, tmp_path):
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = (
            {"text": "hello", "duration": 10.0, "segments": [], "source_url": ""},
            "test",
        )

        wrapper = LongAudioWrapper(mock_transcriber)
        audio_path = tmp_path / "short.mp3"
        audio_path.write_bytes(b"fake")

        with patch("video_audio_transcriber.transcriber._get_audio_duration", return_value=10.0):
            result, video_id = wrapper.transcribe(audio_path, "http://example.com")

        mock_transcriber.transcribe.assert_called_once_with(audio_path, "http://example.com")
        assert result["text"] == "hello"

    def test_long_audio_splits_and_merges(self, tmp_path):
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.side_effect = [
            (
                {"text": "part1", "duration": 300.0, "segments": [
                    {"text": "part1", "start": 0.0, "end": 5.0, "speaker": ""}
                ], "source_url": ""},
                "chunk_0",
            ),
            (
                {"text": "part2", "duration": 200.0, "segments": [
                    {"text": "part2", "start": 0.0, "end": 3.0, "speaker": ""}
                ], "source_url": ""},
                "chunk_1",
            ),
        ]

        wrapper = LongAudioWrapper(mock_transcriber, max_duration_seconds=480)
        audio_path = tmp_path / "long.mp3"
        audio_path.write_bytes(b"fake")

        duration_sequence = [1000.0, 500.0, 500.0]

        def mock_duration(path):
            return duration_sequence.pop(0)

        with patch("video_audio_transcriber.transcriber._get_audio_duration", side_effect=mock_duration):
            with patch.object(wrapper, "_split_audio", return_value=[
                tmp_path / "chunk_0.mp3",
                tmp_path / "chunk_1.mp3",
            ]):
                result, video_id = wrapper.transcribe(audio_path, "http://example.com")

        assert result["text"] == "part1part2"
        assert result["duration"] == 1000.0
        assert result["source_url"] == "http://example.com"
        assert len(result["segments"]) == 2
        assert result["segments"][0]["start"] == 0.0
        assert result["segments"][0]["end"] == 5.0
        assert result["segments"][1]["start"] == 500.0
        assert result["segments"][1]["end"] == 503.0
        assert result["segments"][0]["id"] == 0
        assert result["segments"][1]["id"] == 1

    def test_long_audio_segment_ids_continuous(self, tmp_path):
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.side_effect = [
            ({"text": "a", "segments": [{"text": "a", "start": 0, "end": 1, "speaker": ""}], "source_url": ""}, "c0"),
            ({"text": "b", "segments": [{"text": "b", "start": 0, "end": 1, "speaker": ""}], "source_url": ""}, "c1"),
            ({"text": "c", "segments": [{"text": "c", "start": 0, "end": 1, "speaker": ""}], "source_url": ""}, "c2"),
        ]

        wrapper = LongAudioWrapper(mock_transcriber, max_duration_seconds=100)
        audio_path = tmp_path / "very_long.mp3"
        audio_path.write_bytes(b"fake")

        duration_sequence = [400.0, 100.0, 100.0, 100.0]

        def mock_duration(path):
            return duration_sequence.pop(0)

        with patch("video_audio_transcriber.transcriber._get_audio_duration", side_effect=mock_duration):
            with patch.object(wrapper, "_split_audio", return_value=[
                tmp_path / "chunk_0.mp3",
                tmp_path / "chunk_1.mp3",
                tmp_path / "chunk_2.mp3",
            ]):
                result, _ = wrapper.transcribe(audio_path)

        assert [seg["id"] for seg in result["segments"]] == [0, 1, 2]
