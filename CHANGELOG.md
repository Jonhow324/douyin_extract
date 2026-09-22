# Changelog

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

## [Unreleased]

### Changed
- 阿里云 ASR 模型从 `qwen3-asr-flash` 切换为 `qwen-audio-3.0-asr-flash`，按音频秒数计费（36000秒免费额度）
- 阿里云 ASR 请求格式适配新模型：添加 `parameters.format` 字段，响应解析改为 `output.text` + `output.sentence.words` 结构
- 大文件自动压缩：超过 3.5MB 的音频用 ffmpeg 压缩后发送，绕过 4MB gRPC 限制
- URL 构造修复：从 `DASHSCOPE_BASE_URL` 提取 host，避免 `/compatible-mode/v1` 后缀导致路径错误

## [0.3.0] - 2026-09-22

### Added
- 阿里云 DashScope ASR 引擎支持（`--provider aliyun`）
- Provider 抽象层：`Transcriber` Protocol 接口，支持多引擎切换
- 长音频自动分段转录（超过 8 分钟自动拆分）

### Changed
- API 密钥分离：MiniMax 用 `MINIMAX_ASR_KEY`，阿里云用 `DASHSCOPE_API_KEY`

## [0.2.0] - 2026-09-22

### Added
- 支持 B站视频（www.bilibili.com、b23.tv 短链、m.bilibili.com 移动端）
- 输出 JSON 格式（含时间戳分段）
- 源 URL 参数传递到转录结果
- 转录完成后自动清理临时音频文件

### Changed
- 项目重命名为 `video-audio-transcriber`（原为抖音视频转文字）
- 支持多平台视频提取架构

## [0.1.0] - 2026-09-21

### Added
- 抖音视频语音转录功能
- MiniMax ASR API 集成
- 命令行工具：`python -m video_audio_transcriber <url>`
- 支持 App 分享链接解析
