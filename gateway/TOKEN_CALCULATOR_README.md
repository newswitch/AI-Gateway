# Token计算器子请求解决方案

## 问题背景

在`body_filter_by_lua_block`阶段，无法直接发送HTTP请求到外部服务，因为响应已经开始流式传输给客户端。这导致无法在流式响应过程中实时计算token数量。

## 解决方案

使用Nginx子请求（subrequest）机制，通过内部location调用外部token计算服务。

### 架构设计

```
body_filter_by_lua_block
    ↓
token_calculator.calculate_tokens_with_subrequest()
    ↓
ngx.location.capture("/_token_calc")
    ↓
内部location /_token_calc
    ↓
http.post() 调用外部token服务
    ↓
返回token数量
```

### 核心组件

#### 1. Token计算器模块 (`utils/token_calculator.lua`)

- `calculate_tokens_with_subrequest()`: 使用子请求计算token
- `estimate_tokens()`: 快速估算token数量（降级方案）
- `calculate_tokens_batch()`: 批量计算多个文本的token
- `calculate_tokens_hybrid()`: 混合模式，可选择使用子请求或估算

#### 2. 内部Token计算Location (`/_token_calc`)

- 接收文本和模型参数
- 调用外部token计算服务
- 提供降级估算机制
- 返回JSON格式的token数量

#### 3. 策略执行器更新 (`auth/policy_enforcer.lua`)

- 在`monitor_streaming_tokens()`中使用新的token计算方式
- 保持原有的流式监控逻辑不变

## 使用方法

### 基本用法

```lua
local token_calculator = require "utils.token_calculator"

-- 使用子请求计算token
local tokens = token_calculator.calculate_tokens_with_subrequest("Hello world", "Qwen3-8B")

-- 快速估算token
local estimated = token_calculator.estimate_tokens("Hello world", "Qwen3-8B")

-- 混合模式
local tokens = token_calculator.calculate_tokens_hybrid("Hello world", "Qwen3-8B", true) -- 使用子请求
local estimated = token_calculator.calculate_tokens_hybrid("Hello world", "Qwen3-8B", false) -- 使用估算
```

### 在流式响应中使用

```lua
-- 在body_filter_by_lua_block中
function _M.monitor_streaming_tokens(response_chunk)
    -- 使用子请求方式计算当前块的Token数量
    local chunk_tokens = token_calculator.calculate_tokens_with_subrequest(response_chunk, model)
    current_tokens = current_tokens + chunk_tokens
    
    -- 检查是否超过限制
    if current_tokens > max_output_tokens then
        return response_chunk .. "\n\n[Token limit exceeded, response truncated]", true
    end
    
    return response_chunk, false
end
```

## 优势

1. **解决HTTP请求限制**: 在`body_filter_by_lua_block`阶段可以正常调用外部服务
2. **保持流式性能**: 子请求不会阻塞主响应流
3. **降级机制**: 当外部服务不可用时，自动降级到估算模式
4. **灵活配置**: 支持多种计算模式和模型类型
5. **错误处理**: 完善的错误处理和日志记录

## 配置要求

### Token服务配置

确保在配置中心中正确配置token服务：

```json
{
  "token_service": {
    "url": "http://token-count-service:8080",
    "host": "token-count-service",
    "port": 8080,
    "path": "/calculate",
    "fallback_enabled": true
  }
}
```

### Nginx配置

确保内部location `/_token_calc` 已正确配置，并且token服务可访问。

## 性能考虑

1. **子请求开销**: 每次token计算都会产生子请求开销
2. **缓存机制**: 可以考虑添加token计算结果缓存
3. **批量处理**: 对于大量文本，使用批量计算接口
4. **降级策略**: 在高负载时可以考虑使用估算模式

## 测试

运行测试脚本验证功能：

```bash
cd gateway
lua test_token_calculator.lua
```

## 故障排除

### 常见问题

1. **子请求失败**: 检查内部location配置和token服务可用性
2. **Token计算不准确**: 验证token服务配置和模型参数
3. **性能问题**: 考虑使用估算模式或添加缓存

### 日志监控

关注以下日志：
- `Token calculation subrequest failed`
- `Token calculation failed with status`
- `Using fallback token estimation`

## 未来改进

1. **缓存机制**: 添加token计算结果缓存
2. **异步处理**: 考虑异步token计算
3. **批量优化**: 优化批量token计算性能
4. **监控指标**: 添加token计算性能监控
