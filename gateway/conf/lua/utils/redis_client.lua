-- Redis客户端工具模块
-- 提供Redis连接和操作功能

local _M = {}

local redis = require "resty.redis"

-- 获取Redis配置
local function get_redis_config()
    -- 从环境变量获取配置
    return {
        host = os.getenv("REDIS_HOST") or "redis",
        port = os.getenv("REDIS_PORT") or "6379",
        db = os.getenv("REDIS_DB") or "0",
        timeout = tonumber(os.getenv("REDIS_TIMEOUT")) or 1000,
        pool_size = tonumber(os.getenv("REDIS_POOL_SIZE")) or 100
    }
end

-- 连接池配置
local function get_pool_config()
    return {
        max_idle_timeout = 10000,  -- 10秒
        pool_size = get_redis_config().pool_size
    }
end

-- 获取Redis连接
local function get_redis_connection()
    local config = get_redis_config()
    local red = redis:new()
    
    -- 设置超时
    red:set_timeout(config.timeout)
    
    -- 连接Redis
    local ok, err = red:connect(config.host, config.port)
    if not ok then
        return nil, "Failed to connect to Redis: " .. (err or "unknown error")
    end
    
    -- 选择数据库
    if config.db and config.db ~= "0" then
        local ok, err = red:select(tonumber(config.db))
        if not ok then
            return nil, "Failed to select Redis database: " .. (err or "unknown error")
        end
    end
    
    return red
end

-- 执行Redis命令并自动管理连接
local function execute_redis_command(command, ...)
    local red, err = get_redis_connection()
    if not red then
        return nil, err
    end
    
    local pool_config = get_pool_config()
    
    -- 确保连接被放回连接池
    local function cleanup()
        local ok, err = red:set_keepalive(pool_config.max_idle_timeout, pool_config.pool_size)
        if not ok then
            ngx.log(ngx.ERR, "Failed to put Redis connection back to pool: ", err)
        end
    end
    
    -- 执行命令
    local result, err = red[command](red, ...)
    if not result then
        cleanup()
        return nil, "Redis " .. command .. " failed: " .. (err or "unknown error")
    end
    
    cleanup()
    return result
end

-- 基本操作
function _M.get(key)
    return execute_redis_command("get", key)
end

function _M.set(key, value, ex)
    if ex then
        return execute_redis_command("setex", key, ex, value)
    else
        return execute_redis_command("set", key, value)
    end
end

function _M.del(key)
    return execute_redis_command("del", key)
end

function _M.exists(key)
    return execute_redis_command("exists", key)
end

function _M.expire(key, seconds)
    return execute_redis_command("expire", key, seconds)
end

function _M.ttl(key)
    return execute_redis_command("ttl", key)
end

-- 计数器操作
function _M.incr(key)
    return execute_redis_command("incr", key)
end

function _M.incrby(key, increment)
    return execute_redis_command("incrby", key, increment)
end

function _M.decr(key)
    return execute_redis_command("decr", key)
end

function _M.decrby(key, decrement)
    return execute_redis_command("decrby", key, decrement)
end

-- 哈希操作
function _M.hget(key, field)
    return execute_redis_command("hget", key, field)
end

function _M.hset(key, field, value)
    return execute_redis_command("hset", key, field, value)
end

function _M.hgetall(key)
    return execute_redis_command("hgetall", key)
end

function _M.hdel(key, field)
    return execute_redis_command("hdel", key, field)
end

function _M.hexists(key, field)
    return execute_redis_command("hexists", key, field)
end

-- 列表操作
function _M.lpush(key, value)
    return execute_redis_command("lpush", key, value)
end

function _M.rpush(key, value)
    return execute_redis_command("rpush", key, value)
end

function _M.lpop(key)
    return execute_redis_command("lpop", key)
end

function _M.rpop(key)
    return execute_redis_command("rpop", key)
end

function _M.lrange(key, start, stop)
    return execute_redis_command("lrange", key, start, stop)
end

