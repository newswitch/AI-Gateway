-- 日志记录模块
-- 负责记录结构化日志

local json = require "utils.json"

local _M = {}

-- 日志级别
local LOG_LEVELS = {
    DEBUG = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4
}

-- 获取当前日志级别
local function get_log_level()
    local level = os.getenv("LOG_LEVEL") or "INFO"
    return LOG_LEVELS[level:upper()] or LOG_LEVELS.INFO
end

-- 记录日志
local function log(level, message, data)
    if level < get_log_level() then
        return
    end
    
    local log_entry = {
        timestamp = ngx.time(),
        level = level,
        message = message,
        data = data or {}
    }
    
    -- 添加请求上下文
    if ngx.ctx.request_id then
        log_entry.request_id = ngx.ctx.request_id
    end
    
    if ngx.ctx.namespace_id then
        log_entry.namespace_id = ngx.ctx.namespace_id
    end
    
    if ngx.ctx.upstream then
        log_entry.upstream = ngx.ctx.upstream.name
    end
    
    local log_str = json.encode(log_entry)
    
    if level >= LOG_LEVELS.ERROR then
        ngx.log(ngx.ERR, log_str)
    elseif level >= LOG_LEVELS.WARN then
        ngx.log(ngx.WARN, log_str)
    elseif level >= LOG_LEVELS.INFO then
        ngx.log(ngx.INFO, log_str)
    else
        ngx.log(ngx.DEBUG, log_str)
    end
end

-- 记录请求开始
function _M.log_request_start(request_id, request_info)
    log(LOG_LEVELS.INFO, "Request started", {
        request_id = request_id,
        method = request_info.method,
        path = request_info.path,
        remote_addr = request_info.remote_addr,
        user_agent = request_info.user_agent
    })
end

-- 记录请求结束
function _M.log_request_end(request_id, status, message)
    log(LOG_LEVELS.INFO, "Request completed", {
        request_id = request_id,
        status = status,
        message = message
    })
end

-- 记录错误
function _M.log_error(message, data)
    log(LOG_LEVELS.ERROR, message, data)
end

-- 记录警告
function _M.log_warn(message, data)
    log(LOG_LEVELS.WARN, message, data)
end

-- 记录信息
function _M.log_info(message, data)
    log(LOG_LEVELS.INFO, message, data)
end

-- 记录调试信息
function _M.log_debug(message, data)
    log(LOG_LEVELS.DEBUG, message, data)
end

-- 记录策略执行
function _M.log_policy_execution(namespace_id, policy_name, result, message)
    log(LOG_LEVELS.INFO, "Policy executed", {
        namespace_id = namespace_id,
        policy_name = policy_name,
        result = result,
        message = message
    })
end

-- 记录命名空间匹配
function _M.log_namespace_match(namespace_id, matcher_info)
    log(LOG_LEVELS.INFO, "Namespace matched", {
        namespace_id = namespace_id,
        matcher = matcher_info
    })
end

-- 记录上游选择
function _M.log_upstream_selection(upstream, selection_reason)
    log(LOG_LEVELS.INFO, "Upstream selected", {
        upstream_name = upstream.name,
        upstream_address = upstream.address,
        selection_reason = selection_reason
    })
end

-- 记录代理错误
function _M.log_proxy_error(upstream, status, error_message)
    log(LOG_LEVELS.ERROR, "Proxy error", {
        upstream_name = upstream.name,
        upstream_address = upstream.address,
        status = status,
        error = error_message
    })
end

-- 记录配置更新
function _M.log_config_update(config_type, success, message)
    log(LOG_LEVELS.INFO, "Config updated", {
        config_type = config_type,
        success = success,
        message = message
    })
end

-- 记录健康检查
function _M.log_health_check(service, status, message)
    log(LOG_LEVELS.INFO, "Health check", {
        service = service,
        status = status,
        message = message
    })
end

return _M
