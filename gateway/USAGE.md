# AI智能网关使用指南

## 🚀 快速开始

### 1. 启动网关
```bash
# 进入网关目录
cd gateway

# 启动所有服务
./start.sh
```

### 2. 验证安装
```bash
# 检查健康状态
curl http://localhost:8080/health

# 查看统计信息
curl http://localhost:8080/stats
```

## 📝 使用示例

### 1. 基本API调用

#### 微信渠道请求
```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -H "channelcode: wechat" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    "max_tokens": 100
  }'
```

#### 支付宝渠道请求
```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -H "channelcode: alipay" \
  -d '{
    "messages": [
      {"role": "user", "content": "今天天气怎么样？"}
    ],
    "max_tokens": 50
  }'
```

### 2. 配置管理

#### 创建命名空间
```bash
curl -X POST http://localhost:8000/api/v1/namespaces \
  -H "Content-Type: application/json" \
  -d '{
    "namespace_code": "new_channel",
    "namespace_name": "新渠道",
    "description": "这是一个新的渠道",
    "status": 1
  }'
```

#### 创建报文匹配器
```bash
curl -X POST http://localhost:8000/api/v1/namespaces/1/matchers \
  -H "Content-Type: application/json" \
  -d '{
    "matcher_name": "新渠道匹配器",
    "matcher_type": "header",
    "match_field": "channelcode",
    "match_operator": "equals",
    "match_value": "new_channel",
    "priority": 100
  }'
```

#### 创建规则
```bash
curl -X POST http://localhost:8000/api/v1/namespaces/1/rules \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "Token限制规则",
    "rule_type": "token_limit",
    "rule_config": {
      "max_tokens_per_hour": 50000,
      "max_tokens_per_day": 500000,
      "window_size": 3600
    },
    "priority": 100
  }'
```

### 3. 监控和统计

#### 查看网关统计
```bash
curl http://localhost:8080/stats
```

#### 查看配置中心统计
```bash
curl http://localhost:8000/cache/stats
```

#### 预加载命名空间数据
```bash
curl -X POST http://localhost:8080/preload/1
```

## 🔧 配置示例

### 1. 命名空间配置

#### 微信渠道
```json
{
  "namespace_id": 1,
  "namespace_code": "wechat",
  "namespace_name": "微信渠道",
  "description": "微信小程序和公众号渠道",
  "status": 1,
  "create_time": "2024-01-01T00:00:00",
  "update_time": "2024-01-01T00:00:00"
}
```

#### 支付宝渠道
```json
{
  "namespace_id": 2,
  "namespace_code": "alipay",
  "namespace_name": "支付宝渠道",
  "description": "支付宝小程序渠道",
  "status": 1,
  "create_time": "2024-01-01T00:00:00",
  "update_time": "2024-01-01T00:00:00"
}
```

### 2. 报文匹配器配置

#### Header匹配
```json
{
  "matcher_id": 1,
  "namespace_id": 1,
  "matcher_name": "微信Header匹配",
  "matcher_type": "header",
  "match_field": "channelcode",
  "match_operator": "equals",
  "match_value": "wechat",
  "priority": 100,
  "status": 1
}
```

#### Body匹配
```json
{
  "matcher_id": 2,
  "namespace_id": 1,
  "matcher_name": "微信Body匹配",
  "matcher_type": "body",
  "match_field": "channel",
  "match_operator": "equals",
  "match_value": "wechat",
  "priority": 90,
  "status": 1
}
```

### 3. 规则配置

#### Token限制
```json
{
  "rule_id": 1,
  "namespace_id": 1,
  "rule_name": "微信Token限制",
  "rule_type": "token_limit",
  "rule_config": {
    "max_tokens_per_hour": 100000,
    "max_tokens_per_day": 1000000,
    "window_size": 3600
  },
  "priority": 100,
  "status": 1
}
```

#### 并发限制
```json
{
  "rule_id": 2,
  "namespace_id": 1,
  "rule_name": "微信并发限制",
  "rule_type": "connection_limit",
  "rule_config": {
    "max_connections": 1000,
    "window_size": 3600
  },
  "priority": 90,
  "status": 1
}
```

#### 请求频率限制
```json
{
  "rule_id": 3,
  "namespace_id": 1,
  "rule_name": "微信请求频率限制",
  "rule_type": "request_limit",
  "rule_config": {
    "max_requests_per_minute": 100,
    "max_requests_per_hour": 5000
  },
  "priority": 80,
  "status": 1
}
```

## 🛠️ 故障排除

### 1. 常见问题

#### 网关无法启动
```bash
# 检查日志
docker-compose logs ai-gateway

# 检查配置
docker-compose exec ai-gateway nginx -t
```

#### 配置中心连接失败
```bash
# 检查配置中心状态
curl http://localhost:8000/health

# 检查Redis连接
docker-compose exec redis redis-cli ping
```

#### 命名空间匹配失败
```bash
# 检查命名空间配置
curl http://localhost:8000/api/v1/namespaces

# 检查匹配器配置
curl http://localhost:8000/api/v1/namespaces/1/matchers
```

### 2. 性能优化

#### 增加缓存
```bash
# 预加载热门命名空间
curl -X POST http://localhost:8080/preload/1
curl -X POST http://localhost:8080/preload/2
```

#### 监控性能
```bash
# 查看响应时间统计
curl http://localhost:8080/stats | jq '.metrics.response_time'

# 查看限流统计
curl http://localhost:8080/stats | jq '.metrics.rate_limit'
```

## 📊 监控指标

### 1. 网关指标
- `namespace_match_total`: 命名空间匹配总次数
- `namespace_match_success`: 命名空间匹配成功次数
- `namespace_match_failed`: 命名空间匹配失败次数
- `rule_check_total`: 规则检查总次数
- `rule_check_success`: 规则检查成功次数
- `rule_check_failed`: 规则检查失败次数
- `proxy_success`: 代理成功次数
- `proxy_failed`: 代理失败次数
- `response_time`: 响应时间统计

### 2. 限流指标
- `token_limit_exceeded`: Token限制超限次数
- `connection_limit_exceeded`: 并发限制超限次数
- `request_limit_exceeded`: 请求频率超限次数

### 3. 错误指标
- `request_error`: 请求错误次数
- `upstream_error`: 上游服务错误次数
- `config_error`: 配置错误次数

## 🔒 安全建议

### 1. 网络安全
- 使用HTTPS加密传输
- 配置防火墙规则
- 限制访问IP范围

### 2. 认证授权
- 实现API密钥认证
- 配置访问控制列表
- 定期轮换密钥

### 3. 监控告警
- 设置错误率告警
- 配置响应时间告警
- 监控资源使用情况

## 📚 更多资源

- [OpenResty官方文档](https://openresty.org/en/)
- [Lua编程指南](https://www.lua.org/manual/)
- [Redis命令参考](https://redis.io/commands)
- [Nginx配置指南](https://nginx.org/en/docs/) 