function _M.llen(key)
    return execute_redis_command("llen", key)
end

-- 集合操作
function _M.sadd(key, member)
    return execute_redis_command("sadd", key, member)
end

function _M.srem(key, member)
    return execute_redis_command("srem", key, member)
end

function _M.sismember(key, member)
    return execute_redis_command("sismember", key, member)
end

function _M.smembers(key)
    return execute_redis_command("smembers", key)
end

function _M.scard(key)
    return execute_redis_command("scard", key)
end

-- 有序集合操作
function _M.zadd(key, score, member)
    return execute_redis_command("zadd", key, score, member)
end

function _M.zrem(key, member)
    return execute_redis_command("zrem", key, member)
end

function _M.zscore(key, member)
    return execute_redis_command("zscore", key, member)
end

function _M.zrange(key, start, stop, withscores)
    if withscores then
        return execute_redis_command("zrange", key, start, stop, "withscores")
    else
        return execute_redis_command("zrange", key, start, stop)
    end
end

function _M.zcard(key)
    return execute_redis_command("zcard", key)
end

-- 键操作
function _M.keys(pattern)
    return execute_redis_command("keys", pattern)
end

function _M.scan(cursor, pattern, count)
    if pattern and count then
        return execute_redis_command("scan", cursor, "match", pattern, "count", count)
    elseif pattern then
        return execute_redis_command("scan", cursor, "match", pattern)
    elseif count then
        return execute_redis_command("scan", cursor, "count", count)
    else
        return execute_redis_command("scan", cursor)
    end
end

-- 事务操作
function _M.multi()
    local red, err = get_redis_connection()
    if not red then
        return nil, err
    end
    
    local ok, err = red:multi()
    if not ok then
        red:close()
        return nil, "Failed to start Redis transaction: " .. (err or "unknown error")
    end
    
    return red
end

function _M.exec(red)
    if not red then
        return nil, "No Redis connection provided"
    end
    
    local result, err = red:exec()
    local pool_config = get_pool_config()
    local ok, err2 = red:set_keepalive(pool_config.max_idle_timeout, pool_config.pool_size)
    if not ok then
        ngx.log(ngx.ERR, "Failed to put Redis connection back to pool: ", err2)
    end
    
    if not result then
        return nil, "Redis transaction failed: " .. (err or "unknown error")
    end
    
    return result
end

-- 健康检查
function _M.ping()
    return execute_redis_command("ping")
end

-- 获取Redis信息
function _M.info(section)
    if section then
        return execute_redis_command("info", section)
    else
        return execute_redis_command("info")
    end
end

-- 获取Redis配置
function _M.config_get(parameter)
    return execute_redis_command("config", "get", parameter)
end

-- 设置Redis配置
function _M.config_set(parameter, value)
    return execute_redis_command("config", "set", parameter, value)
end

-- 清理过期键
function _M.memory_purge()
    return execute_redis_command("memory", "purge")
end

-- 获取内存使用情况
function _M.memory_usage(key)
    return execute_redis_command("memory", "usage", key)
end

-- 批量操作
function _M.pipeline(commands)
    local red, err = get_redis_connection()
    if not red then
        return nil, err
    end
    
    local pool_config = get_pool_config()
    
    -- 确保连接被放回连接池
    local function cleanup()
        local ok, err = red:set_keepalive(pool_config.max_idle_timeout, pool_config.pool_size)
        if not ok then
            ngx.log(ngx.ERR, "Failed to put Redis connection back to pool: ", err)
        end
    end
    
    -- 执行批量命令
    local results = {}
    for i, cmd in ipairs(commands) do
        local command = cmd[1]
        local args = {}
        for j = 2, #cmd do
            table.insert(args, cmd[j])
        end
        
        local result, err = red[command](red, unpack(args))
        if not result then
            cleanup()
            return nil, "Redis pipeline command " .. i .. " failed: " .. (err or "unknown error")
        end
        
        table.insert(results, result)
    end
    
    cleanup()
    return results
end

return _M 