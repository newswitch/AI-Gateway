# 配置中心与网关 API 接口清单（AI-Gateway 2.0）

说明
- 所有带“鉴权”的接口默认启用 HTTP Bearer 鉴权（后端当前为简化校验，传任意 `Authorization: Bearer <token>` 可通过）。
- 网关侧通过 Ingress 暴露，推荐通过 Host 头访问：
  - 前端/静态页：`http://ai-gateway.local`
  - 配置中心 API：`http://api.ai-gateway.local`
  - 网关动态代理：`http://gateway.ai-gateway.local`
- 以下路径均为配置中心后端相对路径（未加域名）。

---

## 一、系统/健康类

- GET `/health`
  - 说明：健康检查（Redis/MySQL）
  - 响应格式：
    ```json
    {
      "status": "healthy | unhealthy",
      "storage": { "redis": "healthy|unhealthy", "mysql": "healthy|unhealthy" },
      "timestamp": "2025-08-12T01:19:15.125583"
    }
    ```

- GET `/api/v1/status`
  - 说明：兼容前端的系统状态（与 `/health` 一致）
  - 响应示例：
    ```json
    {
      "status": "healthy",
      "storage": { "redis": "healthy", "mysql": "healthy" },
      "timestamp": "2025-08-12T01:19:23.392534"
    }
    ```

- GET `/stats`
  - 说明：缓存/系统统计
  - 响应示例：
    ```json
    {
      "cache_hits": 123,
      "cache_misses": 45,
      "cache_size": 10485760,
      "cache_free": 7340032
    }
    ```

- POST `/sync`
  - 说明：触发从 MySQL 同步配置到 Redis（可能较耗时）
  - 请求头：`Content-Type: application/json`
  - 响应：
    ```json
    { "message": "数据同步成功" }
    ```

- POST `/preload/{namespace_id}`
  - 说明：预加载指定命名空间相关数据到缓存
  - 响应示例：
    ```json
    { "message": "命名空间 1 数据预加载完成" }
    ```

- GET `/cache/stats`
  - 说明：缓存统计信息
  - 响应示例：同上 `/stats`

- POST `/namespaces/batch`
  - 说明：批量获取命名空间信息
  - 请求示例：
    ```json
    [1, 2, 3]
    ```
  - 响应示例：
    ```json
    [
      {"id":1,"namespace_name":"企业业务","namespace_code":"enterprise","is_active":1},
      {"id":2,"namespace_name":"开发环境","namespace_code":"dev","is_active":1}
    ]
    ```

- POST `/batch-dual-write`
  - 说明：批量双写（按传入操作集执行）
  - 请求示例：
    ```json
    [
      { "op": "create_namespace", "data": { "namespace_name": "A", "namespace_code": "a" } },
      { "op": "update_rule", "id": 12, "data": { "rule_name": "limit-qps", "rule_config": {"max_qps": 50} } }
    ]
    ```
  - 响应示例：
    ```json
    {
      "results": [
        {"op":"create_namespace","success":true,"id": 5},
        {"op":"update_rule","success":true,"id": 12}
      ]
    }
    ```

- GET `/api/v1/namespaces/{namespace_id}/usage`
- GET `/api/v1/namespaces/usage/overview`
- GET `/api/v1/namespaces/{namespace_id}/monitoring`
  - 说明：使用/监控数据接口
  - 响应示例（usage）：
    ```json
    {
      "namespace_id": 1,
      "qps": 18.2,
      "concurrency": 12,
      "token_input_per_min": 12500,
      "token_output_per_min": 8400,
      "rate_limit": {"enabled": true, "max_qps": 50},
      "updated_at": "2025-08-12T01:10:00Z"
    }
    ```
  - 响应示例（overview）：
    ```json
    [
      {"namespace_id":1,"namespace_code":"enterprise","qps":18.2,"concurrency":12},
      {"namespace_id":2,"namespace_code":"dev","qps":3.4,"concurrency":2}
    ]
    ```
  - 响应示例（monitoring）：
    ```json
    {
      "namespace_id": 1,
      "metrics": {
        "req_per_min": [12,18,22,19,25],
        "latency_ms_p95": [480,455,430,460,440],
        "token_in": [1200,1350,1500,1400,1550],
        "token_out": [800,900,950,880,1000]
      },
      "window": "5m",
      "updated_at": "2025-08-12T01:10:00Z"
    }
    ```

示例
```bash
curl -H "Host: api.ai-gateway.local" http://<NODE_IP>:<NODEPORT>/api/v1/status | jq .
```

---

## 二、命名空间（Namespaces）

