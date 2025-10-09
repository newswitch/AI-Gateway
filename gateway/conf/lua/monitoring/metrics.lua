-- 监控指标模块
-- 支持多实例部署，使用 Redis 存储指标
-- 每个实例独立记录，Prometheus 从所有实例拉取

local json = require "utils.json"
local redis = require "utils.redis"
local cjson = require "cjson"

local _M = {}

-- Redis 键前缀
local METRICS_PREFIX = "metrics:"
local GLOBAL_KEY = METRICS_PREFIX .. "global"
local NAMESPACE_PREFIX = METRICS_PREFIX .. "ns:"
local INSTANCE_PREFIX = METRICS_PREFIX .. "instance:"

-- 获取实例ID（基于容器ID或随机生成）
local function get_instance_id()
    local instance_id = ngx.var.hostname or "unknown"
    return instance_id
end

-- 获取namespace_code
local function get_namespace_code(namespace_id)
    if not namespace_id then
        return nil
    end
    
    local cache = require "config.cache"
    local configs = cache.get_all_configs()
    local namespaces = configs.namespaces or {}
    
    -- 转换namespace_id为数字类型进行比较
    local target_id = tonumber(namespace_id)
    
    for _, namespace in ipairs(namespaces) do
        if namespace.namespace_id == target_id then
            return namespace.namespace_code
        end
    end
    
    -- 如果没找到namespace_code，使用namespace_id作为备选
    return tostring(namespace_id)
end

-- 从namespace_code获取namespace_id
local function get_namespace_id_by_code(namespace_code)
    if not namespace_code then
        return nil
    end
    
    local cache = require "config.cache"
    local configs = cache.get_all_configs()
    local namespaces = configs.namespaces or {}
    
    for _, namespace in ipairs(namespaces) do
        if namespace.namespace_code == tostring(namespace_code) then
            return namespace.namespace_id
        end
    end
    
    -- 如果没找到，尝试将namespace_code转换为数字（兼容旧数据）
    local id = tonumber(namespace_code)
    if id then
        return id
    end
    
    return nil
end

-- 记录请求指标
function _M.record_request(namespace_id, request_info, status, response_time)
    if not namespace_id then
        return
    end
    
    local instance_id = get_instance_id()
    local current_time = ngx.time()
    local namespace_code = get_namespace_code(namespace_id)
    local namespace_key = NAMESPACE_PREFIX .. namespace_code
    local instance_key = INSTANCE_PREFIX .. instance_id .. ":" .. namespace_code
    
    -- 使用 Redis 原子操作更新指标
    local redis_client = redis.get_connection()
    if not redis_client then
        ngx.log(ngx.ERR, "Failed to get Redis client for metrics")
        return
    end
    
    -- 更新命名空间指标 - 使用单独的Redis命令
    local function safe_redis_command(command, ...)
        local result, err = redis_client[command](redis_client, ...)
        if not result then
            ngx.log(ngx.ERR, "Redis command failed: ", command, " - ", err)
        end
        return result
    end
    
    -- 增加总请求数
    safe_redis_command("incr", namespace_key .. ":total_requests")
    safe_redis_command("incr", GLOBAL_KEY .. ":total_requests")
    
    -- 更新成功/失败请求数
    if status >= 200 and status < 400 then
        safe_redis_command("incr", namespace_key .. ":successful_requests")
    else
        safe_redis_command("incr", namespace_key .. ":failed_requests")
        safe_redis_command("incr", GLOBAL_KEY .. ":total_errors")
    end
    
    -- 更新响应时间
    if response_time then
        safe_redis_command("incrbyfloat", namespace_key .. ":total_response_time", response_time)
        safe_redis_command("incrbyfloat", GLOBAL_KEY .. ":total_response_time", response_time)
    end
    
    -- 更新状态码计数
    local status_key = tostring(status)
    safe_redis_command("incr", namespace_key .. ":status:" .. status_key)
    
    -- 记录流式/非流式请求统计
    if request_info and request_info.body then
        local json = require "utils.json"
        local body_data, err = json.decode(request_info.body)
        if body_data and body_data.stream then
            -- 流式请求
            safe_redis_command("incr", namespace_key .. ":streaming_requests")
            safe_redis_command("incr", GLOBAL_KEY .. ":streaming_requests")
        else
            -- 非流式请求
            safe_redis_command("incr", namespace_key .. ":non_streaming_requests")
            safe_redis_command("incr", GLOBAL_KEY .. ":non_streaming_requests")
        end
    end
    
    -- 记录用户访问统计（基于Authorization头或用户标识）
    if request_info and request_info.headers then
        local auth_header = request_info.headers["Authorization"] or request_info.headers["authorization"]
        if auth_header then
            -- 使用Authorization头的前8位作为用户标识
            local user_id = string.sub(auth_header, 1, 8)
            safe_redis_command("sadd", namespace_key .. ":unique_users", user_id)
            safe_redis_command("sadd", GLOBAL_KEY .. ":unique_users", user_id)
            safe_redis_command("expire", namespace_key .. ":unique_users", 86400) -- 24小时过期
            safe_redis_command("expire", GLOBAL_KEY .. ":unique_users", 86400)
        end
    end
    
    -- 更新最后请求时间
    safe_redis_command("set", namespace_key .. ":last_request_time", current_time)
    safe_redis_command("set", GLOBAL_KEY .. ":last_request_time", current_time)
    
    -- 设置实例级别的指标（用于实例健康检查）
    safe_redis_command("hset", instance_key, "last_request_time", current_time)
    safe_redis_command("hset", instance_key, "status", "active")
    safe_redis_command("expire", instance_key, 300) -- 5分钟过期
