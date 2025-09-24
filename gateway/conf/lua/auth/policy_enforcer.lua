-- 策略执行器模块
-- 负责执行命名空间关联的策略检查
-- 支持流式与非流式Token限制

local json = require "utils.json"
local redis = require "utils.redis"
local http = require "utils.http"
local core = require "core.init"

local _M = {}

-- 执行Token限制策略
local function enforce_token_limit(policy, request_info)
    ngx.log(ngx.INFO, "=== TOKEN_LIMIT: Starting token limit enforcement ===")
    
    local config = policy.rule_config or policy.config or {}
    local max_input = config.maxInputTokenCount or 0
    local max_output = config.maxOutputTokenCount or 0
    local enable_time_window = config.enableTimeWindow or false
    local time_window_minutes = config.timeWindowMinutes or 60
    local window_max_tokens = config.windowMaxTokenCount or 0
    local stream_mode = config.streamMode or "auto"  -- auto, stream, non-stream
    
    ngx.log(ngx.INFO, "TOKEN_LIMIT: max_input: ", max_input, ", max_output: ", max_output, ", enable_time_window: ", enable_time_window)
    
    -- 解析请求体获取Token信息
    if not request_info.body then
        return true, "No request body to analyze"
    end
    
    local body_data, err = json.decode(request_info.body)
    if not body_data then
        ngx.log(ngx.WARN, "Failed to parse request body for token analysis: ", err)
        return true, "Failed to parse request body"
    end
    
    -- 检测流式模式
    local is_streaming = false
    if stream_mode == "auto" then
        is_streaming = body_data.stream == true or body_data.stream == "true"
    elseif stream_mode == "stream" then
        is_streaming = true
    elseif stream_mode == "non-stream" then
        is_streaming = false
    end
    
    ngx.log(ngx.INFO, "Token limit check - Streaming mode: ", is_streaming)
    
    -- 获取输入Token数量 - 使用Token计算服务
    local input_tokens = 0
    if body_data.messages then
        -- 从配置中获取Token服务设置
        local token_config = core.get_config().token_service
        local token_service_url = token_config.url .. "/calculate"
        
        -- 调用Token计算服务
        local token_request = {
            model = body_data.model or "Qwen3-8B",  -- 默认模型
            messages = body_data.messages
        }
        
        -- 将请求数据编码为JSON
        local request_json, json_err = json.encode(token_request)
        if not request_json then
            ngx.log(ngx.ERR, "Failed to encode token request: ", json_err)
            return false, "Failed to encode token request"
        end
        
        local token_response, err = http.post(token_service_url, request_json)
        if token_response then
            -- 解析JSON响应
            local response_data, parse_err = json.decode(token_response)
            if response_data and response_data.success then
                input_tokens = response_data.token_count or 0
                ngx.log(ngx.INFO, "Token calculation successful: ", input_tokens, " tokens for model: ", response_data.model or "unknown")
            else
                ngx.log(ngx.WARN, "Token calculation response parse failed: ", parse_err or "Invalid response format")
                -- 如果启用了降级机制，使用简单估算
                if token_config.fallback_enabled then
                    for _, message in ipairs(body_data.messages) do
                        if message.content then
                            input_tokens = input_tokens + math.ceil(string.len(message.content) / 4)
                        end
                    end
                    ngx.log(ngx.WARN, "Using fallback token estimation: ", input_tokens, " tokens")
                else
                    ngx.log(ngx.ERR, "Token calculation failed and fallback disabled")
                    return false, "Token calculation service unavailable"
                end
            end
        else
            ngx.log(ngx.WARN, "Token calculation failed: ", err or "Unknown error")
            
            -- 如果启用了降级机制，使用简单估算
            if token_config.fallback_enabled then
                for _, message in ipairs(body_data.messages) do
                    if message.content then
                        input_tokens = input_tokens + math.ceil(string.len(message.content) / 4)
                    end
                end
                ngx.log(ngx.WARN, "Using fallback token estimation: ", input_tokens, " tokens")
            else
                ngx.log(ngx.ERR, "Token calculation failed and fallback disabled")
                return false, "Token calculation service unavailable"
            end
        end
    end
    
    -- 检查输入Token限制
    if max_input > 0 and input_tokens > max_input then
        ngx.log(ngx.WARN, "Input token limit exceeded: ", input_tokens, " > ", max_input)
        return false, "Input token limit exceeded"
    end
    
    -- 获取用户请求的输出Token限制参数
    local max_tokens = body_data.max_tokens or 0
    local max_completion_tokens = body_data.max_completion_tokens or max_tokens
    
    -- max_output 是从策略配置中获取的系统级限制（已从Redis缓存中获取）
    -- max_completion_tokens 是从用户请求中获取的用户级限制
    -- 最终限制 = min(系统限制, 用户限制)
    local final_output_limit = max_output
    if max_output > 0 and max_completion_tokens > 0 then
        final_output_limit = math.min(max_output, max_completion_tokens)
    elseif max_output > 0 then
        final_output_limit = max_output
    elseif max_completion_tokens > 0 then
        final_output_limit = max_completion_tokens
    else
        final_output_limit = 0  -- 无限制
    end
    
    ngx.log(ngx.INFO, "Token limit calculation - System limit: ", max_output, 
            ", User request: ", max_completion_tokens, 
            ", Final limit: ", final_output_limit)
    
    -- 根据流式模式进行不同的处理
    if is_streaming then
        -- 流式模式：设置流式Token限制
        ngx.log(ngx.INFO, "Streaming mode - setting up real-time token monitoring")
        
        -- 检查输出Token限制
        if final_output_limit > 0 and max_completion_tokens > final_output_limit then
            ngx.log(ngx.WARN, "Output token limit exceeded: ", max_completion_tokens, " > ", final_output_limit)
            return false, "Output token limit exceeded"
        end
        
        -- 设置流式Token限制到请求头，供后续处理使用
        ngx.req.set_header("X-Token-Limit-Output", final_output_limit)
        ngx.req.set_header("X-Token-Limit-Streaming", "true")
        ngx.req.set_header("X-Token-Limit-Max-Tokens", max_completion_tokens)
        ngx.req.set_header("X-Token-Limit-Model", body_data.model or "Qwen3-8B")
        
    else
        -- 非流式模式：预检查所有Token限制
        ngx.log(ngx.INFO, "Non-streaming mode - pre-checking all token limits")
        
        -- 检查输出Token限制
        if final_output_limit > 0 and max_completion_tokens > final_output_limit then
            ngx.log(ngx.WARN, "Output token limit exceeded: ", max_completion_tokens, " > ", final_output_limit)
            return false, "Output token limit exceeded"
        end
    end
    
    -- 检查时间窗口限制
    if enable_time_window and window_max_tokens > 0 then
        local namespace_id = policy.namespace_id
        local time_key = "token_usage:" .. namespace_id .. ":" .. math.floor(ngx.time() / (time_window_minutes * 60))
        
        local current_usage, err = redis.get(time_key)
        if not current_usage then
            current_usage = 0
        else
            current_usage = tonumber(current_usage) or 0
        end
        
        -- 计算总Token使用量（输入 + 预期输出）
        local total_tokens = input_tokens + final_output_limit
        
        if current_usage + total_tokens > window_max_tokens then
            ngx.log(ngx.WARN, "Time window token limit exceeded: ", current_usage + total_tokens, " > ", window_max_tokens)
            return false, "Time window token limit exceeded"
        end
        
        -- 更新使用量
        local update_result, update_err = redis.incrby_ex(time_key, input_tokens, time_window_minutes * 60)
        if not update_result then
            ngx.log(ngx.ERR, "Failed to update token usage in Redis: ", update_err)
            -- 即使更新失败，也允许请求继续，但记录错误
        else
            ngx.log(ngx.INFO, "Updated token usage: +", input_tokens, " tokens, total: ", update_result)
        end
        
        -- 为输出Token预留空间（使用负数来预留，实际输出时再增加）
        if final_output_limit > 0 then
            local reserve_result, reserve_err = redis.incrby_ex(time_key, -final_output_limit, time_window_minutes * 60)
            if reserve_result then
                ngx.log(ngx.INFO, "Reserved space for output tokens: ", final_output_limit)
            end
        end
    end
    
    return true, "Token limit check passed"
