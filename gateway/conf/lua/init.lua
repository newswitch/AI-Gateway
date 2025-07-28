-- AI智能网关 - Lua初始化脚本
-- 负责初始化全局配置、加载模块和设置共享内存

local _M = {}

-- 全局配置
local config = {
    -- 配置中心设置
    config_center = {
        host = os.getenv("CONFIG_CENTER_HOST") or "config-center",
        port = os.getenv("CONFIG_CENTER_PORT") or "8000",
        timeout = 5000,  -- 5秒超时
        retry_times = 3
    },
    
    -- Redis设置
    redis = {
        host = os.getenv("REDIS_HOST") or "redis",
        port = os.getenv("REDIS_PORT") or "6379",
        db = os.getenv("REDIS_DB") or "0",
        timeout = 1000,  -- 1秒超时
        pool_size = 100
    },
    
    -- 缓存设置
    cache = {
        namespace_ttl = 3600,      -- 命名空间缓存1小时
        matchers_ttl = 3600,       -- 匹配器缓存1小时
        rules_ttl = 3600,          -- 规则缓存1小时
        upstream_ttl = 1800,       -- 上游服务缓存30分钟
        rate_limit_ttl = 3600      -- 限流数据缓存1小时
    },
    
    -- 限流设置
    rate_limit = {
        default_window = 3600,     -- 默认时间窗口1小时
        max_connections = 1000,    -- 默认最大连接数
        max_requests_per_minute = 100,  -- 默认每分钟最大请求数
        max_tokens_per_hour = 100000    -- 默认每小时最大token数
    },
    
    -- 日志设置
    log = {
        level = os.getenv("LOG_LEVEL") or "info",
        format = "json"
    }
}

-- 共享内存配置
local shared_dicts = {
    config_cache = 10,      -- 10MB配置缓存
    rate_limit = 50,        -- 50MB限流数据
    metrics = 20,           -- 20MB监控指标
    session = 30,           -- 30MB会话数据
    upstream_state = 10     -- 10MB upstream状态管理
}

-- 初始化共享内存
function _M.init_shared_dicts()
    local ngx_shared = ngx.shared
    
    -- 检查共享内存是否已定义
    for name, size in pairs(shared_dicts) do
        if not ngx_shared[name] then
            ngx.log(ngx.ERR, "Shared dict '", name, "' not found in nginx.conf")
            return false
        end
    end
    
    ngx.log(ngx.INFO, "Shared dictionaries initialized successfully")
    return true
end

-- 加载Lua模块
function _M.load_modules()
    -- 工具模块
    require "utils.json_utils"
    require "utils.time_utils"
    require "utils.redis_client"
    require "utils.http_client"
    
    -- 配置模块
    require "config.dynamic_config"
    
    -- 认证模块
    require "auth.rule_checker"
    require "auth.rate_limiter"
    
    -- 路由模块
    require "routing.dynamic_router"
    require "routing.upstream_manager"
    
    -- 监控模块
    require "monitoring.metrics"
    require "monitoring.health_check"
    require "monitoring.log_handler"
    
    ngx.log(ngx.INFO, "All Lua modules loaded successfully")
end

-- 初始化配置
function _M.init_config()
    -- 初始化共享内存
    if not _M.init_shared_dicts() then
        ngx.log(ngx.ERR, "Failed to initialize shared dictionaries")
        return false
    end
    
    -- 加载模块
    _M.load_modules()
    
    -- 注意：不在初始化阶段刷新配置，而是在请求处理阶段进行
    -- 这样可以避免在init_by_lua阶段连接数据库的问题
    
    ngx.log(ngx.INFO, "Gateway initialization completed")
    return true
end

-- 获取配置
function _M.get_config()
    return config
end

-- 获取共享内存
function _M.get_shared_dict(name)
    return ngx.shared[name]
end

-- 健康检查
function _M.health_check()
    local health = {
        status = "healthy",
        timestamp = ngx.time(),
        services = {}
    }
    
    -- 检查Redis连接
    local redis_client = require "utils.redis_client"
    local redis_ok, redis_err = redis_client.ping()
    health.services.redis = {
        status = redis_ok and "healthy" or "unhealthy",
        error = redis_err
    }
    
    -- 检查配置中心连接
    local dynamic_config = require "config.dynamic_config"
    local configs = dynamic_config.get_all_configs()
    health.services.config_center = {
        status = configs and "healthy" or "unhealthy",
        error = configs and nil or "Failed to get configurations"
    }
    
    -- 检查共享内存
    local shared_ok = true
    for name, _ in pairs(shared_dicts) do
        if not ngx.shared[name] then
            shared_ok = false
            break
        end
    end
    health.services.shared_memory = {
        status = shared_ok and "healthy" or "unhealthy"
    }
    
    -- 更新整体状态
    for _, service in pairs(health.services) do
        if service.status ~= "healthy" then
            health.status = "unhealthy"
            break
        end
    end
    
    return health
end

return _M 