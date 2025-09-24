# AI智能网关 - OpenResty模块

基于OpenResty + Lua的高性能AI服务网关，支持动态配置、规则匹配、限流控制和智能路由。

## 🏗️ 架构设计

```
客户端请求 → OpenResty → Lua脚本处理 → 配置验证 → 规则匹配 → 限流检查 → 路由转发 → 大模型服务
                ↓
            配置中心API
                ↓
            Redis缓存优先
                ↓
            MySQL兜底存储
```

## 📁 项目结构

```
gateway/
├── Dockerfile                 # Docker构建文件
├── docker-compose.yml         # 本地开发环境
├── nginx.conf                 # Nginx主配置文件
├── conf/                      # 配置文件目录
│   ├── nginx.conf            # Nginx配置
│   ├── lua/                  # Lua脚本目录
│   │   ├── init.lua          # 初始化脚本
│   │   ├── config/           # 配置管理
│   │   │   ├── config_client.lua    # 配置中心客户端
│   │   │   ├── config_cache.lua     # 配置缓存管理
│   │   │   └── config_sync.lua      # 配置同步
│   │   ├── auth/             # 认证授权
│   │   │   ├── namespace_matcher.lua # 命名空间匹配
│   │   │   ├── rule_checker.lua     # 规则检查
│   │   │   └── rate_limiter.lua     # 限流控制
│   │   ├── routing/          # 路由处理
│   │   │   ├── request_router.lua   # 请求路由
│   │   │   ├── upstream_selector.lua # 上游选择器
│   │   │   └── proxy_handler.lua    # 代理处理
│   │   ├── monitoring/       # 监控统计
│   │   │   ├── metrics.lua          # 指标收集
│   │   │   ├── health_check.lua     # 健康检查
│   │   │   └── log_handler.lua      # 日志处理
│   │   └── utils/            # 工具函数
│   │       ├── redis_client.lua     # Redis客户端
│   │       ├── http_client.lua      # HTTP客户端
│   │       ├── json_utils.lua       # JSON工具
│   │       └── time_utils.lua       # 时间工具
│   └── ssl/                  # SSL证书目录
├── logs/                     # 日志目录
│   ├── access.log           # 访问日志
│   ├── error.log            # 错误日志
│   └── lua.log              # Lua日志
└── tests/                   # 测试目录
    ├── test_config.lua      # 配置测试
    ├── test_rules.lua       # 规则测试
    └── test_routing.lua     # 路由测试
```

## 🚀 核心功能

### 1. 配置管理
- **Redis优先**: 优先从Redis获取配置，提升性能
- **MySQL兜底**: Redis未命中时自动从MySQL获取
- **自动同步**: 配置变更时自动更新缓存
- **多层缓存**: 共享内存 + Redis + MySQL

### 2. 命名空间匹配
- **报文解析**: 解析请求头和请求体
- **字段匹配**: 支持多种匹配操作符
- **优先级**: 支持匹配器优先级设置
- **动态匹配**: 实时匹配命名空间

### 3. 规则验证
- **Token限制**: 检查Token使用量是否超限
- **并发限制**: 检查并发连接数
- **请求限制**: 检查请求频率
- **字段验证**: 验证请求字段合法性

### 4. 限流控制
- **分布式限流**: 基于Redis的分布式限流
- **时间窗口**: 支持灵活的时间窗口配置
- **多维度**: Token、请求数、并发数多维度限流
- **实时统计**: 实时统计和更新限流数据

### 5. 智能路由
- **负载均衡**: 支持多种负载均衡算法
- **健康检查**: 自动剔除不健康的上游服务
- **故障转移**: 自动故障转移
- **动态路由**: 根据配置动态选择上游服务

## 🔧 快速开始

### 1. 本地开发
```bash
# 启动本地开发环境
docker-compose up -d

# 查看日志
docker-compose logs -f ai-gateway

# 测试网关
curl -H "channelcode: wechat" http://localhost:8080/api/chat
```

### 2. 生产部署
```bash
# 构建镜像
docker build -t ai-gateway .

# 运行容器
docker run -d -p 80:80 --name ai-gateway ai-gateway
```

## 📊 配置示例

### 命名空间配置
```json
{
  "namespace_id": 1,
  "namespace_code": "wechat",
  "namespace_name": "微信渠道",
  "status": 1
}
```

### 报文匹配器配置
```json
{
  "matcher_id": 1,
  "namespace_id": 1,
  "matcher_name": "微信渠道匹配",
  "matcher_type": "header",
  "match_field": "channelcode",
  "match_operator": "equals",
  "match_value": "wechat",
  "priority": 100
}
```

### 规则配置
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
  "priority": 100
}
```

## 🔍 监控指标

- **请求量**: 总请求数、成功请求数、失败请求数
- **响应时间**: 平均响应时间、P95、P99
- **限流统计**: 限流次数、限流原因
- **错误统计**: 错误类型、错误频率
- **资源使用**: CPU、内存、连接数

## 🛠️ 开发指南

### 添加新的规则类型
1. 在`lua/auth/rule_checker.lua`中添加规则检查逻辑
2. 在`lua/monitoring/metrics.lua`中添加监控指标
3. 更新配置中心的数据模型
4. 添加相应的测试用例

### 添加新的匹配器类型
1. 在`lua/auth/namespace_matcher.lua`中添加匹配逻辑
2. 更新配置中心的数据模型
3. 添加相应的测试用例

## 📝 日志格式

### 访问日志
```
$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" $request_time $upstream_response_time
```

### 错误日志
```
[ERROR] $time_local: $error_message
[WARN] $time_local: $warning_message
[INFO] $time_local: $info_message
```

## 🔒 安全特性

- **请求验证**: 验证请求格式和内容
- **限流保护**: 防止恶意请求和DDoS攻击
- **错误处理**: 优雅处理各种异常情况
- **日志审计**: 完整的操作日志记录

## 📈 性能优化

- **连接池**: Redis和HTTP连接池复用
- **缓存策略**: 多层缓存减少数据库访问
- **异步处理**: 非阻塞的异步操作
- **内存优化**: 合理的内存使用和垃圾回收

---

**AI智能网关** - 基于OpenResty的高性能AI服务网关 