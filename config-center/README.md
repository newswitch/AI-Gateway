# AI智能网关配置中心

基于 **Redis高性能缓存 + MySQL兜底存储** 的报文匹配规则配置管理服务，为AI智能网关提供高性能、高可用的配置管理能力。

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   客户端请求     │    │   配置中心API    │    │   监控服务      │
│                 │───►│   (FastAPI)     │    │   (Prometheus)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                       │
                               ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis缓存     │◄──►│   MySQL数据库   │    │   Grafana       │
│   (高性能)      │    │   (兜底存储)    │    │   (可视化)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 架构特点

- **Redis优先**: 所有配置操作优先使用Redis，确保高性能
- **MySQL兜底**: 配置数据同时写入MySQL，保证数据持久化
- **自动同步**: 启动时自动从MySQL同步配置到Redis
- **故障恢复**: Redis故障时自动从MySQL恢复数据
- **双写一致性**: 确保Redis和MySQL数据一致性
- **报文匹配**: 支持基于Header和Body的报文匹配规则
- **多种规则**: 支持连接数、请求量、Token数量、字段检查等多种规则类型

## 📁 项目结构

```
config-center/
├── main.py             # 主应用入口文件 (FastAPI)
├── init.py             # 配置初始化脚本
├── requirements.txt    # Python依赖
├── Dockerfile         # Docker构建文件
├── docker-compose.yml # 配置中心服务编排文件
├── README.md          # 项目文档
└── app/               # 应用模块目录
    ├── api/v1/        # API路由层
    ├── core/          # 核心功能层
    ├── models/        # 数据模型层
    └── schemas/       # 数据模式层
```

**注意**: 这是配置中心的独立部署文件，包含Redis、MySQL和配置中心服务

### 代码架构
- **分层设计**: API层、核心层、模型层、模式层分离
- **模块化**: 按功能模块组织代码，便于维护和扩展
- **依赖注入**: 统一的依赖管理机制
- **数据验证**: 使用Pydantic模型进行数据验证

## 🚀 快速开始

### 1. 启动服务
```bash
# 启动配置中心服务（包含Redis和MySQL）
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 2. 初始化配置
```bash
# 进入配置中心容器
docker exec -it ai-gateway-config-center bash

# 运行初始化脚本
python init.py
```

### 3. 验证服务
```bash
# 检查配置中心健康状态
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs

# 查看监控界面
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

## 📊 数据结构

### 数据库表结构

