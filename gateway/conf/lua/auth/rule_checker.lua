-- 规则检查器
-- 负责检查命名空间的各项规则限制

local _M = {}

local cjson = require "cjson"
local config_cache = require "config.config_cache"
local rate_limiter = require "auth.rate_limiter"
local svc = require "utils.service_config"

-- 规则类型定义
local rule_types = {
    token_limit = "token_limit",           -- Token数量限制
    connection_limit = "connection_limit", -- 并发连接数限制
    request_limit = "request_limit",       -- 请求频率限制
    field_check = "field_check"           -- 字段检查
}

-- 配置选项
local USE_PRECISE_TOKEN_CALCULATION = (os.getenv("USE_PRECISE_TOKEN_CALCULATION") or "true") == "true"  -- 是否启用精确token计算
local TOKEN_CALCULATION_TIMEOUT = tonumber(os.getenv("TOKEN_CALCULATION_TIMEOUT") or "3000")  -- token计算超时时间（毫秒）
local TOKEN_CACHE_TTL = tonumber(os.getenv("TOKEN_CACHE_TTL") or "300")  -- token缓存时间（秒）

-- 从环境变量获取token服务URL，如果没有则使用默认值
local function get_token_service_url()
    local token_service_url = os.getenv("TOKEN_SERVICE_URL") or "http://ai-gateway-token-service:8000"
    
    -- 如果URL已经包含完整路径，直接返回
    if string.find(token_service_url, "/calculate") then
        return token_service_url
    end
    
    -- 如果URL以斜杠结尾，直接拼接
    if string.sub(token_service_url, -1) == "/" then
        return token_service_url .. "calculate"
    end
    
    -- 否则添加斜杠和路径
    return token_service_url .. "/calculate"
end

local TOKEN_SERVICE_URL = get_token_service_url()

