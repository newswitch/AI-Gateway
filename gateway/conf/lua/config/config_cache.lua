-- 配置缓存模块
-- 负责从Redis或数据库获取配置并缓存

local _M = {}

local cjson = require "cjson"
local redis = require "resty.redis"
local http = require "resty.http"

-- 缓存配置
local CACHE_TTL = 300 -- 5分钟缓存
local CONFIG_KEYS = {
    RULES = "rules",
    NAMESPACES = "namespaces",
    MATCHERS = "matchers",
    UPSTREAM_SERVERS = "upstream_servers"
}

-- 获取Redis连接
local function get_redis_conn()
    local red = redis:new()
    red:set_timeout(1000)
    
    local ok, err = red:connect("redis", 6379)
    if not ok then
        ngx.log(ngx.ERR, "Failed to connect to Redis: ", err)
        return nil
    end
    
    return red
end

-- 从Redis获取配置
local function get_config_from_redis(config_key)
    local red = get_redis_conn()
    if not red then
        return nil, "Failed to connect to Redis"
    end
    
    local config_data, err = red:get(config_key)
    if not config_data or config_data == ngx.null then
        red:close()
        return nil, "Config not found in Redis"
    end
    
    red:close()
    
    local ok, config = pcall(cjson.decode, config_data)
    if not ok then
        ngx.log(ngx.ERR, "Failed to decode config data for ", config_key, ": ", config)
        return nil, "Failed to decode config data"
    end
    
    return config
end

-- 从配置中心API获取配置
local function get_config_from_api(config_key)
    local httpc = http.new()
    httpc:set_timeout(2000)
    
    local url = string.format("http://config-center:8000/api/v1/config/%s", config_key)
    local res, err = httpc:request_uri(url, {
        method = "GET",
        headers = {
            ["User-Agent"] = "AI-Gateway-Config-Cache"
        }
    })
    
    if not res then
        return nil, "Failed to request config from API: " .. (err or "unknown error")
    end
    
    if res.status ~= 200 then
        return nil, "API returned status " .. res.status
    end
    
    local ok, data = pcall(cjson.decode, res.body)
    if not ok then
        return nil, "Failed to decode API response"
    end
    
    return data
end

-- 获取命名空间规则
function _M.get_namespace_rules(namespace_id)
    -- 首先尝试从Redis获取
    local cache_key = CONFIG_KEYS.RULES .. ":" .. namespace_id
    local rules = get_config_from_redis(cache_key)
    
    if not rules then
        -- 从API获取
        rules = get_config_from_api("rules/" .. namespace_id)
        if rules then
            -- 缓存到Redis（异步，不阻塞）
            local red = get_redis_conn()
            if red then
                local ok, err = red:setex(cache_key, CACHE_TTL, cjson.encode(rules))
                if not ok then
                    ngx.log(ngx.WARN, "Failed to cache rules: ", err)
                end
                red:close()
            end
        end
    end
    
    if not rules then
        return {}, nil
    end
    
    return rules, nil
end

-- 获取命名空间配置
function _M.get_namespace_config(namespace_id)
    local cache_key = CONFIG_KEYS.NAMESPACES .. ":" .. namespace_id
    local namespace = get_config_from_redis(cache_key)
    
    if not namespace then
        namespace = get_config_from_api("namespaces/" .. namespace_id)
        if namespace then
            local red = get_redis_conn()
            if red then
                local ok, err = red:setex(cache_key, CACHE_TTL, cjson.encode(namespace))
                if not ok then
                    ngx.log(ngx.WARN, "Failed to cache namespace: ", err)
                end
                red:close()
            end
        end
    end
    
    return namespace
end

-- 获取匹配器配置
function _M.get_matchers()
    local matchers = get_config_from_redis(CONFIG_KEYS.MATCHERS)
    
    if not matchers then
        matchers = get_config_from_api("matchers")
        if matchers then
            local red = get_redis_conn()
            if red then
                local ok, err = red:setex(CONFIG_KEYS.MATCHERS, CACHE_TTL, cjson.encode(matchers))
                if not ok then
                    ngx.log(ngx.WARN, "Failed to cache matchers: ", err)
                end
                red:close()
            end
        end
    end
    
    return matchers or {}
end

-- 获取上游服务器配置
function _M.get_upstream_servers()
    local servers = get_config_from_redis(CONFIG_KEYS.UPSTREAM_SERVERS)
    
    if not servers then
        servers = get_config_from_api("upstream-servers")
        if servers then
            local red = get_redis_conn()
            if red then
                local ok, err = red:setex(CONFIG_KEYS.UPSTREAM_SERVERS, CACHE_TTL, cjson.encode(servers))
                if not ok then
                    ngx.log(ngx.WARN, "Failed to cache upstream servers: ", err)
                end
                red:close()
            end
        end
    end
    
    return servers or {}
end

-- 刷新配置缓存
function _M.refresh_cache(config_key)
    local red = get_redis_conn()
    if not red then
        return false, "Failed to connect to Redis"
    end
    
    local ok, err = red:del(config_key)
    red:close()
    
    if not ok then
        return false, "Failed to delete cache: " .. (err or "unknown error")
    end
    
    return true
end

-- 刷新所有配置缓存
function _M.refresh_all_cache()
    local red = get_redis_conn()
    if not red then
        return false, "Failed to connect to Redis"
    end
    
    for _, key in pairs(CONFIG_KEYS) do
        red:del(key)
    end
    
    red:close()
    return true
end

return _M 