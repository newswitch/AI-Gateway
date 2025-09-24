-- AI智能网关 - 核心初始化模块
-- 负责初始化全局配置、加载模块和设置共享内存

local _M = {}

-- 全局配置
local config = {
    -- 配置中心设置
    config_center = {
        host = os.getenv("CONFIG_CENTER_HOST") or "ai-gateway-config-center-dev",
        port = os.getenv("CONFIG_CENTER_PORT") or "8001",
        timeout = 5000,  -- 5秒超时
        retry_times = 3
    },
    
    -- Redis设置
    redis = {
        host = os.getenv("REDIS_HOST") or "ai-gateway-redis-dev",
        port = os.getenv("REDIS_PORT") or "6379",
        db = os.getenv("REDIS_DB") or "0",
        timeout = 10000,  -- 10秒超时
        pool_size = 100
    },
    
    -- MySQL设置
    mysql = {
        host = os.getenv("MYSQL_HOST") or "ai-gateway-mysql-dev",
        port = os.getenv("MYSQL_PORT") or "3307",
        database = os.getenv("MYSQL_DATABASE") or "ai_gateway_config",
        user = os.getenv("MYSQL_USER") or "root",
        password = os.getenv("MYSQL_PASSWORD") or "ai_gateway_root",
        timeout = 1000,
        pool_size = 100
    },
    
    -- 缓存设置
    cache = {
        namespace_ttl = 3600,      -- 命名空间缓存1小时
        matchers_ttl = 3600,       -- 匹配器缓存1小时
        policies_ttl = 3600,       -- 策略缓存1小时
        upstream_ttl = 1800,       -- 上游服务缓存30分钟
        locations_ttl = 1800,      -- 路由规则缓存30分钟
        rate_limit_ttl = 3600      -- 限流数据缓存1小时
    },
    
    -- 限流设置
    rate_limit = {
        default_window = 3600,     -- 默认时间窗口1小时
        max_connections = 1000,    -- 默认最大连接数
        max_requests_per_minute = 100,  -- 默认每分钟最大请求数
        max_tokens_per_hour = 100000    -- 默认每小时最大token数
    },
    
    -- Token计算服务设置
    token_service = {
        url = os.getenv("TOKEN_SERVICE_URL") or "http://token-service:8000",
        timeout = 5000,  -- 5秒超时
        retry_count = 2, -- 重试次数
        fallback_enabled = true  -- 启用降级机制
    },
    
    -- 日志设置
    log = {
        level = os.getenv("LOG_LEVEL") or "info",
        format = "json"
    },
    
    -- Prometheus监控设置
    prometheus = {
        enabled = os.getenv("PROMETHEUS_ENABLED") == "true" or true,  -- 默认启用
        job_name = os.getenv("PROMETHEUS_JOB_NAME") or "ai-gateway-lua",
        instance = os.getenv("PROMETHEUS_INSTANCE") or "gateway-1",
        metrics_path = "/metrics",
        scrape_interval = 15,  -- 15秒拉取间隔
        scrape_timeout = 10,   -- 10秒拉取超时
        data_retention = 900   -- 15分钟数据保留时间，确保Prometheus能拉取到
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
    require "utils.json"
    require "utils.redis"
    -- require "utils.mysql"  
    require "utils.http"
    
    -- 配置模块
    require "config.cache"
    require "config.loader"
    -- require "config.sync"  
    
    -- 认证模块
    require "auth.namespace_matcher"
    require "auth.policy_enforcer"
    -- require "auth.rate_limiter"  
    
    -- 路由模块
    require "routing.router"
    require "routing.upstream_selector"
    require "routing.proxy_handler"
    
    -- 监控模块
    require "monitoring.metrics"
    require "monitoring.logger"
    require "monitoring.health"
    require "monitoring.scheduler"
    
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
    local redis_client = require "utils.redis"
    local redis_ok, redis_err = redis_client.ping()
    health.services.redis = {
        status = redis_ok and "healthy" or "unhealthy",
        error = redis_err
    }
    
    -- 检查配置中心连接
    local config_loader = require "config.loader"
    local configs = config_loader.get_all_configs()
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
