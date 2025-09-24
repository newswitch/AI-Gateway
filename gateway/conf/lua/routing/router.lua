---@diagnostic disable: need-check-nil
-- 主路由器模块
-- 负责协调命名空间匹配、策略执行和路由选择

local namespace_matcher = require "auth.namespace_matcher"
local policy_enforcer = require "auth.policy_enforcer"
local upstream_selector = require "routing.upstream_selector"
local proxy_handler = require "routing.proxy_handler"
local metrics = require "monitoring.metrics"
local logger = require "monitoring.logger"
local json = require "utils.json"

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
        host = ngx.var.host,
        user_agent = headers["User-Agent"] or "",
        content_type = headers["Content-Type"] or "",
        content_length = headers["Content-Length"] or "0"
    }
end

-- 处理请求
function _M.handle_request()
    ngx.log(ngx.INFO, "=== ROUTER: Starting request handling ===")
    
    local request_info = get_request_info()
    local request_id = ngx.var.http_x_request_id or ngx.var.request_id or ngx.var.connection .. "-" .. ngx.var.time_iso8601
    
    -- 记录请求开始时间
    local start_time = ngx.now()
    
    ngx.log(ngx.INFO, "ROUTER: Request info - method: ", request_info.method, ", path: ", request_info.path, ", channelcode: ", request_info.headers["channelcode"] or "none")
    
    -- 跳过内部路径
    if request_info.path:match("^/health") or 
       request_info.path:match("^/stats") or 
       request_info.path:match("^/refresh%-config") then
        return
    end
    
    -- 记录请求日志
    logger.log_request_start(request_id, request_info)
    
    -- 匹配命名空间
    ngx.log(ngx.INFO, "ROUTER: Starting namespace matching...")
    local namespace_id = namespace_matcher.find_matching_namespace(request_info)
    if not namespace_id then
        ngx.log(ngx.WARN, "ROUTER: No matching namespace found for request: ", request_info.path)
        metrics.record_request(namespace_id, request_info, 404, ngx.now() - start_time)
        logger.log_request_end(request_id, 404, "No matching namespace found")
        
        ngx.status = 404
        ngx.header.content_type = "application/json"
        ngx.say('{"error": "namespace_not_found", "message": "No matching namespace found for this request"}')
        ngx.exit(404)
    end
    
    ngx.log(ngx.INFO, "ROUTER: Successfully matched namespace: ", namespace_id, " for request: ", request_info.path)
    
    -- 验证命名空间是否有效
    if not namespace_matcher.is_namespace_valid(namespace_id) then
        ngx.log(ngx.WARN, "Namespace is not active: ", namespace_id)
        metrics.record_request(namespace_id, request_info, 403, ngx.now() - start_time)
        logger.log_request_end(request_id, 403, "Namespace not active")
        
        ngx.status = 403
        ngx.header.content_type = "application/json"
        ngx.say('{"error": "namespace_disabled", "message": "Namespace is not active"}')
        ngx.exit(403)
    end
    
    -- 执行策略检查
    ngx.log(ngx.INFO, "ROUTER: Starting policy enforcement for namespace: ", namespace_id)
    local policy_ok, policy_message = policy_enforcer.enforce_namespace_policies(namespace_id, request_info)
    ngx.log(ngx.INFO, "ROUTER: Policy enforcement result - ok: ", policy_ok, ", message: ", policy_message or "none")
    
    if not policy_ok then
        ngx.log(ngx.WARN, "ROUTER: Policy enforcement failed: ", policy_message)
        metrics.record_request(namespace_id, request_info, 403, ngx.now() - start_time)
        logger.log_request_end(request_id, 403, policy_message)
        
        ngx.status = 403
        ngx.header.content_type = "application/json"
        ngx.say('{"error": "policy_violation", "message": "' .. policy_message .. '"}')
        ngx.exit(403)
    end
    
    ngx.log(ngx.INFO, "ROUTER: Policy enforcement passed for namespace: ", namespace_id)
    
    -- 选择上游服务器
    local upstream = upstream_selector.select_upstream(namespace_id, request_info)
    if not upstream then
        ngx.log(ngx.ERR, "No available upstream server for namespace: ", namespace_id)
        metrics.record_request(namespace_id, request_info, 503, ngx.now() - start_time)
        logger.log_request_end(request_id, 503, "No available upstream server")
        
        ngx.status = 503
        ngx.header.content_type = "application/json"
        ngx.say('{"error": "no_upstream", "message": "No available upstream server"}')
        ngx.exit(503)
    end
    
    ngx.log(ngx.INFO, "Selected upstream: ", upstream.name, " for namespace: ", namespace_id)
    
    -- 设置请求上下文
    ngx.ctx.namespace_id = namespace_id
    ngx.ctx.upstream = upstream
    ngx.ctx.request_id = request_id
    ngx.ctx.start_time = start_time
    
    -- 代理到上游服务器
    local success, err = proxy_handler.proxy_to_upstream(upstream, request_info)
    if not success then
        ngx.log(ngx.ERR, "Proxy to upstream failed: ", err)
        metrics.record_request(namespace_id, request_info, 502, ngx.now() - start_time)
        logger.log_request_end(request_id, 502, err)
        
        ngx.status = 502
        ngx.header.content_type = "application/json"
        ngx.say('{"error": "proxy_failed", "message": "' .. err .. '"}')
        ngx.exit(502)
    else
        -- 成功代理，记录指标
        local response_time = ngx.now() - start_time
        metrics.record_request(namespace_id, request_info, 200, response_time)
    end
end

-- 处理请求结束（在log_by_lua阶段调用）
function _M.handle_request_end()
    local namespace_id = ngx.ctx.namespace_id
    local request_id = ngx.ctx.request_id
    local start_time = ngx.ctx.start_time
    
    if namespace_id and request_id and start_time then
        local response_time = ngx.now() - start_time
        local status = ngx.status
        
        -- 记录请求结束日志
        logger.log_request_end(request_id, status, "Request completed")
        
        -- 减少并发计数
        if namespace_id then
            policy_enforcer.decrease_concurrency_count(namespace_id)
        end
    end
end

return _M
