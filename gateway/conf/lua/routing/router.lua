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
        content_length = headers["Content-Length"] or "0",
        namespace_code = nil  -- 将在匹配命名空间后设置
    }
end

-- 处理请求
function _M.handle_request()
    local request_info = get_request_info()
    local request_id = ngx.var.http_x_request_id or ngx.var.request_id or ngx.var.connection .. "-" .. ngx.var.time_iso8601
    
    -- 记录请求开始时间
    local start_time = ngx.now()
    local gateway_start_time = start_time
    
    -- 跳过内部路径
    if request_info.path:match("^/health") or 
       request_info.path:match("^/stats") or 
       request_info.path:match("^/refresh%-config") then
        return
    end
    
    -- 记录请求日志
    logger.log_request_start(request_id, request_info)
    
    -- 匹配命名空间（使用Trie匹配器）
    local ok, namespace = pcall(namespace_matcher.find_matching_namespace, request_info)
    if not ok then
        ngx.log(ngx.ERR, "ROUTER: Error in namespace matching: ", namespace)
        namespace = nil
    end
    
    local namespace_id = namespace and (namespace.namespace_id or namespace.id) or nil
    local namespace_code = namespace and (namespace.namespace_code or namespace.code) or nil
    if not namespace_id then
        ngx.log(ngx.WARN, "ROUTER: No matching namespace found for request: ", request_info.path)
        metrics.record_request(namespace_id, request_info, 404, ngx.now() - start_time)
        logger.log_request_end(request_id, 404, "No matching namespace found")
        
        ngx.status = 404
        ngx.header.content_type = "application/json"
        ngx.say('{"error": "namespace_not_found", "message": "No matching namespace found for this request"}')
        ngx.exit(404)
    end
    
    -- 设置request_info中的namespace_code
    request_info.namespace_code = namespace_code
    
    -- 验证命名空间是否有效
    if not namespace_matcher.is_namespace_valid(namespace_id) then
        ngx.log(ngx.WARN, "ROUTER: Namespace is not active: ", namespace_id)
        metrics.record_request(namespace_id, request_info, 403, ngx.now() - start_time)
        logger.log_request_end(request_id, 403, "Namespace not active")
        
        ngx.status = 403
        ngx.header.content_type = "application/json"
        ngx.say('{"error": "namespace_disabled", "message": "Namespace is not active"}')
        ngx.exit(403)
    end
    
    -- 执行策略检查
    local policy_ok, policy_message = policy_enforcer.enforce_namespace_policies(namespace_id, request_info)
    
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
        ngx.log(ngx.ERR, "ROUTER: No available upstream server for namespace: ", namespace_id)
        metrics.record_request(namespace_id, request_info, 503, ngx.now() - start_time)
        logger.log_request_end(request_id, 503, "No available upstream server")
        
        ngx.status = 503
        ngx.header.content_type = "application/json"
        ngx.say('{"error": "no_upstream", "message": "No available upstream server"}')
        ngx.exit(503)
    end
    
    -- 记录网关处理完成时间
    local gateway_end_time = ngx.now()
    local gateway_processing_time = gateway_end_time - gateway_start_time
    
    -- 直接记录策略匹配时间（在access_by_lua阶段）
    metrics.record_gateway_processing_time(namespace_id, gateway_processing_time)
    ngx.log(ngx.INFO, "ROUTER: Policy matching time recorded: ", gateway_processing_time, " seconds")
    
    -- 设置请求上下文
    ngx.log(ngx.INFO, "ROUTER: Setting context - namespace_id: ", namespace_id, ", namespace_code: ", namespace_code, ", request_id: ", request_id)
    ngx.ctx.namespace_id = namespace_id
    ngx.ctx.namespace_code = namespace_code
    ngx.ctx.upstream = upstream
    ngx.ctx.request_id = request_id
    ngx.ctx.start_time = start_time
    ngx.ctx.gateway_processing_time = gateway_processing_time
    ngx.log(ngx.INFO, "ROUTER: Context set successfully - namespace_id: ", ngx.ctx.namespace_id, ", namespace_code: ", ngx.ctx.namespace_code, ", request_id: ", ngx.ctx.request_id)
    ngx.log(ngx.INFO, "ROUTER: Gateway processing time: ", gateway_processing_time, " seconds")
    
    -- 代理到上游服务器
    local success, err = proxy_handler.proxy_to_upstream(upstream, request_info)
    if not success then
        ngx.log(ngx.ERR, "ROUTER: Proxy to upstream failed: ", err)
        metrics.record_request(namespace_id, request_info, 502, ngx.now() - start_time)
        metrics.record_route_usage(namespace_id, request_info, 502)
        logger.log_request_end(request_id, 502, err)
        
        ngx.status = 502
        ngx.header.content_type = "application/json"
        ngx.say('{"error": "proxy_failed", "message": "' .. err .. '"}')
        ngx.exit(502)
    else
        -- 成功代理，但不在这里记录响应时间
        -- 响应时间将在 log_by_lua 阶段记录，确保包含上游处理时间
        metrics.record_route_usage(namespace_id, request_info, 200)
        
        -- 记录Token使用量（如果有模型信息）
        local model_name = request_info.headers["X-Model"] or request_info.args.model or "unknown"
        if request_info.body and model_name ~= "unknown" then
            local token_calculator = require "utils.token_calculator"
            local token_count = token_calculator.estimate_tokens(request_info.body, model_name)
            if token_count > 0 then
                metrics.record_token_usage(namespace_id, model_name, token_count, request_info)
            end
        end
    end
