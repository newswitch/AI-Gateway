# LLM Gateway Dashboard API 接口文档

## 概述

本文档描述了 LLM Gateway Dashboard 前端应用所需的所有后端API接口。接口采用RESTful设计风格，支持JSON格式的数据交换。

## 基础信息

- **Base URL**: `http://localhost:8080/api`
- **认证方式**: JWT Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "参数错误",
  "error": "详细错误信息",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 分页响应
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "size": 10,
    "pages": 10
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 1. 仪表盘页面 API

### 1.1 获取核心指标统计
```http
GET /api/dashboard/metrics
```

**响应数据：**
```json
{
  "totalRequests": 12856,
  "successRate": "98.7%",
  "growthRate": "12%",
  "inputTokens": 930452,
  "outputTokens": 526831,
  "avgInputTokens": 72.4,
  "avgOutputTokens": 40.9,
  "peakQPS": 36,
  "currentQPS": 12
}
```

### 1.2 获取命名空间统计
```http
GET /api/dashboard/namespaces
```

**响应数据：**
```json
[
  {
    "id": "1",
    "code": "ns-enterprise-001",
    "name": "企业版模型服务",
    "requestCount": 8562,
    "successRate": "99.2%",
    "avgResponseTime": "1.2s",
    "status": "enabled"
  }
]
```

### 1.3 获取实时监控数据
```http
GET /api/dashboard/realtime
```

**查询参数：**
- `timeRange`: 时间范围 (15m, 30m, 1h, 6h, 24h)
- `granularity`: 数据粒度 (minute, hour)
- `namespace`: 命名空间筛选

## 2. 模型路由管理 API

### 2.1 上游服务器管理

#### 获取所有上游服务器
```http
GET /api/upstreams
```

#### 创建上游服务器
```http
POST /api/upstreams
Content-Type: application/json

{
  "name": "ds1_5b",
  "servers": [
    {
      "address": "10.224.104.141",
      "port": 32201,
      "weight": 1
    }
  ],
  "keepalive": 64,
  "health_check": {
    "enabled": true,
    "path": "/health",
    "interval": 30
  }
}
```

#### 更新上游服务器
```http
PUT /api/upstreams/{id}
Content-Type: application/json
```

#### 删除上游服务器
```http
DELETE /api/upstreams/{id}
```

### 2.2 路由规则管理

#### 获取所有路由规则
```http
GET /api/locations
```

#### 创建路由规则
```http
POST /api/locations
Content-Type: application/json

{
  "path": "/ds1_5b/v1/chat/completions",
  "upstream": "ds1_5b",
  "proxy_cache": false,
  "proxy_buffering": false,
  "proxy_pass": "http://ds1_5b/v1/chat/completions",
  "is_regex": false,
  "limit_req": {
    "enabled": true,
    "zone": "llm",
    "burst": 20,
    "nodelay": true
  },
  "sse_support": true,
  "chunked_transfer": true
}
```

#### 更新路由规则
```http
PUT /api/locations/{id}
Content-Type: application/json
```

#### 删除路由规则
```http
DELETE /api/locations/{id}
```

### 2.3 配置同步

#### 同步配置到Nginx
```http
POST /api/config/sync
```

#### 导出配置
```http
GET /api/config/export
```

#### 导入配置
```http
POST /api/config/import
Content-Type: multipart/form-data
```

## 3. 命名空间管理 API

### 3.1 命名空间CRUD

#### 获取命名空间列表
```http
GET /api/namespaces
```

**查询参数：**
- `page`: 页码 (默认: 1)
- `size`: 每页数量 (默认: 10)
- `owner`: 所有者筛选
- `status`: 状态筛选 (enabled/disabled)
- `keyword`: 关键词搜索

#### 创建命名空间
```http
POST /api/namespaces
Content-Type: application/json

{
  "code": "ns-enterprise-001",
  "name": "企业版模型服务",
  "owner": {
    "name": "张三",
    "avatar": "https://example.com/avatar.jpg"
  },
  "defaultUpstream": "llm-gpt4-prod",
  "qps": 100,
  "concurrency": 50,
  "quota": "10万/天",
  "maxSize": "10MB",
  "timeout": "30s"
}
```

#### 更新命名空间
```http
PUT /api/namespaces/{id}
Content-Type: application/json
```

