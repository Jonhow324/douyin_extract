import pytest

from video_audio_transcriber.aliyun_transcriber import AliyunTranscriber
from video_audio_transcriber.transcriber import (
    LongAudioWrapper,
    MiniMaxTranscriber,
    get_transcriber,
)


class TestGetTranscriber:
    def test_minimax(self):
        transcriber = get_transcriber("minimax")
        assert isinstance(transcriber, LongAudioWrapper)
        assert isinstance(transcriber._transcriber, MiniMaxTranscriber)

    def test_aliyun(self):
        transcriber = get_transcriber("aliyun")
        assert isinstance(transcriber, LongAudioWrapper)
        assert isinstance(transcriber._transcriber, AliyunTranscriber)

    def test_invalid_provider(self):
        with pytest.raises(ValueError, match="不支持的 provider: foo"):
            get_transcriber("foo")

    def test_invalid_provider_lists_options(self):
        with pytest.raises(ValueError, match="minimax, aliyun"):
            get_transcriber("unknown")
