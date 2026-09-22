# Spec: 添加阿里云 ASR 引擎

**日期**: 2026-09-22
**状态**: 草案

---

## 1. 问题陈述

当前工具仅支持 MiniMax ASR 作为语音识别引擎。用户希望增加阿里云 `qwen-audio-3.0-asr-flash` 作为备选引擎，以便在 MiniMax 不可用或效果不佳时有替代方案。

两个引擎需要在同一工具中共存，用户通过 CLI 参数选择。

## 2. 方案概述

```
cli.py → --provider aliyun|minimax（默认 minimax）
           ↓
       Transcriber Protocol
       ├── MiniMaxTranscriber   （现有逻辑重构）
       └── AliyunTranscriber    （新增）
           ↑
       长音频包装层（共享分段逻辑，>5min 自动分段后逐段调用 Provider）
```

复用 `extractor.py` 已建立的 Protocol + 注册表模式（`Extractor` Protocol → `EXTRACTORS` 注册表 → `get_extractor()` 工厂函数）。

## 3. 接缝（Seams）

| 接缝 | 职责 | 输入 | 输出 |
|------|------|------|------|
| `Transcriber` Protocol | 定义 ASR 引擎的统一接口 | `audio_path: Path, source_url: str` | `tuple[dict, str]`（标准化结果 + video_id） |
| `MiniMaxTranscriber` | MiniMax API 实现 | 同上 | 同上 |
| `AliyunTranscriber` | 阿里云 DashScope API 实现 | 同上 | 同上 |
| `TranscriberRegistry` | 根据 provider 名称返回对应实例 | `provider: str` | `Transcriber` 实例 |
| 长音频包装层 | 检测音频时长，超限时分段并合并 | `Transcriber` + `audio_path` | 标准化结果 |

## 4. 用户故事

### US-1: 选择阿里云引擎
**作为**用户，**我想**执行 `video-audio-transcriber <url> --provider aliyun`，**以便**使用阿里云 ASR 进行转录。

验收标准：
- `--provider aliyun` 使用 `AliyunTranscriber` 调用 `qwen-audio-3.0-asr-flash` 模型
- 请求发送到 DashScope API（`https://dashscope.aliyuncs.com/api/v1/services/multimodal-generation`）
- 使用环境变量 `DASHSCOPE_API_KEY` 认证

### US-2: 默认使用 MiniMax
**作为**用户，**我想**不指定 `--provider` 时默认使用 MiniMax，**以便**保持现有行为不变。

验收标准：
- 不传 `--provider` 等同于 `--provider minimax`
- 现有 MiniMax 转录行为完全不变

### US-3: 阿里云 API Key 缺失提示
**作为**用户，**当**我没有设置 `DASHSCOPE_API_KEY` 时运行 `--provider aliyun`，**我想**看到清晰的错误提示。

验收标准：
- 输出 "请设置环境变量 DASHSCOPE_API_KEY"
- 以非零退出码退出
- 不抛出原始异常堆栈

### US-4: 输出格式一致
**作为**用户，**我想**无论用哪个引擎，输出的 JSON 结构一致，**以便**下游处理不依赖特定引擎格式。

验收标准：
- 两个引擎输出相同的 JSON 结构：
  ```json
  {
    "text": "完整转录文本",
    "duration": 10.5,
    "segments": [
      {"text": "句子", "start": 0.0, "end": 2.5, "speaker": ""}
    ],
    "source_url": "原始视频链接"
  }
  ```
- `segments` 中每段包含 `text`、`start`、`end` 字段（无 speaker 信息时为空字符串）

### US-5: 长音频自动分段（阿里云）
**作为**用户，**当**音频超过 5 分钟时，**我想**阿里云引擎也能自动分段转录并合并结果。

验收标准：
- 长音频包装层对两个引擎均生效
- 分段后逐段调用 `AliyunTranscriber`，时间戳偏移正确
- 合并后的 segments 按时间顺序排列，ID 连续

### US-6: 无效 provider 提示
**作为**用户，**当**我传入 `--provider foo` 时，**我想**看到支持的引擎列表。

验收标准：
- 报错 "不支持的 provider: foo（可选: minimax, aliyun）"
- 以非零退出码退出

