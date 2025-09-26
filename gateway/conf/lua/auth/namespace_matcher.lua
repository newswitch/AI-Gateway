-- 统一的命名空间匹配器
-- 使用Trie树进行高效匹配，支持header、body、query三种匹配方式

local json = require "utils.json"
local trie = require "utils.trie"
local cache = require "config.cache"

local _M = {}

-- 缓存Trie树
local _cached_tries = {}
local _cache_timestamp = 0
local CACHE_TTL = 60  -- 缓存60秒

-- 创建header匹配的Trie树
function _M._build_header_trie()
    local namespaces = cache.get_namespaces() or {}
    local header_trie = trie.create()
    
    for _, namespace in ipairs(namespaces) do
        if namespace.matcher and 
           namespace.matcher.matcher_type == "header" and 
           namespace.matcher.status == 1 and
           namespace.status == 1 then
            
            local field = namespace.matcher.match_field
            local value = namespace.matcher.match_value
            local key = field .. ":" .. value
            
            -- 插入到Trie树
            trie.insert(header_trie, key, namespace.namespace_id, {
                namespace = namespace,
                matcher = namespace.matcher
            })
        end
    end
    
    return header_trie
end

-- 创建body匹配的Trie树
function _M._build_body_trie()
    local namespaces = cache.get_namespaces() or {}
    local body_trie = trie.create()
    
    for _, namespace in ipairs(namespaces) do
        if namespace.matcher and 
           namespace.matcher.matcher_type == "body" and 
           namespace.matcher.status == 1 and
           namespace.status == 1 then
            
            local field = namespace.matcher.match_field
            local value = namespace.matcher.match_value
            local key = field .. ":" .. value
            
            trie.insert(body_trie, key, namespace.namespace_id, {
                namespace = namespace,
                matcher = namespace.matcher
            })
        end
    end
    
    return body_trie
end

-- 创建query匹配的Trie树
function _M._build_query_trie()
    local namespaces = cache.get_namespaces() or {}
    local query_trie = trie.create()
    
    for _, namespace in ipairs(namespaces) do
        if namespace.matcher and 
           namespace.matcher.matcher_type == "query" and 
           namespace.matcher.status == 1 and
           namespace.status == 1 then
            
            local field = namespace.matcher.match_field
            local value = namespace.matcher.match_value
            local key = field .. ":" .. value
            
            trie.insert(query_trie, key, namespace.namespace_id, {
                namespace = namespace,
                matcher = namespace.matcher
            })
        end
    end
    
    return query_trie
end

-- 通过namespace_code直接获取命名空间
function _M._get_namespace_by_code(namespace_code)
    if not namespace_code then
        return nil
    end
    
    local redis = require "utils.redis"
    local red = redis.get_connection()
    if not red then
        ngx.log(ngx.ERR, "NAMESPACE_MATCHER: Failed to get Redis connection")
        return nil
    end
    
    local key = "config:namespaces:" .. namespace_code
    local data, err = red:get(key)
    red:close()
    
    if err then
        ngx.log(ngx.ERR, "NAMESPACE_MATCHER: Redis error getting namespace by code: ", err)
        return nil
    end
    
    if not data or data == ngx.null then
        ngx.log(ngx.WARN, "NAMESPACE_MATCHER: No namespace found for code: ", namespace_code)
        return nil
    end
    
    local namespace, err = json.decode(data)
    if not namespace then
        ngx.log(ngx.ERR, "NAMESPACE_MATCHER: Failed to parse namespace data: ", err)
        return nil
    end
    
    return namespace
end

-- 获取缓存的Trie树
function _M._get_cached_tries()
    local current_time = ngx.time()
    
    -- 检查缓存是否有效
    if _cached_tries.header and (current_time - _cache_timestamp) < CACHE_TTL then
        return _cached_tries
    end
    
    -- 缓存失效，重新构建
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Building Trie trees...")
    
    _cached_tries.header = _M._build_header_trie()
    _cached_tries.body = _M._build_body_trie()
    _cached_tries.query = _M._build_query_trie()
    _cache_timestamp = current_time
    
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Trie trees built successfully")
    return _cached_tries
