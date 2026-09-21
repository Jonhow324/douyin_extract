# 视频音频转录工具

从视频链接提取音频，通过 MiniMax ASR API 转录为文本，支持长视频自动分割处理。

## 支持平台

- **抖音** - 分享链接、用户页面、modal_id 格式
- **B站（Bilibili）** - 标准链接、短链接、移动端链接

## 功能特性

- 多平台支持（抖音、B站）
- 自动识别平台并提取音频
- 长视频自动分割（超过 8 分钟的视频自动分段处理）
- 输出完整 JSON 格式（包含说话人标识、时间戳等）
- 自动清理中间文件（音频文件转录后自动删除）
- 支持 cookies 访问需要登录的视频

## 安装

```bash
# 克隆仓库
git clone <repository-url>
cd video-audio-transcriber

# 安装依赖
pip install -e .

# 安装开发依赖（包含测试工具）
pip install -e ".[dev]"
```

### 依赖要求

- Python >= 3.10
- ffmpeg（用于音频处理）

**Windows 安装 ffmpeg：**
```powershell
winget install Gyan.FFmpeg
```

## 配置

### 1. 设置 API Key

创建 `.env` 文件（或复制 `.env.example`）：

```bash
MINIMAX_ASR_KEY=your_api_key_here
```

获取 API Key：[MiniMax 开放平台](https://platform.minimax.cn/)

### 2. 获取 Cookies（可选）

部分视频需要登录才能访问，需要提供 cookies 文件。

#### 方法一：浏览器扩展导出（推荐）

1. 安装浏览器扩展：
   - Chrome/Edge: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndikbckbceinackdaeiholbfdgc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. 在浏览器中登录对应平台：
   - [抖音](https://www.douyin.com/)
   - [B站](https://www.bilibili.com/)

3. 点击扩展图标，导出 cookies 为 Netscape 格式文件

4. 保存为 `cookies.txt`（或其他文件名）

#### 方法二：使用浏览器自动提取

```bash
# 从 Chrome 提取（需关闭 Chrome）
video-audio-transcribe <url> --cookies-from-browser chrome

# 从 Edge 提取（需关闭 Edge）
video-audio-transcribe <url> --cookies-from-browser edge

# 从 Firefox 提取
video-audio-transcribe <url> --cookies-from-browser firefox
```

**注意：** 浏览器提取方式可能因系统安全策略失败（如 DPAPI 解密问题），此时请使用扩展导出方法。

## 使用方法

### 基本用法

```bash
# 抖音视频
video-audio-transcribe "https://www.douyin.com/video/xxxxxxxxx"

# B站视频
video-audio-transcribe "https://www.bilibili.com/video/BVxxxxxxxxx"
```

### 带 Cookies 访问

```bash
# 使用 cookies 文件
video-audio-transcribe <url> --cookies cookies.txt

# 使用浏览器 cookies
video-audio-transcribe <url> --cookies-from-browser chrome
```

### 指定输出路径

```bash
video-audio-transcribe <url> -o output.json
```

### 支持的链接格式

**抖音：**
```bash
# 标准视频链接
https://www.douyin.com/video/7683005973090274600

# 分享链接
https://v.douyin.com/xxxxxxx/

# 用户页面 modal_id 格式
https://www.douyin.com/user/self?modal_id=7683005973090274600
```

**B站：**
```bash
# 标准视频链接
https://www.bilibili.com/video/BV1xx411c7mD

# 短链接
https://b23.tv/xxxxxxx

# 移动端链接
https://m.bilibili.com/video/BV1xx411c7mD
```

## 输出格式

转录结果保存为 JSON 文件，包含以下字段：

```json
{
  "text": "完整的转录文本",
  "duration": 2145.8,
  "n_speakers": 2,
  "segments": [
    {
      "id": 0,
      "start": 0.04,
      "end": 12.28,
      "speaker": "S1",
      "text": "这段话的内容"
    }
  ],
  "trace_id": "api-request-trace-id"
}
```

默认保存到 `outputs/json/<platform>_<video_id>.json`

- 抖音视频：`outputs/json/douyin_<video_id>.json`
- B站视频：`outputs/json/bilibili_<video_id>.json`

## 项目结构

```
video-audio-transcriber/
├── src/
│   └── video_audio_transcriber/
│       ├── cli.py          # 命令行入口
│       ├── extractor.py    # 音频提取（多平台）
│       ├── transcriber.py  # 语音转录
│       └── formatter.py    # 文本格式化
├── outputs/
│   ├── audio/              # 临时音频文件（自动清理）
│   └── json/               # 转录结果
├── tests/                  # 测试用例
├── docs/                   # 文档
└── pyproject.toml
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行测试并显示覆盖率
pytest --cov=video_audio_transcriber
```

## 定价说明

MiniMax ASR API 定价约为 2.5 元/小时（实际以官方为准）。

长视频会自动分割为多个片段处理，总费用按实际音频时长计算。

## 许可证

MIT
