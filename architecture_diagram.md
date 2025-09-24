# AI Gateway 架构图

## 🏗️ 整体架构

```mermaid
graph TB
    subgraph "用户层"
        A[Web前端<br/>localhost:3000]
        B[API客户端<br/>HTTP/HTTPS]
        C[管理界面<br/>Dashboard]
    end
    
    subgraph "网关层"
        D[OpenResty/Nginx Gateway<br/>localhost:8080]
        E[Lua脚本模块<br/>路由/策略/监控]
    end
    
    subgraph "服务层"
        F[配置中心<br/>localhost:8001]
        G[Token服务<br/>localhost:8002]
        H[上游AI服务<br/>OpenAI/Claude]
        I[数据库<br/>MySQL/Redis]
    end
    
    subgraph "监控层"
        J[Prometheus<br/>localhost:9090]
        K[Redis缓存<br/>localhost:6379]
        L[日志系统<br/>Nginx日志]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    E --> G
    E --> H
    E --> I
    E --> J
    E --> K
    D --> L
```

## 🔄 数据流向

```mermaid
sequenceDiagram
    participant U as 用户
    participant G as Gateway
    participant L as Lua脚本
    participant C as 配置中心
    participant T as Token服务
    participant A as AI服务
    participant R as Redis
    participant P as Prometheus
    
    U->>G: HTTP请求
    G->>L: 路由匹配
    L->>C: 获取配置
    C-->>L: 返回配置
    L->>L: 策略检查
    L->>T: Token计算
    T-->>L: 返回Token数
    L->>A: 转发请求
    A-->>L: 返回响应
    L->>R: 存储指标
    L->>P: 暴露指标(/metrics)
    L-->>G: 返回响应
    G-->>U: 返回结果
```

## 📊 监控架构

```mermaid
graph LR
    subgraph "数据收集"
        A[Lua脚本] --> B[Redis缓存]
        A --> C[Nginx /metrics]
    end
    
    subgraph "数据存储"
        B --> D[实时数据]
        C --> E[Prometheus TSDB]
    end
    
    subgraph "数据消费"
        E --> F[Prometheus查询]
        E --> G[Grafana可视化]
        F --> H[告警系统]
    end
    
    D --> I[配置中心API]
    E --> J[监控面板]
```

## 🏛️ 组件详细架构

```mermaid
graph TB
    subgraph "Gateway内部架构"
        A[Nginx配置层]
        B[Lua脚本层]
        
        subgraph "Lua模块"
            C[core/init.lua]
            D[auth/namespace_matcher]
            E[auth/policy_enforcer]
            F[routing/router]
            G[monitoring/metrics]
        end
        
        A --> B
        B --> C
        B --> D
        B --> E
        B --> F
        B --> G
    end
```

## 🔧 端口映射

| 服务 | 端口 | 说明 |
|------|------|------|
| Gateway | 8080 | 主服务入口 |
| 配置中心 | 8001 | 配置管理API |
| Token服务 | 8002 | Token计算服务 |
| 前端 | 3000 | Web管理界面 |
| Prometheus | 9090 | 监控数据查询 |
| MySQL | 3307 | 数据库 |
| Redis | 6379 | 缓存 |

## 📈 关键指标

### 业务指标
- `gateway_requests_total`: 总请求数
- `gateway_requests_success_total`: 成功请求数
- `gateway_requests_failed_total`: 失败请求数

### 性能指标
- `gateway_request_duration_seconds`: 请求持续时间
- `gateway_upstream_duration_seconds`: 上游响应时间

### 系统指标
- `gateway_up_time_seconds`: 网关运行时间
- `gateway_upstream_requests_total`: 上游请求数

## 🎯 架构特点

1. **微服务架构**: 各组件独立部署
2. **动态配置**: 通过配置中心管理
3. **实时监控**: 完整的监控体系
4. **高可用**: 支持负载均衡和故障转移
5. **可扩展**: 支持水平扩展