## 5. 已定决策

| 决策 | 理由 |
|------|------|
| 阿里云模型用 `qwen-audio-3.0-asr-flash` | 短音频同步，按音频秒数计费（36000秒免费），和 MiniMax 对等 |
| CLI `--provider aliyun\|minimax` 选择 | 显式、简单、默认 minimax 保持向后兼容 |
| Transcriber Protocol 抽象 | 复用 extractor 已验证的 Protocol 模式，未来加引擎容易 |
| 长音频分段抽为共享包装层 | 两个引擎都有 5min 限制，分段逻辑写一次 |
| 输出 JSON 格式统一 | 不同 API 返回结构不同，需标准化为统一格式 |
| API Key: `DASHSCOPE_API_KEY` / `MINIMAX_ASR_KEY` | 各引擎独立认证，互不影响 |
| 阿里云调用使用 DashScope 原生接口 | 需要时间戳信息，OpenAI 兼容接口不返回时间戳 |

## 6. 测试决策

| 接缝 | 测试策略 | "完成"标准 |
|------|----------|------------|
| `AliyunTranscriber` | Mock DashScope API 响应，验证请求格式和结果解析 | 给定音频路径 → 返回标准化 dict，含 segments + 时间戳 |
| `AliyunTranscriber` 错误路径 | Mock API Key 缺失、API 返回错误 | 抛出 `MissingAPIKeyError`；HTTP 错误抛出异常 |
| `TranscriberRegistry` | 验证 provider 名称到实例的映射 | "minimax" → `MiniMaxTranscriber`；"aliyun" → `AliyunTranscriber`；无效名称报错 |
| 长音频包装层 | Mock Transcriber，验证分段调用和时间戳合并 | 分段后时间戳偏移正确，segments 合并完整 |
| 输出格式标准化 | 分别 mock 两个引擎的原始响应，验证输出结构一致 | 两个引擎输出 JSON 的 key 结构完全相同 |
| CLI 集成 | Mock 外部依赖，验证 `--provider` 参数传递正确 | `--provider aliyun` 走到 AliyunTranscriber |

使用 **pytest** 作为测试框架，沿用现有 mock 模式。

## 7. 明确不做

- ❌ 不接入阿里云 filetrans（长音频异步）模型
- ❌ 不做自动引擎切换/fallback
- ❌ 不做阿里云特有的情感识别、敏感词过滤等高级功能
- ❌ 不改变现有 MiniMax 引擎的行为
- ❌ 不引入新的外部依赖（使用已有的 httpx）

## 8. 补充说明

### 阿里云 API 调用细节

- Endpoint: `POST https://dashscope.aliyuncs.com/api/v1/services/multimodal-generation`
- 认证: `Authorization: Bearer <DASHSCOPE_API_KEY>`
- 模型: `qwen-audio-3.0-asr-flash`
- 音频输入: 支持公网 URL / Base64（短音频场景用 Base64 更简单，无需文件托管）
- 响应: DashScope 原生格式，需解析 `output.choices[0].message.content` 提取文本和时间戳

### 输出格式标准化映射

| 字段 | MiniMax 来源 | 阿里云来源 |
|------|-------------|-----------|
| `text` | `response["text"]` | 从 choices 拼接 |
| `duration` | `response["duration"]` | 从音频 ffprobe 获取 |
| `segments` | `response["segments"]` | 从 choices 解析 |
| `segments[].text` | `seg["text"]` | word/sentence text |
| `segments[].start` | `seg["start"]` | word start_time |
| `segments[].end` | `seg["end"]` | word end_time |
| `segments[].speaker` | `seg["speaker"]` | 空字符串（暂不支持说话人分离） |

### 项目结构变更

```
src/video_audio_transcriber/
├── __init__.py           # TranscriptionResult, TranscriptionSegment（已有）
├── __main__.py
├── cli.py                # 新增 --provider 参数
├── extractor.py          # 不变
├── formatter.py          # 不变
├── transcriber.py        # 重构：拆分为 Protocol + MiniMaxTranscriber + 长音频逻辑
└── aliyun_transcriber.py # 新增：AliyunTranscriber
```
