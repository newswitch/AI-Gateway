-- 日志处理模块
-- 负责处理系统日志记录

local _M = {}

local cjson = require "cjson"

-- 记录请求开始日志
function _M.log_request_start(request_id)
    local log_data = {
        timestamp = ngx.time(),
        level = "INFO",
        event = "request_start",
        request_id = request_id,
        method = ngx.req.get_method(),
        uri = ngx.var.uri,
        remote_addr = ngx.var.remote_addr,
        user_agent = ngx.var.http_user_agent
    }
    
    ngx.log(ngx.INFO, cjson.encode(log_data))
end

-- 记录请求结束日志
function _M.log_request_end(request_id, status, response_time)
    local log_data = {
        timestamp = ngx.time(),
        level = "INFO",
        event = "request_end",
        request_id = request_id,
        status = status,
        response_time = response_time,
        method = ngx.req.get_method(),
        uri = ngx.var.uri
    }
    
    ngx.log(ngx.INFO, cjson.encode(log_data))
end

-- 记录错误日志
function _M.log_error(request_id, error_type, error_message, extra_data)
    local log_data = {
        timestamp = ngx.time(),
        level = "ERROR",
        event = "error",
        request_id = request_id,
        error_type = error_type,
        error_message = error_message,
        method = ngx.req.get_method(),
        uri = ngx.var.uri,
        remote_addr = ngx.var.remote_addr
    }
    
    if extra_data then
        for k, v in pairs(extra_data) do
            log_data[k] = v
        end
    end
    
    ngx.log(ngx.ERR, cjson.encode(log_data))
end

-- 记录配置变更日志
function _M.log_config_change(namespace_id, change_type, details)
    local log_data = {
        timestamp = ngx.time(),
        level = "INFO",
        event = "config_change",
        namespace_id = namespace_id,
        change_type = change_type,
        details = details
    }
    
    ngx.log(ngx.INFO, cjson.encode(log_data))
end

-- 记录限流日志
function _M.log_rate_limit(request_id, namespace_id, rule_type, reason)
    local log_data = {
        timestamp = ngx.time(),
        level = "WARN",
        event = "rate_limit",
        request_id = request_id,
        namespace_id = namespace_id,
        rule_type = rule_type,
        reason = reason,
        method = ngx.req.get_method(),
        uri = ngx.var.uri,
        remote_addr = ngx.var.remote_addr
    }
    
    ngx.log(ngx.WARN, cjson.encode(log_data))
end

-- 记录代理请求开始日志
function _M.log_proxy_start(request_id, upstream_server)
    local log_data = {
        timestamp = ngx.time(),
        level = "INFO",
        event = "proxy_start",
        request_id = request_id,
        upstream_server = upstream_server.server_name,
        upstream_url = upstream_server.server_url,
        server_type = upstream_server.server_type,
        method = ngx.req.get_method(),
        uri = ngx.var.uri
    }
    
    ngx.log(ngx.INFO, cjson.encode(log_data))
end

-- 记录代理请求结束日志
function _M.log_proxy_end(request_id, upstream_server, status)
    local log_data = {
        timestamp = ngx.time(),
        level = "INFO",
        event = "proxy_end",
        request_id = request_id,
        upstream_server = upstream_server and upstream_server.server_name or "unknown",
        status = status,
        method = ngx.req.get_method(),
        uri = ngx.var.uri
    }
    
    ngx.log(ngx.INFO, cjson.encode(log_data))
end

-- 记录错误日志（简化版本）
function _M.log_error(request_id, error_message)
    local log_data = {
        timestamp = ngx.time(),
        level = "ERROR",
        event = "error",
        request_id = request_id,
        error_message = error_message,
        method = ngx.req.get_method(),
        uri = ngx.var.uri,
        remote_addr = ngx.var.remote_addr
    }
    
    ngx.log(ngx.ERR, cjson.encode(log_data))
end

return _M 