end

-- 记录Token使用量
function _M.record_token_usage(namespace_id, model_name, token_count, request_info, token_type)
    if not namespace_id or not token_count or token_count <= 0 then
        return
    end
    
    local namespace_code = get_namespace_code(namespace_id)
    local namespace_key = NAMESPACE_PREFIX .. namespace_code
    local model_key = namespace_key .. ":model:" .. (model_name or "unknown")
    
    local redis_client = redis.get_connection()
    if not redis_client then
        ngx.log(ngx.ERR, "Failed to get Redis client for token metrics")
        return
    end
    
    local function safe_redis_command(command, ...)
        local result, err = redis_client[command](redis_client, ...)
        if not result then
            ngx.log(ngx.ERR, "Redis command failed: ", command, " - ", err)
        end
        return result
    end
    
    -- 记录命名空间总Token使用量
    safe_redis_command("incrby", namespace_key .. ":total_tokens", token_count)
    safe_redis_command("incrby", GLOBAL_KEY .. ":total_tokens", token_count)
    
    -- 记录输入/输出Token分别统计
    local token_type_key = token_type or "input"
    safe_redis_command("incrby", namespace_key .. ":" .. token_type_key .. "_tokens", token_count)
    safe_redis_command("incrby", GLOBAL_KEY .. ":" .. token_type_key .. "_tokens", token_count)
    
    -- 记录模型Token使用量
    safe_redis_command("incrby", model_key .. ":" .. token_type_key .. "_tokens", token_count)
    safe_redis_command("incrby", model_key .. ":requests", 1)
    
    -- 记录路由Token使用量（如果有路由信息）
    if request_info and request_info.path then
        local route_key = namespace_key .. ":route:" .. request_info.path
        safe_redis_command("incrby", route_key .. ":" .. token_type_key .. "_tokens", token_count)
        safe_redis_command("incrby", route_key .. ":requests", 1)
        safe_redis_command("expire", route_key .. ":" .. token_type_key .. "_tokens", 86400) -- 24小时过期
        safe_redis_command("expire", route_key .. ":requests", 86400)
    end
    
    -- 设置过期时间
    safe_redis_command("expire", model_key .. ":" .. token_type_key .. "_tokens", 86400) -- 24小时过期
    safe_redis_command("expire", model_key .. ":requests", 86400)
end

