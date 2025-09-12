-- Prometheus指标收集Lua脚本
-- 用于从OpenResty网关收集指标并推送到Prometheus

local cjson = require "cjson"
local http = require "resty.http"
local prometheus = require "prometheus"

-- 初始化Prometheus指标
local prometheus_metrics = {
    -- HTTP请求指标
    http_requests_total = prometheus:counter("http_requests_total", "Total HTTP requests", {"method", "path", "status_code", "namespace"}),
    http_request_duration_seconds = prometheus:histogram("http_request_duration_seconds", "HTTP request duration", {"method", "path", "namespace"}),
    
    -- 网关指标
    gateway_requests_total = prometheus:counter("gateway_requests_total", "Total gateway requests", {"method", "path", "namespace", "upstream"}),
    gateway_request_duration_seconds = prometheus:histogram("gateway_request_duration_seconds", "Gateway request duration", {"method", "path", "namespace"}),
    
    -- 限流指标
    rate_limit_hits_total = prometheus:counter("rate_limit_hits_total", "Total rate limit hits", {"namespace", "rule_type"}),
    rate_limit_violations_total = prometheus:counter("rate_limit_violations_total", "Total rate limit violations", {"namespace", "rule_type"}),
    
    -- 缓存指标
    cache_hits_total = prometheus:counter("cache_hits_total", "Total cache hits", {"cache_type"}),
    cache_misses_total = prometheus:counter("cache_misses_total", "Total cache misses", {"cache_type"}),
    
    -- 错误指标
    errors_total = prometheus:counter("errors_total", "Total errors", {"error_type", "namespace", "upstream"})
}

-- 配置Prometheus推送地址
local PROMETHEUS_PUSH_URL = "http://ai-gateway-prometheus-dev:9090/api/v1/push"
local CONFIG_CENTER_URL = "http://ai-gateway-config-center-dev:8000"

-- 推送指标到Prometheus
local function push_metrics_to_prometheus()
    local httpc = http.new()
    local metrics_data = {}
    
    -- 收集所有指标
    for name, metric in pairs(prometheus_metrics) do
        local metric_data = metric:collect()
        if metric_data then
            table.insert(metrics_data, metric_data)
        end
    end
    
    -- 推送到Prometheus
    local res, err = httpc:request_uri(PROMETHEUS_PUSH_URL, {
        method = "POST",
        body = table.concat(metrics_data, "\n"),
        headers = {
            ["Content-Type"] = "text/plain"
        }
    })
    
    if not res or res.status ~= 200 then
        ngx.log(ngx.ERR, "Failed to push metrics to Prometheus: ", err or res.body)
    end
end

-- 推送指标到配置中心（备用方案）
local function push_metrics_to_config_center(metric_data)
    local httpc = http.new()
    
    local res, err = httpc:request_uri(CONFIG_CENTER_URL .. "/api/metrics/push", {
        method = "POST",
        body = cjson.encode(metric_data),
        headers = {
            ["Content-Type"] = "application/json"
        }
    })
    
    if not res or res.status ~= 200 then
        ngx.log(ngx.ERR, "Failed to push metrics to config center: ", err or res.body)
    end
end

-- 记录HTTP请求指标
local function record_http_request(method, path, status_code, namespace, duration)
    prometheus_metrics.http_requests_total:inc(1, {method, path, tostring(status_code), namespace})
    prometheus_metrics.http_request_duration_seconds:observe(duration, {method, path, namespace})
end

-- 记录网关请求指标
local function record_gateway_request(method, path, namespace, upstream, duration)
    prometheus_metrics.gateway_requests_total:inc(1, {method, path, namespace, upstream})
    prometheus_metrics.gateway_request_duration_seconds:observe(duration, {method, path, namespace})
end

-- 记录限流指标
local function record_rate_limit_hit(namespace, rule_type)
    prometheus_metrics.rate_limit_hits_total:inc(1, {namespace, rule_type})
end

local function record_rate_limit_violation(namespace, rule_type)
    prometheus_metrics.rate_limit_violations_total:inc(1, {namespace, rule_type})
end

-- 记录缓存指标
local function record_cache_hit(cache_type)
    prometheus_metrics.cache_hits_total:inc(1, {cache_type})
end

local function record_cache_miss(cache_type)
    prometheus_metrics.cache_misses_total:inc(1, {cache_type})
end

-- 记录错误指标
local function record_error(error_type, namespace, upstream)
    prometheus_metrics.errors_total:inc(1, {error_type, namespace, upstream})
end

-- 从请求中提取命名空间信息
local function extract_namespace()
    local headers = ngx.req.get_headers()
    local namespace = headers["X-Namespace"] or "default"
    
    -- 也可以从路径中提取
    local path = ngx.var.request_uri
    if string.match(path, "/api/namespaces/(%w+)") then
        namespace = string.match(path, "/api/namespaces/(%w+)")
    end
    
    return namespace
end

-- 从请求中提取上游信息
local function extract_upstream()
    local headers = ngx.req.get_headers()
    return headers["X-Upstream"] or "unknown"
end

-- 获取请求方法
local function get_request_method()
    return ngx.var.request_method
end

-- 获取请求路径
local function get_request_path()
    return ngx.var.request_uri
end

-- 获取响应状态码
local function get_response_status()
    return ngx.status
end

-- 计算请求持续时间
local function get_request_duration()
    return ngx.var.request_time
end

-- 导出函数
local _M = {
    record_http_request = record_http_request,
    record_gateway_request = record_gateway_request,
    record_rate_limit_hit = record_rate_limit_hit,
    record_rate_limit_violation = record_rate_limit_violation,
    record_cache_hit = record_cache_hit,
    record_cache_miss = record_cache_miss,
    record_error = record_error,
    extract_namespace = extract_namespace,
    extract_upstream = extract_upstream,
    get_request_method = get_request_method,
    get_request_path = get_request_path,
    get_response_status = get_response_status,
    get_request_duration = get_request_duration,
    push_metrics_to_prometheus = push_metrics_to_prometheus,
    push_metrics_to_config_center = push_metrics_to_config_center
}

return _M
