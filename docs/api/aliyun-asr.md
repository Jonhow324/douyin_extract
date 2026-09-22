# 阿里云百炼 语音识别 API

> 来源: https://help.aliyun.com/zh/model-studio/non-realtime-speech-recognition-user-guide

## 模型总览

| 模型 ID | 类型 | 调用方式 | 最长时长 | 情感识别 | 备注 |
|---------|------|----------|----------|----------|------|
| `qwen3-asr-flash` | 短音频 | 同步/流式 | 5 min | 支持 | **推荐**，支持 OpenAI 兼容接口 |
| `qwen3-asr-flash-2026-02-10` | 短音频 | 同步/流式 | 5 min | 支持 | 快照版 |
| `qwen3-asr-flash-2025-09-08` | 短音频 | 同步/流式 | 5 min | 支持 | 快照版 |
| `qwen-audio-3.1-asr-flash` | 短音频 | 同步/流式 | 5 min | 不支持 | |
| `qwen-audio-3.0-asr-flash` | 短音频 | 同步/流式 | 5 min | 不支持 | |
| `fun-asr-flash-2026-06-15` | 短音频 | 同步/流式 | 5 min | 不支持 | |
| `qwen3-asr-flash-filetrans` | 长音频 | 异步 | 12 h | 支持 | **推荐**，文件转写 |
| `qwen3-asr-flash-filetrans-2025-11-17` | 长音频 | 异步 | 12 h | 支持 | 快照版 |
| `qwen-audio-3.1-asr-flash-filetrans` | 长音频 | 异步 | 12 h | 不支持 | |
| `qwen-audio-3.0-asr-flash-filetrans` | 长音频 | 异步 | 12 h | 不支持 | |
| `fun-asr` | 长音频 | 异步 | 12 h | 不支持 | 稳定版 |
| `fun-asr-2025-11-07` | 长音频 | 异步 | 12 h | 不支持 | 快照版 |
| `paraformer-v2` | 长音频 | 异步 | 12 h | 不支持 | 旧版 |
| `paraformer-v1` | 长音频 | 异步 | 12 h | 不支持 | 旧版 |
| `paraformer-mtl-v1` | 长音频 | 异步 | 12 h | 不支持 | 多语言旧版 |

## 可用区域

| 区域 | 支持模型 |
|------|----------|
| 华北2（北京） | 全部 |
| 新加坡 | 全部 |
| 美国（弗吉尼亚） | 仅 `qwen3-asr-flash` |

> 不同区域的 API Key 不通用，需分别获取。

---

## 一、短音频模型（同步/流式）

### Endpoint

```
POST https://dashscope.aliyuncs.com/api/v1/services/multimodal-generation
```

或使用 OpenAI 兼容接口（仅 `qwen3-asr-flash`）：

```
POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
```

### 认证

```
Authorization: Bearer <DASHSCOPE_API_KEY>
```

### 请求格式（DashScope 原生）

Content-Type: `application/json`

```json
{
  "model": "qwen3-asr-flash",
  "input": {
    "messages": [
      {
        "role": "user",
        "content": [
          {"audio": "https://example.com/audio.wav"}
        ]
      }
    ]
  },
  "parameters": {
    "asr_options": {
      "language": "zh",
      "enable_itn": false
    }
  },
  "stream": false
}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 是 | 模型 ID |
| input.messages | array | 是 | 消息列表，content 中放 audio |
| input.messages[].content[].audio | string | 是 | 音频 URL / Base64 / 本地路径 |
| parameters.asr_options.language | string | 否 | 语言提示（如 `zh`, `en`, `ja`） |
| parameters.asr_options.enable_itn | bool | 否 | 是否启用逆文本正则化 |
| stream | bool | 否 | 是否流式输出（SSE） |

### 音频约束

- 支持格式: wav, mp3, aac, flac, opus, ogg 等主流格式
- 最大时长: 5 分钟
- 采样率: 任意
- 音频来源: 公网 URL / Base64 / SDK 本地路径

### 响应格式（DashScope 原生）

```json
{
  "output": {
    "text": "完整转录文本",
    "output": {
      "sentence": {
        "text": "句子文本",
        "words": [
          {"text": "字", "start_time": 0, "end_time": 100}
        ]
      }
    }
  },
  "usage": {
    "duration": 30
  },
  "request_id": "xxx"
}
```

### 响应格式（OpenAI 兼容）

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": [
          {"text": "完整转录文本"}
        ]
      }
    }
  ],
  "usage": {
    "duration": 30
  }
}
```

> 注意：OpenAI 兼容接口**不返回时间戳**。

---

## 二、长音频模型（异步文件转写）

### 调用流程

1. **提交任务** → 获取 `task_id`
2. **轮询结果** 或 **配置 EventBridge 回调**

### Endpoint

```
# 提交任务
POST https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription

# 查询结果
GET https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}
```

### 提交任务请求

```json
{
  "model": "qwen3-asr-flash-filetrans",
  "input": {
    "file_urls": [
      "https://example.com/audio.mp3"
    ]
  },
  "parameters": {
    "diarization_enabled": false,
    "enable_words": false,
    "special_word_filter": {},
    "language_hints": ["zh"]
  }
}
```

