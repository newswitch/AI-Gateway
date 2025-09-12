# Redis缓存结构说明

## 📋 概述

本文档描述了AI智能网关配置中心的Redis缓存结构，包括所有缓存键名、数据格式和TTL配置。

## 🔧 缓存配置

### TTL配置
```python
cache_ttl = {
    'namespace': 3600,      # 命名空间缓存1小时
    'matchers': 3600,       # 匹配器缓存1小时
    'rules': 3600,          # 规则缓存1小时
    'upstream': 1800,       # 上游服务器缓存30分钟
    'proxy': 1800,          # 代理规则缓存30分钟
    'nginx_config': 7200,   # Nginx配置缓存2小时
    'policies': 1800,       # 策略配置缓存30分钟
    'traffic': 300,         # 流量监控缓存5分钟
    'logs': 600,            # 访问日志缓存10分钟
    'dashboard': 60,        # 仪表盘数据缓存1分钟
    'locations': 1800,      # 路由规则缓存30分钟
    'auth': 3600,           # 认证信息缓存1小时
    'alerts': 300,          # 告警信息缓存5分钟
    'stats': 300            # 统计数据缓存5分钟
}
```

## 📊 缓存键名结构

### 1. 基础配置缓存
```
config:{type}:{id}           # 单个配置项
config:{type}:list           # 配置列表
config:{type}:list:{filters} # 带筛选的配置列表
```

### 2. 业务数据缓存
```
traffic:metrics              # 流量监控指标
traffic:alerts               # 告警列表
traffic:alert:{alert_id}     # 单个告警
logs:stats                   # 日志统计
dashboard:metrics            # 仪表盘指标
dashboard:realtime           # 仪表盘实时数据
stats:{stats_type}           # 统计数据
```

### 3. 认证缓存
```
auth:token:{token}           # 认证令牌
auth:permissions:{user_id}   # 用户权限
```

## 🗂️ 详细缓存结构

### 1. 命名空间缓存
```redis
# 单个命名空间
config:namespace:1 = {
    "namespace_id": 1,
    "namespace_code": "wechat",
    "namespace_name": "微信渠道",
    "description": "微信小程序和公众号渠道",
    "status": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}

# 命名空间列表
config:namespace:list = [
    { /* 命名空间对象 */ },
    { /* 命名空间对象 */ }
]
```

### 2. 策略配置缓存
```redis
# 单个策略
config:policies:1 = {
    "policy_id": 1,
    "name": "enterprise-policy",
    "type": "混合策略",
    "namespaces": ["enterprise"],
    "rules": ["限流: 5000 req/hour", "Token限制: 500000/hour"],
    "status": "enabled",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}

# 策略列表
config:policies:list = [
    { /* 策略对象 */ },
    { /* 策略对象 */ }
]

# 带筛选的策略列表
config:policies:list:status=enabled:type=限流策略 = [
    { /* 策略对象 */ }
]
```

### 3. 流量监控缓存
```redis
# 流量指标
traffic:metrics = {
    "total_requests": 150000,
    "success_rate": "98.5%",
    "error_rate": "1.5%",
    "avg_response_time": 250,
    "qps": 1200,
    "active_connections": 45
}

# 告警列表
traffic:alerts = [
    {
        "alert_id": "alert_001",
        "time": "2024-01-15T15:32:45Z",
        "level": "urgent",
        "content": "API /v1/chat/completions 5xx错误率超过阈值 1.5%",
        "route": "/v1/chat/completions",
        "status": "processing"
    }
]

# 单个告警
traffic:alert:alert_001 = {
    "alert_id": "alert_001",
    "time": "2024-01-15T15:32:45Z",
    "level": "urgent",
    "content": "API /v1/chat/completions 5xx错误率超过阈值 1.5%",
    "route": "/v1/chat/completions",
    "status": "processing",
    "details": { /* 详细告警信息 */ }
}
```