end

-- 流式响应Token监控和截断
function _M.monitor_streaming_tokens(response_chunk)
    -- 检查是否设置了流式Token限制
    local streaming_enabled = ngx.var.http_x_token_limit_streaming
    if not streaming_enabled or streaming_enabled ~= "true" then
        return response_chunk, false  -- 未启用流式监控
    end
    
    local max_output_tokens = tonumber(ngx.var.http_x_token_limit_output) or 0
    local max_tokens = tonumber(ngx.var.http_x_token_limit_max_tokens) or 0
    local model = ngx.var.http_x_token_limit_model or "Qwen3-8B"
    
    if max_output_tokens <= 0 and max_tokens <= 0 then
        return response_chunk, false  -- 未设置Token限制
    end
    
    -- 获取当前累积的Token数量
    local current_tokens = tonumber(ngx.var.streaming_token_count) or 0
    
    -- 使用token-count服务计算当前块的Token数量
    local chunk_tokens = _M.calculate_output_tokens_with_service(response_chunk, model)
    current_tokens = current_tokens + chunk_tokens
    
    -- 检查是否超过限制
    if max_output_tokens > 0 and current_tokens > max_output_tokens then
        ngx.log(ngx.WARN, "Streaming output token limit exceeded: ", current_tokens, " > ", max_output_tokens)
        return response_chunk .. "\n\n[Token limit exceeded, response truncated]", true  -- 截断响应
    end
    
    if max_tokens > 0 and current_tokens > max_tokens then
        ngx.log(ngx.WARN, "Streaming max tokens exceeded: ", current_tokens, " > ", max_tokens)
        return response_chunk .. "\n\n[Max tokens exceeded, response truncated]", true  -- 截断响应
    end
    
    -- 更新Token计数
    ngx.var.streaming_token_count = current_tokens
    
    return response_chunk, false  -- 继续响应
