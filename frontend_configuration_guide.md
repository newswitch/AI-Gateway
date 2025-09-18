# 前端配置命名空间路由指南

## 配置流程概览

通过前端界面配置命名空间路由需要按照以下步骤进行：

1. **创建命名空间** → 2. **配置匹配器** → 3. **设置验证规则** → 4. **配置上游服务器** → 5. **测试路由**

## 详细配置步骤

### 第一步：创建命名空间

1. **进入命名空间管理页面**
   - 访问：`http://localhost:3000/namespace-management`
   - 点击"创建命名空间"按钮

2. **填写命名空间信息**
   ```
   命名空间代码: chatgpt-service
   命名空间名称: ChatGPT服务
   匹配字段来源: 报文头(Header)
   匹配字段名称: X-Service-Type
   匹配操作符: 等于(=)
   匹配值: chatgpt
   ```

3. **保存命名空间**
   - 点击"确定"按钮保存
   - 系统会自动创建命名空间和对应的匹配器

### 第二步：配置验证规则

1. **进入策略配置页面**
   - 访问：`http://localhost:3000/policy-configuration`
   - 点击"创建策略"按钮

2. **创建Token限制规则**
   ```
   策略名称: ChatGPT Token限制
   关联命名空间: 选择刚才创建的 chatgpt-service
   策略类型: Token限制
   配置参数:
     - 模型名称: gpt-4
     - 最大Token数: 4000
     - 启用时间窗口: 是
     - 时间窗口(分钟): 60
     - 窗口内最大Token数: 100000
   优先级: 1
   启用: 是
   ```

3. **创建并发限制规则**
   ```
   策略名称: ChatGPT 并发限制
   关联命名空间: 选择 chatgpt-service
   策略类型: 并发限制
   配置参数:
     - 最大并发数: 100
   优先级: 2
   启用: 是
   ```

4. **创建QPS限制规则**
   ```
   策略名称: ChatGPT QPS限制
   关联命名空间: 选择 chatgpt-service
   策略类型: QPS限制
   配置参数:
     - 最大QPS: 10
     - 时间窗口(秒): 60
   优先级: 3
   启用: 是
   ```

### 第三步：配置上游服务器

1. **进入模型路由页面**
   - 访问：`http://localhost:3000/model-routing`
   - 切换到"上游服务器"标签页

2. **创建上游服务器**
   ```
   服务器名称: chatgpt-upstream
   服务器列表:
     - 地址: api.openai.com
     - 端口: 443
     - 权重: 100
   健康检查:
     - 启用健康检查: 是
     - 检查路径: /v1/models
     - 检查间隔: 30秒
     - 超时时间: 5秒
     - 失败阈值: 3次
   ```

3. **创建路径规则**
   - 切换到"路径规则"标签页
   - 点击"添加路径规则"
   ```
   路径匹配: /v1/chat/completions
   上游服务器: 选择 chatgpt-upstream
   代理缓存: 开启
   代理缓冲: 开启
   ```

### 第四步：测试配置

1. **使用测试工具发送请求**
   ```bash
   curl -X POST "http://localhost:8000/v1/chat/completions" \
     -H "X-Service-Type: chatgpt" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-xxx" \
     -d '{
       "model": "gpt-4",
       "messages": [{"role": "user", "content": "Hello"}],
       "max_tokens": 100
     }'
   ```

2. **检查请求处理流程**
   - 请求会被匹配到 `chatgpt-service` 命名空间
   - 系统会应用所有配置的验证规则
   - 通过验证后转发到 `api.openai.com`

## 前端界面说明

### 命名空间管理页面功能

- **命名空间列表**: 显示所有已创建的命名空间
- **创建命名空间**: 支持配置匹配规则
- **编辑命名空间**: 修改命名空间配置
- **删除命名空间**: 软删除命名空间
- **状态管理**: 启用/禁用命名空间

### 策略配置页面功能

- **策略列表**: 显示所有策略配置
- **创建策略**: 支持多种策略类型
- **编辑策略**: 修改策略配置
- **删除策略**: 删除策略配置
- **策略模板**: 快速创建常用策略

### 模型路由页面功能

- **上游服务器管理**: 配置后端服务器
- **路径规则管理**: 配置请求路由
- **健康检查**: 监控服务器状态
- **负载均衡**: 配置权重和策略

## 配置示例

### 完整的ChatGPT服务配置

```json
{
  "namespace": {
    "code": "chatgpt-service",
    "name": "ChatGPT服务",
    "matcher": {
      "type": "header",
      "field": "X-Service-Type",
      "operator": "equals",
      "value": "chatgpt"
    }
  },
  "policies": [
    {
      "name": "Token限制",
      "type": "token_limit",
      "config": {
        "max_tokens": 4000,
        "time_window_minutes": 60,
        "max_tokens_per_window": 100000
      }
    },
    {
      "name": "并发限制",
      "type": "concurrent_limit",
      "config": {
        "max_concurrent": 100
      }
    },
    {
      "name": "QPS限制",
      "type": "rate_limit",
      "config": {
        "max_qps": 10,
        "time_window_seconds": 60
      }
    }
  ],
  "upstream": {
    "name": "chatgpt-upstream",
    "servers": [
      {
        "address": "api.openai.com",
        "port": 443,
        "weight": 100
      }
    ]
  },
  "location_rules": [
    {
      "path": "/v1/chat/completions",
      "upstream": "chatgpt-upstream",
      "proxy_cache": true,
      "proxy_buffering": true
    }
  ]
}
```

## 注意事项

1. **命名空间代码必须唯一**
2. **匹配器规则按优先级执行**
3. **策略规则按优先级验证**
4. **上游服务器需要配置健康检查**
5. **路径规则支持正则表达式**

## 故障排查

### 常见问题

1. **请求无法匹配到命名空间**
   - 检查匹配器配置是否正确
   - 确认请求头包含正确的字段

2. **策略验证失败**
   - 检查策略配置参数
   - 确认策略状态为启用

3. **上游服务器连接失败**
   - 检查服务器地址和端口
   - 确认健康检查配置

4. **路径规则不生效**
   - 检查路径匹配规则
   - 确认上游服务器配置

### 调试方法

1. **查看访问日志**
   - 进入访问日志页面
   - 查看请求处理详情

2. **监控流量指标**
   - 进入流量监控页面
   - 查看实时请求统计

3. **检查系统健康状态**
   - 进入仪表板页面
   - 查看系统整体状态
