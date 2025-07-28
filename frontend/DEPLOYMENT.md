# 前端容器化部署指南

## 📋 概述

前端服务使用React + TypeScript + Ant Design构建，通过Docker容器化部署，使用Nginx作为Web服务器。

## 🐳 容器化特性

### 多阶段构建
- **构建阶段**: 使用Node.js 18 Alpine镜像构建React应用
- **生产阶段**: 使用Nginx Alpine镜像提供静态文件服务

### 安全优化
- 使用非root用户运行Nginx
- 最小化镜像大小
- 清理构建缓存

### 性能优化
- Gzip压缩
- 静态资源缓存
- 健康检查

## 🚀 部署方式

### 方式一：独立部署前端

```bash
# 构建前端镜像
cd frontend
docker build -t ai-gateway-frontend .

# 运行前端容器
docker run -d \
  --name ai-gateway-frontend \
  -p 80:80 \
  --network ai-gateway-network \
  ai-gateway-frontend
```

### 方式二：使用Docker Compose（推荐）

```bash
# 在项目根目录执行
docker-compose up -d frontend
```

### 方式三：一键部署所有服务

```bash
# Linux/Mac
./deploy.sh

# Windows
deploy.bat
```

## 🔧 配置说明

### 环境变量
- `NODE_ENV`: 构建环境（production）
- `VITE_API_BASE_URL`: API基础URL（可选）

### 端口映射
- 容器内端口: 80
- 主机端口: 80

### 网络配置
- 使用Docker网络: `ai-gateway-network`
- API代理到后端服务: `config-center:8001`

## 📊 健康检查

前端服务提供健康检查端点：
- URL: `http://localhost/health`
- 检查间隔: 30秒
- 超时时间: 10秒
- 重试次数: 3次

## 🔍 故障排查

### 查看容器状态
```bash
docker ps -a | grep ai-gateway-frontend
```

### 查看容器日志
```bash
docker logs ai-gateway-frontend
```

### 进入容器调试
```bash
docker exec -it ai-gateway-frontend sh
```

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :80
   # 或使用其他端口
   docker run -p 8080:80 ai-gateway-frontend
   ```

2. **网络连接问题**
   ```bash
   # 检查网络
   docker network ls
   docker network inspect ai-gateway-network
   ```

3. **构建失败**
   ```bash
   # 清理缓存重新构建
   docker build --no-cache -t ai-gateway-frontend .
   ```

## 📈 性能监控

### 资源使用
```bash
docker stats ai-gateway-frontend
```

### 访问日志
```bash
docker exec ai-gateway-frontend tail -f /var/log/nginx/access.log
```

### 错误日志
```bash
docker exec ai-gateway-frontend tail -f /var/log/nginx/error.log
```

## 🔄 更新部署

### 重新构建镜像
```bash
cd frontend
docker build -t ai-gateway-frontend .
docker-compose up -d frontend
```

### 滚动更新
```bash
docker-compose up -d --no-deps --build frontend
```

## 📝 注意事项

1. 确保后端服务正常运行
2. 检查网络连接配置
3. 定期清理未使用的镜像
4. 监控容器资源使用情况
5. 备份重要配置文件 