-- 记录策略限制触发
function _M.record_policy_violation(namespace_id, policy_type, policy_name)
    if not namespace_id or not policy_type then
        return
    end
    
    local namespace_code = get_namespace_code(namespace_id)
    local namespace_key = NAMESPACE_PREFIX .. namespace_code
    
    local redis_client = redis.get_connection()
    if not redis_client then
        ngx.log(ngx.ERR, "Failed to get Redis client for policy metrics")
        return
    end
    
    local function safe_redis_command(command, ...)
        local result, err = redis_client[command](redis_client, ...)
        if not result then
            ngx.log(ngx.ERR, "Redis command failed: ", command, " - ", err)
        end
        return result
    end
    
    -- 记录策略限制触发总数
    safe_redis_command("incr", namespace_key .. ":policy_violations")
    safe_redis_command("incr", GLOBAL_KEY .. ":policy_violations")
    
    -- 记录按策略类型分类的限制触发
    safe_redis_command("incr", namespace_key .. ":policy_violations:" .. policy_type)
    safe_redis_command("incr", GLOBAL_KEY .. ":policy_violations:" .. policy_type)
    
    -- 记录具体策略的限制触发
    if policy_name then
        safe_redis_command("incr", namespace_key .. ":policy_violations:" .. policy_type .. ":" .. policy_name)
        safe_redis_command("incr", GLOBAL_KEY .. ":policy_violations:" .. policy_type .. ":" .. policy_name)
    end
    
    -- 设置过期时间
    safe_redis_command("expire", namespace_key .. ":policy_violations", 86400) -- 24小时过期
    safe_redis_command("expire", GLOBAL_KEY .. ":policy_violations", 86400)
end

-- 记录路由使用次数
function _M.record_route_usage(namespace_id, request_info, status)
    if not namespace_id or not request_info or not request_info.path then
        return
    end
    
    local namespace_code = get_namespace_code(namespace_id)
    local namespace_key = NAMESPACE_PREFIX .. namespace_code
    local route_key = namespace_key .. ":route:" .. request_info.path
    
    local redis_client = redis.get_connection()
    if not redis_client then
        ngx.log(ngx.ERR, "Failed to get Redis client for route metrics")
        return
    end
    
    local function safe_redis_command(command, ...)
        local result, err = redis_client[command](redis_client, ...)
        if not result then
            ngx.log(ngx.ERR, "Redis command failed: ", command, " - ", err)
        end
        return result
    end
    
    -- 记录路由总请求数
    safe_redis_command("incr", route_key .. ":total_requests")
    
    -- 记录路由状态码
    if status then
        local status_key = tostring(status)
        safe_redis_command("incr", route_key .. ":status:" .. status_key)
    end
    
    -- 记录路由最后使用时间
    safe_redis_command("set", route_key .. ":last_used", ngx.time())
    
    -- 设置过期时间
    safe_redis_command("expire", route_key .. ":total_requests", 86400) -- 24小时过期
    safe_redis_command("expire", route_key .. ":last_used", 86400)
end

-- 增加并发请求计数
function _M.incr_concurrent_requests(namespace_id)
    if not namespace_id then
        return
    end
    
    local instance_id = get_instance_id()
    local namespace_code = get_namespace_code(namespace_id)
    local namespace_key = NAMESPACE_PREFIX .. namespace_code
    local instance_key = INSTANCE_PREFIX .. instance_id .. ":" .. namespace_code
    
    local redis_client = redis.get_connection()
    if not redis_client then
        return
    end
    
    local pipeline = redis_client:pipeline()
    pipeline:incr(namespace_key .. ":concurrent_requests")
    pipeline:hset(instance_key, "concurrent_requests", 
        (redis_client:get(namespace_key .. ":concurrent_requests") or 0) + 1)
    pipeline:expire(instance_key, 300)
    
    pipeline:exec()
end

-- 减少并发请求计数
function _M.decr_concurrent_requests(namespace_id)
    if not namespace_id then
        return
    end
    
    local instance_id = get_instance_id()
    local namespace_code = get_namespace_code(namespace_id)
    local namespace_key = NAMESPACE_PREFIX .. namespace_code
    local instance_key = INSTANCE_PREFIX .. instance_id .. ":" .. namespace_code
    
    local redis_client = redis.get_connection()
    if not redis_client then
        return
    end
    
    local pipeline = redis_client:pipeline()
    pipeline:decr(namespace_key .. ":concurrent_requests")
    pipeline:hset(instance_key, "concurrent_requests", 
        math.max(0, (redis_client:get(namespace_key .. ":concurrent_requests") or 0) - 1))
    pipeline:expire(instance_key, 300)
    
    pipeline:exec()