end

-- 处理请求结束（在timer中异步调用）
function _M.handle_request_end(namespace_id, namespace_code, request_id, start_time, request_uri, status)
    -- 跳过健康检查等内部请求
    if request_uri and (request_uri:match("^/health") or 
       request_uri:match("^/stats") or 
       request_uri:match("^/metrics")) then
        -- 静默处理内部请求，不记录日志
        return
    end
    
    -- 业务请求才输出详细日志
    ngx.log(ngx.INFO, "=== ROUTER: handle_request_end called (in timer) ===")
    ngx.log(ngx.INFO, "ROUTER: Context data - namespace_id: ", namespace_id or "nil", 
           ", namespace_code: ", namespace_code or "nil", ", request_id: ", request_id or "nil", ", start_time: ", start_time or "nil")
    ngx.log(ngx.INFO, "ROUTER: Request URI: ", request_uri or "nil")
    
    if namespace_id and request_id and start_time then
        local total_response_time = ngx.now() - start_time
        local gateway_processing_time = ngx.ctx.gateway_processing_time or 0
        
        ngx.log(ngx.INFO, "ROUTER: Request completed - status: ", status or "nil")
        ngx.log(ngx.INFO, "ROUTER: Time breakdown - Total: ", total_response_time, "s, Policy Matching: ", gateway_processing_time, "s")
        
        -- 记录总响应时间（简化版本，只记录基本指标）
        local metrics = require "monitoring.metrics"
        local request_info = {
            path = ngx.var.request_uri or ngx.var.uri or "/unknown" -- 用于路由统计
        }
        
        -- 记录总响应时间
        metrics.record_request(namespace_id, request_info, status, total_response_time)
        
        -- 记录请求结束日志
        logger.log_request_end(request_id, status, "Request completed")
        
        -- 减少并发计数
        if namespace_code then
            ngx.log(ngx.INFO, "ROUTER: Calling decrease_concurrency_count for namespace_code: ", namespace_code)
            local success, err = policy_enforcer.decrease_concurrency_count(namespace_code)
            if success then
                ngx.log(ngx.INFO, "ROUTER: decrease_concurrency_count completed successfully")
            else
                ngx.log(ngx.ERR, "ROUTER: decrease_concurrency_count failed: ", err or "unknown error")
            end
        end
    else
        ngx.log(ngx.WARN, "ROUTER: Missing context data for request end - namespace_id: ", namespace_id or "nil", 
               ", request_id: ", request_id or "nil", ", start_time: ", start_time or "nil")
    end
    
    ngx.log(ngx.INFO, "=== ROUTER: handle_request_end completed (in timer) ===")
end

return _M
