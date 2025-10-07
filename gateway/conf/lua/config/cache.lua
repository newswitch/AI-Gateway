-- 配置缓存模块
-- 负责管理Redis缓存和内存缓存

local redis = require "utils.redis"
local json = require "utils.json"

local _M = {}

-- 缓存键前缀 - 与配置中心保持一致
local CACHE_PREFIX = "config:"
local CACHE_KEYS = {
    namespaces = CACHE_PREFIX .. "namespaces:all",
    policies = CACHE_PREFIX .. "policies:all",
    upstreams = CACHE_PREFIX .. "upstreams:all",
    locations = CACHE_PREFIX .. "locations:all",
    matchers = CACHE_PREFIX .. "matchers:all"      -- 匹配器缓存
}

-- 获取缓存TTL配置
local function get_cache_ttl()
    local config = require "core.init"
    local cache_config = config.get_config().cache
    
    return {
        namespaces = cache_config.namespace_ttl,
        policies = cache_config.policies_ttl,
        upstreams = cache_config.upstream_ttl,
        locations = cache_config.locations_ttl,
        matchers = cache_config.matchers_ttl,
        rate_limit = cache_config.rate_limit_ttl
    }
end

-- 设置命名空间缓存
function _M.set_namespaces(namespaces)
    if not namespaces then
        return false
    end
    
    local ttl_config = get_cache_ttl()
    local ok, err = redis.set_json(CACHE_KEYS.namespaces, namespaces, ttl_config.namespaces)
    if not ok then
        ngx.log(ngx.ERR, "Failed to cache namespaces: ", err)
        return false
    end
    
    ngx.log(ngx.INFO, "Namespaces cached successfully")
    return true
end

-- 获取命名空间缓存
function _M.get_namespaces()
    local namespaces_data, err = redis.get(CACHE_KEYS.namespaces)
    if err then
        ngx.log(ngx.ERR, "CACHE: Redis error getting namespaces: ", err)
    end
    
    if not namespaces_data or namespaces_data == ngx.null then
        ngx.log(ngx.WARN, "No namespaces data in Redis")
        return nil
    end
    
    local namespaces, err = json.decode(namespaces_data)
    if not namespaces then
        ngx.log(ngx.ERR, "Failed to parse namespaces from Redis: ", err)
        return nil
    end
    
    return namespaces
end

-- 设置策略缓存
function _M.set_policies(policies)
    if not policies then
        return false
    end
    
    local ttl_config = get_cache_ttl()
    local ok, err = redis.set_json(CACHE_KEYS.policies, policies, ttl_config.policies)
    if not ok then
        ngx.log(ngx.ERR, "Failed to cache policies: ", err)
        return false
    end
    
    ngx.log(ngx.INFO, "Policies cached successfully")
    return true
end

-- 获取策略缓存
function _M.get_policies()
    local policies_data, err = redis.get(CACHE_KEYS.policies)
    if not policies_data or policies_data == ngx.null then
        ngx.log(ngx.WARN, "No policies data in Redis")
        return nil
    end
    
    local policies, err = json.decode(policies_data)
    if not policies then
        ngx.log(ngx.ERR, "Failed to parse policies from Redis: ", err)
        return nil
    end
    
    return policies
end

-- 设置上游服务器缓存
function _M.set_upstreams(upstreams)
    if not upstreams then
        return false
    end
    
    local ttl_config = get_cache_ttl()
    local ok, err = redis.set_json(CACHE_KEYS.upstreams, upstreams, ttl_config.upstreams)
    if not ok then
        ngx.log(ngx.ERR, "Failed to cache upstreams: ", err)
        return false
    end
    
    ngx.log(ngx.INFO, "Upstreams cached successfully")
    return true
end

-- 获取上游服务器缓存
function _M.get_upstreams()
    local upstreams_data, err = redis.get(CACHE_KEYS.upstreams)
    if err then
        ngx.log(ngx.ERR, "Redis error getting upstreams: ", err)
    end
    
    if not upstreams_data or upstreams_data == ngx.null then
        ngx.log(ngx.WARN, "No upstreams data in Redis")
        return nil
    end
    
    local upstreams, err = json.decode(upstreams_data)
    if not upstreams then
        ngx.log(ngx.ERR, "Failed to parse upstreams from Redis: ", err)
        return nil
    end
    
    return upstreams