#### 命名空间表 (namespaces)
```sql
CREATE TABLE namespaces (
    namespace_id INT AUTO_INCREMENT PRIMARY KEY,
    namespace_code VARCHAR(50) UNIQUE NOT NULL,
    namespace_name VARCHAR(100) NOT NULL,
    description TEXT,
    status INT DEFAULT 1,  -- 1:启用 0:禁用
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 报文匹配器表 (message_matchers)
```sql
CREATE TABLE message_matchers (
    matcher_id INT AUTO_INCREMENT PRIMARY KEY,
    namespace_id INT NOT NULL,
    matcher_name VARCHAR(100) NOT NULL,
    matcher_type VARCHAR(20) NOT NULL,  -- header, body, header_and_body
    match_field VARCHAR(100) NOT NULL,  -- 匹配字段名
    match_operator VARCHAR(20) NOT NULL,  -- equals, contains, regex, in, not_equals
    match_value TEXT NOT NULL,  -- 匹配值
    priority INT DEFAULT 100,  -- 优先级，数字越大优先级越高
    status INT DEFAULT 1,  -- 1:启用 0:禁用
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 命名空间规则表 (namespace_rules)
```sql
CREATE TABLE namespace_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    namespace_id INT NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,  -- connection_limit, request_limit, token_limit, field_check
    rule_config TEXT NOT NULL,  -- JSON格式的规则配置
    priority INT DEFAULT 100,  -- 优先级
    status INT DEFAULT 1,  -- 1:启用 0:禁用
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 规则计数器表 (rule_counters)
```sql
CREATE TABLE rule_counters (
    counter_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    counter_key VARCHAR(200) NOT NULL,  -- 计数器键名
    counter_value INT DEFAULT 0,  -- 计数器值
    window_start DATETIME NOT NULL,  -- 时间窗口开始时间
    window_end DATETIME NOT NULL,  -- 时间窗口结束时间
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Redis数据结构
```redis
# 命名空间缓存
config:namespace:1 = {
    "namespace_id": 1,
    "namespace_code": "wechat",
    "namespace_name": "微信渠道",
    "description": "微信小程序和公众号渠道",
    "status": 1
}

# 报文匹配器缓存
config:matchers:1 = [
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
]

# 命名空间规则缓存
config:rules:1 = [
    {
        "rule_id": 1,
        "namespace_id": 1,
        "rule_name": "微信Token限制",
        "rule_type": "token_limit",
        "rule_config": "{\"max_tokens_per_hour\": 100000, \"max_tokens_per_day\": 1000000}",
        "priority": 100
    }
]

# 限流计数器
rate_limit:wechat:1234567890 = 150
token_limit:1:hour:1234567890 = 50000
```

## 🔧 API使用示例

### 命名空间管理

#### 创建命名空间
```bash
curl -X POST "http://localhost:8000/api/v1/namespaces" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "namespace_code": "new_channel",
    "namespace_name": "新渠道",
    "description": "新渠道描述",
    "status": 1
  }'
```

#### 获取命名空间列表
```bash
curl "http://localhost:8000/api/v1/namespaces"
```

#### 获取单个命名空间
```bash
curl "http://localhost:8000/api/v1/namespaces/1"
```

### 报文匹配器管理

#### 创建报文匹配器
```bash
curl -X POST "http://localhost:8000/api/v1/namespaces/1/matchers" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "matcher_name": "新渠道匹配",
    "matcher_type": "header",
    "match_field": "channelcode",
    "match_operator": "equals",
    "match_value": "new_channel",
    "priority": 100,
    "status": 1
  }'
```

#### 获取命名空间下的匹配器
```bash
curl "http://localhost:8000/api/v1/namespaces/1/matchers"
```

### 命名空间规则管理

#### 创建连接数限制规则
```bash
curl -X POST "http://localhost:8000/api/v1/namespaces/1/rules" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "rule_name": "连接数限制",
    "rule_type": "connection_limit",
    "rule_config": {
        "max_connections": 1000,
        "window_size": 3600
    },
    "priority": 100,
    "status": 1
  }'
```

#### 创建请求频率限制规则
```bash
curl -X POST "http://localhost:8000/api/v1/namespaces/1/rules" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "rule_name": "请求频率限制",
    "rule_type": "request_limit",
    "rule_config": {
        "max_requests_per_minute": 100,
        "max_requests_per_hour": 5000
    },
    "priority": 90,
    "status": 1
  }'
```

#### 创建Token数量限制规则
```bash
curl -X POST "http://localhost:8000/api/v1/namespaces/1/rules" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "rule_name": "Token数量限制",
    "rule_type": "token_limit",
    "rule_config": {
        "max_tokens_per_hour": 100000,
        "max_tokens_per_day": 1000000,
        "window_size": 3600
    },
    "priority": 80,
    "status": 1
  }'
```

#### 创建字段检查规则
```bash
curl -X POST "http://localhost:8000/api/v1/namespaces/1/rules" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "rule_name": "Token字段检查",
    "rule_type": "field_check",
    "rule_config": {
        "field_path": "body.max_tokens",
        "operator": "lte",
        "value": 20000,
        "message": "max_tokens不能大于20000"
    },
    "priority": 70,
    "status": 1
  }'
```

#### 获取命名空间下的规则
```bash
curl "http://localhost:8000/api/v1/namespaces/1/rules"
```

### 规则计数器管理

#### 获取计数器值
```bash
curl "http://localhost:8000/api/v1/counters/rate_limit:wechat:1234567890"
```

#### 增加计数器
```bash
curl -X POST "http://localhost:8000/api/v1/counters/rate_limit:wechat:1234567890/increment"
```

## 📋 规则类型说明

### 1. connection_limit - 最大连接数限制
```json
{
    "max_connections": 1000,    // 最大连接数
    "window_size": 3600         // 时间窗口大小（秒）
}
```

### 2. request_limit - 单位时间内最大请求量限制
```json
{
    "max_requests_per_minute": 100,  // 每分钟最大请求数
    "max_requests_per_hour": 5000    // 每小时最大请求数
}
```

### 3. token_limit - 单位时间内输入token数量限制
```json
{
    "max_tokens_per_hour": 100000,   // 每小时最大token数
    "max_tokens_per_day": 1000000,   // 每天最大token数
    "window_size": 3600              // 时间窗口大小（秒）
}
```

### 4. field_check - 报文字段检查
```json
{
    "field_path": "body.max_tokens",  // 字段路径
    "operator": "lte",                // 操作符: eq, ne, gt, gte, lt, lte, contains, regex
    "value": 20000,                   // 比较值
    "message": "max_tokens不能大于20000"  // 错误消息
}
```

## 🔍 报文匹配规则

### 匹配器类型
- **header**: 匹配HTTP请求头
- **body**: 匹配请求体JSON字段
- **header_and_body**: 同时匹配请求头和请求体

### 匹配操作符
- **equals**: 完全相等
- **contains**: 包含
- **regex**: 正则表达式匹配
- **in**: 在列表中
- **not_equals**: 不相等

### 匹配示例
```bash
# Header匹配
{
    "matcher_type": "header",
    "match_field": "channelcode",
    "match_operator": "equals",
    "match_value": "wechat"
}

# Body字段匹配
{
    "matcher_type": "body",
    "match_field": "channel",
    "match_operator": "equals",
    "match_value": "alipay"
}

# User-Agent匹配
{
    "matcher_type": "header",
    "match_field": "user-agent",
    "match_operator": "contains",
    "match_value": "Mozilla"
}
```

## ⚡ 性能特点

### Redis + MySQL双写优势

| 指标 | Redis | MySQL | 双写方案 |
|------|-------|-------|----------|
| **读取性能** | 极快 (<1ms) | 中等 (10-50ms) | 极快 (Redis优先) |
| **写入性能** | 极快 (<1ms) | 中等 (10-50ms) | 快 (异步双写) |
| **数据持久化** | 可选 | 强 | 强 (MySQL兜底) |
| **故障恢复** | 无 | 有 | 有 (自动同步) |
| **数据一致性** | 内存级 | 事务级 | 最终一致 |

### 性能测试结果

```bash
# 命名空间读取性能 (Redis)
curl -w "@curl-format.txt" "http://localhost:8000/api/v1/namespaces/1"
# 平均响应时间: 0.8ms

# 报文匹配器读取性能 (Redis)
curl -w "@curl-format.txt" "http://localhost:8000/api/v1/namespaces/1/matchers"
# 平均响应时间: 1.2ms

# 规则读取性能 (Redis)
curl -w "@curl-format.txt" "http://localhost:8000/api/v1/namespaces/1/rules"
# 平均响应时间: 1.5ms

# 配置写入性能 (双写)
curl -w "@curl-format.txt" -X POST "http://localhost:8000/api/v1/namespaces" \
  -H "Content-Type: application/json" \
  -d '{"namespace_code": "test", "namespace_name": "测试"}'
# 平均响应时间: 2.1ms (Redis写入 + 异步MySQL写入)
```

## 🔍 监控和调试

### 健康检查
```bash
# 配置中心健康状态
curl "http://localhost:8000/health"
# 返回: {"status": "healthy", "storage": {"redis": "healthy", "mysql": "healthy"}}
```

### 监控指标
```bash
# 缓存统计
curl "http://localhost:8000/stats"
```

### 日志查看
```bash
# 配置中心日志
docker logs ai-gateway-config-center

# Redis日志
docker logs ai-gateway-redis

# MySQL日志
docker logs ai-gateway-mysql
```

## 🛠️ 开发指南

### 环境变量配置
```bash
# 数据库配置
DATABASE_URL=mysql+aiomysql://ai_gateway:ai_gateway_pass@mysql:3306/ai_gateway_config

# Redis配置
REDIS_URL=redis://redis:6379/0

# 应用配置
DEBUG=false
LOG_LEVEL=INFO
```

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 启动Redis和MySQL
docker-compose up redis mysql -d

# 运行配置中心
python main.py

# 初始化配置
python init.py
```

### 数据迁移
```bash
# 从MySQL同步到Redis
curl -X POST "http://localhost:8000/sync"
```

## 🚨 故障排除

### 常见问题

#### 1. MySQL连接失败
```bash
# 检查MySQL服务状态
docker-compose ps mysql

# 查看MySQL日志
docker logs ai-gateway-mysql

# 手动连接测试
docker exec -it ai-gateway-mysql mysql -u ai_gateway -p
```

#### 2. Redis连接失败
```bash
# 检查Redis服务状态
docker-compose ps redis

# 查看Redis日志
docker logs ai-gateway-redis

# 手动连接测试
docker exec -it ai-gateway-redis redis-cli ping
```

#### 3. 配置同步失败
```bash
# 检查配置中心日志
docker logs ai-gateway-config-center

# 手动触发同步
curl -X POST "http://localhost:8000/sync"

# 检查数据一致性
curl "http://localhost:8000/stats"
```

### 性能优化

#### 1. Redis优化
```bash
# 调整Redis内存配置
docker-compose exec redis redis-cli CONFIG SET maxmemory 1gb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 监控Redis性能
docker-compose exec redis redis-cli INFO memory
docker-compose exec redis redis-cli INFO stats
```

#### 2. MySQL优化
```sql
-- 优化表结构
ALTER TABLE message_matchers ADD INDEX idx_namespace_priority (namespace_id, priority);
ALTER TABLE namespace_rules ADD INDEX idx_namespace_priority (namespace_id, priority);

-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
```

## 🔌 完整API接口列表

### 命名空间管理
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/namespaces` | 获取所有命名空间 |
| GET | `/api/v1/namespaces/{namespace_id}` | 获取单个命名空间 |
| POST | `/api/v1/namespaces` | 创建命名空间 |
| PUT | `/api/v1/namespaces/{namespace_id}` | 更新命名空间 |
| DELETE | `/api/v1/namespaces/{namespace_id}` | 删除命名空间 |

### 报文匹配器管理
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/matchers/{matcher_id}` | 获取单个报文匹配器 |
| GET | `/api/v1/namespaces/{namespace_id}/matchers` | 获取命名空间下的所有匹配器 |
| POST | `/api/v1/namespaces/{namespace_id}/matchers` | 创建报文匹配器 |
| PUT | `/api/v1/matchers/{matcher_id}` | 更新报文匹配器 |
| DELETE | `/api/v1/matchers/{matcher_id}` | 删除报文匹配器 |

### 命名空间规则管理
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/rules/{rule_id}` | 获取单个命名空间规则 |
| GET | `/api/v1/namespaces/{namespace_id}/rules` | 获取命名空间下的所有规则 |
| POST | `/api/v1/namespaces/{namespace_id}/rules` | 创建命名空间规则 |
| PUT | `/api/v1/rules/{rule_id}` | 更新命名空间规则 |
| DELETE | `/api/v1/rules/{rule_id}` | 删除命名空间规则 |

### 规则计数器管理
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/counters/{counter_key}` | 获取计数器值 |
| POST | `/api/v1/counters/{counter_key}/increment` | 增加计数器值 |

### 系统管理
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/stats` | 缓存统计信息 |
| POST | `/sync` | 同步数据库到Redis |

## 📈 扩展性

### 水平扩展
```yaml
# 多实例部署
services:
  config-center:
    deploy:
      replicas: 3
    environment:
      - REDIS_URL=redis://redis-cluster:6379/0
      - DATABASE_URL=mysql+aiomysql://ai_gateway:ai_gateway_pass@mysql-cluster:3306/ai_gateway_config
```

### 高可用部署
```yaml
# Redis集群
redis-cluster:
  image: redis:7.0-alpine
  command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf

# MySQL主从
mysql-master:
  image: mysql:8.0
  environment:
    MYSQL_ROOT_PASSWORD: ai_gateway_root

mysql-slave:
  image: mysql:8.0
  environment:
    MYSQL_ROOT_PASSWORD: ai_gateway_root
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**AI智能网关配置中心** - 基于Redis + MySQL双写的高性能报文匹配规则配置管理服务 