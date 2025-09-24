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

-- 记录请求指标
function _M.record_request(namespace_id, request_info, status, response_time)
    if not namespace_id then
        return
    end
    
    local instance_id = get_instance_id()
    local current_time = ngx.time()
    local namespace_key = NAMESPACE_PREFIX .. namespace_id
    local instance_key = INSTANCE_PREFIX .. instance_id .. ":" .. namespace_id
    
    -- 使用 Redis 原子操作更新指标
    local redis_client = redis.get_client()
    if not redis_client then
        ngx.log(ngx.ERR, "Failed to get Redis client for metrics")
        return
    end
    
    -- 更新命名空间指标
    local pipeline = redis_client:pipeline()
    
    -- 增加总请求数
    pipeline:incr(namespace_key .. ":total_requests")
    pipeline:incr(GLOBAL_KEY .. ":total_requests")
    
    -- 更新成功/失败请求数
    if status >= 200 and status < 400 then
        pipeline:incr(namespace_key .. ":successful_requests")
    else
        pipeline:incr(namespace_key .. ":failed_requests")
        pipeline:incr(GLOBAL_KEY .. ":total_errors")
    end
    
    -- 更新响应时间
    if response_time then
        pipeline:incrbyfloat(namespace_key .. ":total_response_time", response_time)
        pipeline:incrbyfloat(GLOBAL_KEY .. ":total_response_time", response_time)
    end
    
    -- 更新状态码计数
    local status_key = tostring(status)
    pipeline:incr(namespace_key .. ":status:" .. status_key)
    
    -- 更新最后请求时间
    pipeline:set(namespace_key .. ":last_request_time", current_time)
    pipeline:set(GLOBAL_KEY .. ":last_request_time", current_time)
    
    -- 设置实例级别的指标（用于实例健康检查）
    pipeline:hset(instance_key, "last_request_time", current_time)
    pipeline:hset(instance_key, "status", "active")
    pipeline:expire(instance_key, 300) -- 5分钟过期
    
    -- 执行管道操作
    local results, err = pipeline:exec()
    if not results then
        ngx.log(ngx.ERR, "Failed to update metrics in Redis: ", err)
    end
end

-- 增加并发请求计数
function _M.incr_concurrent_requests(namespace_id)
    if not namespace_id then
        return
    end
    
    local instance_id = get_instance_id()
    local namespace_key = NAMESPACE_PREFIX .. namespace_id
    local instance_key = INSTANCE_PREFIX .. instance_id .. ":" .. namespace_id
    
    local redis_client = redis.get_client()
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
    local namespace_key = NAMESPACE_PREFIX .. namespace_id
    local instance_key = INSTANCE_PREFIX .. instance_id .. ":" .. namespace_id
    
    local redis_client = redis.get_client()
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
    
    local redis_client = redis.get_client()
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
    
    local namespace_key = NAMESPACE_PREFIX .. namespace_id
    
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
    local redis_client = redis.get_client()
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
    local redis_client = redis.get_client()
    if not redis_client then
        return result
    end
    
    -- 获取所有命名空间键
    local namespace_keys = redis_client:keys(NAMESPACE_PREFIX .. "*:total_requests")
    for _, key in ipairs(namespace_keys) do
        local namespace_id = key:match(NAMESPACE_PREFIX .. "(.+):total_requests")
        if namespace_id then
            result[namespace_id] = _M.get_namespace_metrics(namespace_id)
        end
    end
    
    return result
end

-- 获取实例健康状态
function _M.get_instance_health()
    local result = {}
    local redis_client = redis.get_client()
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
    
    -- 命名空间指标
    local namespace_metrics = _M.get_all_namespace_metrics()
    for namespace_id, metrics in pairs(namespace_metrics) do
        table.insert(lines, "# HELP ai_gateway_namespace_requests_total Total number of requests per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_requests_total counter")
        table.insert(lines, string.format("ai_gateway_namespace_requests_total{namespace_id=\"%s\"} %d", 
            namespace_id, metrics.total_requests or 0))
        
        table.insert(lines, "# HELP ai_gateway_namespace_concurrent_requests Current number of concurrent requests per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_concurrent_requests gauge")
        table.insert(lines, string.format("ai_gateway_namespace_concurrent_requests{namespace_id=\"%s\"} %d", 
            namespace_id, metrics.concurrent_requests or 0))
        
        table.insert(lines, "# HELP ai_gateway_namespace_response_time_seconds Average response time per namespace")
        table.insert(lines, "# TYPE ai_gateway_namespace_response_time_seconds gauge")
        table.insert(lines, string.format("ai_gateway_namespace_response_time_seconds{namespace_id=\"%s\"} %.4f", 
            namespace_id, metrics.average_response_time or 0))
        
        -- 状态码指标
        for status_code, count in pairs(metrics.status_codes or {}) do
            table.insert(lines, "# HELP ai_gateway_namespace_status_codes_total Total number of requests by status code per namespace")
            table.insert(lines, "# TYPE ai_gateway_namespace_status_codes_total counter")
            table.insert(lines, string.format("ai_gateway_namespace_status_codes_total{namespace_id=\"%s\",status_code=\"%s\"} %d",
                namespace_id, status_code, count or 0))
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
    local redis_client = redis.get_client()
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