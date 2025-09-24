# AI-Gateway 2.0

## 📋 项目简介

AI-Gateway 2.0 是一个企业级智能API网关系统，基于OpenResty/Nginx+Lua构建，提供精确的Token计算、智能限流、负载均衡、实时监控等功能。**支持流式和非流式API的完整Token限制**。

## 🎯 核心功能

- ✅ **精确Token计算**: 集成专业Token计算服务，支持多种模型
- ✅ **智能限流策略**: 支持QPS、并发数、Token数量、时间窗口限流
- ✅ **流式输出控制**: 实时监控流式响应Token数量，支持动态截断
- ✅ **负载均衡**: 轮询、权重、路径匹配等多种算法，支持健康检查
- ✅ **配置管理**: 轻量级配置中心，支持动态配置和热更新
- ✅ **实时监控**: 集成Prometheus监控，支持指标收集和可视化
- ✅ **命名空间管理**: 基于匹配器的多租户命名空间隔离
- ✅ **策略执行**: 灵活的权限控制和资源限制策略
- ✅ **一键部署**: 使用Docker Compose实现一键启动

## 🚀 快速开始

### 环境要求
- **Docker** 20.10+
- **Docker Compose** 2.0+

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/newswitch/AI-Gateway-2.0.git
cd AI-Gateway-2.0

# 2. 启动开发环境（推荐）
docker-compose -f docker-compose.dev.yml up -d

# 3. 查看服务状态
docker-compose -f docker-compose.dev.yml ps
```

### 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 🖥️ **前端管理界面** | http://localhost:8080 | React管理界面 |
| 🔧 **配置中心API** | http://localhost:8001 | FastAPI后端服务 |
| 🌐 **网关服务** | http://localhost:8081 | Nginx+Lua网关入口 |
| 📊 **Prometheus监控** | http://localhost:9090 | 监控指标收集 |
| 🔢 **Token计算服务** | http://localhost:8002 | 专业Token计算 |
| 🗄️ **MySQL数据库** | localhost:3307 | 配置数据存储 |
| 📦 **Redis缓存** | localhost:6379 | 缓存和限流数据 |

### 常用命令

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 启动生产环境
docker-compose up -d

# 停止服务
docker-compose -f docker-compose.dev.yml down

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 重启特定服务
docker-compose -f docker-compose.dev.yml restart gateway

# 重新构建
docker-compose -f docker-compose.dev.yml up -d --build

# 查看网关日志
docker-compose -f docker-compose.dev.yml logs -f gateway
```

## 📁 项目结构

```
AI-Gateway-2.0/
├── 📁 config-center/          # 配置中心服务 (FastAPI)
│   ├── 📁 app/api/v2/        # V2 API接口
│   ├── 📁 app/schemas/       # 数据模型
│   └── 📁 app/services/      # 业务服务
├── 📁 frontend/              # 前端管理界面 (React+TypeScript)
│   ├── 📁 src/pages/         # 页面组件
│   └── 📁 src/services/      # API服务
├── 📁 gateway/               # 网关服务 (OpenResty/Nginx+Lua)
│   ├── 📁 conf/lua/          # Lua脚本模块
│   │   ├── 📁 auth/          # 认证和策略执行
│   │   ├── 📁 routing/       # 路由和负载均衡
│   │   ├── 📁 monitoring/    # 监控和调度
│   │   └── 📁 utils/         # 工具函数
│   └── 📄 nginx.conf         # Nginx配置
├── 📁 services/              # 微服务
│   ├── 📁 token-count/       # Token计算服务
│   └── 📁 mock-llm/          # 模拟LLM服务
├── 📁 monitoring/            # 监控配置
│   └── 📄 prometheus.yml     # Prometheus配置
├── 📁 k8s/                  # Kubernetes部署文件
├── 📁 docs/                 # 项目文档
├── 📄 docker-compose.dev.yml # 开发环境编排
├── 📄 docker-compose.yml    # 生产环境编排
└── 📄 README.md            # 项目说明
```

## 🔧 配置说明

### 环境变量配置

主要配置项：

