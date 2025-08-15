-- 配置中心API客户端
-- 负责与配置中心服务进行通信

local _M = {}

local cjson = require "cjson"
local http = require "resty.http"

-- 配置中心基础URL
-- 在 K8s 中使用 Service 名称
-- 使用完整 K8s FQDN，避免解析 search 域依赖
local svc = require "utils.service_config"
local CONFIG_CENTER_BASE_URL = svc.get_config_center_base_url()

-- HTTP请求封装
local function make_request(method, path, data, headers)
    local httpc = http.new()
    httpc:set_timeout(5000)  -- 5秒超时
    
    -- 设置默认请求头
    local request_headers = {
        ["Content-Type"] = "application/json",
        ["User-Agent"] = "AI-Gateway-Config-Client"
    }
    
    -- 合并自定义请求头
    if headers then
        for k, v in pairs(headers) do
            request_headers[k] = v
        end
    end
    
    local url = CONFIG_CENTER_BASE_URL .. path
    
    local res, err = httpc:request_uri(url, {
        method = method,
        headers = request_headers,
        body = data and cjson.encode(data) or nil
    })
    
    if not res then
        return nil, "HTTP request failed: " .. (err or "unknown error")
    end
    
    if res.status >= 400 then
        return nil, "HTTP " .. res.status .. ": " .. (res.body or "")
    end
    
    -- 解析响应
    if res.body and res.body ~= "" then
        local ok, data = pcall(cjson.decode, res.body)
        if ok then
            return data
        else
            return nil, "Failed to parse JSON response: " .. data
        end
    end
    
    return {}
end

-- 获取命名空间列表
function _M.get_namespaces()
    return make_request("GET", "/api/v1/namespaces")
end

-- 获取指定命名空间
function _M.get_namespace(namespace_id)
    return make_request("GET", "/api/v1/namespaces/" .. namespace_id)
end

-- 获取匹配器列表
function _M.get_matchers()
    return make_request("GET", "/api/v1/matchers")
end

-- 获取规则列表
function _M.get_rules()
    return make_request("GET", "/api/v1/rules")
end

-- 获取指定命名空间的规则
function _M.get_namespace_rules(namespace_id)
    return make_request("GET", "/api/v1/rules?namespace_id=" .. namespace_id)
end

-- 获取上游服务器列表
function _M.get_upstream_servers()
    return make_request("GET", "/api/v1/upstream-servers")
end

-- 获取代理规则列表
function _M.get_proxy_rules()
    return make_request("GET", "/api/v1/proxy-rules")
end

-- 创建命名空间
function _M.create_namespace(namespace_data)
    return make_request("POST", "/api/v1/namespaces", namespace_data)
end

-- 更新命名空间
function _M.update_namespace(namespace_id, namespace_data)
    return make_request("PUT", "/api/v1/namespaces/" .. namespace_id, namespace_data)
end

-- 删除命名空间
function _M.delete_namespace(namespace_id)
    return make_request("DELETE", "/api/v1/namespaces/" .. namespace_id)
end

-- 创建匹配器
function _M.create_matcher(matcher_data)
    return make_request("POST", "/api/v1/matchers", matcher_data)
end

-- 更新匹配器
function _M.update_matcher(matcher_id, matcher_data)
    return make_request("PUT", "/api/v1/matchers/" .. matcher_id, matcher_data)
end

-- 删除匹配器
function _M.delete_matcher(matcher_id)
    return make_request("DELETE", "/api/v1/matchers/" .. matcher_id)
end

-- 创建规则
function _M.create_rule(rule_data)
    return make_request("POST", "/api/v1/rules", rule_data)
end

-- 更新规则
function _M.update_rule(rule_id, rule_data)
    return make_request("PUT", "/api/v1/rules/" .. rule_id, rule_data)
end

-- 删除规则
function _M.delete_rule(rule_id)
    return make_request("DELETE", "/api/v1/rules/" .. rule_id)
end

-- 创建上游服务器
function _M.create_upstream_server(server_data)
    return make_request("POST", "/api/v1/upstream-servers", server_data)
end

-- 更新上游服务器
function _M.update_upstream_server(server_id, server_data)
    return make_request("PUT", "/api/v1/upstream-servers/" .. server_id, server_data)
end

-- 删除上游服务器
function _M.delete_upstream_server(server_id)
    return make_request("DELETE", "/api/v1/upstream-servers/" .. server_id)
end

-- 创建代理规则
function _M.create_proxy_rule(rule_data)
    return make_request("POST", "/api/v1/proxy-rules", rule_data)
end

-- 更新代理规则
function _M.update_proxy_rule(rule_id, rule_data)
    return make_request("PUT", "/api/v1/proxy-rules/" .. rule_id, rule_data)
end

-- 删除代理规则
function _M.delete_proxy_rule(rule_id)
    return make_request("DELETE", "/api/v1/proxy-rules/" .. rule_id)
end

-- 刷新配置缓存
function _M.refresh_cache()
    return make_request("POST", "/api/v1/cache/refresh")
end

-- 获取系统状态
function _M.get_system_status()
    return make_request("GET", "/api/v1/status")
end

-- 健康检查
function _M.health_check()
    return make_request("GET", "/health")
end

return _M 