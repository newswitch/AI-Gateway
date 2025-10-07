# 路径重写功能使用说明

## 功能概述

路径重写功能允许AI网关将客户端请求的路径重写为不同的路径后再转发给上游服务器。这对于统一不同大模型服务的API接口非常有用。

## 功能特点

- **灵活的路径匹配**：支持精确匹配、前缀匹配和通配符匹配
- **优先级控制**：支持规则优先级设置，数字越小优先级越高
- **实时配置**：支持动态加载和更新路径重写规则
- **缓存优化**：使用Redis缓存提高性能
- **调试支持**：提供完整的测试和调试接口

## 配置方式

### 1. 前端配置

在模型路由管理页面中：

1. 点击"添加规则"按钮
2. 填写路径匹配规则（如 `/qwen`）
3. 选择上游服务器
4. 在"路径重写配置"部分：
   - 开启"启用路径重写"开关
   - 填写匹配路径模式：`/qwen`
   - 填写重写目标路径：`/v1/chat/completions`
5. 保存规则

### 2. 数据库配置

路径重写配置存储在 `location_rules` 表的 `path_rewrite_config` 字段中：

```json
{
  "enabled": true,
  "from": "/qwen",
  "to": "/v1/chat/completions"
}
```

## 使用示例

### 示例1：基本路径重写

**配置：**
- 匹配路径：`/qwen`
- 重写规则：`/qwen` → `/v1/chat/completions`

**效果：**
- 客户端请求：`POST /qwen`
- 实际转发：`POST /v1/chat/completions`

### 示例2：带后缀的路径重写

**配置：**
- 匹配路径：`/qwen`
- 重写规则：`/qwen` → `/v1/chat/completions`

**效果：**
- 客户端请求：`POST /qwen/stream`
- 实际转发：`POST /v1/chat/completions/stream`

### 示例3：通配符路径重写

**配置：**
- 匹配路径：`/qwen*`
- 重写规则：`/qwen*` → `/v1/chat/*`

**效果：**
- 客户端请求：`POST /qwen/stream`
- 实际转发：`POST /v1/chat/stream`

## 生成的Nginx配置

路径重写功能会生成如下的Nginx配置：

```nginx
location /qwen {
    proxy_cache off;
    proxy_buffering off;
    rewrite ^/qwen(.*)$ /v1/chat/completions$1 last;
    proxy_pass http://mock-llm-server/v1/chat/completions;
}
```

## 测试接口

### 1. 测试路径重写功能

```bash
# 测试基本路径重写
curl "http://localhost:8080/test/path-rewrite?path=/qwen"

# 测试带后缀的路径重写
curl "http://localhost:8080/test/path-rewrite?path=/qwen/stream"
```

**响应示例：**
```json
{
  "success": true,
  "test_path": "/qwen",
  "original_path": "/qwen",
  "rewritten_path": "/v1/chat/completions",
  "was_rewritten": true,
  "rewrite_rule_id": 1,
  "timestamp": 1705123456
}
```

### 2. 获取重写规则信息

```bash
curl "http://localhost:8080/test/rewrite-rules"
```

**响应示例：**
```json
{
  "success": true,
  "stats": {
    "total_rules": 3,
    "cache_timestamp": 1705123456,
    "cache_age": 30
  },
  "timestamp": 1705123456
}
```

### 3. 调试重写规则

```bash
curl "http://localhost:8080/test/debug-rules"
```

### 4. 运行测试套件

```bash
curl "http://localhost:8080/test/run-tests"
```

## 配置优先级

路径重写规则按以下优先级执行：

1. **精确匹配**：`/qwen` 只匹配 `/qwen`
2. **前缀匹配**：`/qwen/` 匹配 `/qwen/` 开头的所有路径
3. **通配符匹配**：`/qwen*` 匹配 `/qwen` 开头的所有路径

## 性能优化

- **缓存机制**：路径重写规则缓存在Redis中，TTL为30分钟
- **优先级排序**：规则按优先级排序，只应用第一个匹配的规则
- **异步处理**：路径重写处理不会阻塞主请求流程

## 故障排除

### 1. 路径重写不生效

检查以下项目：
- 规则是否启用（`enabled: true`）
- 匹配路径是否正确
- 规则优先级是否合适
- Redis缓存是否正常

### 2. 查看调试信息

```bash
# 查看Nginx错误日志
docker logs ai-gateway-gateway-1

# 查看路径重写规则
curl "http://localhost:8080/test/debug-rules"
```

### 3. 清除缓存

```bash
# 通过配置中心API清除缓存
curl -X POST "http://localhost:8001/api/config/refresh"
```

## 注意事项

1. **路径冲突**：避免配置相互冲突的路径重写规则
2. **性能影响**：大量规则可能影响性能，建议定期清理无用规则
3. **测试验证**：在生产环境部署前，务必在测试环境验证路径重写功能
4. **监控告警**：建议监控路径重写的使用情况和错误率

## 扩展功能

未来可能支持的功能：
- 基于请求头的条件重写
- 基于请求体的内容重写
- 正则表达式路径匹配
- 重写规则模板
- 重写历史记录和回滚
