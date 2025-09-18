-- 策略执行器模块
-- 负责执行命名空间关联的策略检查

local json = require "utils.json"
local redis = require "utils.redis"

local _M = {}

-- 执行Token限制策略
local function enforce_token_limit(policy, request_info)
    local config = policy.config or {}
    local max_input = config.maxInputTokenCount or 0
    local max_output = config.maxOutputTokenCount or 0
    local enable_time_window = config.enableTimeWindow or false
    local time_window_minutes = config.timeWindowMinutes or 60
    local window_max_tokens = config.windowMaxTokenCount or 0
    
    -- 解析请求体获取Token信息
    if not request_info.body then
        return true, "No request body to analyze"
    end
    
    local body_data, err = json.decode(request_info.body)
    if not body_data then
        ngx.log(ngx.WARN, "Failed to parse request body for token analysis: ", err)
        return true, "Failed to parse request body"
    end
    
    -- 获取输入Token数量
    local input_tokens = 0
    if body_data.messages then
        for _, message in ipairs(body_data.messages) do
            if message.content then
                -- 简单的Token估算（实际应该调用Token计算服务）
                input_tokens = input_tokens + math.ceil(string.len(message.content) / 4)
            end
        end
    end
    
    -- 检查输入Token限制
    if max_input > 0 and input_tokens > max_input then
        ngx.log(ngx.WARN, "Input token limit exceeded: ", input_tokens, " > ", max_input)
        return false, "Input token limit exceeded"
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
        
        if current_usage + input_tokens > window_max_tokens then
            ngx.log(ngx.WARN, "Time window token limit exceeded: ", current_usage + input_tokens, " > ", window_max_tokens)
            return false, "Time window token limit exceeded"
        end
        
        -- 更新使用量
        redis.incr_ex(time_key, time_window_minutes * 60)
    end
    
    return true, "Token limit check passed"
end

-- 执行QPS限制策略
local function enforce_qps_limit(policy, request_info)
    local config = policy.config or {}
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
    local config = policy.config or {}
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
    local config = policy.config or {}
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
    if not policy or not policy.is_active then
        return true, "Policy not active"
    end
    
    local policy_type = policy.type or policy.policy_type
    
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
    local cache = require "config.cache"
    local configs = cache.get_all_configs()
    
    local policies = configs.policies or {}
    local namespace_policies = {}
    
    -- 筛选出该命名空间的策略
    for _, policy in ipairs(policies) do
        if policy.namespace_id == namespace_id or 
           (policy.namespaces and type(policy.namespaces) == "table") then
            -- 检查策略是否关联到该命名空间
            local is_associated = false
            if policy.namespace_id == namespace_id then
                is_associated = true
            elseif policy.namespaces then
                for _, ns in ipairs(policy.namespaces) do
                    if (type(ns) == "string" and ns == namespace_id) or
                       (type(ns) == "table" and ns.id == namespace_id) then
                        is_associated = true
                        break
                    end
                end
            end
            
            if is_associated then
                table.insert(namespace_policies, policy)
            end
        end
    end
    
    -- 按优先级排序
    table.sort(namespace_policies, function(a, b)
        return (a.priority or 100) < (b.priority or 100)
    end)
    
    -- 执行策略
    for _, policy in ipairs(namespace_policies) do
        local ok, message = _M.enforce_policy(policy, request_info)
        if not ok then
            ngx.log(ngx.WARN, "Policy enforcement failed: ", policy.name or policy.policy_name, " - ", message)
            return false, message
        end
    end
    
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