end

-- 获取命名空间指标
function _M.get_namespace_metrics(namespace_id)
    if not namespace_id then
        return {
            total_requests = 0,
            successful_requests = 0,
            failed_requests = 0,
            average_response_time = 0,
            status_codes = {},
            concurrent_requests = 0,
            uptime = 0,
            last_request_time = 0
        }
    end
    
    local redis_client = redis.get_connection()
    if not redis_client then
        return {
            total_requests = 0,
            successful_requests = 0,
            failed_requests = 0,
            average_response_time = 0,
            status_codes = {},
            concurrent_requests = 0,
            uptime = 0,
            last_request_time = 0
        }
    end
    
    local namespace_code = get_namespace_code(namespace_id)
    local namespace_key = NAMESPACE_PREFIX .. namespace_code
    
    -- 获取基础指标
    local total_requests = tonumber(redis_client:get(namespace_key .. ":total_requests")) or 0
    local successful_requests = tonumber(redis_client:get(namespace_key .. ":successful_requests")) or 0
    local failed_requests = tonumber(redis_client:get(namespace_key .. ":failed_requests")) or 0
    local total_response_time = tonumber(redis_client:get(namespace_key .. ":total_response_time")) or 0
    local concurrent_requests = tonumber(redis_client:get(namespace_key .. ":concurrent_requests")) or 0
    local last_request_time = tonumber(redis_client:get(namespace_key .. ":last_request_time")) or 0
    
    -- 计算平均响应时间
    local avg_response_time = 0
    if total_requests > 0 and total_response_time > 0 then
        avg_response_time = total_response_time / total_requests
    end
    
    -- 获取状态码统计
    local status_codes = {}
    local status_keys = redis_client:keys(namespace_key .. ":status:*")
    for _, key in ipairs(status_keys) do
        local status_code = key:match(":status:(.+)")
        if status_code then
            local count = tonumber(redis_client:get(key)) or 0
            status_codes[status_code] = count
        end
    end
    
    -- 计算运行时间（从第一次请求开始）
    local uptime = 0
    if last_request_time > 0 then
        uptime = ngx.time() - last_request_time
    end
    
    return {
        total_requests = total_requests,
        successful_requests = successful_requests,
        failed_requests = failed_requests,
        average_response_time = avg_response_time,
        status_codes = status_codes,
        concurrent_requests = concurrent_requests,
        uptime = uptime,
        last_request_time = last_request_time
    }
end

-- 获取全局指标
function _M.get_global_metrics()
    local redis_client = redis.get_connection()
    if not redis_client then
        return {
            total_requests = 0,
            total_errors = 0,
            average_response_time = 0,
            uptime = 0
        }
    end
    
    local total_requests = tonumber(redis_client:get(GLOBAL_KEY .. ":total_requests")) or 0
    local total_errors = tonumber(redis_client:get(GLOBAL_KEY .. ":total_errors")) or 0
    local total_response_time = tonumber(redis_client:get(GLOBAL_KEY .. ":total_response_time")) or 0
    local last_request_time = tonumber(redis_client:get(GLOBAL_KEY .. ":last_request_time")) or 0
    
    -- 计算平均响应时间
    local avg_response_time = 0
    if total_requests > 0 and total_response_time > 0 then
        avg_response_time = total_response_time / total_requests
    end
    
    -- 计算运行时间
    local uptime = 0
    if last_request_time > 0 then
        uptime = ngx.time() - last_request_time
    end
    
    return {
        total_requests = total_requests,
        total_errors = total_errors,
        average_response_time = avg_response_time,
        uptime = uptime
    }
end

-- 获取所有命名空间指标
function _M.get_all_namespace_metrics()
    local result = {}
    local redis_client = redis.get_connection()
    if not redis_client then
        return result
    end
    
    -- 获取所有命名空间键
    local namespace_keys = redis_client:keys(NAMESPACE_PREFIX .. "*:total_requests")
    for _, key in ipairs(namespace_keys) do
        local namespace_code = key:match(NAMESPACE_PREFIX .. "(.+):total_requests")
        if namespace_code then
            -- 从namespace_code反推namespace_id
            local namespace_id = get_namespace_id_by_code(namespace_code)
            if namespace_id then
                result[namespace_id] = _M.get_namespace_metrics(namespace_id)
            end
        end
    end
    
    return result
