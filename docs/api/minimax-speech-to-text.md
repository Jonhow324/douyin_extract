# MiniMax Speech-to-Text API

> 来源: https://platform.minimax.cn/docs/api-reference/speech-to-text

## Endpoint

```
POST https://api.minimax.cn/v1/speech_to_text
```

## 认证

```
Authorization: Bearer <API_KEY>
```

## 请求格式

Content-Type: `multipart/form-data`

### Headers

| Header    | 类型   | 必填 | 说明                                      |
|-----------|--------|------|-------------------------------------------|
| Authorization | string | 是 | `Bearer <API_KEY>`                     |
| language  | string | 否   | BCP-47 语言标签（如 `zh`, `en`）         |

### Body 参数

| 参数              | 类型    | 必填 | 默认值    | 说明                                                        |
|-------------------|---------|------|-----------|-------------------------------------------------------------|
| model             | string  | 是   | -         | 模型名称，当前为 `asr-1.0`                                  |
| file              | binary  | 是   | -         | 音频文件                                                    |
| response_format   | string  | 否   | `json`    | 响应格式: `json` / `verbose_json` / `srt` / `vtt`          |
| timestamp_level   | string  | 否   | `""`      | 时间戳粒度: `sentence`（句子级）/ `word`（词级）/ `""`（无）|
| stream            | boolean | 否   | `false`   | 是否使用流式响应                                            |

### 音频文件约束

- 支持格式: wav, aiff, flac, alac, mp3, aac, opus, ogg
- 最大时长: 500 秒
- 最大文件: 50MB

## 响应格式

### json / verbose_json

```json
{
  "text": "完整的转录文本",
  "duration": 130.22,
  "n_speakers": 1,
  "segments": [
    {
      "id": 0,
      "start": 0.02,
      "end": 55.1,
      "speaker": "S1",
      "text": "句子级别的文本"
    }
  ],
  "trace_id": "请求追踪ID"
}
```

| 字段        | 类型      | 说明                          |
|-------------|-----------|-------------------------------|
| text        | string    | 完整转录文本                  |
| duration    | float     | 音频时长（秒）                |
| n_speakers  | int       | 说话人数量                    |
| segments    | array     | 分段信息（verbose_json 时返回）|
| trace_id    | string    | 请求追踪 ID                   |

### Segment 对象

| 字段    | 类型   | 说明                |
|---------|--------|---------------------|
| id      | int    | 片段序号            |
| start   | float  | 开始时间（秒）      |
| end     | float  | 结束时间（秒）      |
| speaker | string | 说话人标识（如 S1） |
| text    | string | 该片段的文本        |

### srt / vtt

返回对应格式的字幕文本（纯文本）。

## 实测完整响应

> 视频: `7687069721010638089`，时长 130s，mp3 3.1MB
> 请求参数: `model=asr-1.0`, `response_format=verbose_json`, `timestamp_level=sentence`

```json
{
  "text": "这是911 GT3的SC，就是敞篷版，这你受得了吗？不过很遗憾啊，这个车咱们那是不引进的。...(完整文本省略)",
  "duration": 130.220408,
  "n_speakers": 1,
  "segments": [
    {
      "id": 0,
      "start": 0.02,
      "end": 55.1,
      "speaker": "S1",
      "text": "这是911 GT3的SC，就是敞篷版，这你受得了吗？不过很遗憾啊，这个车咱们那是不引进的。911 GT3 Touring和SC这两台GT3应该是所有的911 GT3里最低调的两个版本了。911 GT3的Touring就不跟大家去多赘述了啊，主要就是后面没有尾翼，而边上这又是什么呢？猛的一看这是一个敞篷，对吗？软顶敞篷，这是911 GT3的SC，就是敞篷版，这你受得了吗？不过很遗憾啊，这个车咱们那是不引进的。来看一下它整个的这个敞篷过程，其实这就跟其他的敞篷版本的911车型这个逻辑是一致的，只不过这台车它的动力系统呢是一台GT3，这你受得了吗？然后这台车呢也是没有选后座，然后选了碳椅，然后全部都是手动挡。重要的事儿说三遍，全部都是手动挡乘以三，这你受得了吗？这也是这台GT3敞篷版没有引进到国内。"
    },
    {
      "id": 1,
      "start": 55.24,
      "end": 109.2,
      "speaker": "S1",
      "text": "的一个很重要的点就是因为这个G T三的I C它是没有P D K版本的，这你受得了吗？但这台车真的是玩具属性很强啊，因为这台车你在开着它的时候，你知道就是G T三本身有一个很大的特点，就是它的排气声浪非常的好听。但是如果你开这个硬顶版啊，不论是呃这个Torrin也好，还是R S也好，还是普通的G T三也好，基本上你也就是顶多离墙近一点，然后把车窗打开听一听边上过来的这个回声。而这个敞篷版它就彻底不一样了，就是你在开这台车的时候，真的你在车里能随时随地听到后边排气非常性感的那个升档降档还有拉高转的时候那个咆哮的嗓门，那个咆哮的声音，这你受得了吗？就是这个九幺幺G T三的I C，但很可惜啊，这台车是不来咱们这儿的，官方不引进，但后续如果是平行进口。"
    },
    {
      "id": 2,
      "start": 109.34,
      "end": 127.6,
      "speaker": "S1",
      "text": "的话，这就不好说了。那么正好借这个视频呢，也是吧提醒一下广大平行进口商们，是不是可以考虑一下你们在引进这个Torrin的同时，也考虑一下这个S C呗G T三S C G T三Torrin两台非常性感且低调的街道玩具，这你受了吗？"
    }
  ],
  "trace_id": "06fe01fb2c8e22a47d80f47ac095a2a3"
}
```

### 响应 Headers

```
content-type: application/json; charset=utf-8
trace-id: 06fe01fb2c8e22a47d80f47ac095a2a3
minimax-request-id: 33de6cea11d2e7b0295ccea13e08d3a7
```

## 错误响应

遵循 OpenAI 错误格式:

```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "错误描述"
  },
  "request_id": "请求ID"
}
```

## curl 示例

```bash
curl -X POST https://api.minimax.cn/v1/speech_to_text \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "model=asr-1.0" \
  -F "file=@audio.mp3" \
  -F "response_format=verbose_json" \
  -F "timestamp_level=sentence"
```
