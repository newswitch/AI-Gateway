-- 健康检查模块
-- 负责检查系统各组件的健康状态

local _M = {}

local cjson = require "cjson"
local config_client = require "config.config_client"

-- 检查所有服务健康状态
function _M.check_all_services()
    local health_status = {
        timestamp = ngx.time(),
        status = "healthy",
        services = {}
    }
    
    -- 检查配置中心
    local config_center_ok = _M.check_config_center()
    health_status.services.config_center = {
        status = config_center_ok and "healthy" or "unhealthy",
        timestamp = ngx.time()
    }
    
    -- 检查Redis
    local redis_ok = _M.check_redis()
    health_status.services.redis = {
        status = redis_ok and "healthy" or "unhealthy",
        timestamp = ngx.time()
    }
    
    -- 检查上游服务器
    local upstream_ok = _M.check_upstream_servers()
    health_status.services.upstream = {
        status = upstream_ok and "healthy" or "unhealthy",
        timestamp = ngx.time()
    }
    
    -- 更新整体状态
    if not config_center_ok or not redis_ok or not upstream_ok then
        health_status.status = "degraded"
    end
    
    return health_status
end

-- 检查配置中心健康状态
function _M.check_config_center()
    local ok, err = pcall(function()
        local response = config_client.get_namespaces()
        return response ~= nil
    end)
    
    return ok
end

-- 检查Redis健康状态
function _M.check_redis()
    local redis = require "utils.redis_client"
    
    local ok, err = pcall(function()
        local result = redis.ping()
        return result == "PONG"
    end)
    
    return ok
end

-- 检查上游服务器健康状态
function _M.check_upstream_servers()
    -- 这里实现上游服务器健康检查
    -- 暂时返回true
    return true
end

-- 获取健康状态
function _M.get_health_status()
    return _M.check_all_services()
end

return _M 