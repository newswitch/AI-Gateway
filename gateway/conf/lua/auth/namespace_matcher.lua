-- 命名空间匹配器模块
-- 负责根据请求信息匹配到对应的命名空间

local json = require "utils.json"

local _M = {}

-- 匹配请求头
local function match_header(matcher, request_info)
    local field_name = matcher.match_field
    local expected_value = matcher.match_value
    local operator = matcher.match_operator or "equals"
    
    local header_value = request_info.headers[field_name]
    if not header_value then
        return false
    end
    
    return _M.match_value(header_value, expected_value, operator)
end

-- 匹配请求体
local function match_body(matcher, request_info)
    local field_name = matcher.match_field
    local expected_value = matcher.match_value
    local operator = matcher.match_operator or "equals"
    
    if not request_info.body then
        return false
    end
    
    -- 解析JSON请求体
    local body_data, err = json.decode(request_info.body)
    if not body_data then
        ngx.log(ngx.WARN, "Failed to parse request body: ", err)
        return false
    end
    
    -- 获取嵌套字段值
    local field_value = _M.get_nested_field(body_data, field_name)
    if not field_value then
        return false
    end
    
    return _M.match_value(tostring(field_value), expected_value, operator)
end

-- 获取嵌套字段值
function _M.get_nested_field(data, field_path)
    local fields = {}
    for field in string.gmatch(field_path, "[^%.]+") do
        table.insert(fields, field)
    end
    
    local current = data
    for _, field in ipairs(fields) do
        if type(current) == "table" and current[field] then
            current = current[field]
        else
            return nil
        end
    end
    
    return current
end

-- 匹配值
function _M.match_value(actual, expected, operator)
    if not actual or not expected then
        return false
    end
    
    actual = tostring(actual)
    expected = tostring(expected)
    
    if operator == "equals" then
        return actual == expected
    elseif operator == "contains" then
        return string.find(actual, expected, 1, true) ~= nil
    elseif operator == "regex" then
        return string.match(actual, expected) ~= nil
    elseif operator == "in" then
        -- 支持逗号分隔的值列表
        local values = {}
        for value in string.gmatch(expected, "[^,]+") do
            table.insert(values, value:match("^%s*(.-)%s*$")) -- 去除空格
        end
        for _, value in ipairs(values) do
            if actual == value then
                return true
            end
        end
        return false
    elseif operator == "starts_with" then
        return string.sub(actual, 1, #expected) == expected
    elseif operator == "ends_with" then
        return string.sub(actual, -#expected) == expected
    else
        ngx.log(ngx.WARN, "Unknown match operator: ", operator)
        return false
    end
end

-- 匹配命名空间
function _M.match_namespace(matcher, request_info)
    if not matcher or not matcher.is_active then
        return false
    end
    
    local matcher_type = matcher.matcher_type or "header"
    
    if matcher_type == "header" then
        return match_header(matcher, request_info)
    elseif matcher_type == "body" then
        return match_body(matcher, request_info)
    else
        ngx.log(ngx.WARN, "Unknown matcher type: ", matcher_type)
        return false
    end
end

-- 查找匹配的命名空间
function _M.find_matching_namespace(request_info)
    ngx.log(ngx.INFO, "=== NAMESPACE_MATCHER: Starting namespace matching ===")
    
    local cache = require "config.cache"
    local configs = cache.get_all_configs()
    
    local namespaces = configs.namespaces or {}
    local matchers = {}
    
    ngx.log(ngx.ERR, "NAMESPACE_MATCHER: Found ", #namespaces, " namespaces in config")
    ngx.log(ngx.ERR, "NAMESPACE_MATCHER: Configs keys: ", json.encode(configs and configs.namespaces and "namespaces exists" or "namespaces nil"))
    
    -- 从命名空间配置中提取匹配器信息
    for _, namespace in ipairs(namespaces) do
        ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Processing namespace: ", namespace.code, " (", namespace.name, "), id: ", namespace.id)
        if namespace.matcher then
            local matcher = {
                namespace_id = namespace.id,
                matcher_type = namespace.matcher.matcher_type,
                match_field = namespace.matcher.match_field,
                match_operator = namespace.matcher.match_operator,
                match_value = namespace.matcher.match_value,
                priority = namespace.matcher.priority or 100,
                is_active = namespace.status == "enabled"
            }
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Added matcher for namespace ", namespace.code, ": ", matcher.match_field, " ", matcher.match_operator, " ", matcher.match_value)
            table.insert(matchers, matcher)
        else
            ngx.log(ngx.WARN, "NAMESPACE_MATCHER: No matcher found for namespace: ", namespace.code)
        end
    end
    
    ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Found ", #matchers, " matchers")
    
    -- 按优先级排序
    table.sort(matchers, function(a, b)
        return (a.priority or 100) < (b.priority or 100)
    end)
    
    -- 尝试匹配
    for _, matcher in ipairs(matchers) do
        ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Trying to match: ", matcher.match_field, " ", matcher.match_operator, " ", matcher.match_value)
        if _M.match_namespace(matcher, request_info) then
            ngx.log(ngx.INFO, "NAMESPACE_MATCHER: Matched namespace: ", matcher.namespace_id, " with matcher: ", matcher.match_field, " ", matcher.match_operator, " ", matcher.match_value)
            return matcher.namespace_id
        end
    end
    
    ngx.log(ngx.WARN, "NAMESPACE_MATCHER: No matching namespace found")
    return nil
end

-- 获取命名空间信息
function _M.get_namespace_info(namespace_id)
    local cache = require "config.cache"
    local configs = cache.get_all_configs()
    
    local namespaces = configs.namespaces or {}
    for _, namespace in ipairs(namespaces) do
        if namespace.id == namespace_id then
            return namespace
        end
    end
    
    return nil
end

-- 验证命名空间是否有效
function _M.is_namespace_valid(namespace_id)
    local namespace = _M.get_namespace_info(namespace_id)
    return namespace and namespace.status == "enabled"
end

return _M