-- 调用token计算服务获取精确的token数量（带缓存）
local function get_precise_tokens(text, model_name)
    -- 如果禁用精确计算，直接使用简单估算
    if not USE_PRECISE_TOKEN_CALCULATION then
        return math.floor(#text / 4)
    end
    if not text or text == "" then
        return 0
    end
    
    -- 使用Redis缓存来避免重复计算
    local redis = require "resty.redis"
    local red = redis:new()
    local rc = svc.get_redis_config()
    local ok, err = red:connect(rc.host, rc.port or 6379)
    
    if ok then
        -- 构建缓存键
        local cache_key = string.format("token_cache:%s:%s", model_name or "gpt-3.5-turbo", ngx.md5(text))
        local cached_tokens = red:get(cache_key)
        
        if cached_tokens and cached_tokens ~= ngx.null then
            red:close()
            return tonumber(cached_tokens) or 0
        end
        red:close()
    end
    
    -- 缓存未命中，调用token服务
    local http = require "resty.http"
    local httpc = http.new()
    httpc:set_timeout(TOKEN_CALCULATION_TIMEOUT)  -- 使用配置的超时时间
    
    local request_body = cjson.encode({
        text = text,
        model_name = model_name or "gpt-3.5-turbo"  -- 默认模型
    })
    
    local res, err = httpc:request_uri(TOKEN_SERVICE_URL, {
        method = "POST",
        headers = {
            ["Content-Type"] = "application/json",
            ["Content-Length"] = #request_body
        },
        body = request_body
    })
    
    if not res then
        ngx.log(ngx.ERR, "Failed to call token service: ", err)
        -- 降级到简单估算
        return math.floor(#text / 4)
    end
    
    if res.status ~= 200 then
        ngx.log(ngx.ERR, "Token service returned status: ", res.status, ", body: ", res.body)
        -- 降级到简单估算
        return math.floor(#text / 4)
    end
    
    local ok, data = pcall(cjson.decode, res.body)
    if not ok or not data then
        ngx.log(ngx.ERR, "Failed to parse token service response: ", res.body)
        return 0
    end
    
    if not data.success then
        ngx.log(ngx.WARN, "Token calculation failed: ", data.error)
        return 0
    end
    
    local token_count = data.token_count or 0
    
    -- 缓存结果（5分钟过期）
    if ok then
        local red = redis:new()
        local rc = svc.get_redis_config()
        local ok, err = red:connect(rc.host, rc.port or 6379)
        if ok then
            local cache_key = string.format("token_cache:%s:%s", model_name or "gpt-3.5-turbo", ngx.md5(text))
            red:setex(cache_key, TOKEN_CACHE_TTL, tostring(token_count))  -- 使用配置的缓存时间
            red:close()
        end
    end
    
    -- 记录token计算日志
    ngx.log(ngx.INFO, "Token calculation: text_length=", #text, ", model=", model_name, ", tokens=", token_count)
    
    return token_count
end

-- 从请求中提取模型名称
local function extract_model_name(data)
    -- 优先从model字段获取
    if data.model then
        return data.model
    end
    
    -- 从messages中获取模型信息
    if data.messages and #data.messages > 0 then
        for _, message in ipairs(data.messages) do
            if message.model then
                return message.model
            end
        end
    end
    
    -- 默认模型
    return "gpt-3.5-turbo"
end

-- 获取请求中的Token数量
local function get_request_tokens()
    local content_type = ngx.var.content_type or ""
    local tokens = 0
    
    if string.find(content_type, "application/json") then
        ngx.req.read_body()
        local body = ngx.req.get_body_data()
        if body then
            local ok, data = pcall(cjson.decode, body)
            if ok and data then
                -- 提取模型名称
                local model_name = extract_model_name(data)
                
                -- 从请求体中提取Token相关信息
                if data.messages then
                    -- OpenAI格式
                    for _, message in ipairs(data.messages) do
                        if message.content then
                            tokens = tokens + get_precise_tokens(message.content, model_name)
                        end
                    end
                elseif data.prompt then
                    -- 其他格式
                    tokens = tokens + get_precise_tokens(data.prompt, model_name)
                end
                
                -- 如果有max_tokens字段，也计入
                if data.max_tokens then
                    tokens = tokens + tonumber(data.max_tokens) or 0
                end
            end
        end
    end
    
    return math.floor(tokens)
end

-- 检查Token限制
local function check_token_limit(namespace_id, rule_config)
    local current_tokens = get_request_tokens()
    if current_tokens <= 0 then
        return true  -- 没有Token消耗，直接通过
    end
    
    -- 获取时间窗口
    local window_size = rule_config.window_size or 3600  -- 默认1小时
    local current_time = ngx.time()
    local window_start = math.floor(current_time / window_size) * window_size
    
    -- 构建计数器键（使用新的格式，支持配置变更重置）
    local counter_key = string.format("rate_limit:%d:token:%d", namespace_id, window_start)
    
    -- 获取当前Token使用量
    local current_usage, err = rate_limiter.get_counter(counter_key)
    if err then
        ngx.log(ngx.ERR, "Failed to get token usage: ", err)
        return false, "Failed to check token limit"
    end
    
    current_usage = current_usage or 0
    
    -- 检查是否超限
    local max_tokens = rule_config.max_tokens_per_hour or rule_config.max_tokens_per_window
    if current_usage + current_tokens > max_tokens then
        ngx.log(ngx.WARN, "Token limit exceeded for namespace ", namespace_id, 
                ": current=", current_usage, ", request=", current_tokens, ", limit=", max_tokens)
        return false, "Token limit exceeded"
    end
    
    -- 增加Token使用量
    local ok, err = rate_limiter.increment_counter(counter_key, current_tokens, window_size)
    if not ok then
        ngx.log(ngx.ERR, "Failed to increment token usage: ", err)
        return false, "Failed to update token usage"
    end
    
    return true
end

-- 检查并发连接数限制
local function check_connection_limit(namespace_id, rule_config)
    local max_connections = rule_config.max_connections or 1000
    local window_size = rule_config.window_size or 3600
    
    -- 构建计数器键
    local current_time = ngx.time()
    local window_start = math.floor(current_time / window_size) * window_size
    local counter_key = string.format("connection_limit:%d:%d:%d", namespace_id, window_size, window_start)
    
    -- 获取当前连接数
    local current_connections, err = rate_limiter.get_counter(counter_key)
    if err then
        ngx.log(ngx.ERR, "Failed to get connection count: ", err)
        return false, "Failed to check connection limit"
    end
    
    current_connections = current_connections or 0
    
    -- 检查是否超限
    if current_connections >= max_connections then
        ngx.log(ngx.WARN, "Connection limit exceeded for namespace ", namespace_id,
                ": current=", current_connections, ", limit=", max_connections)
        return false, "Connection limit exceeded"
    end
    
    -- 增加连接数
    local ok, err = rate_limiter.increment_counter(counter_key, 1, window_size)
    if not ok then
        ngx.log(ngx.ERR, "Failed to increment connection count: ", err)
        return false, "Failed to update connection count"
    end
    
    return true
end

-- 检查请求频率限制
local function check_request_limit(namespace_id, rule_config)
    local max_requests_per_minute = rule_config.max_requests_per_minute or 100
    local max_requests_per_hour = rule_config.max_requests_per_hour or 5000
    
    local current_time = ngx.time()
    
    -- 检查每分钟限制（使用新的格式，支持配置变更重置）
    local minute_window = math.floor(current_time / 60) * 60
    local minute_key = string.format("rate_limit:%d:qps:%d", namespace_id, minute_window)
    
    local minute_requests, err = rate_limiter.get_counter(minute_key)
    if err then
        ngx.log(ngx.ERR, "Failed to get minute request count: ", err)
        return false, "Failed to check request limit"
    end
    
    minute_requests = minute_requests or 0
    if minute_requests >= max_requests_per_minute then
        ngx.log(ngx.WARN, "Minute request limit exceeded for namespace ", namespace_id,
                ": current=", minute_requests, ", limit=", max_requests_per_minute)
        return false, "Request rate limit exceeded"
    end
    
    -- 检查每小时限制（使用新的格式，支持配置变更重置）
    local hour_window = math.floor(current_time / 3600) * 3600
    local hour_key = string.format("rate_limit:%d:qps:%d", namespace_id, hour_window)
    
    local hour_requests, err = rate_limiter.get_counter(hour_key)
    if err then
        ngx.log(ngx.ERR, "Failed to get hour request count: ", err)
        return false, "Failed to check request limit"
    end
    
    hour_requests = hour_requests or 0
    if hour_requests >= max_requests_per_hour then
        ngx.log(ngx.WARN, "Hour request limit exceeded for namespace ", namespace_id,
                ": current=", hour_requests, ", limit=", max_requests_per_hour)
        return false, "Request rate limit exceeded"
    end
    
    -- 增加请求计数
    local ok, err = rate_limiter.increment_counter(minute_key, 1, 60)
    if not ok then
        ngx.log(ngx.ERR, "Failed to increment minute request count: ", err)
        return false, "Failed to update request count"
    end
    
    ok, err = rate_limiter.increment_counter(hour_key, 1, 3600)
    if not ok then
        ngx.log(ngx.ERR, "Failed to increment hour request count: ", err)
        return false, "Failed to update request count"
    end
    
    return true
end

-- 检查字段验证
local function check_field_validation(namespace_id, rule_config)
    local field_path = rule_config.field_path
    local operator = rule_config.operator
    local expected_value = rule_config.value
    
    if not field_path then
        return true  -- 没有字段路径，跳过检查
    end
    
    -- 解析请求体
    local content_type = ngx.var.content_type or ""
    local field_value
    
    if string.find(content_type, "application/json") then
        ngx.req.read_body()
        local body = ngx.req.get_body_data()
        if body then
            local ok, data = pcall(cjson.decode, body)
            if ok and data then
                -- 解析字段路径
                local fields = {}
                for field in string.gmatch(field_path, "[^.]+") do
                    table.insert(fields, field)
                end
                
                local current = data
                for _, field in ipairs(fields) do
                    if type(current) == "table" then
                        current = current[field]
                    else
                        current = nil
                        break
                    end
                end
                
                field_value = current
            end
        end
    end
    
    if field_value == nil then
        return false, "Required field not found: " .. field_path
    end
    
    -- 执行验证
    local valid = false
    if operator == "eq" then
        valid = tostring(field_value) == tostring(expected_value)
    elseif operator == "ne" then
        valid = tostring(field_value) ~= tostring(expected_value)
    elseif operator == "gt" then
        valid = tonumber(field_value) and tonumber(expected_value) and tonumber(field_value) > tonumber(expected_value)
    elseif operator == "gte" then
        valid = tonumber(field_value) and tonumber(expected_value) and tonumber(field_value) >= tonumber(expected_value)
    elseif operator == "lt" then
        valid = tonumber(field_value) and tonumber(expected_value) and tonumber(field_value) < tonumber(expected_value)
    elseif operator == "lte" then
        valid = tonumber(field_value) and tonumber(expected_value) and tonumber(field_value) <= tonumber(expected_value)
    elseif operator == "contains" then
        valid = string.find(tostring(field_value), tostring(expected_value), 1, true) ~= nil
    else
        ngx.log(ngx.WARN, "Unknown field validation operator: ", operator)
        return true  -- 未知操作符，跳过检查
    end
    
    if not valid then
        local message = rule_config.message or string.format("Field validation failed: %s %s %s", field_path, operator, expected_value)
        return false, message
    end
    
    return true
end

-- 检查命名空间规则
function _M.check_namespace_rules(namespace_id)
    -- 获取命名空间的规则
    local rules, err = config_cache.get_namespace_rules(namespace_id)
    if err then
        ngx.log(ngx.ERR, "Failed to get rules for namespace ", namespace_id, ": ", err)
        return false, "Failed to get rules"
    end
    
    -- 如果没有规则，直接通过
    if not rules or #rules == 0 then
        return true
    end
    
    -- 按优先级排序规则
    table.sort(rules, function(a, b)
        return (a.priority or 0) > (b.priority or 0)
    end)
    
    -- 检查每个规则
    for _, rule in ipairs(rules) do
        if rule.status == 1 then  -- 只检查启用的规则
            local rule_config = rule.rule_config
            if type(rule_config) == "string" then
                local ok, data = pcall(cjson.decode, rule_config)
                if ok then
                    rule_config = data
                else
                    ngx.log(ngx.ERR, "Failed to parse rule config for rule ", rule.rule_id)
                    return false, "Invalid rule configuration"
                end
            end
            
            local passed, error_msg
            
            if rule.rule_type == rule_types.token_limit then
                passed, error_msg = check_token_limit(namespace_id, rule_config)
            elseif rule.rule_type == rule_types.connection_limit then
                passed, error_msg = check_connection_limit(namespace_id, rule_config)
            elseif rule.rule_type == rule_types.request_limit then
                passed, error_msg = check_request_limit(namespace_id, rule_config)
            elseif rule.rule_type == rule_types.field_check then
                passed, error_msg = check_field_validation(namespace_id, rule_config)
            else
                ngx.log(ngx.WARN, "Unknown rule type: ", rule.rule_type)
                passed = true  -- 未知规则类型，跳过
            end
            
            if not passed then
                ngx.log(ngx.WARN, "Rule check failed for rule ", rule.rule_id, ": ", error_msg)
                return false, error_msg
            end
        end
    end
    
    return true
end

-- 获取规则统计
function _M.get_rule_stats(namespace_id)
    local stats = {
        total_checks = 0,
        passed_checks = 0,
        failed_checks = 0,
        rule_stats = {}
    }
    
    -- 从共享内存获取统计信息
    local metrics_dict = ngx.shared.metrics
    if metrics_dict then
        local prefix = "rule_check:" .. namespace_id .. ":"
        stats.total_checks = metrics_dict:get(prefix .. "total") or 0
        stats.passed_checks = metrics_dict:get(prefix .. "passed") or 0
        stats.failed_checks = metrics_dict:get(prefix .. "failed") or 0
    end
    
    return stats
end

-- 更新规则检查统计
function _M.update_rule_stats(namespace_id, passed)
    local metrics_dict = ngx.shared.metrics
    if not metrics_dict then
        return
    end
    
    local prefix = "rule_check:" .. namespace_id .. ":"
    
    -- 更新总检查数
    metrics_dict:incr(prefix .. "total", 1)
    
    -- 更新检查结果统计
    if passed then
        metrics_dict:incr(prefix .. "passed", 1)
    else
        metrics_dict:incr(prefix .. "failed", 1)
    end
end

return _M 