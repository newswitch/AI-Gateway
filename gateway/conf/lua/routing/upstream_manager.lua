local cjson = require "cjson"
local redis = require "resty.redis"
local mysql = require "resty.mysql"

local _M = {}

-- 缓存配置
local CACHE_TTL = 300 -- 5分钟缓存
local UPSTREAM_CACHE_KEY = "upstream_servers"

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

-- 获取MySQL连接
local function get_mysql_conn()
    local db, err = mysql:new()
    if not db then
        ngx.log(ngx.ERR, "Failed to create MySQL connection: ", err)
        return nil
    end
    
    db:set_timeout(1000)
    
    local ok, err = db:connect({
        host = "mysql",
        port = 3306,
        database = "ai_gateway_config",
        user = "ai_gateway",
        password = "ai_gateway_pass"
    })
    
    if not ok then
        ngx.log(ngx.ERR, "Failed to connect to MySQL: ", err)
        return nil
    end
    
    return db
end

-- 从Redis获取upstream配置
function _M.get_upstream_from_redis()
    local red = get_redis_conn()
    if not red then
        return nil
    end
    
    local upstream_data, err = red:get(UPSTREAM_CACHE_KEY)
    if not upstream_data or upstream_data == ngx.null then
        red:close()
        return nil
    end
    
    red:close()
    
    local ok, upstream_servers = pcall(cjson.decode, upstream_data)
    if not ok then
        ngx.log(ngx.ERR, "Failed to decode upstream data: ", upstream_servers)
        return nil
    end
    
    return upstream_servers
end

-- 从MySQL获取upstream配置
function _M.get_upstream_from_mysql()
    local db = get_mysql_conn()
    if not db then
        return nil
    end
    
    local sql = [[
        SELECT 
            us.id,
            us.server_name,
            us.server_address,
            us.server_port,
            us.server_type,
            us.weight,
            us.max_connections,
            us.health_check_url,
            us.is_active,
            us.created_at,
            us.updated_at
        FROM upstream_servers us
        WHERE us.is_active = 1
        ORDER BY us.weight DESC, us.id ASC
    ]]
    
    local res, err = db:query(sql)
    if not res then
        ngx.log(ngx.ERR, "Failed to query upstream servers: ", err)
        db:close()
        return nil
    end
    
    db:close()
    
    local upstream_servers = {}
    for _, row in ipairs(res) do
        local server = {
            id = row.id,
            name = row.server_name,
            address = row.server_address,
            port = row.server_port,
            type = row.server_type,
            weight = row.weight or 1,
            max_connections = row.max_connections or 100,
            health_check_url = row.health_check_url,
            is_active = row.is_active == 1
        }
        table.insert(upstream_servers, server)
    end
    
    return upstream_servers
end

-- 更新Redis缓存
function _M.update_redis_cache(upstream_servers)
    local red = get_redis_conn()
    if not red then
        return false
    end
    
    local upstream_data = cjson.encode(upstream_servers)
    local ok, err = red:setex(UPSTREAM_CACHE_KEY, CACHE_TTL, upstream_data)
    if not ok then
        ngx.log(ngx.ERR, "Failed to update Redis cache: ", err)
        red:close()
        return false
    end
    
    red:close()
    return true
end

-- 健康检查
function _M.health_check(server)
    if not server.health_check_url then
        return true -- 如果没有健康检查URL，假设服务器是健康的
    end
    
    local http = require "resty.http"
    local httpc = http.new()
    
    httpc:set_timeout(2000)
    
    local url = string.format("http://%s:%s%s", 
        server.address, 
        server.port, 
        server.health_check_url
    )
    
    local res, err = httpc:request_uri(url, {
        method = "GET",
        headers = {
            ["User-Agent"] = "AI-Gateway-Health-Check"
        }
    })
    
    if not res then
        ngx.log(ngx.WARN, "Health check failed for ", url, ": ", err)
        return false
    end
    
    return res.status == 200
end

-- 负载均衡算法
function _M.select_server(upstream_servers, algorithm)
    if not upstream_servers or #upstream_servers == 0 then
        return nil
    end
    
    algorithm = algorithm or "round_robin"
    
    if algorithm == "round_robin" then
        return _M.round_robin_select(upstream_servers)
    elseif algorithm == "weighted_round_robin" then
        return _M.weighted_round_robin_select(upstream_servers)
    elseif algorithm == "least_connections" then
        return _M.least_connections_select(upstream_servers)
    elseif algorithm == "ip_hash" then
        return _M.ip_hash_select(upstream_servers)
    elseif algorithm == "random" then
        return _M.random_select(upstream_servers)
    else
        return _M.round_robin_select(upstream_servers)
    end
