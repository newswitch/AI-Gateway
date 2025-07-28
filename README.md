# AI-Gateway

## 📋 项目简介

AI-Gateway 是一个智能API网关系统，提供精确的Token计算、流量控制、负载均衡等功能，支持Docker Compose和Kubernetes部署。

## 🎯 核心功能

- ✅ **精确Token计算**: 集成专业Token计算服务，支持多种大模型
- ✅ **智能限流**: 支持QPS、并发数、Token数量等多种限流策略
- ✅ **负载均衡**: 多种负载均衡算法，支持健康检查和故障转移
- ✅ **配置管理**: 轻量级配置中心，支持动态配置更新
- ✅ **监控告警**: 完整的监控和告警体系
- ✅ **多环境部署**: 支持Docker Compose和Kubernetes部署

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Gateway       │    │   Services      │
│   (React)       │    │   (Nginx+Lua)   │    │   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Config Center │
                    │   (FastAPI)     │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Infrastructure│
                    │   (MySQL+Redis) │
                    └─────────────────┘
```

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- Python 3.8+
- Node.js 16+

### 开发环境部署

```bash
# 1. 克隆项目
git clone https://github.com/newswitch/AI-Gateway.git
cd AI-Gateway

# 2. 复制环境配置
cp env.example .env

# 3. 启动服务
docker-compose up -d

# 4. 访问服务
# 前端界面: http://localhost:8080
# API接口: http://localhost:8001
# Gateway服务: http://localhost:8081
```

### 生产环境部署

```bash
# 1. 构建镜像
docker build -t ai-gateway-token-service:latest ./services/token-count
docker build -t ai-gateway-config-center:latest ./config-center
docker build -t ai-gateway-frontend:latest ./frontend
docker build -t ai-gateway-nginx:latest ./gateway

# 2. 部署到Kubernetes
cd k8s
./deploy.sh
```

## 📁 项目结构

```
AI-Gateway/
├── config-center/          # 配置中心服务
├── frontend/              # 前端管理界面
├── gateway/               # 网关服务
├── k8s/                  # Kubernetes部署文件
├── services/              # 微服务
│   └── token-count/      # Token计算服务
├── docs/                 # 项目文档
├── env.example           # 环境变量配置模板
└── docker-compose.yml    # Docker编排文件
```

## 🔧 配置说明

### 环境变量配置

项目使用统一的环境变量配置，支持以下配置项：

- **数据库配置**: `DATABASE_URL`
- **Redis配置**: `REDIS_URL`
- **Token服务配置**: `TOKEN_SERVICE_URL`, `USE_PRECISE_TOKEN_CALCULATION`
- **服务配置**: `DEBUG`, `LOG_LEVEL`, `MONITORING_ENABLED`

详细配置说明请参考 [env.example](env.example) 文件。

## 📚 文档

- [部署指南](docs/智能网关需求文档.md)
- [配置中心设计](docs/轻量级配置中心设计.md)
- [监控仪表盘说明](docs/命名空间监控仪表盘功能说明.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目地址: https://github.com/newswitch/AI-Gateway
- 问题反馈: [Issues](https://github.com/newswitch/AI-Gateway/issues)

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！ 