#### 删除命名空间
```http
DELETE /api/namespaces/{id}
```

#### 启用/禁用命名空间
```http
PUT /api/namespaces/{id}/status
Content-Type: application/json

{
  "status": "enabled"
}
```

### 3.2 命名空间统计

#### 获取命名空间统计信息
```http
GET /api/namespaces/{id}/stats
```

## 4. 策略配置 API

### 4.1 策略管理

#### 获取策略列表
```http
GET /api/policies
```

**查询参数：**
- `page`: 页码
- `size`: 每页数量
- `type`: 策略类型筛选
- `status`: 状态筛选
- `keyword`: 关键词搜索

#### 创建策略
```http
POST /api/policies
Content-Type: application/json

{
  "name": "enterprise-policy",
  "type": "混合策略",
  "namespaces": ["enterprise"],
  "rules": [
    {
      "type": "rate_limit",
      "value": "5000 req/hour"
    },
    {
      "type": "token_limit",
      "value": "500000/hour"
    }
  ],
  "status": "enabled"
}
```

#### 更新策略
```http
PUT /api/policies/{id}
Content-Type: application/json
```

#### 删除策略
```http
DELETE /api/policies/{id}
```

#### 复制策略
```http
POST /api/policies/{id}/copy
Content-Type: application/json

{
  "name": "新策略名称"
}
```

### 4.2 策略模板

#### 获取策略模板列表
```http
GET /api/policy-templates
```

#### 使用模板创建策略
```http
POST /api/policies/from-template
Content-Type: application/json

{
  "templateId": "1",
  "name": "新策略名称",
  "namespaces": ["enterprise"]
}
```

### 4.3 策略规则配置

#### 获取策略规则类型
```http
GET /api/policy-rule-types
```

#### 验证策略规则
```http
POST /api/policies/validate
Content-Type: application/json

{
  "rules": [...]
}
```

## 5. 统一配置管理 API

### 5.1 Nginx配置管理

#### 获取Nginx配置
```http
GET /api/nginx/config
```

#### 更新Nginx配置
```http
PUT /api/nginx/config
Content-Type: application/json

{
  "user": "nginx",
  "worker_processes": "auto",
  "error_log": "/var/log/nginx/error.log notice",
  "pid": "/var/run/nginx.pid",
  "events": {
    "use": "epoll",
    "worker_connections": 4096,
    "multi_accept": true
  },
  "http": {
    "client_max_body_size": "256M",
    "proxy_http_version": "1.1",
    "proxy_buffers": "4 256K",
    "proxy_buffer_size": "256K",
    "proxy_busy_buffers_size": "512K",
    "proxy_connect_timeout": "900s",
    "proxy_read_timeout": "1800s",
    "proxy_send_timeout": "1800s",
    "keepalive_timeout": "180s",
    "keepalive_requests": 100,
    "access_log": "/var/log/nginx/access.log main",
    "log_format": "main",
    "sendfile": true,
    "tcp_nopush": true,
    "tcp_nodelay": true,
    "server": {
      "listen": 8080,
      "server_name": "localhost",
      "proxy_headers": {
        "host": true,
        "real_ip": true,
        "forwarded_for": true,
        "forwarded_proto": true,
        "connection": true
      },
      "health_check": {
        "enabled": true,
        "path": "/health"
      }
    },
    "limit_req": {
      "enabled": true,
      "zone": "llm:10m",
      "rate": "30r/s"
    }
  }
}
```

#### 验证Nginx配置
```http
POST /api/nginx/validate
```

#### 重载Nginx配置
```http
POST /api/nginx/reload
```

#### 测试Nginx配置
```http
POST /api/nginx/test
```

## 6. 流量监控 API

### 6.1 监控数据

#### 获取监控指标
```http
GET /api/monitoring/metrics
```

**查询参数：**
- `namespace`: 命名空间筛选
- `rule`: 规则筛选
- `upstream`: 上游服务器筛选
- `statusCode`: 状态码筛选
- `method`: 请求方法筛选
- `timeRange`: 时间范围

#### 获取实时QPS
```http
GET /api/monitoring/qps
```

**查询参数：**
- `namespace`: 命名空间筛选
- `timeRange`: 时间范围

#### 获取响应时间统计
```http
GET /api/monitoring/response-time
```