end

-- 使用token-count服务计算输出Token
function _M.calculate_output_tokens_with_service(text, model)
    local token_config = core.get_config().token_service
    local token_service_url = token_config.url .. "/calculate"
    
    local token_request = {
        text = text,
        model_name = model or "Qwen3-8B"
    }
    
    local request_json, json_err = json.encode(token_request)
    if not request_json then
        ngx.log(ngx.WARN, "Failed to encode output token request: ", json_err)
        return math.ceil(string.len(text) / 4)  -- 降级估算
    end
    
    local token_response, err = http.post(token_service_url, request_json)
    if token_response then
        local response_data, parse_err = json.decode(token_response)
        if response_data and response_data.success then
            return response_data.token_count or 0
        else
            ngx.log(ngx.WARN, "Output token calculation response parse failed: ", parse_err or "Invalid response format")
        end
    else
        ngx.log(ngx.WARN, "Output token calculation failed: ", err or "Unknown error")
    end
    
    -- 降级到简单估算
    return math.ceil(string.len(text) / 4)
end

-- 执行QPS限制策略
local function enforce_qps_limit(policy, request_info)
    local config = policy.rule_config or policy.config or {}
    local max_qps = config.maxQPS or 0
    local time_window = config.timeWindow or 60
    
    if max_qps <= 0 then
        return true, "QPS limit not configured"
    end
    
    local namespace_id = policy.namespace_id
    local current_time = ngx.time()
    local window_key = "qps:" .. namespace_id .. ":" .. math.floor(current_time / time_window)
    
    local current_count, err = redis.get(window_key)
    if not current_count then
        current_count = 0
    else
        current_count = tonumber(current_count) or 0
    end
    
    if current_count >= max_qps then
        ngx.log(ngx.WARN, "QPS limit exceeded: ", current_count, " >= ", max_qps)
        return false, "QPS limit exceeded"
    end
    
    -- 增加计数
    redis.incr_ex(window_key, time_window)
    
    return true, "QPS limit check passed"
