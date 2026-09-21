from video_audio_transcriber import TranscriptionResult, TranscriptionSegment


def test_dataclass_imports():
    seg = TranscriptionSegment(text="hello", start=0.0, end=1.5)
    result = TranscriptionResult(segments=[seg], video_id="test123")
    assert result.video_id == "test123"
    assert len(result.segments) == 1
    assert result.segments[0].text == "hello"
    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 1.5


def test_dataclass_defaults():
    seg = TranscriptionSegment(text="no timestamps")
    assert seg.start is None
    assert seg.end is None

    result = TranscriptionResult()
    assert result.segments == []
    assert result.video_id == ""