- GET `/api/v1/namespaces` → List
- GET `/api/v1/namespaces/{namespace_id}` → Dict
- POST `/api/v1/namespaces`            （鉴权）
- PUT `/api/v1/namespaces/{namespace_id}`   （鉴权）
- DELETE `/api/v1/namespaces/{namespace_id}`（鉴权）

请求/响应字段（示例）
```json
// POST /api/v1/namespaces
{
  "namespace_name": "企业业务",
  "namespace_code": "enterprise",
  "description": "说明",
  "is_active": 1
}

// GET item 响应
{
  "id": 1,
  "namespace_name": "企业业务",
  "namespace_code": "enterprise",
  "description": "说明",
  "is_active": 1,
  "created_at": "2025-08-01 10:00:00",
  "updated_at": "2025-08-11 09:00:00"
}
```

列表响应示例
```json
[
  {"id":1,"namespace_name":"企业业务","namespace_code":"enterprise","is_active":1},
  {"id":2,"namespace_name":"开发环境","namespace_code":"dev","is_active":1}
]
```

更新响应示例
```json
{
  "message": "命名空间更新成功",
  "namespace_id": 1,
  "namespace": {"id":1,"namespace_name":"企业业务","namespace_code":"enterprise","is_active":1}
}
```

删除响应示例
```json
{ "message": "命名空间删除成功" }
```

路由规则（Namespace Route）
- GET `/api/v1/namespaces/{namespace_id}/route`
- POST `/api/v1/namespaces/{namespace_id}/route`（鉴权）
- DELETE `/api/v1/namespaces/{namespace_id}/route`（鉴权）

规则验证
- POST `/api/v1/namespaces/{namespace_id}/validate`（鉴权）

路由规则响应示例
```json
// GET /api/v1/namespaces/1/route
{
  "route_id": 10,
  "namespace_id": 1,
  "match_strategy": "header:x-tenant=enterprise",
  "priority": 10,
  "status": 1
}
```

保存路由响应示例
```json
{
  "message": "命名空间路由规则保存成功",
  "route_id": 10,
  "route": {"route_id":10,"namespace_id":1,"priority":10,"status":1}
}
```

删除路由响应示例
```json
{ "message": "命名空间路由规则删除成功" }
```

验证规则请求/响应示例
```json
// POST /api/v1/namespaces/1/validate
{
  "headers": {"x-tenant": "enterprise"},
  "path": "/v1/chat/completions"
}

// 响应
{
  "allowed": true,
  "namespace_id": 1,
  "namespace_code": "enterprise",
  "namespace_name": "企业业务",
  "rules": [
    {"rule_id":101,"rule_name":"only-enterprise","rule_type":"matcher","passed":true,"details":{"message":"规则验证通过"}}
  ]
}
```

---

## 三、代理规则（Proxy Rules）

- GET `/api/v1/proxy-rules` → List
- GET `/api/v1/proxy-rules/{rule_id}` → Dict
- POST `/api/v1/proxy-rules`              （鉴权）
- PUT `/api/v1/proxy-rules/{rule_id}`     （鉴权）
- DELETE `/api/v1/proxy-rules/{rule_id}`  （鉴权）

返回字段常见：`rule_id|id, rule_name|name, namespace_id|namespace_code|namespace_name, upstream_server_id|upstream_server_address|upstream_server_port, priority, is_active, ...`

请求/响应示例
```json
// POST /api/v1/proxy-rules
{
  "rule_name": "enterprise-policy",
  "namespace_id": 1,
  "upstream_server_id": 2,
  "path_pattern": "/v1/.*",
  "method_pattern": "GET|POST",
  "header_pattern": "x-tenant:enterprise",
  "body_pattern": null,
  "priority": 10,
  "is_active": 1
}

// GET item 响应（示例字段）
{
  "rule_id": 12,
  "rule_name": "enterprise-policy",
  "namespace_id": 1,
  "namespace_name": "企业业务",
  "namespace_code": "enterprise",
  "upstream_server_id": 2,
  "upstream_server_address": "llm-upstream",
  "upstream_server_port": 8000,
  "priority": 10,
  "is_active": 1
}
```

列表响应示例
```json
[
  {"rule_id":12,"rule_name":"enterprise-policy","namespace_id":1,"upstream_server_id":2,"priority":10,"is_active":1},
  {"rule_id":13,"rule_name":"dev-policy","namespace_id":2,"upstream_server_id":3,"priority":50,"is_active":1}
]
```

更新响应示例
```json
{
  "message": "代理规则更新成功",
  "rule": {"rule_id":12,"rule_name":"enterprise-policy","priority":5,"is_active":1}
}
```

