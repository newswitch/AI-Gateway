-- 路径重写模块
-- 负责根据路由规则进行路径重写

local json = require "utils.json"
local cache = require "config.cache"

local _M = {}

-- 缓存路径重写规则
local _cached_rules = {}
local _cache_timestamp = 0
local CACHE_TTL = 60  -- 缓存60秒

-- 获取路径重写规则
local function get_path_rewrite_rules()
    local current_time = ngx.time()
    
    -- 检查缓存是否有效
    if _cached_rules and (current_time - _cache_timestamp) < CACHE_TTL then
        return _cached_rules
    end
    
    -- 从缓存获取路由规则
    local location_rules = cache.get_location_rules() or {}
    local rules = {}
    
    for _, rule in ipairs(location_rules) do
        if rule.status == 1 and rule.path_rewrite_config then
            local path_rewrite_config = rule.path_rewrite_config
            if type(path_rewrite_config) == "string" then
                local ok, config = pcall(json.decode, path_rewrite_config)
                if ok and config then
                    path_rewrite_config = config
                else
                    ngx.log(ngx.ERR, "PATH_REWRITER: Failed to parse path_rewrite_config: ", path_rewrite_config)
                    goto continue
                end
            end
            
            if path_rewrite_config.enabled and 
               path_rewrite_config.from and 
               path_rewrite_config.to and
               path_rewrite_config.from ~= "" and
               path_rewrite_config.to ~= "" then
                
                table.insert(rules, {
                    path = rule.path,
                    from = path_rewrite_config.from,
                    to = path_rewrite_config.to,
                    priority = rule.priority or 100,
                    rule_id = rule.location_id
                })
            end
        end
        ::continue::
    end
    
    -- 按优先级排序（数字越小优先级越高）
    table.sort(rules, function(a, b)
        return a.priority < b.priority
    end)
    
    _cached_rules = rules
    _cache_timestamp = current_time
    
    ngx.log(ngx.INFO, "PATH_REWRITER: Loaded ", #rules, " path rewrite rules")
    return rules
end

-- 检查路径是否匹配规则
local function matches_path(request_path, rule_path)
    if not request_path or not rule_path then
        return false
    end
    
    -- 精确匹配
    if request_path == rule_path then
        return true
    end
    
    -- 前缀匹配（以/结尾的规则）
    if rule_path:sub(-1) == "/" then
        return request_path:sub(1, #rule_path) == rule_path
    end
    
    -- 通配符匹配（包含*的规则）
    if rule_path:find("*") then
        local pattern = rule_path:gsub("%*", ".*")
        return request_path:match("^" .. pattern .. "$") ~= nil
    end
    
    return false
end

-- 执行路径重写
local function rewrite_path(request_path, from_pattern, to_pattern)
    if not request_path or not from_pattern or not to_pattern then
        return request_path
    end
    
    -- 使用Lua模式匹配进行重写
    local rewritten_path = request_path:gsub("^" .. from_pattern:gsub("%.", "%%."), to_pattern)
    
    -- 如果重写没有改变路径，尝试更复杂的匹配
    if rewritten_path == request_path then
        -- 尝试匹配整个路径
        if request_path == from_pattern then
            rewritten_path = to_pattern
        else
            -- 尝试前缀匹配
            local prefix = from_pattern:gsub("%*$", "")
            if request_path:sub(1, #prefix) == prefix then
                local suffix = request_path:sub(#prefix + 1)
                rewritten_path = to_pattern:gsub("%*", suffix)
            end
        end
    end
    
    return rewritten_path
end

-- 应用路径重写
function _M.apply_path_rewrite(request_info)
    if not request_info or not request_info.path then
        return request_info
    end
    
    local rules = get_path_rewrite_rules()
    local original_path = request_info.path
    local rewritten_path = original_path
    
    ngx.log(ngx.INFO, "PATH_REWRITER: Checking path rewrite for: ", original_path)
    
    for _, rule in ipairs(rules) do
        if matches_path(original_path, rule.path) then
            ngx.log(ngx.INFO, "PATH_REWRITER: Found matching rule: ", rule.path, " -> ", rule.from, " -> ", rule.to)
            
            local new_path = rewrite_path(rewritten_path, rule.from, rule.to)
            if new_path ~= rewritten_path then
                rewritten_path = new_path
                ngx.log(ngx.INFO, "PATH_REWRITER: Path rewritten: ", original_path, " -> ", rewritten_path)
                
                -- 更新request_info中的路径
                request_info.path = rewritten_path
                request_info.original_path = original_path
                request_info.rewrite_rule_id = rule.rule_id
                
                -- 只应用第一个匹配的规则
                break
            end
        end
    end
    
    return request_info
end

-- 获取重写统计信息
function _M.get_rewrite_stats()
    local rules = get_path_rewrite_rules()
    return {
        total_rules = #rules,
        cache_timestamp = _cache_timestamp,
        cache_age = ngx.time() - _cache_timestamp
    }
end

-- 清空缓存
function _M.clear_cache()
    _cached_rules = {}
    _cache_timestamp = 0
    ngx.log(ngx.INFO, "PATH_REWRITER: Cache cleared")
end

-- 调试：打印重写规则
function _M.debug_print_rules()
    local rules = get_path_rewrite_rules()
    
    ngx.log(ngx.INFO, "=== Path Rewrite Rules ===")
    for i, rule in ipairs(rules) do
        ngx.log(ngx.INFO, string.format("[%d] %s: %s -> %s (priority: %d)", 
            i, rule.path, rule.from, rule.to, rule.priority))
    end
end

return _M
