@echo off
chcp 65001 >nul
echo 部署模拟大模型服务...

echo.
echo 1. 停止现有容器...
docker stop mock-llm 2>nul
docker rm mock-llm 2>nul

echo.
echo 2. 构建镜像...
cd services/mock-llm
docker build -t mock-llm:latest .

echo.
echo 3. 运行容器...
docker run -d --name mock-llm -p 8003:8003 mock-llm:latest

echo.
echo 4. 等待服务启动...
timeout /t 10 /nobreak >nul

echo.
echo 5. 检查容器状态...
docker ps | findstr mock-llm

echo.
echo 6. 测试服务...
echo 健康检查: http://localhost:8003/health
echo API文档: http://localhost:8003/docs
echo 模型列表: http://localhost:8003/v1/models

echo.
echo 模拟大模型服务部署完成！
echo 服务地址: http://localhost:8003
echo.
echo 测试命令:
echo curl http://localhost:8003/health
echo curl http://localhost:8003/v1/models
echo.
echo 停止服务: docker stop mock-llm
echo 删除服务: docker rm mock-llm
echo.
pause