删除响应示例
```json
{ "message": "代理规则删除成功" }
```

---

## 四、通用规则（Rules）

- GET `/api/v1/rules/types`
  - 说明：支持的规则类型及字段 schema
  - 响应示例（节选）：
    ```json
    {
      "rule_types": [
        {"type":"matcher","config_schema":{"matcher_type":{"type":"string","enum":["header","body","query","path"]},"match_field":{"type":"string"},"match_operator":{"type":"string","enum":["eq","ne","gt","gte","lt","lte","contains","regex"]},"match_value":{"type":"string"},"action":{"type":"string","enum":["allow","deny"]}}},
        {"type":"token_limit","config_schema":{"model_name":{"type":"string"},"max_tokens":{"type":"number"},"time_window_enabled":{"type":"boolean"},"time_window_minutes":{"type":"number"},"max_tokens_per_window":{"type":"number"}}}
      ]
    }
    ```

- GET `/api/v1/rules`（可选 `rule_type` 过滤）
- GET `/api/v1/rules/{rule_id}`
- GET `/api/v1/namespaces/{namespace_id}/rules`（可选 `rule_type` 过滤）

- POST `/api/v1/namespaces/{namespace_id}/rules`（鉴权）
- PUT `/api/v1/rules/{rule_id}`          （鉴权）
- DELETE `/api/v1/rules/{rule_id}`       （鉴权）

rule_config 约定：入参为对象时后端会序列化为 JSON 字符串进行存储。

示例
```json
// 创建规则
{
  "rule_name": "limit-qps",
  "rule_type": "rate_limit",
  "rule_config": {"max_qps": 50, "time_window_seconds": 1}
}
```

列表响应示例
```json
[
  {"rule_id":201,"namespace_id":1,"rule_type":"rate_limit","priority":10,"status":1,"rule_config":{"max_qps":50}},
  {"rule_id":202,"namespace_id":1,"rule_type":"token_limit","priority":20,"status":1,"rule_config":{"max_tokens":4096}}
]
```

单项响应示例
```json
{
  "rule_id": 201,
  "namespace_id": 1,
  "rule_name": "limit-qps",
  "rule_type": "rate_limit",
  "priority": 10,
  "status": 1,
  "rule_config": {"max_qps": 50, "time_window_seconds": 1}
}
```

创建响应示例
```json
{ "message": "规则创建成功", "rule_id": 201 }
```

更新响应示例
```json
{ "message": "规则更新成功", "rule_id": 201 }
```

删除响应示例
```json
{ "message": "规则删除成功", "rule_id": 201 }
```

---

## 五、报文匹配器（Matchers）

- GET `/api/v1/matchers`
- GET `/api/v1/matchers/{matcher_id}`
- GET `/api/v1/namespaces/{namespace_id}/matchers`

- POST `/api/v1/namespaces/{namespace_id}/matchers`（鉴权）
- PUT `/api/v1/matchers/{matcher_id}`    （鉴权）
- DELETE `/api/v1/matchers/{matcher_id}` （鉴权）

示例
```json
// 创建匹配器
{
  "matcher_name": "route-by-header",
  "matcher_type": "header",
  "matcher_config": {"match_field":"x-tenant","match_operator":"eq","match_value":"enterprise","action":"allow"},
  "priority": 10,
  "is_active": 1
}
```

列表响应示例
```json
[
  {"matcher_id":301,"namespace_id":1,"matcher_type":"header","priority":10,"is_active":1,"matcher_config":{"match_field":"x-tenant","match_operator":"eq","match_value":"enterprise"}},
  {"matcher_id":302,"namespace_id":1,"matcher_type":"query","priority":50,"is_active":1,"matcher_config":{"match_field":"model","match_operator":"contains","match_value":"gpt"}}
]
```

单项响应示例
```json
{
  "matcher_id": 301,
  "namespace_id": 1,
  "matcher_name": "route-by-header",
  "matcher_type": "header",
  "priority": 10,
  "is_active": 1,
  "matcher_config": {"match_field": "x-tenant", "match_operator": "eq", "match_value": "enterprise", "action": "allow"}
}
```

创建/更新/删除响应示例
```json
{ "message": "报文匹配器创建成功", "matcher_id": 301 }
{ "message": "报文匹配器更新成功", "matcher_id": 301 }
{ "message": "报文匹配器删除成功", "matcher_id": 301 }
```

---

## 六、上游服务器（Upstream Servers）

