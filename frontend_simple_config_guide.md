# 前端配置命名空间路由 - 简化指南

## 当前前端界面配置流程

基于现有的前端界面，您可以通过以下步骤配置命名空间路由：

### 第一步：创建命名空间（在命名空间管理页面）

1. **访问命名空间管理页面**
   - 打开浏览器访问：`http://localhost:3000/namespace-management`
   - 点击右上角的"创建命名空间"按钮

2. **填写命名空间信息**
   ```
   命名空间代码: chatgpt-service
   命名空间名称: ChatGPT服务
   匹配字段来源: 报文头(Header)
   匹配字段名称: X-Service-Type
   匹配操作符: 等于(=)
   匹配值: chatgpt
   ```

3. **保存配置**
   - 点击"确定"按钮
   - 系统会自动创建命名空间和匹配器

### 第二步：配置验证规则（在策略配置页面）

1. **访问策略配置页面**
   - 打开：`http://localhost:3000/policy-configuration`
   - 点击"创建策略"按钮

2. **创建Token限制策略**
   ```
   策略名称: ChatGPT Token限制
   关联命名空间: 选择 chatgpt-service
   策略类型: Token限制
   优先级: 1
   启用: 是
   ```

3. **创建并发限制策略**
   ```
   策略名称: ChatGPT 并发限制
   关联命名空间: 选择 chatgpt-service
   策略类型: 并发限制
   优先级: 2
   启用: 是
   ```

4. **创建QPS限制策略**
   ```
   策略名称: ChatGPT QPS限制
   关联命名空间: 选择 chatgpt-service
   策略类型: QPS限制
   优先级: 3
   启用: 是
   ```

### 第三步：配置上游服务器（在模型路由页面）

1. **访问模型路由页面**
   - 打开：`http://localhost:3000/model-routing`
   - 确保在"上游服务器"标签页

2. **创建上游服务器**
   ```
   服务器名称: chatgpt-upstream
   服务器地址: api.openai.com
   端口: 443
   权重: 100
   ```

3. **配置路径规则**
   - 切换到"路径规则"标签页
   - 点击"添加路径规则"
   ```
   路径匹配: /v1/chat/completions
   上游服务器: chatgpt-upstream
   代理缓存: 开启
   代理缓冲: 开启
   ```

## 配置完成后的测试

### 测试请求示例

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

### 预期处理流程

1. **请求到达网关** → 提取请求头 `X-Service-Type: chatgpt`
2. **匹配命名空间** → 找到 `chatgpt-service` 命名空间
3. **应用验证规则**：
   - 检查Token数量限制
   - 检查并发连接数限制
   - 检查QPS限制
4. **验证通过** → 转发到 `api.openai.com/v1/chat/completions`
5. **验证失败** → 返回相应的错误信息

## 前端界面功能说明

### 命名空间管理页面
- **位置**: `http://localhost:3000/namespace-management`
- **功能**: 创建、编辑、删除命名空间
- **特点**: 支持在创建时直接配置匹配规则

### 策略配置页面
- **位置**: `http://localhost:3000/policy-configuration`
- **功能**: 创建、编辑、删除验证规则
- **支持类型**: Token限制、并发限制、QPS限制、报文匹配

### 模型路由页面
- **位置**: `http://localhost:3000/model-routing`
- **功能**: 配置上游服务器和路径规则
- **特点**: 支持负载均衡和健康检查

## 注意事项

1. **命名空间代码必须唯一**
2. **匹配器规则按优先级执行**
3. **策略规则按优先级验证**
4. **确保上游服务器可访问**
5. **路径规则支持正则表达式**

## 常见问题解决

### 问题1：请求无法匹配到命名空间
**解决方案**：
- 检查请求头是否包含 `X-Service-Type: chatgpt`
- 确认命名空间中的匹配器配置正确
- 检查匹配操作符和匹配值

### 问题2：策略验证失败
**解决方案**：
- 检查策略配置参数是否合理
- 确认策略状态为"启用"
- 查看访问日志了解具体失败原因

### 问题3：上游服务器连接失败
**解决方案**：
- 检查服务器地址和端口是否正确
- 确认网络连接正常
- 检查SSL证书配置

## 监控和调试

### 查看访问日志
- 访问：`http://localhost:3000/access-logs`
- 查看请求处理详情和错误信息

### 监控流量指标
- 访问：`http://localhost:3000/traffic-monitoring`
- 查看实时请求统计和性能指标

### 检查系统状态
- 访问：`http://localhost:3000/dashboard`
- 查看系统整体健康状态

## 配置验证

完成配置后，您可以通过以下方式验证：

1. **发送测试请求** - 使用curl或Postman
2. **查看访问日志** - 确认请求被正确处理
3. **监控流量指标** - 观察请求统计
4. **检查错误日志** - 排查配置问题

通过以上步骤，您就可以通过前端界面完成命名空间路由的配置了！