end

-- 获取命名空间Token使用统计
function _M.get_namespace_token_usage(namespace_id)
    if not namespace_id then
        return {}
    end
    
    local namespace_code = get_namespace_code(namespace_id)
    local namespace_key = NAMESPACE_PREFIX .. namespace_code
    
    local redis_client = redis.get_connection()
    if not redis_client then
        return {}
    end
    
    local result = {
        total_tokens = 0,
        models = {},
        routes = {}
    }
    
    -- 获取总Token使用量
    result.total_tokens = tonumber(redis_client:get(namespace_key .. ":total_tokens")) or 0
    
    -- 获取模型Token使用量
    local model_keys = redis_client:keys(namespace_key .. ":model:*:tokens")
    for _, key in ipairs(model_keys) do
        local model_name = key:match(":model:(.+):tokens")
        if model_name then
            local tokens = tonumber(redis_client:get(key)) or 0
            local requests = tonumber(redis_client:get(namespace_key .. ":model:" .. model_name .. ":requests")) or 0
            result.models[model_name] = {
                tokens = tokens,
                requests = requests
            }
        end
    end
    
    -- 获取路由Token使用量
    local route_keys = redis_client:keys(namespace_key .. ":route:*:tokens")
    for _, key in ipairs(route_keys) do
        local route_path = key:match(":route:(.+):tokens")
        if route_path then
            local tokens = tonumber(redis_client:get(key)) or 0
            local requests = tonumber(redis_client:get(namespace_key .. ":route:" .. route_path .. ":requests")) or 0
            result.routes[route_path] = {
                tokens = tokens,
                requests = requests
            }
        end
    end
    
    return result
end

-- 获取命名空间路由使用统计
function _M.get_namespace_route_usage(namespace_id)
    if not namespace_id then
        return {}
    end
    
    local namespace_code = get_namespace_code(namespace_id)
    local namespace_key = NAMESPACE_PREFIX .. namespace_code
    
    local redis_client = redis.get_connection()
    if not redis_client then
        return {}
    end
    
    local result = {}
    
    -- 获取路由使用统计
    local route_keys = redis_client:keys(namespace_key .. ":route:*:total_requests")
    for _, key in ipairs(route_keys) do
        local route_path = key:match(":route:(.+):total_requests")
        if route_path then
            local total_requests = tonumber(redis_client:get(key)) or 0
            local last_used = tonumber(redis_client:get(namespace_key .. ":route:" .. route_path .. ":last_used")) or 0
            
            result[route_path] = {
                total_requests = total_requests,
                last_used = last_used,
                status_codes = {}
            }
            
            -- 获取状态码统计
            local status_keys = redis_client:keys(namespace_key .. ":route:" .. route_path .. ":status:*")
            for _, status_key in ipairs(status_keys) do
                local status_code = status_key:match(":status:(.+)")
                if status_code then
                    local count = tonumber(redis_client:get(status_key)) or 0
                    result[route_path].status_codes[status_code] = count
                end
            end
        end
    end
    
    return result
end

-- 获取实例健康状态
function _M.get_instance_health()
    local result = {}
    local redis_client = redis.get_connection()
    if not redis_client then
        return result
    end
    
    local instance_keys = redis_client:keys(INSTANCE_PREFIX .. "*")
    for _, key in ipairs(instance_keys) do
        local instance_id = key:match(INSTANCE_PREFIX .. "(.+):")
        if instance_id then
            local health_data = redis_client:hgetall(key)
            result[instance_id] = {
                status = health_data.status or "unknown",
                last_request_time = tonumber(health_data.last_request_time) or 0,
                concurrent_requests = tonumber(health_data.concurrent_requests) or 0
            }
        end
    end
    
    return result
end