- GET `/api/v1/upstream-servers`
- GET `/api/v1/upstream-servers/{server_id}`
- POST `/api/v1/upstream-servers`             （鉴权）
- PUT `/api/v1/upstream-servers/{server_id}`   （鉴权）
- DELETE `/api/v1/upstream-servers/{server_id}`（鉴权）

示例
```json
// 创建上游
{
  "server_name": "llm-upstream",
  "server_address": "llm-upstream",
  "server_port": 8000,
  "server_type": "http",
  "weight": 10,
  "max_connections": 100,
  "health_check_url": "/health",
  "is_active": 1
}
```

列表响应示例
```json
[
  {"server_id":2,"server_name":"llm-upstream","server_address":"llm-upstream","server_port":8000,"server_type":"http","weight":10,"max_connections":100,"is_active":1},
  {"server_id":3,"server_name":"dev-upstream","server_address":"dev-upstream","server_port":8001,"server_type":"http","weight":5,"max_connections":50,"is_active":1}
]
```

单项响应示例
```json
{
  "server_id": 2,
  "server_name": "llm-upstream",
  "server_address": "llm-upstream",
  "server_port": 8000,
  "server_type": "http",
  "weight": 10,
  "max_connections": 100,
  "health_check_url": "/health",
  "is_active": 1
}
```

创建/更新/删除响应示例
```json
{ "message": "上游服务器创建成功", "server_id": 2, "server": {"server_id":2} }
{ "message": "上游服务器更新成功", "server": {"server_id":2} }
{ "message": "上游服务器删除成功" }
```

---

## 七、命名空间路由（Routing）

- POST `/api/v1/route/namespace`（鉴权）
  - 说明：根据请求头/查询/体/路径进行匹配，返回目标命名空间

- POST `/api/v1/route/validate`（鉴权）
  - 说明：对当前规则集进行匹配测试，返回每条规则是否命中

请求示例
```json
{
  "headers": {"X-Service-Type": "chatgpt"},
  "query_params": {"model": "gpt-4"},
  "body": {"prompt": "Hello"},
  "path": "/v1/chat/completions"
}
```

响应示例（命中）
```json
{
  "matched": true,
  "rule_id": 101,
  "rule_name": "route-enterprise",
  "target_namespace": "enterprise",
  "namespace_info": {"namespace_id":1,"namespace_code":"enterprise","namespace_name":"enterprise Service","status":1},
  "matched_config": {"matcher_type":"header","match_field":"x-tenant","match_operator":"eq","match_value":"enterprise"}
}
```

响应示例（未命中，走默认）
```json
{
  "matched": false,
  "target_namespace": "default",
  "namespace_info": {"namespace_id":1,"namespace_code":"default","namespace_name":"Default Service","status":1},
  "message": "未找到匹配的规则，使用默认命名空间"
}
```

路由验证响应示例
```json
{
  "request_data": {"headers": {"x-tenant": "enterprise"}},
  "rules": [
    {"rule_id":101,"rule_name":"route-enterprise","priority":10,"status":1,"matched":true,"config":{"matcher_type":"header","match_field":"x-tenant","match_operator":"eq","match_value":"enterprise"}}
  ]
}
```

---

## 八、Nginx 配置（后端存储）

- GET `/api/v1/nginx-configs`（可选 `config_type` 过滤）
- GET `/api/v1/nginx-configs/{config_type}`
- GET `/api/v1/nginx-configs/{config_id}`
- POST `/api/v1/nginx-configs`               （鉴权）
- PUT `/api/v1/nginx-configs/{config_id}`    （鉴权）
- DELETE `/api/v1/nginx-configs/{config_id}` （鉴权）

示例
```json
// 创建 Nginx 片段
{
  "config_type": "http",  
  "config_name": "gzip-settings",
  "config_content": "gzip on; gzip_comp_level 6;",
  "is_active": 1
}
```

列表响应示例（按类型）
```json
[
  {"config_id":11,"config_type":"http","config_name":"gzip-settings","config_content":"gzip on; gzip_comp_level 6;","is_active":1}
]
```

列表响应示例（不带类型，即全部）
```json
[
  {"config_id":11,"config_type":"http","config_name":"gzip-settings","config_value":{"gzip_level":6},"status":1}
]
```

单项响应示例
```json
{
  "config_id": 11,
  "config_type": "http",
  "config_name": "gzip-settings",
  "config_content": "gzip on; gzip_comp_level 6;",
  "is_active": 1
}
```

创建/更新/删除响应示例
```json
{ "message": "nginx配置创建成功", "config_id": 11, "config": {"config_id":11} }
{ "message": "nginx配置更新成功", "config": {"config_id":11} }
{ "message": "nginx配置删除成功" }
```

