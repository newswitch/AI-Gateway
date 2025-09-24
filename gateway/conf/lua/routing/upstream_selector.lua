-- 上游选择器模块
-- 负责根据命名空间和请求信息选择合适的上游服务器

local cache = require "config.cache"
local http = require "utils.http"

local _M = {}

-- 健康检查
local function health_check(upstream)
    if not upstream.health_check_url then
        return true -- 如果没有健康检查URL，假设服务器是健康的
    end
    
    local url = upstream.server_url .. upstream.health_check_url
    local res, err = http.get(url, {
        ["User-Agent"] = "AI-Gateway-Health-Check"
    })
    
    if not res then
        ngx.log(ngx.WARN, "Health check failed for ", upstream.server_name, ": ", err)
        return false
    end
    
    return res.status == 200
end

-- 获取健康的上游服务器
local function get_healthy_upstreams(upstreams)
    local healthy = {}
    
    for _, upstream in ipairs(upstreams) do
        if upstream.status == 1 and health_check(upstream) then  -- 使用数字状态
            table.insert(healthy, upstream)
        end
    end
    
    return healthy
end

-- 轮询选择算法
local function round_robin_select(upstreams)
    if #upstreams == 0 then
        return nil
    end
    
    local ngx_shared = ngx.shared.upstream_state
    local key = "round_robin_index"
    local current_index = ngx_shared:get(key) or 0
    
    current_index = (current_index % #upstreams) + 1
    ngx_shared:set(key, current_index)
    
    return upstreams[current_index]
end

-- 权重选择算法
local function weighted_select(upstreams)
    if #upstreams == 0 then
        return nil
    end
    
    -- 计算总权重
    local total_weight = 0
    for _, upstream in ipairs(upstreams) do
        total_weight = total_weight + (upstream.weight or 1)
    end
    
    if total_weight == 0 then
        return round_robin_select(upstreams)
    end
    
    -- 生成随机数
    local random = math.random() * total_weight
    local current_weight = 0
    
    for _, upstream in ipairs(upstreams) do
        current_weight = current_weight + (upstream.weight or 1)
        if random <= current_weight then
            return upstream
        end
    end
    
    -- 如果随机数超出范围，返回最后一个
    return upstreams[#upstreams]
end

-- 根据路径匹配选择上游
local function select_by_path_matching(namespace_id, request_info)
    local configs = cache.get_all_configs()
    local locations = configs.locations or {}
    
    -- 按优先级排序
    table.sort(locations, function(a, b)
        return (a.priority or 100) < (b.priority or 100)
    end)
    
    -- 查找匹配的路由规则
    for _, location in ipairs(locations) do
        if location.status == 1 and location.path then  -- 使用数字状态
            -- 简单的路径匹配（支持通配符）
            local path_pattern = location.path:gsub("*", ".*")
            if string.match(request_info.path, "^" .. path_pattern) then
                -- 找到匹配的路由规则，返回对应的上游服务器
                local upstreams = configs.upstreams or {}
                for _, upstream in ipairs(upstreams) do
                    if upstream.server_id == location.upstream_id then
                        ngx.log(ngx.INFO, "Found matching upstream for path ", location.path, ": ", upstream.server_name)
                        return upstream
                    end
                end
            end
        end
    end
    
    return nil
end

-- 选择上游服务器
function _M.select_upstream(namespace_id, request_info)
    local configs = cache.get_all_configs()
    local upstreams = configs.upstreams or {}
    
    -- 首先尝试根据路径匹配选择
    local selected_upstream = select_by_path_matching(namespace_id, request_info)
    if selected_upstream then
        ngx.log(ngx.INFO, "Selected upstream by path matching: ", selected_upstream.name)
        return selected_upstream
    end
    
    -- 获取健康的上游服务器
    local healthy_upstreams = get_healthy_upstreams(upstreams)
    if #healthy_upstreams == 0 then
        ngx.log(ngx.ERR, "No healthy upstream servers available")
        return nil
    end
    
    -- 根据负载均衡策略选择
    local load_balance_strategy = os.getenv("LOAD_BALANCE_STRATEGY") or "weighted"
    
    if load_balance_strategy == "round_robin" then
        selected_upstream = round_robin_select(healthy_upstreams)
    else
        selected_upstream = weighted_select(healthy_upstreams)
    end
    
    if selected_upstream then
        ngx.log(ngx.INFO, "Selected upstream by load balancing: ", selected_upstream.name)
    else
        ngx.log(ngx.ERR, "Failed to select upstream server")
    end
    
    return selected_upstream
end

-- 获取上游服务器信息
function _M.get_upstream_info(upstream_id)
    local configs = cache.get_all_configs()
    local upstreams = configs.upstreams or {}
    
    for _, upstream in ipairs(upstreams) do
        if upstream.server_id == upstream_id then
            return upstream
        end
    end
    
    return nil
end

-- 检查上游服务器是否健康
function _M.is_upstream_healthy(upstream_id)
    local upstream = _M.get_upstream_info(upstream_id)
    if not upstream then
        return false
    end
    
    return health_check(upstream)
end

-- 获取所有健康的上游服务器
function _M.get_all_healthy_upstreams()
    local configs = cache.get_all_configs()
    local upstreams = configs.upstreams or {}
    
    return get_healthy_upstreams(upstreams)
end

return _M