#### 获取错误率统计
```http
GET /api/monitoring/error-rate
```

### 6.2 告警管理

#### 获取告警列表
```http
GET /api/alerts
```

**查询参数：**
- `page`: 页码
- `size`: 每页数量
- `level`: 告警级别筛选
- `status`: 状态筛选
- `timeRange`: 时间范围

#### 创建告警规则
```http
POST /api/alerts/rules
Content-Type: application/json

{
  "name": "错误率告警",
  "condition": "error_rate > 0.01",
  "threshold": 0.01,
  "level": "warning",
  "enabled": true
}
```

#### 更新告警规则
```http
PUT /api/alerts/rules/{id}
Content-Type: application/json
```

#### 删除告警规则
```http
DELETE /api/alerts/rules/{id}
```

#### 标记告警为已处理
```http
PUT /api/alerts/{id}/resolve
```

## 7. 访问日志 API

### 7.1 日志查询

#### 获取访问日志
```http
GET /api/logs/access
```

**查询参数：**
- `page`: 页码
- `size`: 每页数量
- `level`: 日志级别筛选
- `model`: 模型筛选
- `status`: 状态筛选
- `keyword`: 关键词搜索
- `timeRange`: 时间范围
- `clientIp`: 客户端IP筛选
- `apiKey`: API Key筛选

#### 获取日志统计
```http
GET /api/logs/statistics
```

**查询参数：**
- `timeRange`: 时间范围
- `level`: 日志级别筛选
- `model`: 模型筛选

#### 导出日志
```http
GET /api/logs/export
```

**查询参数：**
- `format`: 导出格式 (json, csv, xlsx)
- `timeRange`: 时间范围
- `filters`: 筛选条件

### 7.2 日志分析

#### 获取日志级别分布
```http
GET /api/logs/level-distribution
```

**查询参数：**
- `timeRange`: 时间范围

#### 获取日志趋势
```http
GET /api/logs/trend
```

**查询参数：**
- `timeRange`: 时间范围
- `granularity`: 数据粒度

#### 获取热门路径
```http
GET /api/logs/popular-paths
```

**查询参数：**
- `timeRange`: 时间范围
- `limit`: 返回数量限制

## 8. 通用API

### 8.1 系统信息

#### 获取系统状态
```http
GET /api/system/status
```

#### 获取系统健康检查
```http
GET /api/system/health
```

#### 获取系统版本信息
```http
GET /api/system/version
```

### 8.2 用户认证

#### 用户登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

#### 用户登出
```http
POST /api/auth/logout
```

#### 获取用户信息
```http
GET /api/auth/user
```

#### 刷新Token
```http
POST /api/auth/refresh
```

### 8.3 文件上传

#### 上传配置文件
```http
POST /api/upload/config
Content-Type: multipart/form-data
```

#### 上传日志文件
```http
POST /api/upload/logs
Content-Type: multipart/form-data
```

## 9. WebSocket 实时数据

### 9.1 实时监控

```javascript
// WebSocket连接
const ws = new WebSocket('ws://localhost:8080/ws/monitoring');

// 订阅实时数据
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'metrics',
  namespace: 'all'
}));

// 接收实时数据
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('实时数据:', data);
};
```

## 10. 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 1001 | 配置验证失败 |
| 1002 | 上游服务器连接失败 |
| 1003 | Nginx配置重载失败 |

## 11. 开发建议

1. **统一响应格式**：所有API都使用相同的响应结构
2. **错误处理**：提供详细的错误信息和错误码
3. **分页支持**：列表接口都支持分页查询
4. **参数验证**：所有输入参数都要进行验证
5. **日志记录**：记录所有API调用日志
6. **权限控制**：实现基于角色的访问控制
7. **限流保护**：对API进行限流保护
8. **监控告警**：监控API性能和错误率
9. **接口版本**：支持API版本控制
10. **文档更新**：保持接口文档与代码同步

## 12. 测试建议

1. **单元测试**：为每个API编写单元测试
2. **集成测试**：测试API之间的交互
3. **性能测试**：测试API的响应时间和并发能力
4. **安全测试**：测试API的安全性
5. **兼容性测试**：测试不同客户端的兼容性

---

**文档版本**: v1.0  
**最后更新**: 2024-01-15  
**维护人员**: 开发团队
