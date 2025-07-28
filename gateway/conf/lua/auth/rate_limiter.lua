-- 限流器模块
-- 负责管理各种限流计数器，支持配置变更时的重置

local _M = {}

local cjson = require "cjson"
local redis_client = require "utils.redis_client"

-- 获取计数器值
function _M.get_counter(counter_key)
    local redis = redis_client.get_connection()
    if not redis then
        return nil, "Failed to get Redis connection"
    end
    
    local value = redis:get(counter_key)
    redis_client.release_connection(redis)
    
    return tonumber(value) or 0
end

-- 增加计数器值
function _M.increment_counter(counter_key, value, ttl)
    value = value or 1
    ttl = ttl or 3600  -- 默认1小时过期
    
    local redis = redis_client.get_connection()
    if not redis then
        return false, "Failed to get Redis connection"
    end
    
    -- 使用Redis的INCR命令原子性增加
    local new_value = redis:incrby(counter_key, value)
    
    -- 设置过期时间（如果还没有设置）
    redis:expire(counter_key, ttl)
    
    redis_client.release_connection(redis)
    
    return true, new_value
end

-- 重置计数器
function _M.reset_counter(counter_key)
    local redis = redis_client.get_connection()
    if not redis then
        return false, "Failed to get Redis connection"
    end
    
    redis:set(counter_key, "0")
    redis_client.release_connection(redis)
    
    return true
end

-- 清理计数器
function _M.cleanup_counter(counter_key)
    local redis = redis_client.get_connection()
    if not redis then
        return false, "Failed to get Redis connection"
    end
    
    redis:del(counter_key)
    redis_client.release_connection(redis)
    
    return true
end

-- 获取Token使用量
function _M.get_token_usage(namespace_id, rule_id, window_start)
    local counter_key = string.format("rate_limit:%d:%d:token:%d", namespace_id, rule_id, window_start)
    return _M.get_counter(counter_key)
end

-- 增加Token使用量
function _M.increment_token_usage(namespace_id, rule_id, window_start, token_count, ttl)
    local counter_key = string.format("rate_limit:%d:%d:token:%d", namespace_id, rule_id, window_start)
    return _M.increment_counter(counter_key, token_count, ttl)
end

-- 获取QPS计数
function _M.get_qps_count(namespace_id, rule_id, window_start)
    local counter_key = string.format("rate_limit:%d:qps:%d", namespace_id, window_start)
    return _M.get_counter(counter_key)
end

-- 增加QPS计数
function _M.increment_qps_count(namespace_id, rule_id, window_start, count, ttl)
    local counter_key = string.format("rate_limit:%d:qps:%d", namespace_id, window_start)
    return _M.increment_counter(counter_key, count, ttl)
end

-- 获取并发连接数
function _M.get_concurrent_count(namespace_id)
    local counter_key = string.format("concurrent:%d:current", namespace_id)
    return _M.get_counter(counter_key)
end

-- 增加并发连接数
function _M.increment_concurrent_count(namespace_id, count)
    local counter_key = string.format("concurrent:%d:current", namespace_id)
    return _M.increment_counter(counter_key, count, 0)  -- 并发计数器不过期
end

-- 减少并发连接数
function _M.decrement_concurrent_count(namespace_id, count)
    count = count or 1
    local redis = redis_client.get_connection()
    if not redis then
        return false, "Failed to get Redis connection"
    end
    
    local counter_key = string.format("concurrent:%d:current", namespace_id)
    local new_value = redis:decrby(counter_key, count)
    
    -- 确保不会变成负数
    if new_value < 0 then
        redis:set(counter_key, "0")
        new_value = 0
    end
    
    redis_client.release_connection(redis)
    
    return true, new_value
end

-- 重置命名空间的所有计数器
function _M.reset_namespace_counters(namespace_id)
    local redis = redis_client.get_connection()
    if not redis then
        return false, "Failed to get Redis connection"
    end
    
    local current_time = ngx.time()
    
    -- 重置Token计数器
    local token_pattern = string.format("rate_limit:%d:*:token:*", namespace_id)
    local token_keys = redis:keys(token_pattern)
    if token_keys then
        for _, key in ipairs(token_keys) do
            redis:set(key, "0")
        end
    end
    
    -- 重置QPS计数器
    local qps_pattern = string.format("rate_limit:%d:qps:*", namespace_id)
    local qps_keys = redis:keys(qps_pattern)
    if qps_keys then
        for _, key in ipairs(qps_keys) do
            redis:set(key, "0")
        end
    end
    
    -- 重置并发计数器
    local concurrent_key = string.format("concurrent:%d:current", namespace_id)
    redis:set(concurrent_key, "0")
    
    redis_client.release_connection(redis)
    
    ngx.log(ngx.INFO, "Reset all counters for namespace: ", namespace_id)
    return true
end

-- 清理过期的计数器
function _M.cleanup_expired_counters()
    local redis = redis_client.get_connection()
    if not redis then
        return false, "Failed to get Redis connection"
    end
    
    local current_time = ngx.time()
    
    -- 清理过期的Token计数器（超过2小时）
    local token_pattern = "rate_limit:*:*:token:*"
    local token_keys = redis:keys(token_pattern)
    if token_keys then
        for _, key in ipairs(token_keys) do
            local ttl = redis:ttl(key)
            if ttl == -1 or ttl > 7200 then  -- 没有过期时间或超过2小时
                redis:del(key)
            end
        end
    end
    
    -- 清理过期的QPS计数器（超过2分钟）
    local qps_pattern = "rate_limit:*:qps:*"
    local qps_keys = redis:keys(qps_pattern)
    if qps_keys then
        for _, key in ipairs(qps_keys) do
            local ttl = redis:ttl(key)
            if ttl == -1 or ttl > 120 then  -- 没有过期时间或超过2分钟
                redis:del(key)
            end
        end
    end
    
    redis_client.release_connection(redis)
    
    ngx.log(ngx.INFO, "Cleaned up expired counters")
    return true
end

return _M 