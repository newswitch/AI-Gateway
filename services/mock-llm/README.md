# 模拟大模型服务

这是一个模拟vLLM API接口的服务，用于本地开发测试。

## 功能特性

- 模拟vLLM的完整API接口
- 支持聊天完成和文本完成
- 模拟token计算
- 支持多模型切换
- 随机响应生成
- 完整的错误处理

## 支持的API接口

### 1. 健康检查
- `GET /health` - 服务健康状态

### 2. 模型管理
- `GET /v1/models` - 列出所有模型
- `GET /v1/models/{model_id}` - 获取特定模型信息

### 3. 聊天完成
- `POST /v1/chat/completions` - 创建聊天完成

### 4. 文本完成
- `POST /v1/completions` - 创建文本完成

## 模拟的模型

- `qwen2.5-7b` - 模拟Qwen2.5-7B模型
- `qwen2.5-14b` - 模拟Qwen2.5-14B模型
- `deepseek-r1-7b` - 模拟DeepSeek-R1-7B模型

## 使用方法

### 本地运行
```bash
cd services/mock-llm
pip install -r requirements.txt
python main.py
```

### Docker运行
```bash
cd services/mock-llm
docker build -t mock-llm .
docker run -p 8003:8003 mock-llm
```

### 测试API
```bash
# 健康检查
curl http://localhost:8003/health

# 列出模型
curl http://localhost:8003/v1/models

# 聊天完成
curl -X POST http://localhost:8003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100
  }'
```

## API文档

启动服务后，访问 http://localhost:8003/docs 查看完整的API文档。

## 配置说明

- 端口：8003
- 响应延迟：0.5-2.0秒（模拟真实模型）
- Token计算：基于字符数粗略估算
- 支持参数：temperature, max_tokens, top_p, n等
