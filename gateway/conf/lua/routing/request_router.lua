-- 请求路由器
-- 负责处理健康检查、统计信息等请求

local _M = {}

local cjson = require "cjson"

-- 健康检查处理
function _M.handle_health_check()
    local health_status = {
        status = "healthy",
        timestamp = ngx.time(),
        service = "ai-gateway",
        version = "2.0.0",
        services = {}
    }
    
    -- 检查Redis连接
    local redis_ok = _M.check_redis_health()
    health_status.services.redis = {
        status = redis_ok and "healthy" or "unhealthy"
    }
    
    -- 检查配置中心连接
    local config_ok = _M.check_config_center_health()
    health_status.services.config_center = {
        status = config_ok and "healthy" or "unhealthy"
    }
    
    -- 检查共享内存
    local shared_ok = _M.check_shared_memory_health()
    health_status.services.shared_memory = {
        status = shared_ok and "healthy" or "unhealthy"
    }
    
    -- 更新整体状态
    if not redis_ok or not config_ok or not shared_ok then
        health_status.status = "unhealthy"
    end
    
    ngx.header.content_type = "application/json"
    ngx.say(cjson.encode(health_status))
end

-- 统计信息处理
function _M.handle_stats()
    local stats = {
        timestamp = ngx.time(),
        service = "ai-gateway",
        metrics = {}
    }
    
    -- 获取请求统计
    stats.metrics.requests = _M.get_request_stats()
    
    -- 获取错误统计
    stats.metrics.errors = _M.get_error_stats()
    
    -- 获取性能统计
    stats.metrics.performance = _M.get_performance_stats()
    
    -- 获取缓存统计
    stats.metrics.cache = _M.get_cache_stats()
    
    ngx.header.content_type = "application/json"
    ngx.say(cjson.encode(stats))
end

-- 清理过期数据
function _M.cleanup_expired_data()
    -- 清理过期的限流数据
    _M.cleanup_rate_limit_data()
    
    -- 清理过期的会话数据
    _M.cleanup_session_data()
    
    -- 清理过期的监控数据
    _M.cleanup_monitoring_data()
end

-- 检查Redis健康状态
function _M.check_redis_health()
    local redis = require "resty.redis"
    local red = redis:new()
    red:set_timeout(1000)
    
    local ok, err = red:connect("redis", 6379)
    if not ok then
        return false
    end
    
    local ok, err = red:ping()
    red:close()
    
    return ok == "PONG"
end

-- 检查配置中心健康状态
function _M.check_config_center_health()
    local http = require "resty.http"
    local httpc = http.new()
    httpc:set_timeout(2000)
    
    local res, err = httpc:request_uri("http://config-center:8000/health", {
        method = "GET",
        headers = {
            ["User-Agent"] = "AI-Gateway-Health-Check"
        }
    })
    
    if not res then
        return false
    end
    
    return res.status == 200
end

-- 检查共享内存健康状态
function _M.check_shared_memory_health()
    local shared_dicts = {
        "config_cache",
        "rate_limit", 
        "metrics",
        "session",
        "upstream_state"
    }
    
    for _, dict_name in ipairs(shared_dicts) do
        if not ngx.shared[dict_name] then
            return false
        end
    end
    
    return true
end

-- 获取请求统计
function _M.get_request_stats()
    local metrics_dict = ngx.shared.metrics
    if not metrics_dict then
        return {}
    end
    
    return {
        total_requests = metrics_dict:get("requests:total") or 0,
        successful_requests = metrics_dict:get("requests:success") or 0,
        failed_requests = metrics_dict:get("requests:failed") or 0,
        current_requests = metrics_dict:get("requests:current") or 0
    }
end

-- 获取错误统计
function _M.get_error_stats()
    local metrics_dict = ngx.shared.metrics
    if not metrics_dict then
        return {}
    end
    
    return {
        total_errors = metrics_dict:get("errors:total") or 0,
        error_4xx = metrics_dict:get("errors:4xx") or 0,
        error_5xx = metrics_dict:get("errors:5xx") or 0,
        rate_limit_errors = metrics_dict:get("errors:rate_limit") or 0,
        auth_errors = metrics_dict:get("errors:auth") or 0
    }
end

-- 获取性能统计
function _M.get_performance_stats()
    local metrics_dict = ngx.shared.metrics
    if not metrics_dict then
        return {}
    end
    
    return {
        avg_response_time = metrics_dict:get("performance:avg_response_time") or 0,
        max_response_time = metrics_dict:get("performance:max_response_time") or 0,
        min_response_time = metrics_dict:get("performance:min_response_time") or 0,
        total_response_time = metrics_dict:get("performance:total_response_time") or 0
    }
end

-- 获取缓存统计
function _M.get_cache_stats()
    local cache_dict = ngx.shared.config_cache
    if not cache_dict then
        return {}
    end
    
    return {
        cache_hits = cache_dict:get("stats:hits") or 0,
        cache_misses = cache_dict:get("stats:misses") or 0,
        cache_size = cache_dict:capacity(),
        cache_free = cache_dict:free_space()
    }
end

-- 清理限流数据
function _M.cleanup_rate_limit_data()
    local rate_limit_dict = ngx.shared.rate_limit
    if not rate_limit_dict then
        return
    end
    
    local current_time = ngx.time()
    local keys = rate_limit_dict:get_keys()
    
    for _, key in ipairs(keys) do
        local expire_time = rate_limit_dict:get(key .. ":expire")
        if expire_time and current_time > expire_time then
            rate_limit_dict:delete(key)
            rate_limit_dict:delete(key .. ":expire")
        end
    end
end

-- 清理会话数据
function _M.cleanup_session_data()
    local session_dict = ngx.shared.session
    if not session_dict then
        return
    end
    
    local current_time = ngx.time()
    local keys = session_dict:get_keys()
    
    for _, key in ipairs(keys) do
        local expire_time = session_dict:get(key .. ":expire")
        if expire_time and current_time > expire_time then
            session_dict:delete(key)
            session_dict:delete(key .. ":expire")
        end
    end
end

-- 清理监控数据
function _M.cleanup_monitoring_data()
    local metrics_dict = ngx.shared.metrics
    if not metrics_dict then
        return
    end
    
    local current_time = ngx.time()
    local keys = metrics_dict:get_keys()
    
    for _, key in ipairs(keys) do
        if string.find(key, "temp:") then
            local expire_time = metrics_dict:get(key .. ":expire")
            if expire_time and current_time > expire_time then
                metrics_dict:delete(key)
                metrics_dict:delete(key .. ":expire")
            end
        end
    end
end

return _M 