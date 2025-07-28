-- 监控指标模块
-- 负责收集和记录系统监控指标

local _M = {}

local cjson = require "cjson"

-- 增加计数器
function _M.increment_counter(counter_name, value)
    value = value or 1
    
    -- 记录到共享内存
    local metrics = ngx.shared.metrics
    local current = metrics:get(counter_name) or 0
    metrics:set(counter_name, current + value)
    
    return true
end

-- 获取计数器值
function _M.get_counter(counter_name)
    local metrics = ngx.shared.metrics
    return metrics:get(counter_name) or 0
end

-- 记录请求指标
function _M.record_request_metrics(namespace_id, status, response_time)
    _M.increment_counter("requests_total", 1)
    _M.increment_counter("requests_namespace_" .. namespace_id, 1)
    
    if status >= 200 and status < 300 then
        _M.increment_counter("requests_success", 1)
    elseif status >= 400 and status < 500 then
        _M.increment_counter("requests_client_error", 1)
    elseif status >= 500 then
        _M.increment_counter("requests_server_error", 1)
    end
    
    -- 记录响应时间
    if response_time then
        _M.record_response_time(response_time)
    end
end

-- 记录响应时间
function _M.record_response_time(response_time)
    local metrics = ngx.shared.metrics
    
    -- 记录平均响应时间
    local total_time = metrics:get("response_time_total") or 0
    local count = metrics:get("response_time_count") or 0
    
    metrics:set("response_time_total", total_time + response_time)
    metrics:set("response_time_count", count + 1)
    
    -- 记录最大响应时间
    local max_time = metrics:get("response_time_max") or 0
    if response_time > max_time then
        metrics:set("response_time_max", response_time)
    end
end

-- 获取监控统计
function _M.get_metrics()
    local metrics = ngx.shared.metrics
    local result = {}
    
    -- 获取所有指标
    local keys = metrics:get_keys()
    for _, key in ipairs(keys) do
        result[key] = metrics:get(key)
    end
    
    return result
end

return _M 