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
function _M._build_header_trie(namespaces)
    local header_trie = trie.create()
    
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Building header trie with ", #namespaces, " namespaces")
    
    local added_count = 0
    local skipped_count = 0
    
    for _, namespace in ipairs(namespaces) do
        ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Processing namespace: ", namespace.code, " (id: ", namespace.id, ")")
        
        if namespace.matcher and 
           namespace.matcher.matcher_type == "header" and 
           tonumber(namespace.matcher.status) == 1 and
           tonumber(namespace.status) == 1 then
            
            local field = namespace.matcher.match_field
            local value = namespace.matcher.match_value
            local key = field .. ":" .. value
            
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Adding header rule: ", key, " -> ", namespace.id)
            
            -- 插入到Trie树
            trie.insert(header_trie, key, namespace.id, {
                namespace = namespace,
                matcher = namespace.matcher
            })
            added_count = added_count + 1
        else
            ngx.log(ngx.WARN, "NAMESPACE_MATCHER: Skipping namespace ", namespace.code, " - matcher: ", namespace.matcher and "exists" or "nil", ", type: ", namespace.matcher and namespace.matcher.matcher_type or "nil", ", matcher_status: ", namespace.matcher and namespace.matcher.status or "nil", ", namespace_status: ", namespace.status)
            skipped_count = skipped_count + 1
        end
    end
    
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Header trie built - Added: ", added_count, ", Skipped: ", skipped_count, ", Total entries: ", trie.size(header_trie))
    
    -- 输出Trie树结构用于调试
    _M._debug_trie_structure(header_trie, "header")
    
    return header_trie
end

-- 创建body匹配的Trie树
function _M._build_body_trie(namespaces)
    local body_trie = trie.create()
    
    for _, namespace in ipairs(namespaces) do
        if namespace.matcher and 
           namespace.matcher.matcher_type == "body" and 
           tonumber(namespace.matcher.status) == 1 and
           tonumber(namespace.status) == 1 then
            
            local field = namespace.matcher.match_field
            local value = namespace.matcher.match_value
            local key = field .. ":" .. value
            
            trie.insert(body_trie, key, namespace.id, {
                namespace = namespace,
                matcher = namespace.matcher
            })
        end
    end
    
    return body_trie
end

-- 创建query匹配的Trie树
function _M._build_query_trie(namespaces)
    local query_trie = trie.create()
    
    for _, namespace in ipairs(namespaces) do
        if namespace.matcher and 
           namespace.matcher.matcher_type == "query" and 
           tonumber(namespace.matcher.status) == 1 and
           tonumber(namespace.status) == 1 then
            
            local field = namespace.matcher.match_field
            local value = namespace.matcher.match_value
            local key = field .. ":" .. value
            
            trie.insert(query_trie, key, namespace.id, {
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
        -- 只在DEBUG模式下记录缓存使用
        if ngx.var.debug == "true" then
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Using cached Trie trees")
        end
        return _cached_tries
    end
    
    -- 缓存失效，重新构建
    if ngx.var.debug == "true" then
        ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Building Trie trees...")
    end
    
    -- 只调用一次 get_namespaces()
    local loader = require "config.loader"
    local namespaces = loader.get_namespaces() or {}
    
    _cached_tries.header = _M._build_header_trie(namespaces)
    _cached_tries.body = _M._build_body_trie(namespaces)
    _cached_tries.query = _M._build_query_trie(namespaces)
    _cache_timestamp = current_time
    
    if ngx.var.debug == "true" then
        ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Trie trees built successfully")
    end
    return _cached_tries
end

-- 使用Trie树匹配命名空间
function _M.find_matching_namespace(request_info)
    -- 只在DEBUG模式下记录匹配开始
    if ngx.var.debug == "true" then
        ngx.log(ngx.INFO, "=== NAMESPACE_MATCHER: Starting Trie-based matching ===")
        ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Request info: ", json.encode(request_info or {}))
    end
    
    local tries = _M._get_cached_tries()
    
    -- 只在DEBUG模式下记录Trie树状态
    if ngx.var.debug == "true" then
        ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Got tries, header_trie exists: ", tries.header ~= nil)
    end
    
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
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Matching headers against trie...")
    
    for field, value in pairs(headers) do
        local key = field .. ":" .. value
        ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Checking header key: ", key)
        
        local result = trie.search(header_trie, key)
        if result then
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Header match found: ", field, "=", value, " -> namespace_id: ", result.namespace_id)
            return result
        else
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: No match for key: ", key)
        end
    end
    
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: No header matches found")
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
    local loader = require "config.loader"
    local namespaces = loader.get_namespaces() or {}
    
    for _, namespace in ipairs(namespaces) do
        if namespace.id == namespace_id then
            return namespace
        end
    end
    
    return nil
end

-- 验证命名空间是否有效
function _M.is_namespace_valid(namespace_id)
    local namespace = _M.get_namespace_info(namespace_id)
    return namespace and tonumber(namespace.status) == 1
end

-- 清空缓存
function _M.clear_cache()
    _cached_tries = {}
    _cache_timestamp = 0
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Cache cleared")
end

-- 调试Trie树结构
function _M._debug_trie_structure(trie_tree, trie_type)
    if not trie_tree then
        ngx.log(ngx.INFO, "NAMESPACE_MATCHER: ", trie_type, " trie is nil")
        return
    end
    
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: ", trie_type, " trie structure:")
    ngx.log(ngx.INFO, "  - Size: ", trie.size(trie_tree))
    
    -- 尝试获取所有键值对
    local keys = {}
    trie._collect_keys(trie_tree, "", keys)
    if #keys > 0 then
        local key_strings = {}
        for _, key_info in ipairs(keys) do
            table.insert(key_strings, key_info.key)
        end
        ngx.log(ngx.INFO, "  - Keys: ", table.concat(key_strings, ", "))
        for _, key_info in ipairs(keys) do
            ngx.log(ngx.INFO, "    ", key_info.key, " -> namespace_id: ", key_info.namespace_id)
        end
    else
        ngx.log(ngx.INFO, "  - No keys found")
    end
end

-- 强制重建Trie树（用于调试）
function _M.force_rebuild()
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Force rebuilding Trie trees...")
    _M.clear_cache()
    return _M._get_cached_tries()
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