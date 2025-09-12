# AI智能网关配置中心 - 新前端接口对接说明

## 📋 对接概述

本文档说明了新前端与后端API的对接情况，包括已实现的接口、数据格式转换和测试方法。

## ✅ 已对接的接口

### 1. 命名空间管理 (`/api/namespaces`)

| 接口 | 方法 | 路径 | 状态 | 说明 |
|------|------|------|------|------|
| 获取列表 | GET | `/api/namespaces` | ✅ 已对接 | 支持分页、筛选、搜索 |
| 获取详情 | GET | `/api/namespaces/{id}` | ✅ 已对接 | 获取单个命名空间信息 |
| 创建 | POST | `/api/namespaces` | ✅ 已对接 | 创建新命名空间 |
| 更新 | PUT | `/api/namespaces/{id}` | ✅ 已对接 | 更新命名空间信息 |
| 删除 | DELETE | `/api/namespaces/{id}` | ✅ 已对接 | 删除命名空间 |
| 状态切换 | PUT | `/api/namespaces/{id}/status` | ✅ 已对接 | 启用/禁用命名空间 |
| 统计信息 | GET | `/api/namespaces/{id}/stats` | ✅ 已对接 | 获取命名空间统计数据 |

### 2. 上游服务器管理 (`/api/upstreams`)

| 接口 | 方法 | 路径 | 状态 | 说明 |
|------|------|------|------|------|
| 获取列表 | GET | `/api/upstreams` | ✅ 已对接 | 支持分页、搜索 |
| 获取详情 | GET | `/api/upstreams/{id}` | ✅ 已对接 | 获取单个服务器信息 |
| 创建 | POST | `/api/upstreams` | ✅ 已对接 | 创建新上游服务器 |
| 更新 | PUT | `/api/upstreams/{id}` | ✅ 已对接 | 更新服务器信息 |
| 删除 | DELETE | `/api/upstreams/{id}` | ✅ 已对接 | 删除上游服务器 |
| 状态切换 | PUT | `/api/upstreams/{id}/status` | ✅ 已对接 | 启用/禁用服务器 |

### 3. 路由规则管理 (`/api/locations`)

| 接口 | 方法 | 路径 | 状态 | 说明 |
|------|------|------|------|------|
| 获取列表 | GET | `/api/locations` | ✅ 已对接 | 支持分页、搜索 |
| 获取详情 | GET | `/api/locations/{id}` | ✅ 已对接 | 获取单个规则信息 |
| 创建 | POST | `/api/locations` | ✅ 已对接 | 创建新路由规则 |
| 更新 | PUT | `/api/locations/{id}` | ✅ 已对接 | 更新路由规则 |
| 删除 | DELETE | `/api/locations/{id}` | ✅ 已对接 | 删除路由规则 |
| 状态切换 | PUT | `/api/locations/{id}/status` | ✅ 已对接 | 启用/禁用规则 |

### 4. 仪表盘统计 (`/api/dashboard`)

| 接口 | 方法 | 路径 | 状态 | 说明 |
|------|------|------|------|------|
| 核心指标 | GET | `/api/dashboard/metrics` | ✅ 已对接 | 获取核心统计数据 |
| 命名空间统计 | GET | `/api/dashboard/namespaces` | ✅ 已对接 | 获取命名空间统计 |
| 实时监控 | GET | `/api/dashboard/realtime` | ✅ 已对接 | 获取实时监控数据 |
| 系统健康 | GET | `/api/dashboard/health` | ✅ 已对接 | 获取系统健康状态 |

## 🔄 数据格式转换

### 命名空间数据转换

**新前端格式 → 后端格式**
```json
{
  "code": "ns-enterprise-001",           → "namespace_code"
  "name": "企业版模型服务",                → "namespace_name"
  "status": "enabled"                    → "status": 1
}
```

**后端格式 → 新前端格式**
```json
{
  "namespace_id": 1,                     → "id"
  "namespace_code": "ns-001",            → "code"
  "namespace_name": "测试服务",           → "name"
  "status": 1,                          → "status": "enabled"
  "create_time": "2024-01-15",          → "createdAt"
  "update_time": "2024-01-15"           → "updatedAt"
}
```

### 上游服务器数据转换

**新前端格式 → 后端格式**
```json
{
  "name": "test-server",                 → "server_name"
  "servers": [{"address": "127.0.0.1", "port": 8080}] → "server_url": "http://127.0.0.1:8080"
  "keepalive": 64,                      → "max_connections"
  "health_check": {"enabled": true}     → "health_check_url": "/health"
}
```

## 🚀 快速启动

### 1. 启动后端服务
```bash
cd config-center
python main.py
```

### 2. 运行接口测试
```bash
cd config-center
python test_api_integration.py
```

### 3. 启动前端服务
```bash
cd frontend
npm run dev
```

### 4. 使用集成测试脚本
```bash
# Windows
start_integration_test.bat

# Linux/Mac
chmod +x start_integration_test.sh
./start_integration_test.sh
```

## 📱 访问地址

- **前端界面**: http://localhost:5173
- **后端API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 🧪 测试验证

### 1. 命名空间管理测试
- ✅ 创建命名空间
- ✅ 查看命名空间列表
- ✅ 编辑命名空间信息
- ✅ 启用/禁用命名空间
- ✅ 删除命名空间

### 2. 上游服务器管理测试
- ✅ 添加上游服务器
- ✅ 查看服务器列表
- ✅ 编辑服务器配置
- ✅ 启用/禁用服务器
- ✅ 删除服务器

### 3. 路由规则管理测试
- ✅ 创建路由规则
- ✅ 查看规则列表
- ✅ 编辑规则配置
- ✅ 启用/禁用规则
- ✅ 删除规则

### 4. 仪表盘功能测试
- ✅ 查看核心指标
- ✅ 查看命名空间统计
- ✅ 查看实时监控数据
- ✅ 查看系统健康状态

## ⚠️ 注意事项

1. **认证方式**: 当前使用简化的Bearer Token认证，生产环境需要实现完整的JWT验证
2. **数据模拟**: 部分接口返回模拟数据，需要连接真实的监控和统计系统
3. **错误处理**: 已实现基本的错误处理，建议增加更详细的错误信息
4. **性能优化**: 大量数据查询时建议增加缓存和分页优化

## 🔧 后续开发

### 需要实现的功能
1. **策略配置管理** - 限流、配额、鉴权策略
2. **流量监控** - QPS、响应时间、告警管理
3. **访问日志** - 日志查询、分析、导出
4. **Nginx配置管理** - 配置验证、重载、测试

### 优化建议
1. 增加数据验证和错误处理
2. 实现真实的统计数据获取
3. 添加接口性能监控
4. 完善日志记录和审计功能

## 📞 技术支持

如有问题，请检查：
1. 后端服务是否正常运行
2. 数据库连接是否正常
3. Redis连接是否正常
4. 前端服务是否正常启动
5. 网络连接是否正常
