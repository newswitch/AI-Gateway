# AI-Gateway

## 📋 项目简介

AI-Gateway 是一个智能API网关系统，提供精确的Token计算、流量控制、负载均衡等功能。**推荐使用Docker Compose进行快速部署**。

## 🎯 核心功能

- ✅ **精确Token计算**: 集成专业Token计算服务
- ✅ **智能限流**: 支持QPS、并发数、Token数量限流
- ✅ **负载均衡**: 多种负载均衡算法，支持健康检查
- ✅ **配置管理**: 轻量级配置中心，支持动态配置
- ✅ **监控告警**: 完整的监控和告警体系
- ✅ **一键部署**: 使用Docker Compose实现一键启动

## 🚀 快速开始

### 环境要求
- **Docker** 20.10+
- **Docker Compose** 2.0+

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/newswitch/AI-Gateway.git
cd AI-Gateway

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps
```

### 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 🖥️ **前端管理界面** | http://localhost:8080 | React管理界面 |
| 🔧 **配置中心API** | http://localhost:8001 | FastAPI后端服务 |
| 🌐 **网关服务** | http://localhost:8081 | Nginx网关入口 |

### 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 重新构建
docker-compose up -d --build
```

## 📁 项目结构

```
AI-Gateway/
├── 📁 config-center/          # 配置中心服务 (FastAPI)
├── 📁 frontend/              # 前端管理界面 (React)
├── 📁 gateway/               # 网关服务 (Nginx+Lua)
├── 📁 services/              # 微服务
│   └── 📁 token-count/      # Token计算服务
├── 📁 k8s/                  # Kubernetes部署文件
├── 📄 env.example           # 环境变量配置模板
├── 📄 docker-compose.yml    # Docker编排文件
└── 📄 README.md            # 项目说明
```

## 🔧 配置说明

### 环境变量配置

主要配置项：

```bash
# 数据库配置
DATABASE_URL=mysql://root:password@mysql:3306/ai_gateway

# Redis配置
REDIS_URL=redis://redis:6379/0

# Token计算服务配置
TOKEN_SERVICE_URL=http://ai-gateway-token-service:8000
USE_PRECISE_TOKEN_CALCULATION=true

# 服务端口配置
FRONTEND_PORT=8080
CONFIG_CENTER_PORT=8001
GATEWAY_PORT=8081
```

详细配置说明请参考 [env.example](env.example) 文件。

## 🚀 部署

### Docker Compose 生产环境

```bash
# 1. 设置生产环境变量
cp env.example .env.prod
# 编辑 .env.prod 文件，设置生产环境配置

# 2. 使用生产环境配置启动
docker-compose --env-file .env.prod up -d
```

### Kubernetes 部署

```bash
# 1. 进入k8s目录
cd k8s

# 2. 部署到Kubernetes集群
kubectl apply -f .

# 3. 查看部署状态
kubectl get pods -n ai-gateway
```

## 📚 文档

- [智能网关需求文档](docs/智能网关需求文档.md)
- [轻量级配置中心设计](docs/轻量级配置中心设计.md)
- [命名空间监控仪表盘功能说明](docs/命名空间监控仪表盘功能说明.md)

## 📞 联系方式

- 项目地址: https://github.com/newswitch/AI-Gateway
- 问题反馈: [Issues](https://github.com/newswitch/AI-Gateway/issues)

---

⭐ 如果这个项目对您有帮助，请给我一个星标！ 