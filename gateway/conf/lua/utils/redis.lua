-- Redis客户端工具模块
local redis = require "resty.redis"
local json = require "utils.json"

local _M = {}

-- 连接池配置
local pool_config = {
    max_idle_timeout = 60000,  -- 60秒空闲超时
    pool_size = 100            -- 连接池大小
}

-- 获取Redis连接（支持连接池）
function _M.get_connection()
    local red = redis:new()
    
    local config = require "core.init"
    local redis_config = config.get_config().redis
    
    -- 使用配置中的超时时间
    red:set_timeout(redis_config.timeout)
    
    local ok, err = red:connect(redis_config.host, redis_config.port)
    if not ok then
        ngx.log(ngx.ERR, "Failed to connect to Redis: ", err)
        return nil, err
    end
    
    -- 选择数据库
    if redis_config.db and redis_config.db ~= "0" then
        local ok, err = red:select(redis_config.db)
        if not ok then
            ngx.log(ngx.ERR, "Failed to select Redis database: ", err)
            red:close()
            return nil, err
        end
    end
    
    return red
end

-- 关闭Redis连接（支持连接池）
function _M.close_connection(red)
    if not red then
        return
    end
    
    -- 将连接放回连接池而不是直接关闭
    local ok, err = red:set_keepalive(pool_config.max_idle_timeout, pool_config.pool_size)
    if not ok then
        ngx.log(ngx.ERR, "Failed to set keepalive: ", err)
        red:close()
    end
end

-- 执行Redis命令
function _M.execute_command(command, ...)
    local red, err = _M.get_connection()
    if not red then
        return nil, err
    end
    
    local result, err = red[command](red, ...)
    _M.close_connection(red)  -- 使用连接池
    
    if not result then
        ngx.log(ngx.ERR, "Redis command failed: ", err)
        return nil, err
    end
    
    return result
end

-- 获取字符串值
function _M.get(key)
    return _M.execute_command("get", key)
end

-- 设置字符串值
function _M.set(key, value, ttl)
    if ttl then
        return _M.execute_command("setex", key, ttl, value)
    else
        return _M.execute_command("set", key, value)
    end
end

-- 获取并解析JSON值
function _M.get_json(key)
    local value, err = _M.get(key)
    if not value then
        return nil, err
    end
    
    return json.decode(value)
end

-- 设置JSON值
function _M.set_json(key, data, ttl)
    local json_str, err = json.encode(data)
    if not json_str then
        return nil, err
    end
    
    return _M.set(key, json_str, ttl)
end

-- 删除键
function _M.del(key)
    return _M.execute_command("del", key)
end

-- 检查键是否存在
function _M.exists(key)
    return _M.execute_command("exists", key)
end

-- 设置过期时间
function _M.expire(key, ttl)
    return _M.execute_command("expire", key, ttl)
end

-- 获取哈希值
function _M.hget(key, field)
    return _M.execute_command("hget", key, field)
end

-- 设置哈希值
function _M.hset(key, field, value)
    return _M.execute_command("hset", key, field, value)
end

-- 获取所有哈希值
function _M.hgetall(key)
    return _M.execute_command("hgetall", key)
end

-- 增加计数器
function _M.incr(key)
    return _M.execute_command("incr", key)
end

-- 增加计数器并设置过期时间
function _M.incr_ex(key, ttl)
    local red, err = _M.get_connection()
    if not red then
        return nil, err
    end
    
    local result, err = red:incr(key)
    if result then
        red:expire(key, ttl)
    end
    
    _M.close_connection(red)  -- 使用连接池
    return result, err
end

-- 增加指定数值并设置过期时间
function _M.incrby_ex(key, increment, ttl)
    local red, err = _M.get_connection()
    if not red then
        return nil, err
    end
    
    local result, err = red:incrby(key, increment)
    if result then
        red:expire(key, ttl)
    end
    
    _M.close_connection(red)  -- 使用连接池
    return result, err
end

-- 检查连接
function _M.ping()
    local red, err = _M.get_connection()
    if not red then
        return false, err
    end
    
    local result, err = red:ping()
    _M.close_connection(red)  -- 使用连接池
    
    return result == "PONG", err
end

return _M
