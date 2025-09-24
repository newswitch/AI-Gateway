# 复制预下载分词器文件的Docker镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY main.py .
COPY token_service.py .
COPY config.py .

# 复制预下载的分词器文件
COPY models/ ./models/

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH=/app
ENV MODELS_DIR=/app/models

# 启动命令
CMD ["python", "main.py"] 