end

-- 使用Trie树匹配命名空间
function _M.find_matching_namespace(request_info)
    ngx.log(ngx.INFO, "=== NAMESPACE_MATCHER: Starting Trie-based matching ===")
    
    local tries = _M._get_cached_tries()
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Got tries, header_trie exists: ", tries.header ~= nil)
    
    -- 1. 尝试header匹配
    if request_info.headers then
        local result = _M._match_headers(tries.header, request_info.headers)
        if result then
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Found by header, result type: ", type(result))
            if result.data and result.data.namespace then
                ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Found by header: ", result.data.namespace.namespace_code)
                return result.data.namespace
            else
                ngx.log(ngx.ERR, "NAMESPACE_MATCHER: Result has no data.namespace field")
                return nil
            end
        end
    end
    
    -- 2. 尝试body匹配
    if request_info.body then
        local body_data = json.decode(request_info.body)
        if body_data then
            local result = _M._match_body(tries.body, body_data)
        if result then
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Found by body: ", result.data.namespace.namespace_code)
            return result.data.namespace
        end
        end
    end
    
    -- 3. 尝试query匹配
    if request_info.query_params then
        local result = _M._match_query(tries.query, request_info.query_params)
        if result then
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Found by query: ", result.data.namespace.namespace_code)
            return result.data.namespace
        end
    end
    
    ngx.log(ngx.ERR, "NAMESPACE_MATCHER: No matching namespace found")
    return nil
end

-- 匹配headers
function _M._match_headers(header_trie, headers)
    for field, value in pairs(headers) do
        local key = field .. ":" .. value
        local result = trie.search(header_trie, key)
        if result then
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Header match: ", field, "=", value, " -> ", result.namespace_id)
            return result
        end
    end
    return nil
end

-- 匹配body
function _M._match_body(body_trie, body_data)
    for field, value in pairs(body_data) do
        if type(value) == "string" then
            local key = field .. ":" .. value
            local result = trie.search(body_trie, key)
            if result then
                ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Body match: ", field, "=", value, " -> ", result.namespace_id)
                return result
            end
        end
    end
    return nil
end

-- 匹配query参数
function _M._match_query(query_trie, query_params)
    for field, value in pairs(query_params) do
        local key = field .. ":" .. value
        local result = trie.search(query_trie, key)
        if result then
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Query match: ", field, "=", value, " -> ", result.namespace_id)
            return result
        end
    end
    return nil
end

-- 获取命名空间信息
function _M.get_namespace_info(namespace_id)
    local namespaces = cache.get_namespaces() or {}
    
    for _, namespace in ipairs(namespaces) do
        if namespace.namespace_id == namespace_id then
            return namespace
        end
    end
    
    return nil
end

-- 验证命名空间是否有效
function _M.is_namespace_valid(namespace_id)
    local namespace = _M.get_namespace_info(namespace_id)
    return namespace and namespace.status == 1
end

-- 清空缓存
function _M.clear_cache()
    _cached_tries = {}
    _cache_timestamp = 0
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Cache cleared")
end

-- 获取缓存统计
function _M.get_cache_stats()
    local tries = _M._get_cached_tries()
    return {
        header_trie_size = trie.size(tries.header),
        body_trie_size = trie.size(tries.body),
        query_trie_size = trie.size(tries.query),
        cache_timestamp = _cache_timestamp,
        cache_age = ngx.time() - _cache_timestamp
    }
end

-- 调试：打印Trie树结构
function _M.debug_print_tries()
    local tries = _M._get_cached_tries()
    
    ngx.log(ngx.INFO, "=== Header Trie ===")
    trie.print(tries.header)
    
    ngx.log(ngx.INFO, "=== Body Trie ===")
    trie.print(tries.body)
    
    ngx.log(ngx.INFO, "=== Query Trie ===")
    trie.print(tries.query)
end

return _M