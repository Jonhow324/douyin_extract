import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from douyin_transcriber.extractor import AudioExtractor, InvalidURLError
from douyin_transcriber.transcriber import MissingAPIKeyError, Transcriber


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="从抖音链接提取语音转录"
    )
    parser.add_argument(
        "url",
        help="抖音分享链接"
    )
    parser.add_argument(
        "-o", "--output",
        help="指定输出文件路径（默认: douyin_<video_id>.json）"
    )
    parser.add_argument(
        "--cookies",
        help="cookies 文件路径（Netscape 格式，用于访问需要登录的视频）"
    )
    parser.add_argument(
        "--cookies-from-browser",
        choices=["chrome", "edge", "firefox", "opera", "brave"],
        help="从浏览器自动提取 cookies（需关闭对应浏览器）"
    )
    args = parser.parse_args()

    extractor = AudioExtractor()
    transcriber = Transcriber()

    cookies_path = Path(args.cookies) if args.cookies else None

    try:
        print("正在提取音频…", file=sys.stderr)
        audio_path = extractor.extract(
            args.url,
            cookies_path=cookies_path,
            cookies_from_browser=args.cookies_from_browser,
        )

        print("正在转录…", file=sys.stderr)
        data, video_id = transcriber.transcribe(audio_path)

        if args.output:
            output_file = Path(args.output)
        else:
            output_dir = Path("outputs/json")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"douyin_{video_id}.json"

        if output_file.exists():
            print(f"文件已存在: {output_file}", file=sys.stderr)
            sys.exit(1)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存到 {output_file}", file=sys.stderr)

        if audio_path.exists():
            audio_path.unlink()
            print(f"已清理音频文件: {audio_path}", file=sys.stderr)
    except MissingAPIKeyError:
        print("请设置环境变量 MINIMAX_ASR_KEY", file=sys.stderr)
        sys.exit(1)
    except InvalidURLError:
        print("仅支持抖音链接", file=sys.stderr)
        sys.exit(1)
    except Exception:
        print("视频不可用", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