```bash
# 数据库配置
MYSQL_ROOT_PASSWORD=ai_gateway_root
MYSQL_DATABASE=ai_gateway_config
MYSQL_USER=ai_gateway
MYSQL_PASSWORD=ai_gateway_pass

# Redis配置
REDIS_PASSWORD=ai_gateway_redis_pass

# Token计算服务配置
TOKEN_SERVICE_URL=http://token-service:8002
USE_PRECISE_TOKEN_CALCULATION=true

# Prometheus监控配置
PROMETHEUS_ENABLED=true
PROMETHEUS_JOB_NAME=ai-gateway-lua

# 服务端口配置
FRONTEND_PORT=8080
CONFIG_CENTER_PORT=8001
GATEWAY_PORT=8081
TOKEN_SERVICE_PORT=8002
PROMETHEUS_PORT=9090
```

详细配置说明请参考 [env.example](env.example) 文件。

### 核心功能配置

#### Token限制策略
- **输入Token限制**: 单次请求最大输入Token数
- **输出Token限制**: 单次请求最大输出Token数  
- **时间窗口限制**: 指定时间内的Token使用量限制
- **流式输出控制**: 实时监控和截断流式响应

#### 负载均衡策略
- **轮询算法**: 基于共享内存的多进程轮询
- **权重算法**: 基于权重的随机选择
- **路径匹配**: 基于请求路径的精确路由

#### 监控指标
- **请求指标**: 总请求数、成功/失败请求数
- **性能指标**: 响应时间、QPS、并发数
- **Token指标**: Token使用量、限制命中率
- **系统指标**: 上游健康状态、错误率

## 🚀 部署

### 开发环境部署（推荐）

```bash
# 1. 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 2. 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 3. 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 生产环境部署

```bash
# 1. 设置生产环境变量
cp env.example .env.prod
# 编辑 .env.prod 文件，设置生产环境配置

# 2. 使用生产环境配置启动
docker-compose --env-file .env.prod up -d

# 3. 查看服务状态
docker-compose ps
```

### Kubernetes 部署

```bash
# 1. 进入k8s目录
cd k8s

# 2. 部署到Kubernetes集群
kubectl apply -f .

# 3. 查看部署状态
kubectl get pods -n ai-gateway

# 4. 查看服务
kubectl get svc -n ai-gateway
```

### 监控部署

```bash
# 1. 启动Prometheus监控
docker-compose -f docker-compose.dev.yml up -d prometheus

# 2. 访问监控界面
# Prometheus: http://localhost:9090
# 网关指标: http://localhost:8081/metrics
```

## 📚 文档

- [智能网关需求文档](docs/智能网关需求文档.md)
- [轻量级配置中心设计](docs/轻量级配置中心设计.md)
- [命名空间监控仪表盘功能说明](docs/命名空间监控仪表盘功能说明.md)
- [Prometheus集成启动指南](docs/Prometheus集成启动指南.md)
- [前端V2接口需求](docs/前端V2接口需求.md)
- [API接口清单](docs/API接口清单.md)

## 🔧 技术特性

### 架构特点
- **高性能**: 基于OpenResty/Nginx，支持高并发处理
- **模块化**: Lua模块化设计，易于扩展和维护
- **实时性**: 流式响应实时监控和截断
- **可观测性**: 完整的监控指标和日志记录

### 核心模块
- **命名空间匹配器**: 基于匹配器的多租户隔离
- **策略执行器**: 灵活的权限控制和资源限制
- **上游选择器**: 多种负载均衡算法
- **代理处理器**: 智能请求代理和响应处理
- **监控调度器**: 定时任务和指标收集

## 🚀 快速测试

### 测试Token计算服务
```bash
curl -X POST http://localhost:8002/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-8B",
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'
```

### 测试网关代理
```bash
curl -X POST http://localhost:8081/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Channel-Code: test-channel" \
  -d '{
    "model": "Qwen3-8B",
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'
```

### 查看监控指标
```bash
# 查看网关指标
curl http://localhost:8081/metrics

# 查看Prometheus指标
curl http://localhost:9090/api/v1/query?query=gateway_requests_total
```

## 📞 联系方式

- 项目地址: https://github.com/newswitch/AI-Gateway-2.0
- 问题反馈: [Issues](https://github.com/newswitch/AI-Gateway-2.0/issues)

---

⭐ 如果这个项目对您有帮助，请给我一个星标！ 