---

## 九、网关侧（OpenResty）

- GET `/health`（Host: `gateway.ai-gateway.local`）
  - 说明：网关健康（共享内存、Redis、配置中心）
  - 响应示例：
    ```json
    {
      "status": "healthy",
      "service": "ai-gateway",
      "version": "2.0.0",
      "timestamp": 1754904203,
      "services": {
        "shared_memory": {"status": "healthy"},
        "config_center": {"status": "healthy"},
        "redis": {"status": "healthy"}
      }
    }
    ```

- GET `/stats`
  - 说明：监控统计（共享字典）
  - 响应示例：
    ```json
    {
      "requests_total": 12345,
      "requests_2xx": 11890,
      "requests_4xx": 290,
      "requests_5xx": 165,
      "latency_ms_p95": 420,
      "upstream_failures": 12,
      "updated_at": 1754904203
    }
    ```

- GET `/refresh-config`
  - 说明：触发刷新配置（Redis/MySQL → Redis 缓存）
  - 响应示例（成功）：
    ```json
    {"success": true, "message": "All configurations refreshed successfully"}
    ```
  - 响应示例（失败）：
    ```json
    {"success": false, "error": "Failed to refresh configurations"}
    ```

- 动态代理：其余路径由 `routing.dynamic_router` 动态路由到上游；`proxy_pass $upstream_backend`。

---

## 十、Token 计算服务（内部服务）

- GET `/`  → 服务信息
  - 响应示例：
    ```json
    {
      "message": "Token计算服务",
      "version": "1.0.0",
      "endpoints": {
        "计算单个文本token": "/calculate",
        "批量计算token": "/batch-calculate",
        "获取可用模型": "/models",
        "下载模型": "/download-model",
        "健康检查": "/health"
      }
    }
    ```

- POST `/calculate`  → 单文本计算
  - 请求示例：
    ```json
    {"text":"你好，世界","model_name":"gpt2"}
    ```
  - 响应示例：
    ```json
    {
      "success": true,
      "model_name": "gpt2",
      "model_type": "decoder-only",
      "text": "你好，世界",
      "token_count": 6,
      "tokenizer_type": "hf-tokenizers"
    }
    ```

- POST `/batch-calculate`  → 批量计算
  - 请求示例：
    ```json
    {"texts":["hello","world"],"model_name":"gpt2"}
    ```
  - 响应示例：
    ```json
    [
      {"success":true,"model_name":"gpt2","text":"hello","token_count":5},
      {"success":true,"model_name":"gpt2","text":"world","token_count":5}
    ]
    ```

- GET `/models`  → 可用模型
  - 响应示例：
    ```json
    [
      {"name":"gpt2","description":"OpenAI GPT-2","downloaded":false,"available":true,"url":"https://...","type":"decoder-only","tokenizer_type":"hf-tokenizers"}
    ]
    ```

- POST `/download-model`  → 下载模型
  - 请求示例：
    ```json
    {"model_name":"gpt2"}
    ```
  - 响应示例（成功）：
    ```json
    {"success": true, "message": "模型 gpt2 下载成功"}
    ```
  - 响应示例（失败）：
    ```json
    {"detail": "下载失败: 网络错误"}
    ```

- GET `/health`  → 健康
  - 响应示例：
    ```json
    {"status":"healthy","service":"token-calculator","version":"1.0.0"}
    ```

---

## 统一错误响应格式

- 404 示例：
  ```json
  {"detail": "资源不存在"}
  ```
- 400 示例：
  ```json
  {"detail": "缺少必要字段: rule_name"}
  ```
- 500 示例：
  ```json
  {"detail": "服务器内部错误: ..."}
  ```

---

## 十一、调用示例（curl）

```bash
# 健康
curl -H "Host: api.ai-gateway.local" http://<NODE_IP>:<NODEPORT>/api/v1/status | jq .

# 代理规则列表
curl -H "Host: api.ai-gateway.local" http://<NODE_IP>:<NODEPORT>/api/v1/proxy-rules | jq .

# 新增代理规则（示意）
curl -H "Host: api.ai-gateway.local" -H "Authorization: Bearer admin" \
     -H "Content-Type: application/json" \
     -d '{"rule_name":"demo","namespace_id":1,"upstream_server_id":1,"priority":10,"is_active":1}' \
     http://<NODE_IP>:<NODEPORT>/api/v1/proxy-rules | jq .

# 网关健康
curl -H "Host: gateway.ai-gateway.local" http://<NODE_IP>:<NODEPORT>/health | jq .
```
