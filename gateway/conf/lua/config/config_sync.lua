-- 配置同步模块
local _M = {}

local cjson = require "cjson"
local redis = require "resty.redis"
local http = require "resty.http"

-- 配置中心API基础URL
local CONFIG_CENTER_BASE_URL = "http://config-center:8000"

-- 同步所有配置
function _M.sync_all_configs()
    local ok, err = pcall(function()
        -- 同步命名空间配置
        _M.sync_namespaces()
        
        -- 同步规则配置
        _M.sync_rules()
        
        -- 同步匹配器配置
        _M.sync_matchers()
        
        -- 同步上游服务器配置
        _M.sync_upstream_servers()
        
        -- 同步代理规则配置
        _M.sync_proxy_rules()
    end)
    
    if not ok then
        ngx.log(ngx.ERR, "Failed to sync configurations: ", err)
        return false
    end
    
    return true
end

-- 同步命名空间配置
function _M.sync_namespaces()
    local httpc = http.new()
    local res, err = httpc:request_uri(CONFIG_CENTER_BASE_URL .. "/api/v1/namespaces", {
        method = "GET",
        headers = {
            ["Content-Type"] = "application/json"
        }
    })
    
    if not res then
        ngx.log(ngx.ERR, "Failed to sync namespaces: ", err)
        return false
    end
    
    if res.status == 200 then
        local data = cjson.decode(res.body)
        if data and data.data then
            -- 缓存到Redis
            local red = redis:new()
            local ok, err = red:connect("redis", 6379)
            if ok then
                red:set("namespaces", cjson.encode(data.data))
                red:expire("namespaces", 300) -- 5分钟过期
                red:close()
            end
        end
    end
    
    return true
end

-- 同步规则配置
function _M.sync_rules()
    local httpc = http.new()
    local res, err = httpc:request_uri(CONFIG_CENTER_BASE_URL .. "/api/v1/rules", {
        method = "GET",
        headers = {
            ["Content-Type"] = "application/json"
        }
    })
    
    if not res then
        ngx.log(ngx.ERR, "Failed to sync rules: ", err)
        return false
    end
    
    if res.status == 200 then
        local data = cjson.decode(res.body)
        if data and data.data then
            -- 缓存到Redis
            local red = redis:new()
            local ok, err = red:connect("redis", 6379)
            if ok then
                red:set("rules", cjson.encode(data.data))
                red:expire("rules", 300) -- 5分钟过期
                red:close()
            end
        end
    end
    
    return true
end

-- 同步匹配器配置
function _M.sync_matchers()
    local httpc = http.new()
    local res, err = httpc:request_uri(CONFIG_CENTER_BASE_URL .. "/api/v1/matchers", {
        method = "GET",
        headers = {
            ["Content-Type"] = "application/json"
        }
    })
    
    if not res then
        ngx.log(ngx.ERR, "Failed to sync matchers: ", err)
        return false
    end
    
    if res.status == 200 then
        local data = cjson.decode(res.body)
        if data and data.data then
            -- 缓存到Redis
            local red = redis:new()
            local ok, err = red:connect("redis", 6379)
            if ok then
                red:set("matchers", cjson.encode(data.data))
                red:expire("matchers", 300) -- 5分钟过期
                red:close()
            end
        end
    end
    
    return true
end

-- 同步上游服务器配置
function _M.sync_upstream_servers()
    local httpc = http.new()
    local res, err = httpc:request_uri(CONFIG_CENTER_BASE_URL .. "/api/v1/upstream-servers", {
        method = "GET",
        headers = {
            ["Content-Type"] = "application/json"
        }
    })
    
    if not res then
        ngx.log(ngx.ERR, "Failed to sync upstream servers: ", err)
        return false
    end
    
    if res.status == 200 then
        local data = cjson.decode(res.body)
        if data and data.data then
            -- 缓存到Redis
            local red = redis:new()
            local ok, err = red:connect("redis", 6379)
            if ok then
                red:set("upstream_servers", cjson.encode(data.data))
                red:expire("upstream_servers", 300) -- 5分钟过期
                red:close()
            end
        end
    end
    
    return true
end

-- 同步代理规则配置
function _M.sync_proxy_rules()
    local httpc = http.new()
    local res, err = httpc:request_uri(CONFIG_CENTER_BASE_URL .. "/api/v1/proxy-rules", {
        method = "GET",
        headers = {
            ["Content-Type"] = "application/json"
        }
    })
    
    if not res then
        ngx.log(ngx.ERR, "Failed to sync proxy rules: ", err)
        return false
    end
    
    if res.status == 200 then
        local data = cjson.decode(res.body)
        if data and data.data then
            -- 缓存到Redis
            local red = redis:new()
            local ok, err = red:connect("redis", 6379)
            if ok then
                red:set("proxy_rules", cjson.encode(data.data))
                red:expire("proxy_rules", 300) -- 5分钟过期
                red:close()
            end
        end
    end
    
    return true
end

return _M 