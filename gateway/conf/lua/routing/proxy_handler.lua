-- 代理处理器模块
-- 负责将请求代理到选定的上游服务器

local _M = {}

-- 构建目标URL
local function build_target_url(upstream, request_info)
    -- 直接使用 server_url，并替换路径
    local base_url = upstream.server_url
    local target_url = base_url .. request_info.path
    
    return target_url
end

-- 设置代理头
local function set_proxy_headers(upstream, request_info)
    -- 从 server_url 解析主机名和端口
    local host = upstream.server_url:match("://([^:/]+)")
    local port = upstream.server_url:match("://[^:]+:([0-9]+)")
    if not port then
        if upstream.server_url:match("https://") then
            port = "443"
        else
            port = "80"
        end
    end
    
    -- 设置Host头
    ngx.req.set_header("Host", host .. ":" .. port)
    
    -- 设置真实IP头
    ngx.req.set_header("X-Real-IP", request_info.remote_addr)
    ngx.req.set_header("X-Forwarded-For", request_info.remote_addr)
    ngx.req.set_header("X-Forwarded-Proto", ngx.var.scheme)
    
    -- 设置请求ID
    local request_id = ngx.var.http_x_request_id or ngx.var.request_id or ngx.var.connection .. "-" .. ngx.var.time_iso8601
    ngx.req.set_header("X-Request-ID", request_id)
    
    -- 设置网关标识
    ngx.req.set_header("X-Gateway", "AI-Gateway-2.0")
    
    -- 设置命名空间信息
    if ngx.ctx.namespace_id then
        ngx.req.set_header("X-Namespace-ID", ngx.ctx.namespace_id)
    end
    
    -- 保留原始请求头（除了Host）
    for name, value in pairs(request_info.headers) do
        if name:lower() ~= "host" and name:lower() ~= "content-length" then
            ngx.req.set_header(name, value)
        end
    end
end

-- 代理到上游服务器
function _M.proxy_to_upstream(upstream, request_info)
    if not upstream or not request_info then
        return false, "Invalid upstream or request info"
    end
    
    -- 构建目标URL
    local target_url = build_target_url(upstream, request_info)
    
    -- 设置代理变量
    ngx.var.upstream_backend = target_url
    
    -- 设置代理头
    set_proxy_headers(upstream, request_info)
    
    ngx.log(ngx.INFO, "Proxying request to: ", target_url)
    
    return true, "Proxy configured successfully"
end

-- 处理代理错误
function _M.handle_proxy_error(status, upstream, request_info)
    local error_messages = {
        [502] = "Bad Gateway - Upstream server returned invalid response",
        [503] = "Service Unavailable - Upstream server is temporarily unavailable",
        [504] = "Gateway Timeout - Upstream server did not respond in time"
    }
    
    local message = error_messages[status] or "Unknown proxy error"
    
    ngx.log(ngx.ERR, "Proxy error ", status, " for upstream ", upstream.name, ": ", message)
    
    -- 记录错误指标
    if ngx.ctx.namespace_id then
        local metrics = require "monitoring.metrics"
        metrics.record_request(ngx.ctx.namespace_id, request_info, status, ngx.now() - (ngx.ctx.start_time or ngx.now()))
    end
    
    return {
        error = "proxy_error",
        message = message,
        status = status,
        upstream = upstream.name,
        request_id = ngx.var.http_x_request_id or ngx.var.request_id
    }
end

-- 验证上游服务器配置
function _M.validate_upstream(upstream)
    if not upstream then
        return false, "Upstream is nil"
    end
    
    if not upstream.address then
        return false, "Upstream address is required"
    end
    
    if not upstream.port then
        return false, "Upstream port is required"
    end
    
    if not upstream.name then
        return false, "Upstream name is required"
    end
    
    return true, "Upstream is valid"
end

-- 获取代理统计信息
function _M.get_proxy_stats()
    local stats = {
        total_requests = 0,
        successful_requests = 0,
        failed_requests = 0,
        average_response_time = 0,
        upstreams = {}
    }
    
    -- 这里可以从共享内存或Redis获取统计信息
    -- 暂时返回基础结构
    
    return stats
end

return _M