### 4. 访问日志缓存
```redis
# 日志列表
config:logs:list:level=ERROR:start_time=2024-01-15:end_time=2024-01-16 = [
    {
        "log_id": "log_001",
        "timestamp": "2024-01-15T15:32:45Z",
        "level": "ERROR",
        "request_id": "req_123456",
        "model": "gpt-4",
        "client_ip": "192.168.1.100",
        "status": "500",
        "response_time": 1200,
        "message": "Internal server error"
    }
]

# 日志统计
logs:stats = {
    "total_logs": 50000,
    "error_count": 250,
    "warning_count": 1200,
    "info_count": 48000,
    "debug_count": 550,
    "error_rate": "0.5%",
    "avg_response_time": 180
}
```

### 5. 仪表盘数据缓存
```redis
# 仪表盘指标
dashboard:metrics = {
    "total_requests": 150000,
    "success_rate": "98.5%",
    "growth_rate": "12.5%",
    "input_tokens": 5000000,
    "output_tokens": 2000000,
    "avg_input_tokens": 33,
    "avg_output_tokens": 13,
    "peak_qps": 1500,
    "current_qps": 1200
}

# 实时数据
dashboard:realtime = {
    "time_range": "15m",
    "granularity": "minute",
    "data": [
        {
            "timestamp": "2024-01-15T15:30:00Z",
            "requests": 1200,
            "errors": 18,
            "avg_response_time": 250
        }
    ]
}
```

### 6. 路由规则缓存
```redis
# 单个路由规则
config:locations:1 = {
    "location_id": 1,
    "path": "/v1/chat/completions",
    "upstream": "gpt-4-upstream",
    "proxy_cache": true,
    "proxy_buffering": true,
    "proxy_pass": "http://gpt-4-upstream/v1/chat/completions",
    "status": "enabled"
}

# 路由规则列表
config:locations:list = [
    { /* 路由规则对象 */ },
    { /* 路由规则对象 */ }
]
```

### 7. 认证信息缓存
```redis
# 认证令牌
auth:token:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... = {
    "user_id": "admin",
    "username": "admin",
    "email": "admin@example.com",
    "roles": ["admin", "user"],
    "permissions": ["read", "write", "delete"],
    "expires_at": "2024-01-15T16:30:00Z"
}

# 用户权限
auth:permissions:admin = [
    "namespace:read",
    "namespace:write",
    "namespace:delete",
    "policy:read",
    "policy:write",
    "policy:delete",
    "traffic:read",
    "logs:read",
    "config:read",
    "config:write"
]
```

### 8. 统计数据缓存
```redis
# 策略统计
stats:policies = {
    "total_policies": 25,
    "enabled_policies": 20,
    "disabled_policies": 5,
    "policy_types": {
        "限流策略": 10,
        "安全策略": 8,
        "混合策略": 7
    }
}

# 流量统计
stats:traffic = {
    "total_requests": 150000,
    "success_requests": 147750,
    "error_requests": 2250,
    "avg_response_time": 250,
    "peak_qps": 1500,
    "current_qps": 1200
}
```

## 🔄 缓存更新策略

### 1. 写入策略
- **双写模式**: 同时写入Redis和MySQL
- **异步写入**: MySQL写入异步执行，不阻塞Redis操作
- **错误处理**: Redis写入失败时降级到MySQL

### 2. 读取策略
- **缓存优先**: 优先从Redis读取
- **降级机制**: Redis不可用时从MySQL读取
- **自动更新**: 缓存未命中时自动更新缓存

### 3. 删除策略
- **级联删除**: 删除主记录时同时删除相关缓存
- **列表更新**: 删除/更新记录时清除相关列表缓存
- **批量清理**: 定期清理过期和无效缓存

## 🚀 性能优化

### 1. 缓存预热
- 系统启动时预加载常用数据
- 定期刷新热点数据
- 智能预测用户访问模式

### 2. 缓存分层
- **L1**: 内存缓存（应用层）
- **L2**: Redis缓存（分布式）
- **L3**: MySQL数据库（持久化）

### 3. 缓存监控
- 缓存命中率监控
- 缓存响应时间监控
- 缓存容量使用监控
- 异常告警机制

## 📝 注意事项

1. **数据一致性**: 确保Redis和MySQL数据一致性
2. **内存管理**: 合理设置TTL，避免内存溢出
3. **键名规范**: 使用统一的键名命名规范
4. **错误处理**: 完善的错误处理和降级机制
5. **监控告警**: 实时监控缓存状态和性能
