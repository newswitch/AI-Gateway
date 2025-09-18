-- 配置加载器模块
-- 负责从配置中心API获取配置数据

local http = require "utils.http"
local json = require "utils.json"
local redis = require "utils.redis"

local _M = {}

-- 配置中心API端点
local API_ENDPOINTS = {
    namespaces = "/api/namespaces",        -- V2 API，包含匹配器信息
    policies = "/api/policies",            -- V2 API
    upstreams = "/api/upstreams",          -- V2 API
    locations = "/api/locations"           -- V2 API
}

-- 获取配置中心基础URL
local function get_config_center_url()
    local config = require "core.init"
    local config_center = config.get_config().config_center
    return "http://" .. config_center.host .. ":" .. config_center.port
end

-- 获取认证头
local function get_auth_headers()
    return {
        ["Authorization"] = "Bearer dummy-token",
        ["Content-Type"] = "application/json"
    }
end

-- 从API获取命名空间配置
function _M.get_namespaces()
    local url = get_config_center_url() .. API_ENDPOINTS.namespaces
    local res, err = http.get(url, get_auth_headers())
    
    if not res then
        ngx.log(ngx.ERR, "Failed to get namespaces from API: ", err)
        return nil, err
    end
    
    if not http.is_success(res) then
        ngx.log(ngx.ERR, "API returned error status: ", res.status)
        return nil, "API error: " .. res.status
    end
    
    local data, err = http.parse_json_response(res)
    if not data then
        ngx.log(ngx.ERR, "Failed to parse namespaces response: ", err)
        return nil, err
    end
    
    return data.data and data.data.items or data.data or {}
end

-- 从命名空间数据中提取匹配器信息
function _M.extract_matchers_from_namespaces(namespaces)
    local matchers = {}
    
    for _, namespace in ipairs(namespaces) do
        if namespace.matcher then
            local matcher = {
                matcher_id = namespace.matcher.matcher_id,
                namespace_id = namespace.id,
                matcher_name = namespace.matcher.matcher_name or (namespace.name .. "渠道匹配"),
                matcher_type = namespace.matcher.matcher_type or "header",
                match_field = namespace.matcher.match_field or "channelcode",
                match_operator = namespace.matcher.match_operator or "equals",
                match_value = namespace.matcher.match_value or namespace.code,
                priority = namespace.matcher.priority or 100,
                status = namespace.matcher.status or 1
            }
            table.insert(matchers, matcher)
        end
    end
    
    return matchers
end

-- 从API获取策略配置
function _M.get_policies()
    local url = get_config_center_url() .. API_ENDPOINTS.policies
    local res, err = http.get(url, get_auth_headers())
    
    if not res then
        ngx.log(ngx.ERR, "Failed to get policies from API: ", err)
        return nil, err
    end
    
    if not http.is_success(res) then
        ngx.log(ngx.ERR, "API returned error status: ", res.status)
        return nil, "API error: " .. res.status
    end
    
    local data, err = http.parse_json_response(res)
    if not data then
        ngx.log(ngx.ERR, "Failed to parse policies response: ", err)
        return nil, err
    end
    
    return data.data and data.data.items or data.data or {}
end

-- 从API获取上游服务器配置
function _M.get_upstreams()
    local url = get_config_center_url() .. API_ENDPOINTS.upstreams
    local res, err = http.get(url, get_auth_headers())
    
    if not res then
        ngx.log(ngx.ERR, "Failed to get upstreams from API: ", err)
        return nil, err
    end
    
    if not http.is_success(res) then
        ngx.log(ngx.ERR, "API returned error status: ", res.status)
        return nil, "API error: " .. res.status
    end
    
    local data, err = http.parse_json_response(res)
    if not data then
        ngx.log(ngx.ERR, "Failed to parse upstreams response: ", err)
        return nil, err
    end
    
    return data.data and data.data.items or data.data or {}
end

-- 从API获取路由规则配置
function _M.get_locations()
    local url = get_config_center_url() .. API_ENDPOINTS.locations
    local res, err = http.get(url, get_auth_headers())
    
    if not res then
        ngx.log(ngx.ERR, "Failed to get locations from API: ", err)
        return nil, err
    end
    
    if not http.is_success(res) then
        ngx.log(ngx.ERR, "API returned error status: ", res.status)
        return nil, err
    end
    
    local data, err = http.parse_json_response(res)
    if not data then
        ngx.log(ngx.ERR, "Failed to parse locations response: ", err)
        return nil, err
    end
    
    return data.data and data.data.items or data.data or {}
end


-- 获取所有配置
function _M.get_all_configs()
    local configs = {}
    
    -- 获取命名空间配置
    local namespaces, err = _M.get_namespaces()
    if namespaces then
        configs.namespaces = namespaces
        -- 从命名空间中提取匹配器信息
        configs.matchers = _M.extract_matchers_from_namespaces(namespaces)
    else
        ngx.log(ngx.WARN, "Failed to load namespaces: ", err)
        configs.namespaces = {}
        configs.matchers = {}
    end
    
    -- 获取策略配置
    local policies, err = _M.get_policies()
    if policies then
        configs.policies = policies
    else
        ngx.log(ngx.WARN, "Failed to load policies: ", err)
        configs.policies = {}
    end
    
    -- 获取上游服务器配置
    local upstreams, err = _M.get_upstreams()
    if upstreams then
        configs.upstreams = upstreams
    else
        ngx.log(ngx.WARN, "Failed to load upstreams: ", err)
        configs.upstreams = {}
    end
    
    -- 获取路由规则配置
    local locations, err = _M.get_locations()
    if locations then
        configs.locations = locations
    else
        ngx.log(ngx.WARN, "Failed to load locations: ", err)
        configs.locations = {}
    end
    
    
    return configs
end

-- 刷新所有配置
function _M.refresh_all_configs()
    local configs = _M.get_all_configs()
    
    -- 更新Redis缓存
    local cache = require "config.cache"
    local success = true
    
    success = success and cache.set_namespaces(configs.namespaces)
    success = success and cache.set_policies(configs.policies)
    success = success and cache.set_upstreams(configs.upstreams)
    success = success and cache.set_locations(configs.locations)
    success = success and cache.set_matchers(configs.matchers)
    
    if success then
        ngx.log(ngx.INFO, "All configurations refreshed successfully")
    else
        ngx.log(ngx.ERR, "Failed to refresh some configurations")
    end
    
    return success
end

return _M
