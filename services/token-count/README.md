# Token计算服务 (轻量级版本)

一个基于FastAPI的轻量级Token计算服务，支持多种大语言模型的Token计算。

## 🎯 项目特点

- 🚀 **分离式构建** - 分词器下载和镜像构建完全分离
- ⚡ **快速构建** - 构建时间仅3-10分钟
- 🔧 **内网部署** - 支持离线使用，分词器规则本地化
- 📊 **批量计算** - 支持批量文本Token计算
- 🎯 **精确计算** - 基于Hugging Face的准确Token计算
- 🔍 **健康检查** - 完整的服务健康监控
- 📚 **API文档** - 自动生成的Swagger文档

## 📦 支持的模型

| 模型系列 | 模型名称 | 描述 |
|---------|---------|------|
| **GPT系列** | gpt-3.5-turbo, gpt-4 | GPT-2模型，适用于GPT系列 |
| **Qwen系列** | qwen, qwen2, qwen3, qwen3.5 | Qwen系列模型 |
| **DeepSeek系列** | deepseek-coder, deepseek-llm, deepseek-math等8个模型 | DeepSeek系列模型 |
| **其他模型** | claude-3, llama-2, chatglm, baichuan, internlm | 其他主流模型 |

## 🚀 快速开始

### Windows用户
```bash
# 双击运行构建脚本
build_with_download.bat
```

### Linux/Mac用户
```bash
# 给脚本执行权限
chmod +x build_with_download.sh

# 运行构建脚本
./build_with_download.sh
```

### 手动构建
```bash
# 第一步：下载分词器文件
python download_tokenizers_local.py

# 第二步：构建Docker镜像
docker build -f Dockerfile.copy -t token-service .

# 第三步：运行容器
docker run -d --name token-service-container -p 8000:8000 token-service
```

## 📊 性能特点

| 特性 | 数值 |
|------|------|
| **镜像大小** | 500-800MB |
| **构建时间** | 3-10分钟 |
| **启动时间** | 3-5秒 |
| **存储空间** | 需要2-3GB |
| **分词器大小** | 50-100MB |

## 🌐 API使用

### 计算Token
```bash
curl -X POST "http://localhost:8000/calculate" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, 世界！", "model_name": "gpt-3.5-turbo"}'
```

### 批量计算
```bash
curl -X POST "http://localhost:8000/batch-calculate" \
     -H "Content-Type: application/json" \
     -d '{"texts": ["Hello", "你好", "def hello(): pass"], "model_name": "deepseek-coder"}'
```

### 获取模型列表
```bash
curl http://localhost:8000/models
```

### 健康检查
```bash
curl http://localhost:8000/health
```

## 🔍 验证部署

### 运行测试
```bash
# 测试API接口
curl http://localhost:8000/health
curl http://localhost:8000/models

# 测试Token计算
curl -X POST "http://localhost:8000/calculate" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, 世界！", "model_name": "gpt-3.5-turbo"}'
```

### 查看服务状态
```bash
# 查看容器状态
docker ps --filter name=token-service-container

# 查看实时日志
docker logs -f token-service-container
```

## 📁 项目结构

```
aigateway/
├── main.py                    # FastAPI应用入口
├── token_service.py           # Token计算服务核心
├── config.py                  # 配置文件
├── download_tokenizers_local.py # 本地分词器下载脚本
├── requirements.txt           # Python依赖
├── Dockerfile.copy            # 复制预下载分词器的Dockerfile
├── build_with_download.sh     # Linux/Mac构建脚本
├── build_with_download.bat    # Windows构建脚本
├── README.md                  # 项目说明
├── models/                    # 分词器存储目录
└── .gitignore                 # Git忽略文件
```

## ⚙️ 配置说明

### 环境变量
- `HOST`: 服务监听地址 (默认: 0.0.0.0)
- `PORT`: 服务端口 (默认: 8000)
- `MODELS_DIR`: 分词器存储目录 (默认: ./models)
- `LOG_LEVEL`: 日志级别 (默认: INFO)

### 模型配置
在 `config.py` 中可以配置支持的模型：

```python
MODEL_MAPPINGS = {
    "gpt-3.5-turbo": {
        "name": "gpt2",
        "url": "https://huggingface.co/gpt2",
        "description": "GPT-2模型，适用于GPT-3.5-turbo"
    },
    # ... 更多模型配置
}
```

## 🔧 开发说明

### 添加新模型
1. 在 `config.py` 中添加模型配置
2. 重新下载分词器：`python download_tokenizers_local.py`
3. 重新构建镜像：`docker build -f Dockerfile.copy -t token-service .`
4. 重启容器

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务
python main.py
```

## 🚨 注意事项

1. **构建时间**：首次构建需要5-15分钟下载分词器文件
2. **网络要求**：构建时需要访问Hugging Face，运行时可完全离线
3. **存储空间**：确保有足够的磁盘空间（建议至少3GB）
4. **镜像大小**：轻量级版本约500-800MB，相比完整版本大幅减少

## 📞 故障排除

### 常见问题
1. **构建失败**：检查网络连接和Docker资源
2. **分词器加载失败**：确认镜像构建成功，检查容器日志
3. **性能问题**：检查容器资源限制和内存使用情况

## 🎉 优势总结

- ✅ **分离式构建**：分词器下载和镜像构建完全分离
- ✅ **可重复使用**：已下载的分词器可以重复使用
- ✅ **构建可控**：构建过程更加可控和透明
- ✅ **离线支持**：支持完全离线构建
- ✅ **开发友好**：便于调试和开发

## �� 许可证

MIT License 