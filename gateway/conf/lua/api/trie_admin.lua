-- Trie匹配器管理接口
-- 提供Trie树的监控和管理功能

local namespace_matcher = require "auth.namespace_matcher"
local json = require "utils.json"

local _M = {}

-- 获取Trie树统计信息
function _M.get_stats()
    local stats = namespace_matcher.get_cache_stats()
    
    return {
        success = true,
        data = {
            cache_stats = stats,
            timestamp = ngx.time()
        }
    }
end

-- 清空Trie缓存
function _M.clear_cache()
    namespace_matcher.clear_cache()
    
    return {
        success = true,
        message = "Trie cache cleared successfully"
    }
end

-- 重新构建Trie树
function _M.rebuild_tries()
    namespace_matcher.clear_cache()
    -- 触发重新构建
    local stats = namespace_matcher.get_cache_stats()
    
    return {
        success = true,
        message = "Trie trees rebuilt successfully",
        data = stats
    }
end

-- 调试：打印Trie树结构
function _M.debug_print()
    namespace_matcher.debug_print_tries()
    
    return {
        success = true,
        message = "Trie structure printed to logs"
    }
end

-- 测试Trie匹配
function _M.test_match()
    local request_info = {
        headers = {
            ["channelcode"] = "web"
        },
        body = '{"user_id": "12345"}',
        query_params = {
            ["version"] = "v2"
        }
    }
    
    local namespace = namespace_matcher.find_matching_namespace(request_info)
    
    return {
        success = true,
        data = {
            request_info = request_info,
            matched_namespace = namespace,
            timestamp = ngx.time()
        }
    }
end

-- 获取所有可用的匹配字段
function _M.get_available_fields()
    local stats = namespace_matcher.get_cache_stats()
    
    return {
        success = true,
        data = {
            header_fields_count = stats.header_trie_size,
            body_fields_count = stats.body_trie_size,
            query_fields_count = stats.query_trie_size,
            cache_age = stats.cache_age
        }
    }
end

return _M
