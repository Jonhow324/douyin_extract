from douyin_transcriber import TranscriptionResult


class OutputFormatter:
    @staticmethod
    def format_plain_text(result: TranscriptionResult) -> str:
        if not result.segments:
            return ""
        return "\n".join(seg.text for seg in result.segments)

    @staticmethod
    def format_with_timestamps(result: TranscriptionResult) -> str:
        if not result.segments:
            return ""

        lines = []
        for seg in result.segments:
            ts = OutputFormatter._format_timestamp(seg.start)
            lines.append(f"{ts} {seg.text}")
        return "\n".join(lines)

    @staticmethod
    def _format_timestamp(seconds: float | None) -> str:
        if seconds is None:
            return "[??:??]"
        total_seconds = int(seconds)
        minutes = total_seconds // 60
        secs = total_seconds % 60
        return f"[{minutes:02d}:{secs:02d}]"
