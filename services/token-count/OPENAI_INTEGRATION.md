# OpenAI 格式集成说明

## 概述

Token 计算服务现在支持 OpenAI 格式的 API 接口，可以直接接收 OpenAI 格式的请求并返回标准的 OpenAI 格式响应，同时提供精确的 Token 计算信息。

## 新增接口

### 1. OpenAI 聊天完成接口

**端点：**
- `POST /v1/chat/completions` (标准 OpenAI 格式)
- `POST /openai/chat/completions` (兼容格式)

**功能：**
- 接收 OpenAI 格式的聊天请求
- 计算输入和输出 Token 数量
- 返回标准的 OpenAI 格式响应

## 请求格式

### 请求报文示例

```json
{
  "model": "Deepseek-R1-7B",
  "messages": [
    {
      "role": "system",
      "content": "你是一个专业的AI助手"
    },
    {
      "role": "user",
      "content": "你好，请介绍一下人工智能的发展历史"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

### 请求字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `model` | string | ✅ | 模型名称，支持所有配置的模型 |
| `messages` | array | ✅ | 消息列表，包含 role 和 content |
| `temperature` | float | ❌ | 温度参数，默认 0.7 |
| `max_tokens` | integer | ❌ | 最大输出 Token 数，默认 1000 |
| `stream` | boolean | ❌ | 是否流式输出，默认 false |
| `top_p` | float | ❌ | Top-p 参数，默认 1.0 |
| `frequency_penalty` | float | ❌ | 频率惩罚，默认 0.0 |
| `presence_penalty` | float | ❌ | 存在惩罚，默认 0.0 |
| `stop` | array | ❌ | 停止词列表 |

### 消息格式

```json
{
  "role": "system|user|assistant",
  "content": "消息内容"
}
```

## 响应格式

### 成功响应示例

```json
{
  "id": "chatcmpl-1704067200-abc12345",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "Deepseek-R1-7B",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "这是基于 Deepseek-R1-7B 模型的 Token 计算响应。\n\n输入 Token 数量: 25\n输出 Token 数量: 1000\n总 Token 数量: 1025\n模型类型: Standard\n分词器类型: AutoTokenizer\n文本长度: 20 字符"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 1000,
    "total_tokens": 1025
  }
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 响应唯一标识符 |
| `object` | string | 对象类型，固定为 "chat.completion" |
| `created` | integer | 创建时间戳 |
| `model` | string | 使用的模型名称 |
| `choices` | array | 选择列表，包含响应消息 |
| `usage` | object | Token 使用统计 |

### 错误响应示例

```json
{
  "detail": "Token 计算失败: 无法加载模型: Deepseek-R1-7B"
}
```

## 支持的模型

| 模型名称 | 类型 | 分词器 |
|----------|------|--------|
| Deepseek-R1-1.5B | Standard | AutoTokenizer |
| Deepseek-R1-7B | Standard | AutoTokenizer |
| Deepseek-R1-14B | Standard | AutoTokenizer |
| Deepseek-R1-32B | Standard | AutoTokenizer |
| Deepseek-R1-70B | Standard | AutoTokenizer |
| Deepseek-R1 | Standard | AutoTokenizer |
| Deepseek-V3 | Standard | AutoTokenizer |
| Qwen2.5-72B-Instruct-GPTQ-int4 | Qwen | QwenTokenizer |
| Qwen2.5-VL-72B | Qwen | QwenTokenizer |
| Qwen3-8B | Qwen | QwenTokenizer |
| Qwen3-32B | Qwen | QwenTokenizer |
| Qwen3-235B | Qwen | QwenTokenizer |
| QWQ-32B | Qwen | QwenTokenizer |

## 使用示例

### Python 示例

```python
import requests
import json

# 请求数据
request_data = {
    "model": "Deepseek-R1-7B",
    "messages": [
        {
            "role": "system",
            "content": "你是一个专业的AI助手"
        },
        {
            "role": "user",
            "content": "你好，请介绍一下人工智能的发展历史"
        }
    ],
    "temperature": 0.7,
    "max_tokens": 1000
}

# 发送请求
response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json=request_data,
    headers={"Content-Type": "application/json"}
)

# 处理响应
if response.status_code == 200:
    result = response.json()
    print(f"输入Token: {result['usage']['prompt_tokens']}")
    print(f"输出Token: {result['usage']['completion_tokens']}")
    print(f"总Token: {result['usage']['total_tokens']}")
    print(f"响应内容: {result['choices'][0]['message']['content']}")
else:
    print(f"请求失败: {response.status_code} - {response.text}")
```

### curl 示例

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Deepseek-R1-7B",
    "messages": [
      {
        "role": "system",
        "content": "你是一个专业的AI助手"
      },
      {
        "role": "user",
        "content": "你好，请介绍一下人工智能的发展历史"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### JavaScript 示例

```javascript
const response = await fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'Deepseek-R1-7B',
    messages: [
      {
        role: 'system',
        content: '你是一个专业的AI助手'
      },
      {
        role: 'user',
        content: '你好，请介绍一下人工智能的发展历史'
      }
    ],
    temperature: 0.7,
    max_tokens: 1000
  })
});

const result = await response.json();
console.log('Token使用情况:', result.usage);
console.log('响应内容:', result.choices[0].message.content);
```

## 在网关中的使用

### Lua 脚本示例

```lua
-- 处理 OpenAI 格式的请求
local function process_openai_request(request_body)
    local httpc = require "resty.http"
    local cjson = require "cjson"
    
    -- 发送到 Token 计算服务
    local http = httpc:new()
    local res, err = http:request_uri("http://ai-gateway-token-service-dev:8000/v1/chat/completions", {
        method = "POST",
        headers = {
            ["Content-Type"] = "application/json"
        },
        body = request_body
    })
    
    if res and res.status == 200 then
        local result = cjson.decode(res.body)
        
        -- 检查 Token 限制
        if result.usage.total_tokens > 4000 then
            return ngx.HTTP_BAD_REQUEST, "Token 数量超过限制"
        end
        
        return ngx.HTTP_OK, result
    end
    
    return ngx.HTTP_INTERNAL_SERVER_ERROR, "Token 计算失败"
end
```

## 测试

运行测试脚本：

```bash
cd services/token-count
python test_openai.py
```

## 注意事项

1. **模型支持**：确保请求的模型在配置中存在且已下载
2. **Token 限制**：建议设置合理的 max_tokens 参数
3. **错误处理**：请妥善处理各种错误情况
4. **性能考虑**：大批量请求时建议使用批量计算接口
5. **兼容性**：完全兼容 OpenAI API 格式，可直接替换使用
