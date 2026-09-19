import pytest
from douyin_transcriber import TranscriptionResult, TranscriptionSegment
from douyin_transcriber.formatter import OutputFormatter


class TestOutputFormatter:
    def test_format_plain_text_single_segment(self):
        result = TranscriptionResult(
            segments=[TranscriptionSegment(text="大家好")],
            video_id="test123"
        )
        output = OutputFormatter.format_plain_text(result)
        assert output == "大家好"

    def test_format_plain_text_multiple_segments(self):
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(text="大家好"),
                TranscriptionSegment(text="今天聊一下"),
                TranscriptionSegment(text="这个话题")
            ],
            video_id="test123"
        )
        output = OutputFormatter.format_plain_text(result)
        assert output == "大家好\n今天聊一下\n这个话题"

    def test_format_plain_text_empty_segments(self):
        result = TranscriptionResult(segments=[], video_id="test123")
        output = OutputFormatter.format_plain_text(result)
        assert output == ""

    def test_format_plain_text_ignores_timestamps(self):
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(text="有时间的文字", start=10.5, end=15.0)
            ],
            video_id="test123"
        )
        output = OutputFormatter.format_plain_text(result)
        assert output == "有时间的文字"
        assert "[" not in output

    def test_format_with_timestamps_single_segment(self):
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(text="大家好", start=0.0, end=2.5)
            ],
            video_id="test123"
        )
        output = OutputFormatter.format_with_timestamps(result)
        assert output == "[00:00] 大家好"

    def test_format_with_timestamps_multiple_segments(self):
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(text="大家好", start=0.0, end=2.5),
                TranscriptionSegment(text="今天聊一下", start=3.0, end=8.5),
                TranscriptionSegment(text="这个话题", start=10.0, end=15.0)
            ],
            video_id="test123"
        )
        output = OutputFormatter.format_with_timestamps(result)
        expected = "[00:00] 大家好\n[00:03] 今天聊一下\n[00:10] 这个话题"
        assert output == expected

    def test_format_with_timestamps_empty_segments(self):
        result = TranscriptionResult(segments=[], video_id="test123")
        output = OutputFormatter.format_with_timestamps(result)
        assert output == ""

    def test_format_with_timestamps_conversion(self):
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(text="72.5秒", start=72.5, end=75.0)
            ],
            video_id="test123"
        )
        output = OutputFormatter.format_with_timestamps(result)
        assert output == "[01:12] 72.5秒"

    def test_format_with_timestamps_none_start(self):
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(text="无时间", start=None, end=None)
            ],
            video_id="test123"
        )
        output = OutputFormatter.format_with_timestamps(result)
        assert output == "[??:??] 无时间"
