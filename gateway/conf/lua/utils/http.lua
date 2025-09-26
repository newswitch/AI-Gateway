-- HTTP客户端工具模块
local cjson = require "cjson"

local _M = {}

-- 发送GET请求
function _M.get(url, headers)
    return _M.request("GET", url, nil, headers)
end

-- 发送POST请求
function _M.post(url, body, headers)
    return _M.request("POST", url, body, headers)
end

-- 发送PUT请求
function _M.put(url, body, headers)
    return _M.request("PUT", url, body, headers)
end

-- 发送DELETE请求
function _M.delete(url, headers)
    return _M.request("DELETE", url, nil, headers)
end

-- 通用HTTP请求方法
function _M.request(method, url, body, headers)
    -- 解析URL - 修复端口解析问题
    local host, port, path = url:match("http://([^:/]+):?(%d*)(.*)")
    if not host then
        return nil, "Invalid URL format"
    end
    
    -- 修复端口解析：如果端口为空或无效，使用默认端口
    if port == "" or not port then
        port = 80
    else
        port = tonumber(port)
        if not port then
            return nil, "Invalid port number"
        end
    end
    
    -- 修复路径解析：确保路径正确提取
    if not path or path == "" then
        path = "/"
    end
    
    -- 确保路径以 / 开头
    if not path:match("^/") then
        path = "/" .. path
    end
    
    -- 构建内部请求路径
    local internal_path = "/_http_proxy" .. path
    
    -- 设置请求头
    local request_headers = headers or {}
    request_headers["Host"] = host .. ":" .. port
    request_headers["X-Real-IP"] = ngx.var.remote_addr or "127.0.0.1"
    request_headers["X-Forwarded-For"] = ngx.var.remote_addr or "127.0.0.1"
    request_headers["X-Forwarded-Proto"] = "http"
    
    if body and method ~= "GET" then
        request_headers["Content-Type"] = request_headers["Content-Type"] or "application/json"
        request_headers["Content-Length"] = #body
    end
    
    -- 构建查询参数 - 修复URL编码问题
    local query_string = "target_host=" .. ngx.escape_uri(host) .. 
                        "&target_port=" .. port .. 
                        "&target_path=" .. path
    
    -- 使用ngx.location.capture发送内部请求
    local res = ngx.location.capture(internal_path .. "?" .. query_string, {
        method = method == "GET" and ngx.HTTP_GET or 
                 method == "POST" and ngx.HTTP_POST or
                 method == "PUT" and ngx.HTTP_PUT or
                 method == "DELETE" and ngx.HTTP_DELETE or
                 ngx.HTTP_GET,
        body = body,
        headers = request_headers
    })
    
    if not res then
        return nil, "Request failed"
    end
    
    -- 解析响应头
    local response_headers = {}
    if res.header then
        for k, v in pairs(res.header) do
            response_headers[k] = v
        end
    end
    
    return {
        status = res.status,
        body = res.body,
        headers = response_headers
    }
end

-- 构建URL
function _M.build_url(host, port, path, query)
    local url = "http://" .. host
    if port and port ~= 80 then
        url = url .. ":" .. port
    end
    url = url .. path
    
    if query then
        local query_str = ""
        for k, v in pairs(query) do
            if query_str ~= "" then
                query_str = query_str .. "&"
            end
            query_str = query_str .. k .. "=" .. ngx.escape_uri(tostring(v))
        end
        if query_str ~= "" then
            url = url .. "?" .. query_str
        end
    end
    
    return url
end

-- 检查响应状态
function _M.is_success(res)
    return res and res.status >= 200 and res.status < 300
end

-- 解析JSON响应
function _M.parse_json_response(res)
    if not res or not res.body then
        return nil, "empty response"
    end
    
    local json = require "utils.json"
    return json.decode(res.body)
end

return _M