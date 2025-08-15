-- 统一的服务配置与发现工具
-- 集中管理各个内部服务的地址，避免在多处硬编码

local _M = {}

-- 解析形如: redis://host:port/db 的 URL（简化版，不处理用户名密码）
local function parse_redis_url(redis_url)
    if not redis_url or redis_url == "" then
        return nil
    end
    local host, port, db = string.match(redis_url, "redis://([^:/]+):?(%d*)/?(%d*)")
    return host, tonumber(port), tonumber(db)
end

-- Redis 配置
function _M.get_redis_config()
    local default_host = "ai-gateway-redis.ai-gateway.svc.cluster.local"
    local default_port = 6379
    local default_db = 0

    local env_url = os.getenv("REDIS_URL")
    local host, port, db = parse_redis_url(env_url)

    return {
        host = host or os.getenv("REDIS_HOST") or default_host,
        port = port or tonumber(os.getenv("REDIS_PORT") or "" ) or default_port,
        db   = db   or tonumber(os.getenv("REDIS_DB") or "" ) or default_db
    }
end

-- 配置中心 URL（基础地址，末尾不带斜杠）
function _M.get_config_center_base_url()
    local url = os.getenv("CONFIG_CENTER_URL")
    if url and url ~= "" then
        return url
    end
    return "http://ai-gateway-config-center.ai-gateway.svc.cluster.local:8000"
end

-- MySQL 配置（供需要直连 MySQL 的模块使用）
function _M.get_mysql_config()
    return {
        host = os.getenv("MYSQL_HOST") or "ai-gateway-mysql.ai-gateway.svc.cluster.local",
        port = tonumber(os.getenv("MYSQL_PORT") or "3306"),
        database = os.getenv("MYSQL_DATABASE") or "ai_gateway_config",
        user = os.getenv("MYSQL_USER") or "ai_gateway",
        password = os.getenv("MYSQL_PASSWORD") or "ai_gateway_pass"
    }
end

-- Token 服务 URL（返回 /calculate 末尾路径）
function _M.get_token_service_url()
    local token_service_url = os.getenv("TOKEN_SERVICE_URL") or "http://ai-gateway-token-service.ai-gateway.svc.cluster.local:8000"
    if string.find(token_service_url, "/calculate") then
        return token_service_url
    end
    if string.sub(token_service_url, -1) == "/" then
        return token_service_url .. "calculate"
    end
    return token_service_url .. "/calculate"
end

return _M