end

-- 执行并发限制策略
local function enforce_concurrency_limit(policy, request_info)
    local config = policy.rule_config or policy.config or {}
    local max_concurrent = config.maxConcurrentConnections or 0
    
    if max_concurrent <= 0 then
        return true, "Concurrency limit not configured"
    end
    
    local namespace_id = policy.namespace_id
    local concurrency_key = "concurrent:" .. namespace_id
    
    local current_count, err = redis.get(concurrency_key)
    if not current_count then
        current_count = 0
    else
        current_count = tonumber(current_count) or 0
    end
    
    if current_count >= max_concurrent then
        ngx.log(ngx.WARN, "Concurrency limit exceeded: ", current_count, " >= ", max_concurrent)
        return false, "Concurrency limit exceeded"
    end
    
    -- 增加并发计数
    redis.incr(concurrency_key)
    
    -- 设置过期时间（防止计数永远不减少）
    redis.expire(concurrency_key, 300) -- 5分钟
    
    return true, "Concurrency limit check passed"
end

-- 执行报文匹配策略
local function enforce_message_matching(policy, request_info)
    local config = policy.rule_config or policy.config or {}
    local field_source = config.matchingFieldSource or "header"
    local field_name = config.matchingFieldName or ""
    local operator = config.matchingOperator or "equals"
    local expected_value = config.matchingValue or ""
    local action = config.matchingAction or "allow"
    
    if field_name == "" or expected_value == "" then
        return true, "Message matching not configured"
    end
    
    local actual_value = nil
    
    if field_source == "header" then
        actual_value = request_info.headers[field_name]
    elseif field_source == "body" then
        if request_info.body then
            local body_data, err = json.decode(request_info.body)
            if body_data then
                actual_value = _M.get_nested_field(body_data, field_name)
            end
        end
    end
    
    if not actual_value then
        ngx.log(ngx.WARN, "Field not found: ", field_source, ".", field_name)
        return action == "deny", "Field not found"
    end
    
    local matcher = require "auth.namespace_matcher"
    local matched = matcher.match_value(tostring(actual_value), expected_value, operator)
    
    if action == "allow" then
        return matched, matched and "Message matched" or "Message not matched"
    else
        return not matched, not matched and "Message not matched (deny)" or "Message matched (deny)"
    end
end

-- 获取嵌套字段值
function _M.get_nested_field(data, field_path)
    local fields = {}
    for field in string.gmatch(field_path, "[^%.]+") do
        table.insert(fields, field)
    end
    
    local current = data
    for _, field in ipairs(fields) do
        if type(current) == "table" and current[field] then
            current = current[field]
        else
            return nil
        end
    end
    
    return current
end

-- 执行策略
function _M.enforce_policy(policy, request_info)
    if not policy then
        ngx.log(ngx.WARN, "Policy is nil")
        return true, "Policy is nil"
    end
    
    if not policy.is_active then
        ngx.log(ngx.INFO, "Policy not active: ", policy.name or policy.policy_name or "unknown")
        return true, "Policy not active"
    end
    
    local policy_type = policy.type or policy.policy_type
    ngx.log(ngx.INFO, "Enforcing policy: ", policy.name or policy.policy_name or "unknown", " (type: ", policy_type, ")")
    
    if policy_type == "token-limit" then
        return enforce_token_limit(policy, request_info)
    elseif policy_type == "qps-limit" then
        return enforce_qps_limit(policy, request_info)
    elseif policy_type == "concurrency-limit" then
        return enforce_concurrency_limit(policy, request_info)
    elseif policy_type == "message-matching" then
        return enforce_message_matching(policy, request_info)
    else
        ngx.log(ngx.WARN, "Unknown policy type: ", policy_type)
        return true, "Unknown policy type"
    end
