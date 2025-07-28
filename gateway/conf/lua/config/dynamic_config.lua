local cjson = require "cjson"
local redis = require "resty.redis"
local mysql = require "resty.mysql"

local _M = {}

-- 缓存配置
local CACHE_TTL = 300 -- 5分钟缓存
local CONFIG_KEYS = {
    UPSTREAM_SERVERS = "upstream_servers",
    PROXY_RULES = "proxy_rules", 
    NAMESPACES = "namespaces",
    RULES = "rules",
    MATCHERS = "matchers",
    NGINX_CONFIG = "nginx_config"
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

-- 从Redis获取配置
function _M.get_config_from_redis(config_key)
    local red = get_redis_conn()
    if not red then
        return nil
    end
    
    local config_data, err = red:get(config_key)
    if not config_data or config_data == ngx.null then
        red:close()
        return nil
    end
    
    red:close()
    
    local ok, config = pcall(cjson.decode, config_data)
    if not ok then
        ngx.log(ngx.ERR, "Failed to decode config data for ", config_key, ": ", config)
        return nil
    end
    
    return config
end

-- 从MySQL获取upstream服务器配置
function _M.get_upstream_servers_from_mysql()
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

-- 从MySQL获取代理规则配置
function _M.get_proxy_rules_from_mysql()
    local db = get_mysql_conn()
    if not db then
        return nil
    end
    
    local sql = [[
        SELECT 
            pr.id,
            pr.rule_name,
            pr.namespace_id,
            pr.upstream_server_id,
            pr.path_pattern,
            pr.method_pattern,
            pr.header_pattern,
            pr.body_pattern,
            pr.priority,
            pr.is_active,
            pr.created_at,
            pr.updated_at,
            n.namespace_name,
            n.namespace_code,
            us.server_name,
            us.server_address,
            us.server_port,
            us.server_type
        FROM proxy_rules pr
        LEFT JOIN namespaces n ON pr.namespace_id = n.id
        LEFT JOIN upstream_servers us ON pr.upstream_server_id = us.id
        WHERE pr.is_active = 1
        ORDER BY pr.priority ASC, pr.id ASC
    ]]
    
    local res, err = db:query(sql)
    if not res then
        ngx.log(ngx.ERR, "Failed to query proxy rules: ", err)
        db:close()
        return nil
    end
    
    db:close()
    
    local proxy_rules = {}
    for _, row in ipairs(res) do
        local rule = {
            id = row.id,
            name = row.rule_name,
            namespace_id = row.namespace_id,
            namespace_name = row.namespace_name,
            namespace_code = row.namespace_code,
            upstream_server_id = row.upstream_server_id,
            upstream_server_name = row.server_name,
            upstream_server_address = row.server_address,
            upstream_server_port = row.server_port,
            upstream_server_type = row.server_type,
            path_pattern = row.path_pattern,
            method_pattern = row.method_pattern,
            header_pattern = row.header_pattern,
            body_pattern = row.body_pattern,
            priority = row.priority or 0,
            is_active = row.is_active == 1
        }
        table.insert(proxy_rules, rule)
    end
    
    return proxy_rules
end

-- 从MySQL获取命名空间配置
function _M.get_namespaces_from_mysql()
    local db = get_mysql_conn()
    if not db then
        return nil
    end
    
    local sql = [[
        SELECT 
            id,
            namespace_name,
            namespace_code,
            description,
            is_active,
            created_at,
            updated_at
        FROM namespaces
        WHERE is_active = 1
        ORDER BY id ASC
    ]]
    
    local res, err = db:query(sql)
    if not res then
        ngx.log(ngx.ERR, "Failed to query namespaces: ", err)
        db:close()
        return nil
    end
    
    db:close()
    
    local namespaces = {}
    for _, row in ipairs(res) do
        local namespace = {
            id = row.id,
            name = row.namespace_name,
            code = row.namespace_code,
            description = row.description,
            is_active = row.is_active == 1
        }
        table.insert(namespaces, namespace)
    end
    
    return namespaces
end

-- 从MySQL获取规则配置
function _M.get_rules_from_mysql()
    local db = get_mysql_conn()
    if not db then
        return nil
    end
    
    local sql = [[
        SELECT 
            r.id,
            r.namespace_id,
            r.rule_type,
            r.rule_name,
            r.rule_config,
            r.priority,
            r.is_active,
            r.created_at,
            r.updated_at,
            n.namespace_name,
            n.namespace_code
        FROM rules r
        LEFT JOIN namespaces n ON r.namespace_id = n.id
        WHERE r.is_active = 1
        ORDER BY r.priority ASC, r.id ASC
    ]]
    
    local res, err = db:query(sql)
    if not res then
        ngx.log(ngx.ERR, "Failed to query rules: ", err)
        db:close()
        return nil
    end
    
    db:close()
    
    local rules = {}
    for _, row in ipairs(res) do
        local rule_config = {}
        if row.rule_config then
            local ok, config = pcall(cjson.decode, row.rule_config)
            if ok then
                rule_config = config
            end
        end
        
        local rule = {
            id = row.id,
            namespace_id = row.namespace_id,
            namespace_name = row.namespace_name,
            namespace_code = row.namespace_code,
            rule_type = row.rule_type,
            rule_name = row.rule_name,
            rule_config = rule_config,
            priority = row.priority or 0,
            is_active = row.is_active == 1
        }
        table.insert(rules, rule)
    end
    
    return rules
end

-- 从MySQL获取匹配器配置
function _M.get_matchers_from_mysql()
    local db = get_mysql_conn()
    if not db then
        return nil
    end
    
    local sql = [[
        SELECT 
            mm.id,
            mm.namespace_id,
            mm.matcher_name,
            mm.matcher_type,
            mm.matcher_config,
            mm.priority,
            mm.is_active,
            mm.created_at,
            mm.updated_at,
            n.namespace_name,
            n.namespace_code
        FROM message_matchers mm
        LEFT JOIN namespaces n ON mm.namespace_id = n.id
        WHERE mm.is_active = 1
        ORDER BY mm.priority ASC, mm.id ASC
    ]]
    
    local res, err = db:query(sql)
    if not res then
        ngx.log(ngx.ERR, "Failed to query matchers: ", err)
        db:close()
        return nil
    end
    
    db:close()
    
    local matchers = {}
    for _, row in ipairs(res) do
        local matcher_config = {}
        if row.matcher_config then
            local ok, config = pcall(cjson.decode, row.matcher_config)
            if ok then
                matcher_config = config
            end
        end
        
        local matcher = {
            id = row.id,
            namespace_id = row.namespace_id,
            namespace_name = row.namespace_name,
            namespace_code = row.namespace_code,
            matcher_name = row.matcher_name,
            matcher_type = row.matcher_type,
            matcher_config = matcher_config,
            priority = row.priority or 0,
            is_active = row.is_active == 1
        }
        table.insert(matchers, matcher)
    end
    
    return matchers
end

-- 从MySQL获取Nginx全局配置
function _M.get_nginx_config_from_mysql()
    local db = get_mysql_conn()
    if not db then
        return nil
    end
    
    local sql = [[
        SELECT 
            id,
            config_type,
            config_name,
            config_content,
            is_active,
            created_at,
            updated_at
        FROM nginx_config
        WHERE is_active = 1
        ORDER BY config_type ASC, id ASC
    ]]
    
    local res, err = db:query(sql)
    if not res then
        ngx.log(ngx.ERR, "Failed to query nginx config: ", err)
        db:close()
        return nil
    end
    
    db:close()
    
    local nginx_config = {
        global = {},
        http = {},
        server = {},
        upstream = {}
    }
    
    for _, row in ipairs(res) do
        local config = {
            id = row.id,
            type = row.config_type,
            name = row.config_name,
            content = row.config_content,
            is_active = row.is_active == 1
        }
        
        if row.config_type == "global" then
            table.insert(nginx_config.global, config)
        elseif row.config_type == "http" then
            table.insert(nginx_config.http, config)
        elseif row.config_type == "server" then
            table.insert(nginx_config.server, config)
        elseif row.config_type == "upstream" then
            table.insert(nginx_config.upstream, config)
        end
    end
    
    return nginx_config
end

-- 更新Redis缓存
function _M.update_redis_cache(config_key, config_data)
    local red = get_redis_conn()
    if not red then
        return false
    end
    
    local data = cjson.encode(config_data)
    local ok, err = red:setex(config_key, CACHE_TTL, data)
    if not ok then
        ngx.log(ngx.ERR, "Failed to update Redis cache for ", config_key, ": ", err)
        red:close()
        return false
    end
    
    red:close()
    return true
end

-- 获取所有配置
function _M.get_all_configs()
    local configs = {}
    
    -- 获取upstream服务器配置
    local upstream_servers = _M.get_config_from_redis(CONFIG_KEYS.UPSTREAM_SERVERS)
    if not upstream_servers then
        upstream_servers = _M.get_upstream_servers_from_mysql()
        if upstream_servers then
            _M.update_redis_cache(CONFIG_KEYS.UPSTREAM_SERVERS, upstream_servers)
        end
    end
    configs.upstream_servers = upstream_servers or {}
    
    -- 获取代理规则配置
    local proxy_rules = _M.get_config_from_redis(CONFIG_KEYS.PROXY_RULES)
    if not proxy_rules then
        proxy_rules = _M.get_proxy_rules_from_mysql()
        if proxy_rules then
            _M.update_redis_cache(CONFIG_KEYS.PROXY_RULES, proxy_rules)
        end
    end
    configs.proxy_rules = proxy_rules or {}
    
    -- 获取命名空间配置
    local namespaces = _M.get_config_from_redis(CONFIG_KEYS.NAMESPACES)
    if not namespaces then
        namespaces = _M.get_namespaces_from_mysql()
        if namespaces then
            _M.update_redis_cache(CONFIG_KEYS.NAMESPACES, namespaces)
        end
    end
    configs.namespaces = namespaces or {}
    
    -- 获取规则配置
    local rules = _M.get_config_from_redis(CONFIG_KEYS.RULES)
    if not rules then
        rules = _M.get_rules_from_mysql()
        if rules then
            _M.update_redis_cache(CONFIG_KEYS.RULES, rules)
        end
    end
    configs.rules = rules or {}
    
    -- 获取匹配器配置
    local matchers = _M.get_config_from_redis(CONFIG_KEYS.MATCHERS)
    if not matchers then
        matchers = _M.get_matchers_from_mysql()
        if matchers then
            _M.update_redis_cache(CONFIG_KEYS.MATCHERS, matchers)
        end
    end
    configs.matchers = matchers or {}
    
    -- 获取Nginx配置
    local nginx_config = _M.get_config_from_redis(CONFIG_KEYS.NGINX_CONFIG)
    if not nginx_config then
        nginx_config = _M.get_nginx_config_from_mysql()
        if nginx_config then
            _M.update_redis_cache(CONFIG_KEYS.NGINX_CONFIG, nginx_config)
        end
    end
    configs.nginx_config = nginx_config or {}
    
    return configs
end

-- 刷新所有配置
function _M.refresh_all_configs()
    local success = true
    
    -- 刷新upstream服务器配置
    local upstream_servers = _M.get_upstream_servers_from_mysql()
    if upstream_servers then
        success = success and _M.update_redis_cache(CONFIG_KEYS.UPSTREAM_SERVERS, upstream_servers)
    end
    
    -- 刷新代理规则配置
    local proxy_rules = _M.get_proxy_rules_from_mysql()
    if proxy_rules then
        success = success and _M.update_redis_cache(CONFIG_KEYS.PROXY_RULES, proxy_rules)
    end
    
    -- 刷新命名空间配置
    local namespaces = _M.get_namespaces_from_mysql()
    if namespaces then
        success = success and _M.update_redis_cache(CONFIG_KEYS.NAMESPACES, namespaces)
    end
    
    -- 刷新规则配置
    local rules = _M.get_rules_from_mysql()
    if rules then
        success = success and _M.update_redis_cache(CONFIG_KEYS.RULES, rules)
    end
    
    -- 刷新匹配器配置
    local matchers = _M.get_matchers_from_mysql()
    if matchers then
        success = success and _M.update_redis_cache(CONFIG_KEYS.MATCHERS, matchers)
    end
    
    -- 刷新Nginx配置
    local nginx_config = _M.get_nginx_config_from_mysql()
    if nginx_config then
        success = success and _M.update_redis_cache(CONFIG_KEYS.NGINX_CONFIG, nginx_config)
    end
    
    return success
end

-- 根据请求动态选择upstream服务器
function _M.select_upstream_server(request_info)
    local configs = _M.get_all_configs()
    
    -- 首先根据代理规则匹配
    for _, rule in ipairs(configs.proxy_rules) do
        if _M.match_proxy_rule(rule, request_info) then
            -- 找到匹配的规则，返回对应的upstream服务器
            for _, server in ipairs(configs.upstream_servers) do
                if server.id == rule.upstream_server_id then
                    return server
                end
            end
        end
    end
    
    -- 如果没有匹配的代理规则，使用默认的负载均衡
    return _M.select_default_upstream(configs.upstream_servers)
end

-- 匹配代理规则
function _M.match_proxy_rule(rule, request_info)
    -- 路径匹配
    if rule.path_pattern and not string.match(request_info.path, rule.path_pattern) then
        return false
    end
    
    -- 方法匹配
    if rule.method_pattern and not string.match(request_info.method, rule.method_pattern) then
        return false
    end
    
    -- 头部匹配
    if rule.header_pattern then
        local header_match = false
        for name, value in pairs(request_info.headers) do
            if string.match(name .. ":" .. value, rule.header_pattern) then
                header_match = true
                break
            end
        end
        if not header_match then
            return false
        end
    end
    
    -- 请求体匹配
    if rule.body_pattern and request_info.body then
        if not string.match(request_info.body, rule.body_pattern) then
            return false
        end
    end
    
    return true
end

-- 选择默认upstream服务器
function _M.select_default_upstream(upstream_servers)
    if not upstream_servers or #upstream_servers == 0 then
        return nil
    end
    
    -- 简单的轮询选择
    local ngx_shared = ngx.shared.upstream_state
    local current_index = ngx_shared:get("default_upstream_index") or 0
    
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
    ngx_shared:set("default_upstream_index", current_index)
    
    return healthy_servers[current_index]
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

return _M 