end

-- 设置路由规则缓存
function _M.set_locations(locations)
    if not locations then
        return false
    end
    
    local ttl_config = get_cache_ttl()
    local ok, err = redis.set_json(CACHE_KEYS.locations, locations, ttl_config.locations)
    if not ok then
        ngx.log(ngx.ERR, "Failed to cache locations: ", err)
        return false
    end
    
    ngx.log(ngx.INFO, "Locations cached successfully")
    return true
end

-- 获取路由规则缓存
function _M.get_locations()
    local locations_data, err = redis.get(CACHE_KEYS.locations)
    if not locations_data or locations_data == ngx.null then
        ngx.log(ngx.WARN, "No locations data in Redis")
        return nil
    end
    
    local locations, err = json.decode(locations_data)
    if not locations then
        ngx.log(ngx.ERR, "Failed to parse locations from Redis: ", err)
        return nil
    end
    
    return locations
end

-- 获取路由规则缓存（别名，用于路径重写模块）
function _M.get_location_rules()
    return _M.get_locations()
end

-- 设置匹配器缓存
function _M.set_matchers(matchers)
    if not matchers then
        return false
    end
    
    local ttl_config = get_cache_ttl()
    local ok, err = redis.set_json(CACHE_KEYS.matchers, matchers, ttl_config.matchers)
    if not ok then
        ngx.log(ngx.ERR, "Failed to cache matchers: ", err)
        return false
    end
    
    ngx.log(ngx.INFO, "Matchers cached successfully")
    return true
end

-- 获取匹配器缓存
function _M.get_matchers()
    local matchers_data, err = redis.get(CACHE_KEYS.matchers)
    if not matchers_data or matchers_data == ngx.null then
        ngx.log(ngx.WARN, "No matchers data in Redis")
        return nil
    end
    
    local matchers, err = json.decode(matchers_data)
    if not matchers then
        ngx.log(ngx.ERR, "Failed to parse matchers from Redis: ", err)
        return nil
    end
    
    return matchers
end

-- 获取所有缓存配置
function _M.get_all_configs()
    local configs = {}
    local loader = require "config.loader"
    
    configs.namespaces = loader.get_namespaces() or {}
    configs.policies = _M.get_policies() or {}
    configs.upstreams = _M.get_upstreams() or {}
    configs.locations = _M.get_locations() or {}
    -- 匹配器信息已嵌入到命名空间数据中，不再需要单独的匹配器缓存
    
    return configs
end

-- 清除所有缓存
function _M.clear_all_cache()
    local success = true
    
    for _, key in pairs(CACHE_KEYS) do
        local ok, err = redis.del(key)
        if not ok then
            ngx.log(ngx.ERR, "Failed to clear cache key ", key, ": ", err)
            success = false
        end
    end
    
    if success then
        ngx.log(ngx.INFO, "All cache cleared successfully")
    else
        ngx.log(ngx.ERR, "Failed to clear some cache keys")
    end
    
    return success
end

-- 检查缓存是否存在
function _M.cache_exists(cache_type)
    local key = CACHE_KEYS[cache_type]
    if not key then
        return false
    end
    
    local exists, err = redis.exists(key)
    return exists == 1, err
end

-- 获取缓存TTL配置（公共方法）
function _M.get_cache_ttl_config()
    return get_cache_ttl()
end

-- 刷新缓存TTL
function _M.refresh_cache_ttl(cache_type)
    local key = CACHE_KEYS[cache_type]
    local ttl_config = get_cache_ttl()
    local ttl = ttl_config[cache_type]
    
    if not key or not ttl then
        return false
    end
    
    local ok, err = redis.expire(key, ttl)
    if not ok then
        ngx.log(ngx.ERR, "Failed to refresh cache TTL for ", cache_type, ": ", err)
        return false
    end
    
    return true
end

return _M
