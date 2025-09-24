-- 健康检查模块
-- 负责检查各个服务的健康状态

local redis = require "utils.redis"
local http = require "utils.http"
local cache = require "config.cache"

local _M = {}

-- 检查Redis健康状态
local function check_redis_health()
    local ok, err = redis.ping()
    if ok then
        return true, "Redis is healthy"
    else
        return false, "Redis health check failed: " .. (err or "unknown error")
    end
end

-- 检查配置中心健康状态
local function check_config_center_health()
    local config = require "core.init"
    local config_center = config.get_config().config_center
    
    local url = "http://" .. config_center.host .. ":" .. config_center.port .. "/health"
    local res, err = http.get(url)
    
    if not res then
        return false, "Config center health check failed: " .. (err or "unknown error")
    end
    
    if res.status == 200 then
        return true, "Config center is healthy"
    else
        return false, "Config center returned status: " .. res.status
    end
end

-- 检查上游服务器健康状态
local function check_upstreams_health()
    local configs = cache.get_all_configs()
    local upstreams = configs.upstreams or {}
    local healthy_count = 0
    local total_count = #upstreams
    
    for _, upstream in ipairs(upstreams) do
        if upstream.status == 1 then  -- 使用数字状态
            local health_url = upstream.server_url .. (upstream.health_check_url or "/health")
            local res, err = http.get(health_url)
            
            if res and res.status == 200 then
                healthy_count = healthy_count + 1
            end
        end
    end
    
    if total_count == 0 then
        return true, "No upstream servers configured"
    end
    
    if healthy_count == 0 then
        return false, "No healthy upstream servers available"
    end
    
    return true, string.format("%d/%d upstream servers healthy", healthy_count, total_count)
end

-- 检查共享内存健康状态
local function check_shared_memory_health()
    local shared_dicts = {
        "config_cache",
        "rate_limit", 
        "metrics",
        "session",
        "upstream_state"
    }
    
    for _, dict_name in ipairs(shared_dicts) do
        if not ngx.shared[dict_name] then
            return false, "Shared dict '" .. dict_name .. "' not found"
        end
    end
    
    return true, "All shared dictionaries are available"
end

-- 执行健康检查
function _M.check_health()
    local health = {
        status = "healthy",
        timestamp = ngx.time(),
        services = {}
    }
    
    -- 检查Redis
    local redis_ok, redis_msg = check_redis_health()
    health.services.redis = {
        status = redis_ok and "healthy" or "unhealthy",
        message = redis_msg
    }
    
    -- 检查配置中心
    local config_ok, config_msg = check_config_center_health()
    health.services.config_center = {
        status = config_ok and "healthy" or "unhealthy",
        message = config_msg
    }
    
    -- 检查上游服务器
    local upstream_ok, upstream_msg = check_upstreams_health()
    health.services.upstreams = {
        status = upstream_ok and "healthy" or "unhealthy",
        message = upstream_msg
    }
    
    -- 检查共享内存
    local shared_ok, shared_msg = check_shared_memory_health()
    health.services.shared_memory = {
        status = shared_ok and "healthy" or "unhealthy",
        message = shared_msg
    }
    
    -- 确定整体状态
    for _, service in pairs(health.services) do
        if service.status ~= "healthy" then
            health.status = "unhealthy"
            break
        end
    end
    
    return health
end

-- 获取服务状态
function _M.get_service_status(service_name)
    local health = _M.check_health()
    return health.services[service_name]
end

-- 检查服务是否健康
function _M.is_service_healthy(service_name)
    local status = _M.get_service_status(service_name)
    return status and status.status == "healthy"
end

-- 获取健康统计
function _M.get_health_stats()
    local health = _M.check_health()
    local stats = {
        overall_status = health.status,
        healthy_services = 0,
        total_services = 0,
        services = {}
    }
    
    for name, service in pairs(health.services) do
        stats.total_services = stats.total_services + 1
        if service.status == "healthy" then
            stats.healthy_services = stats.healthy_services + 1
        end
        stats.services[name] = service.status
    end
    
    return stats
end

return _M