> 必须设置请求头 `X-DashScope-Async: enable`

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 是 | 模型 ID |
| input.file_urls | array | 是 | 音频文件公网 URL 列表 |
| parameters.diarization_enabled | bool | 否 | 说话人分离（建议音频 < 2h） |
| parameters.enable_words | bool | 否 | 字级时间戳（仅 Qwen3 系列） |
| parameters.language_hints | array | 否 | 语言提示列表 |
| parameters.special_word_filter | object | 否 | 敏感词过滤配置 |

### 音频约束

- 支持格式: wav, mp3, aac, flac 等主流格式
- 最大时长: 12 小时
- 最大体积: 2 GB
- 采样率: 任意
- 音频来源: **仅公网 URL**（建议上传至 OSS）

### 提交任务响应

```json
{
  "output": {
    "task_id": "xxx",
    "task_status": "PENDING"
  },
  "request_id": "xxx"
}
```

### 查询结果响应

```json
{
  "output": {
    "task_id": "xxx",
    "task_status": "SUCCEEDED",
    "results": [
      {
        "transcription_url": "https://xxx/result.json"
      }
    ]
  }
}
```

> `transcription_url` 有效期 24 小时，需及时下载。

### 转写结果文件结构

```json
{
  "transcripts": [
    {
      "sentences": [
        {
          "text": "句子文本",
          "begin_time": 0,
          "end_time": 3000,
          "words": [
            {"text": "字", "begin_time": 0, "end_time": 200}
          ],
          "speaker_id": "spk_0",
          "emotion": "neutral"
        }
      ]
    }
  ]
}
```

---

## 三、进阶功能

### 说话人分离

- 异步接口参数: `diarization_enabled: true`
- 同步接口参数: `speaker_diarization_enabled: true`
- 限制: 仅支持单声道，建议音频 < 2 小时

### 敏感词过滤

```json
{
  "special_word_filter": {
    "filter_with_signed": {
      "word_list": ["敏感词1", "敏感词2"]
    },
    "filter_with_empty": {
      "word_list": ["屏蔽词"]
    },
    "system_reserved_filter": true
  }
}
```

- `filter_with_signed`: 替换为 `*` 号
- `filter_with_empty`: 直接移除
- `system_reserved_filter`: 启用系统预置词表

### 情感识别（仅 Qwen3 系列）

固定开启，返回 7 类情绪标签:

| 标签 | 含义 |
|------|------|
| `neutral` | 中性 |
| `happy` | 开心 |
| `sad` | 悲伤 |
| `angry` | 愤怒 |
| `surprised` | 惊讶 |
| `disgusted` | 厌恶 |
| `fearful` | 恐惧 |

### 时间戳

- 句级时间戳: 默认开启
- 字级时间戳: `enable_words: true`（仅 Qwen3-ASR-Flash-Filetrans 系列）
  - 支持语言: 中、英、日、韩、德、法、西、意、葡、俄

---

## 四、最佳实践

1. **文件托管**: 将音频上传至阿里云 OSS，通过 URL 调用（本地上传限 100 QPS 不可扩容）
2. **回调通知**: 异步任务使用 EventBridge 回调，避免频繁轮询（查询接口默认 20 QPS，最高 100 QPS）
3. **重试机制**: 实现指数退避重试
4. **音频预处理**: 噪声大时建议 FFmpeg 降噪

```bash
# 转为 16kHz 单声道 WAV（推荐预处理）
ffmpeg -i input.mp3 -ac 1 -ar 16000 -sample_fmt s16 output.wav
```

5. **安全**: 消费 EventBridge 回调时校验 `X-Eventbridge-Signature*` 头部

---

## 五、代码示例

### Python - 短音频同步（DashScope 原生）

```python
import os
import dashscope

messages = [
    {"role": "user", "content": [{"audio": "https://example.com/audio.wav"}]}
]

response = dashscope.MultiModalConversation.call(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen3-asr-flash",
    messages=messages,
    result_format="message",
    asr_options={"language": "zh", "enable_itn": False},
)

print(response.output.choices[0].message.content[0]["text"])
```

### Python - 短音频（OpenAI 兼容）

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen3-asr-flash",
    messages=[
        {"role": "user", "content": [
            {"type": "input_audio", "input_audio": {"data": "https://example.com/audio.wav", "format": "wav"}}
        ]}
    ],
    extra_body={"asr_options": {"language": "zh"}}
)

print(response.choices[0].message.content)
```

### Python - 长音频异步

```python
import os
import dashscope
from dashscope.audio.asr import Transcription

# 提交任务
task = Transcription.async_call(
    model="qwen3-asr-flash-filetrans",
    file_urls=["https://example.com/long_audio.mp3"],
    language_hints=["zh"],
)

# 等待结果
result = Transcription.wait(task.output.task_id)

# 获取转写 URL
print(result.output.results[0].transcription_url)
```

### curl - 短音频

```bash
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/multimodal-generation \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-asr-flash",
    "input": {
      "messages": [{"role": "user", "content": [{"audio": "https://example.com/audio.wav"}]}]
    },
    "parameters": {
      "asr_options": {"language": "zh"}
    }
  }'
```

---

## 六、计费

按音频时长计费，具体单价参考: https://help.aliyun.com/zh/model-studio/billing-for-speech-models
