local cjson = require "cjson"
local http = require "resty.http"

local _M = {}

-- 获取请求信息
local function get_request_info()
    local headers = ngx.req.get_headers()
    local method = ngx.req.get_method()
    local uri = ngx.var.uri
    local args = ngx.req.get_uri_args()
    
    -- 获取请求体
    local body = nil
    if method == "POST" or method == "PUT" or method == "PATCH" then
        ngx.req.read_body()
        body = ngx.req.get_body_data()
    end
    
    return {
        method = method,
        uri = uri,
        path = ngx.var.request_uri,
        headers = headers,
        args = args,
        body = body,
        remote_addr = ngx.var.remote_addr,
        host = ngx.var.host
    }
end

-- 应用规则检查
local function apply_rules(request_info, namespace_id)
    local dynamic_config = require "config.dynamic_config"
    local configs = dynamic_config.get_all_configs()
    
    -- 获取该命名空间的所有规则
    local namespace_rules = {}
    for _, rule in ipairs(configs.rules) do
        if rule.namespace_id == namespace_id and rule.is_active then
            table.insert(namespace_rules, rule)
        end
    end
    
    -- 按优先级排序
    table.sort(namespace_rules, function(a, b)
        return (a.priority or 0) < (b.priority or 0)
    end)
    
    -- 应用规则
    for _, rule in ipairs(namespace_rules) do
        local rule_handler = require("rules." .. rule.rule_type)
        if rule_handler then
            local ok, result = pcall(rule_handler.apply, rule, request_info)
            if not ok then
                ngx.log(ngx.ERR, "Rule application failed: ", result)
                return false, "Rule application failed"
            end
            
            if not result then
                return false, "Rule check failed"
            end
        end
    end
    
    return true
end

-- 匹配命名空间
local function match_namespace(request_info)
    local dynamic_config = require "config.dynamic_config"
    local configs = dynamic_config.get_all_configs()
    
    -- 获取所有匹配器
    local matchers = configs.matchers or {}
    
    -- 按优先级排序
    table.sort(matchers, function(a, b)
        return (a.priority or 0) < (b.priority or 0)
    end)
    
    -- 尝试匹配
    for _, matcher in ipairs(matchers) do
        if matcher.is_active then
            local matcher_handler = require("matchers." .. matcher.matcher_type)
            if matcher_handler then
                local ok, matched = pcall(matcher_handler.match, matcher, request_info)
                if ok and matched then
                    return matcher.namespace_id
                end
            end
        end
    end
    
    return nil
end

-- 选择上游服务器
local function select_upstream_server(request_info, namespace_id)
    local dynamic_config = require "config.dynamic_config"
    
    -- 首先尝试根据代理规则选择
    local server = dynamic_config.select_upstream_server(request_info)
    if server then
        return server
    end
    
    -- 如果没有匹配的代理规则，使用默认选择
    local configs = dynamic_config.get_all_configs()
    return dynamic_config.select_default_upstream(configs.upstream_servers)
end

-- 代理请求到上游服务器
local function proxy_to_upstream(server, request_info)
    -- 构建目标URL
    local protocol = server.type == "https" and "https" or "http"
    local target_url = string.format("%s://%s:%s%s", 
        protocol, 
        server.address, 
        server.port, 
        request_info.path
    )
    
    -- 设置代理变量
    ngx.var.upstream_backend = target_url
    
    -- 设置代理头
    ngx.req.set_header("Host", server.address .. ":" .. server.port)
    ngx.req.set_header("X-Real-IP", request_info.remote_addr)
    ngx.req.set_header("X-Forwarded-For", request_info.remote_addr)
    ngx.req.set_header("X-Forwarded-Proto", ngx.var.scheme)
    ngx.req.set_header("X-Request-ID", request_info.headers["X-Request-ID"] or "")
    
    -- 使用内置的proxy_pass
    ngx.exec("@proxy_backend")
end

-- 主要处理函数
function _M.handle_request()
    local request_info = get_request_info()
    
    -- 跳过内部路径
    if request_info.path:match("^/health") or 
       request_info.path:match("^/stats") or 
       request_info.path:match("^/refresh%-config") then
        return
    end
    
    -- 匹配命名空间
    local namespace_id = match_namespace(request_info)
    if not namespace_id then
        ngx.status = 404
        ngx.say('{"error": "namespace_not_found", "message": "No matching namespace found"}')
        ngx.exit(404)
    end
    
    -- 应用规则检查
    local ok, err = apply_rules(request_info, namespace_id)
    if not ok then
        ngx.status = 403
        ngx.say(string.format('{"error": "rule_check_failed", "message": "%s"}', err))
        ngx.exit(403)
    end
    
    -- 选择上游服务器
    local server = select_upstream_server(request_info, namespace_id)
    if not server then
        ngx.status = 503
        ngx.say('{"error": "no_available_upstream", "message": "No available upstream servers"}')
        ngx.exit(503)
    end
    
    -- 代理到上游服务器
    local ok, err = pcall(proxy_to_upstream, server, request_info)
    if not ok then
        ngx.status = 502
        ngx.say(string.format('{"error": "proxy_failed", "message": "%s"}', err))
        ngx.exit(502)
    end
end

return _M 