end

-- 执行命名空间的所有策略
function _M.enforce_namespace_policies(namespace_id, request_info)
    ngx.log(ngx.INFO, "=== POLICY_ENFORCER: Starting policy enforcement ===")
    
    local cache = require "config.cache"
    local configs = cache.get_all_configs()
    
    local policies = configs.policies or {}
    local namespace_policies = {}
    
    ngx.log(ngx.INFO, "POLICY_ENFORCER: Enforcing policies for namespace_id: ", namespace_id, " (type: ", type(namespace_id), ")")
    ngx.log(ngx.INFO, "POLICY_ENFORCER: Total policies found: ", #policies)
    
    -- 筛选出该命名空间的策略
    for _, policy in ipairs(policies) do
        ngx.log(ngx.INFO, "POLICY_ENFORCER: Checking policy: ", policy.policy_name, ", namespace_id: ", policy.namespace_id, " (type: ", type(policy.namespace_id), ")")
        
        -- 类型转换比较
        local policy_namespace_id = tostring(policy.namespace_id)
        local request_namespace_id = tostring(namespace_id)
        
        if policy_namespace_id == request_namespace_id or 
           (policy.namespaces and type(policy.namespaces) == "table") then
            -- 检查策略是否关联到该命名空间
            local is_associated = false
            if policy_namespace_id == request_namespace_id then
                is_associated = true
                ngx.log(ngx.INFO, "POLICY_ENFORCER: Policy ", policy.policy_name, " directly associated with namespace ", namespace_id)
            elseif policy.namespaces then
                for _, ns in ipairs(policy.namespaces) do
                    local ns_id = tostring(ns.id or ns)
                    if ns_id == request_namespace_id then
                        is_associated = true
                        ngx.log(ngx.INFO, "POLICY_ENFORCER: Policy ", policy.policy_name, " associated with namespace ", namespace_id, " via namespaces array")
                        break
                    end
                end
            end
            
            if is_associated then
                table.insert(namespace_policies, policy)
                ngx.log(ngx.INFO, "POLICY_ENFORCER: Added policy ", policy.policy_name, " to namespace policies")
            end
        end
    end
    
    -- 按优先级排序
    table.sort(namespace_policies, function(a, b)
        return (a.priority or 100) < (b.priority or 100)
    end)
    
    ngx.log(ngx.INFO, "POLICY_ENFORCER: Found ", #namespace_policies, " policies for namespace: ", namespace_id)
    
    -- 执行策略
    for _, policy in ipairs(namespace_policies) do
        ngx.log(ngx.INFO, "POLICY_ENFORCER: Executing policy: ", policy.policy_name, " (", policy.policy_type, ")")
        local ok, message = _M.enforce_policy(policy, request_info)
        if not ok then
            ngx.log(ngx.WARN, "POLICY_ENFORCER: Policy enforcement failed: ", policy.name or policy.policy_name, " - ", message)
            return false, message
        end
        ngx.log(ngx.INFO, "POLICY_ENFORCER: Policy enforcement passed: ", policy.policy_name)
    end
    
    ngx.log(ngx.INFO, "POLICY_ENFORCER: All policies passed for namespace: ", namespace_id)
    return true, "All policies passed"
end

-- 减少并发计数（在请求结束时调用）
function _M.decrease_concurrency_count(namespace_id)
    local concurrency_key = "concurrent:" .. namespace_id
    local current_count, err = redis.get(concurrency_key)
    
    if current_count and tonumber(current_count) > 0 then
        redis.execute_command("decr", concurrency_key)
    end
end

return _M
