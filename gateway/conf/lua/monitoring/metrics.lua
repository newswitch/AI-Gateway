-- 监控指标模块
-- 负责收集和记录各种监控指标

local redis = require "utils.redis"
local json = require "utils.json"

local _M = {}

-- 指标键前缀
local METRICS_PREFIX = "ai_gateway:metrics:"

-- 记录请求指标
function _M.record_request(namespace_id, request_info, status, response_time)
    if not namespace_id then
        return
    end
    
    local current_time = ngx.time()
    local minute_key = METRICS_PREFIX .. "requests:" .. namespace_id .. ":" .. math.floor(current_time / 60)
    local hour_key = METRICS_PREFIX .. "requests:" .. namespace_id .. ":" .. math.floor(current_time / 3600)
    
    -- 记录每分钟请求数
    redis.incr_ex(minute_key, 300) -- 5分钟过期
    
    -- 记录每小时请求数
    redis.incr_ex(hour_key, 3600) -- 1小时过期
    
    -- 记录响应时间
    if response_time then
        local response_time_key = METRICS_PREFIX .. "response_time:" .. namespace_id .. ":" .. math.floor(current_time / 60)
        local response_times = redis.get_json(response_time_key) or {}
        table.insert(response_times, response_time)
        
        -- 只保留最近100个响应时间
        if #response_times > 100 then
            table.remove(response_times, 1)
        end
        
        redis.set_json(response_time_key, response_times, 300)
    end
    
    -- 记录状态码分布
    local status_key = METRICS_PREFIX .. "status:" .. namespace_id .. ":" .. status .. ":" .. math.floor(current_time / 60)
    redis.incr_ex(status_key, 300)
    
    -- 记录错误请求
    if status >= 400 then
        local error_key = METRICS_PREFIX .. "errors:" .. namespace_id .. ":" .. math.floor(current_time / 60)
        redis.incr_ex(error_key, 300)
    end
end

-- 记录上游服务器指标
function _M.record_upstream_request(upstream_id, status, response_time)
    if not upstream_id then
        return
    end
    
    local current_time = ngx.time()
    local minute_key = METRICS_PREFIX .. "upstream:" .. upstream_id .. ":" .. math.floor(current_time / 60)
    
    -- 记录每分钟请求数
    redis.incr_ex(minute_key, 300)
    
    -- 记录响应时间
    if response_time then
        local response_time_key = METRICS_PREFIX .. "upstream_response_time:" .. upstream_id .. ":" .. math.floor(current_time / 60)
        local response_times = redis.get_json(response_time_key) or {}
        table.insert(response_times, response_time)
        
        -- 只保留最近100个响应时间
        if #response_times > 100 then
            table.remove(response_times, 1)
        end
        
        redis.set_json(response_time_key, response_times, 300)
    end
end

-- 获取命名空间指标
function _M.get_namespace_metrics(namespace_id, time_range)
    time_range = time_range or 3600 -- 默认1小时
    
    local current_time = ngx.time()
    local start_time = current_time - time_range
    
    local metrics = {
        total_requests = 0,
        successful_requests = 0,
        failed_requests = 0,
        average_response_time = 0,
        status_codes = {},
        response_times = {}
    }
    
    -- 统计请求数
    for i = start_time, current_time, 60 do
        local minute_key = METRICS_PREFIX .. "requests:" .. namespace_id .. ":" .. math.floor(i / 60)
        local count = redis.get(minute_key) or 0
        metrics.total_requests = metrics.total_requests + tonumber(count)
    end
    
    -- 统计状态码
    for status_code = 200, 599 do
        local status_count = 0
        for i = start_time, current_time, 60 do
            local status_key = METRICS_PREFIX .. "status:" .. namespace_id .. ":" .. status_code .. ":" .. math.floor(i / 60)
            local count = redis.get(status_key) or 0
            status_count = status_count + tonumber(count)
        end
        
        if status_count > 0 then
            metrics.status_codes[status_code] = status_count
            if status_code >= 200 and status_code < 300 then
                metrics.successful_requests = metrics.successful_requests + status_count
            elseif status_code >= 400 then
                metrics.failed_requests = metrics.failed_requests + status_count
            end
        end
    end
    
    -- 计算平均响应时间
    local total_response_time = 0
    local response_time_count = 0
    
    for i = start_time, current_time, 60 do
        local response_time_key = METRICS_PREFIX .. "response_time:" .. namespace_id .. ":" .. math.floor(i / 60)
        local response_times = redis.get_json(response_time_key) or {}
        
        for _, time in ipairs(response_times) do
            total_response_time = total_response_time + time
            response_time_count = response_time_count + 1
            table.insert(metrics.response_times, time)
        end
    end
    
    if response_time_count > 0 then
        metrics.average_response_time = total_response_time / response_time_count
    end
    
    return metrics
end

-- 获取上游服务器指标
function _M.get_upstream_metrics(upstream_id, time_range)
    time_range = time_range or 3600 -- 默认1小时
    
    local current_time = ngx.time()
    local start_time = current_time - time_range
    
    local metrics = {
        total_requests = 0,
        average_response_time = 0,
        response_times = {}
    }
    
    -- 统计请求数
    for i = start_time, current_time, 60 do
        local minute_key = METRICS_PREFIX .. "upstream:" .. upstream_id .. ":" .. math.floor(i / 60)
        local count = redis.get(minute_key) or 0
        metrics.total_requests = metrics.total_requests + tonumber(count)
    end
    
    -- 计算平均响应时间
    local total_response_time = 0
    local response_time_count = 0
    
    for i = start_time, current_time, 60 do
        local response_time_key = METRICS_PREFIX .. "upstream_response_time:" .. upstream_id .. ":" .. math.floor(i / 60)
        local response_times = redis.get_json(response_time_key) or {}
        
        for _, time in ipairs(response_times) do
            total_response_time = total_response_time + time
            response_time_count = response_time_count + 1
            table.insert(metrics.response_times, time)
        end
    end
    
    if response_time_count > 0 then
        metrics.average_response_time = total_response_time / response_time_count
    end
    
    return metrics
end

-- 获取全局指标
function _M.get_global_metrics(time_range)
    time_range = time_range or 3600 -- 默认1小时
    
    local current_time = ngx.time()
    local start_time = current_time - time_range
    
    local metrics = {
        total_requests = 0,
        total_namespaces = 0,
        total_upstreams = 0,
        average_response_time = 0
    }
    
    -- 这里可以从配置中心获取命名空间和上游服务器数量
    local cache = require "config.cache"
    local configs = cache.get_all_configs()
    
    metrics.total_namespaces = #(configs.namespaces or {})
    metrics.total_upstreams = #(configs.upstreams or {})
    
    return metrics
end

-- 清理过期指标
function _M.cleanup_expired_metrics()
    local current_time = ngx.time()
    local expired_time = current_time - 86400 -- 24小时前
    
    -- 这里可以实现清理过期指标的逻辑
    -- 暂时跳过，因为Redis会自动过期
end

return _M
