-- HTTP客户端工具模块
local http = require "resty.http"

local _M = {}

-- 创建HTTP客户端
function _M.new()
    local httpc = http.new()
    httpc:set_timeout(5000)  -- 5秒超时
    return httpc
end

-- 发送GET请求
function _M.get(url, headers)
    local httpc = _M.new()
    local res, err = httpc:request_uri(url, {
        method = "GET",
        headers = headers or {}
    })
    
    if not res then
        ngx.log(ngx.ERR, "HTTP GET request failed: ", err)
        return nil, err
    end
    
    return res
end

-- 发送POST请求
function _M.post(url, body, headers)
    local httpc = _M.new()
    local res, err = httpc:request_uri(url, {
        method = "POST",
        headers = headers or {},
        body = body
    })
    
    if not res then
        ngx.log(ngx.ERR, "HTTP POST request failed: ", err)
        return nil, err
    end
    
    return res
end

-- 发送PUT请求
function _M.put(url, body, headers)
    local httpc = _M.new()
    local res, err = httpc:request_uri(url, {
        method = "PUT",
        headers = headers or {},
        body = body
    })
    
    if not res then
        ngx.log(ngx.ERR, "HTTP PUT request failed: ", err)
        return nil, err
    end
    
    return res
end

-- 发送DELETE请求
function _M.delete(url, headers)
    local httpc = _M.new()
    local res, err = httpc:request_uri(url, {
        method = "DELETE",
        headers = headers or {}
    })
    
    if not res then
        ngx.log(ngx.ERR, "HTTP DELETE request failed: ", err)
        return nil, err
    end
    
    return res
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