-- 生成 Prometheus 格式的指标
function _M.get_prometheus_metrics()
    local lines = {}
    local instance_id = get_instance_id()
    
    -- 全局指标
    local global_metrics = _M.get_global_metrics()
    table.insert(lines, "# HELP ai_gateway_requests_total Total number of requests")
    table.insert(lines, "# TYPE ai_gateway_requests_total counter")
    table.insert(lines, "ai_gateway_requests_total " .. (global_metrics.total_requests or 0))
    
    table.insert(lines, "# HELP ai_gateway_errors_total Total number of errors")
    table.insert(lines, "# TYPE ai_gateway_errors_total counter")
    table.insert(lines, "ai_gateway_errors_total " .. (global_metrics.total_errors or 0))
    
    table.insert(lines, "# HELP ai_gateway_response_time_seconds Average response time in seconds")
    table.insert(lines, "# TYPE ai_gateway_response_time_seconds gauge")
    table.insert(lines, "ai_gateway_response_time_seconds " .. string.format("%.4f", global_metrics.average_response_time or 0))
    
    table.insert(lines, "# HELP ai_gateway_uptime_seconds Gateway uptime in seconds")
    table.insert(lines, "# TYPE ai_gateway_uptime_seconds gauge")
    table.insert(lines, "ai_gateway_uptime_seconds " .. (global_metrics.uptime or 0))
    
    -- 全局Token使用量
    local redis_client = redis.get_connection()
    if redis_client then
        local global_tokens = tonumber(redis_client:get(GLOBAL_KEY .. ":total_tokens")) or 0
        local global_input_tokens = tonumber(redis_client:get(GLOBAL_KEY .. ":input_tokens")) or 0
        local global_output_tokens = tonumber(redis_client:get(GLOBAL_KEY .. ":output_tokens")) or 0
        local global_streaming_requests = tonumber(redis_client:get(GLOBAL_KEY .. ":streaming_requests")) or 0
        local global_non_streaming_requests = tonumber(redis_client:get(GLOBAL_KEY .. ":non_streaming_requests")) or 0
        local global_policy_violations = tonumber(redis_client:get(GLOBAL_KEY .. ":policy_violations")) or 0
        local global_unique_users = redis_client:scard(GLOBAL_KEY .. ":unique_users") or 0
        
        table.insert(lines, "# HELP ai_gateway_total_tokens Total token usage")
        table.insert(lines, "# TYPE ai_gateway_total_tokens counter")
        table.insert(lines, "ai_gateway_total_tokens " .. global_tokens)
        
        table.insert(lines, "# HELP ai_gateway_input_tokens_total Total input token usage")
        table.insert(lines, "# TYPE ai_gateway_input_tokens_total counter")
        table.insert(lines, "ai_gateway_input_tokens_total " .. global_input_tokens)
        
        table.insert(lines, "# HELP ai_gateway_output_tokens_total Total output token usage")
        table.insert(lines, "# TYPE ai_gateway_output_tokens_total counter")
        table.insert(lines, "ai_gateway_output_tokens_total " .. global_output_tokens)
        
        table.insert(lines, "# HELP ai_gateway_streaming_requests_total Total streaming requests")
        table.insert(lines, "# TYPE ai_gateway_streaming_requests_total counter")
        table.insert(lines, "ai_gateway_streaming_requests_total " .. global_streaming_requests)
        
        table.insert(lines, "# HELP ai_gateway_non_streaming_requests_total Total non-streaming requests")
        table.insert(lines, "# TYPE ai_gateway_non_streaming_requests_total counter")
        table.insert(lines, "ai_gateway_non_streaming_requests_total " .. global_non_streaming_requests)
        
        table.insert(lines, "# HELP ai_gateway_policy_violations_total Total policy violations")
        table.insert(lines, "# TYPE ai_gateway_policy_violations_total counter")
        table.insert(lines, "ai_gateway_policy_violations_total " .. global_policy_violations)
        
        table.insert(lines, "# HELP ai_gateway_unique_users_total Total unique users")
        table.insert(lines, "# TYPE ai_gateway_unique_users_total gauge")
        table.insert(lines, "ai_gateway_unique_users_total " .. global_unique_users)
    end
    
    -- 命名空间指标
    local namespace_metrics = _M.get_all_namespace_metrics()
    for namespace_id, metrics in pairs(namespace_metrics) do
        -- 获取namespace_code用于标签
        local namespace_code = get_namespace_code(namespace_id)
        
        table.insert(lines, "# HELP ai_gateway_namespace_requests_total Total number of requests per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_requests_total counter")
        table.insert(lines, string.format("ai_gateway_namespace_requests_total{namespace_code=\"%s\"} %d", 
            namespace_code, metrics.total_requests or 0))
        
        table.insert(lines, "# HELP ai_gateway_namespace_concurrent_requests Current number of concurrent requests per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_concurrent_requests gauge")
        table.insert(lines, string.format("ai_gateway_namespace_concurrent_requests{namespace_code=\"%s\"} %d", 
            namespace_code, metrics.concurrent_requests or 0))
        
        table.insert(lines, "# HELP ai_gateway_namespace_response_time_seconds Average response time per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_response_time_seconds gauge")
        table.insert(lines, string.format("ai_gateway_namespace_response_time_seconds{namespace_code=\"%s\"} %.4f", 
            namespace_code, metrics.average_response_time or 0))
        
        -- 状态码指标
        for status_code, count in pairs(metrics.status_codes or {}) do
            table.insert(lines, "# HELP ai_gateway_namespace_status_codes_total Total number of requests by status code per namespace")
            table.insert(lines, "# TYPE ai_gateway_namespace_status_codes_total counter")
            table.insert(lines, string.format("ai_gateway_namespace_status_codes_total{namespace_code=\"%s\",status_code=\"%s\"} %d",
                namespace_code, status_code, count or 0))
        end
        
        -- Token使用量指标
        local token_usage = _M.get_namespace_token_usage(namespace_id)
        table.insert(lines, "# HELP ai_gateway_namespace_tokens_total Total token usage per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_tokens_total counter")
        table.insert(lines, string.format("ai_gateway_namespace_tokens_total{namespace_code=\"%s\"} %d", 
            namespace_code, token_usage.total_tokens or 0))
        
        -- 输入/输出Token分别统计
        local input_tokens = tonumber(redis_client:get(NAMESPACE_PREFIX .. namespace_code .. ":input_tokens")) or 0
        local output_tokens = tonumber(redis_client:get(NAMESPACE_PREFIX .. namespace_code .. ":output_tokens")) or 0
        table.insert(lines, "# HELP ai_gateway_namespace_input_tokens_total Input token usage per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_input_tokens_total counter")
        table.insert(lines, string.format("ai_gateway_namespace_input_tokens_total{namespace_code=\"%s\"} %d", 
            namespace_code, input_tokens))
        
        table.insert(lines, "# HELP ai_gateway_namespace_output_tokens_total Output token usage per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_output_tokens_total counter")
        table.insert(lines, string.format("ai_gateway_namespace_output_tokens_total{namespace_code=\"%s\"} %d", 
            namespace_code, output_tokens))
        
        -- 流式/非流式请求统计
        local streaming_requests = tonumber(redis_client:get(NAMESPACE_PREFIX .. namespace_code .. ":streaming_requests")) or 0
        local non_streaming_requests = tonumber(redis_client:get(NAMESPACE_PREFIX .. namespace_code .. ":non_streaming_requests")) or 0
        table.insert(lines, "# HELP ai_gateway_namespace_streaming_requests_total Streaming requests per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_streaming_requests_total counter")
        table.insert(lines, string.format("ai_gateway_namespace_streaming_requests_total{namespace_code=\"%s\"} %d", 
            namespace_code, streaming_requests))
        
        table.insert(lines, "# HELP ai_gateway_namespace_non_streaming_requests_total Non-streaming requests per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_non_streaming_requests_total counter")
        table.insert(lines, string.format("ai_gateway_namespace_non_streaming_requests_total{namespace_code=\"%s\"} %d", 
            namespace_code, non_streaming_requests))
        
        -- 用户访问量统计
        local unique_users = redis_client:scard(NAMESPACE_PREFIX .. namespace_code .. ":unique_users") or 0
        table.insert(lines, "# HELP ai_gateway_namespace_unique_users_total Unique users per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_unique_users_total gauge")
        table.insert(lines, string.format("ai_gateway_namespace_unique_users_total{namespace_code=\"%s\"} %d", 
            namespace_code, unique_users))
        
        -- 策略限制触发统计
        local policy_violations = tonumber(redis_client:get(NAMESPACE_PREFIX .. namespace_code .. ":policy_violations")) or 0
        table.insert(lines, "# HELP ai_gateway_namespace_policy_violations_total Policy violations per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_policy_violations_total counter")
        table.insert(lines, string.format("ai_gateway_namespace_policy_violations_total{namespace_code=\"%s\"} %d", 
            namespace_code, policy_violations))
        
        -- 按策略类型分类的限制触发
        local policy_types = {"concurrency-limit", "token-limit", "qps-limit", "message-matching"}
        for _, policy_type in ipairs(policy_types) do
            local violations = tonumber(redis_client:get(NAMESPACE_PREFIX .. namespace_code .. ":policy_violations:" .. policy_type)) or 0
            table.insert(lines, "# HELP ai_gateway_namespace_policy_violations_by_type_total Policy violations by type per namespace")
            table.insert(lines, "# TYPE ai_gateway_namespace_policy_violations_by_type_total counter")
            table.insert(lines, string.format("ai_gateway_namespace_policy_violations_by_type_total{namespace_code=\"%s\",policy_type=\"%s\"} %d", 
                namespace_code, policy_type, violations))
        end
        
        -- 模型Token使用量
        for model_name, model_data in pairs(token_usage.models or {}) do
            table.insert(lines, "# HELP ai_gateway_model_tokens_total Total token usage per model per namespace")
            table.insert(lines, "# TYPE ai_gateway_model_tokens_total counter")
            table.insert(lines, string.format("ai_gateway_model_tokens_total{namespace_code=\"%s\",model_name=\"%s\"} %d", 
                namespace_code, model_name, model_data.tokens or 0))
            
            table.insert(lines, "# HELP ai_gateway_model_requests_total Total requests per model per namespace")
            table.insert(lines, "# TYPE ai_gateway_model_requests_total counter")
            table.insert(lines, string.format("ai_gateway_model_requests_total{namespace_code=\"%s\",model_name=\"%s\"} %d", 
                namespace_code, model_name, model_data.requests or 0))
        end
        
        -- 路由使用统计
        local route_usage = _M.get_namespace_route_usage(namespace_id)
        for route_path, route_data in pairs(route_usage) do
            table.insert(lines, "# HELP ai_gateway_route_requests_total Total requests per route per namespace")
            table.insert(lines, "# TYPE ai_gateway_route_requests_total counter")
            table.insert(lines, string.format("ai_gateway_route_requests_total{namespace_code=\"%s\",route_path=\"%s\"} %d", 
                namespace_code, route_path, route_data.total_requests or 0))
            
            -- 路由状态码统计
            for status_code, count in pairs(route_data.status_codes or {}) do
                table.insert(lines, "# HELP ai_gateway_route_status_codes_total Total requests by status code per route per namespace")
                table.insert(lines, "# TYPE ai_gateway_route_status_codes_total counter")
                table.insert(lines, string.format("ai_gateway_route_status_codes_total{namespace_code=\"%s\",route_path=\"%s\",status_code=\"%s\"} %d",
                    namespace_code, route_path, status_code, count or 0))
            end
        end
    end
    
    -- 实例健康指标
    local instance_health = _M.get_instance_health()
    for inst_id, health in pairs(instance_health) do
        table.insert(lines, "# HELP ai_gateway_instance_status Instance health status")
        table.insert(lines, "# TYPE ai_gateway_instance_status gauge")
        local status_value = health.status == "active" and 1 or 0
        table.insert(lines, string.format("ai_gateway_instance_status{instance_id=\"%s\"} %d", 
            inst_id, status_value))
    end
    
    return table.concat(lines, "\n")
end

-- 获取 JSON 格式的指标
function _M.get_json_metrics()
    return {
        global = _M.get_global_metrics(),
        namespaces = _M.get_all_namespace_metrics(),
        instances = _M.get_instance_health(),
        timestamp = ngx.time()
    }
end

-- 重置所有指标
function _M.reset_metrics()
    local redis_client = redis.get_connection()
    if not redis_client then
        return
    end
    
    -- 删除所有指标键
    local keys = redis_client:keys(METRICS_PREFIX .. "*")
    for _, key in ipairs(keys) do
        redis_client:del(key)
    end
end

return _M