end

-- 轮询选择
function _M.round_robin_select(upstream_servers)
    local ngx_shared = ngx.shared.upstream_state
    local current_index = ngx_shared:get("round_robin_index") or 0
    
    local healthy_servers = {}
    for _, server in ipairs(upstream_servers) do
        if _M.health_check(server) then
            table.insert(healthy_servers, server)
        end
    end
    
    if #healthy_servers == 0 then
        return nil
    end
    
    current_index = (current_index % #healthy_servers) + 1
    ngx_shared:set("round_robin_index", current_index)
    
    return healthy_servers[current_index]
end

-- 加权轮询选择
function _M.weighted_round_robin_select(upstream_servers)
    local ngx_shared = ngx.shared.upstream_state
    local current_weight = ngx_shared:get("weighted_index") or 0
    
    local healthy_servers = {}
    for _, server in ipairs(upstream_servers) do
        if _M.health_check(server) then
            table.insert(healthy_servers, server)
        end
    end
    
    if #healthy_servers == 0 then
        return nil
    end
    
    -- 找到权重最大的服务器
    local max_weight = 0
    for _, server in ipairs(healthy_servers) do
        max_weight = math.max(max_weight, server.weight or 1)
    end
    
    current_weight = (current_weight % max_weight) + 1
    ngx_shared:set("weighted_index", current_weight)
    
    -- 选择当前权重对应的服务器
    for _, server in ipairs(healthy_servers) do
        if (server.weight or 1) >= current_weight then
            return server
        end
    end
    
    return healthy_servers[1]
end

-- 最少连接选择
function _M.least_connections_select(upstream_servers)
    local healthy_servers = {}
    for _, server in ipairs(upstream_servers) do
        if _M.health_check(server) then
            table.insert(healthy_servers, server)
        end
    end
    
    if #healthy_servers == 0 then
        return nil
    end
    
    local ngx_shared = ngx.shared.upstream_state
    local min_connections = math.huge
    local selected_server = nil
    
    for _, server in ipairs(healthy_servers) do
        local conn_key = "connections_" .. server.id
        local connections = ngx_shared:get(conn_key) or 0
        
        if connections < min_connections then
            min_connections = connections
            selected_server = server
        end
    end
    
    return selected_server
end

-- IP哈希选择
function _M.ip_hash_select(upstream_servers)
    local healthy_servers = {}
    for _, server in ipairs(upstream_servers) do
        if _M.health_check(server) then
            table.insert(healthy_servers, server)
        end
    end
    
    if #healthy_servers == 0 then
        return nil
    end
    
    local client_ip = ngx.var.remote_addr
    local hash = 0
    
    for i = 1, #client_ip do
        hash = ((hash * 31) + string.byte(client_ip, i)) % 0x7fffffff
    end
    
    local index = (hash % #healthy_servers) + 1
    return healthy_servers[index]
end

-- 随机选择
function _M.random_select(upstream_servers)
    local healthy_servers = {}
    for _, server in ipairs(upstream_servers) do
        if _M.health_check(server) then
            table.insert(healthy_servers, server)
        end
    end
    
    if #healthy_servers == 0 then
        return nil
    end
    
    local index = math.random(1, #healthy_servers)
    return healthy_servers[index]
end

-- 获取上游服务器URL
function _M.get_upstream_server_url(server)
    if not server then
        return nil
    end
    
    local protocol = "http"
    if server.type == "https" then
        protocol = "https"
    end
    
    return string.format("%s://%s:%s", protocol, server.address, server.port)
end

-- 主要接口：获取上游服务器
function _M.get_upstream_server()
    -- 首先尝试从Redis获取
    local upstream_servers = _M.get_upstream_from_redis()
    
    -- 如果Redis中没有，从MySQL获取并缓存
    if not upstream_servers then
        upstream_servers = _M.get_upstream_from_mysql()
        if upstream_servers then
            _M.update_redis_cache(upstream_servers)
        end
    end
    
    if not upstream_servers or #upstream_servers == 0 then
        return nil
    end
    
    -- 根据负载均衡算法选择服务器
    local selected_server = _M.select_server(upstream_servers, "round_robin")
    if not selected_server then
        return nil
    end
    
    -- 返回服务器URL
    return _M.get_upstream_server_url(selected_server)
end

-- 刷新upstream配置
function _M.refresh_upstream_config()
    local upstream_servers = _M.get_upstream_from_mysql()
    if upstream_servers then
        _M.update_redis_cache(upstream_servers)
        return true
    end
    return false
end

return _M 