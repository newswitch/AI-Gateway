-- HTTP客户端工具
-- 提供HTTP请求功能

local _M = {}

-- 尝试加载http模块，如果失败则记录警告但继续
local http
local ok, result = pcall(require, "resty.http")
if ok then
    http = result
else
    ngx.log(ngx.WARN, "Failed to load resty.http: ", result)
    -- 创建一个简单的fallback
    http = {
        new = function()
            return {
                set_timeout = function() end,
                request_uri = function() 
                    return nil, "HTTP module not available"
                end
            }
        end
    }
end
local cjson = require "cjson"

-- HTTP请求封装
function _M.request(method, url, data, headers, timeout)
    timeout = timeout or 5000  -- 默认5秒超时
    
    local httpc = http.new()
    httpc:set_timeout(timeout)
    
    -- 设置默认请求头
    local request_headers = {
        ["Content-Type"] = "application/json",
        ["User-Agent"] = "AI-Gateway/1.0"
    }
    
    -- 合并自定义请求头
    if headers then
        for k, v in pairs(headers) do
            request_headers[k] = v
        end
    end
    
    -- 发送请求
    local res, err = httpc:request_uri(url, {
        method = method,
        headers = request_headers,
        body = data and cjson.encode(data) or nil
    })
    
    if not res then
        return nil, "HTTP request failed: " .. (err or "unknown error")
    end
    
    -- 检查HTTP状态码
    if res.status >= 400 then
        return nil, "HTTP " .. res.status .. ": " .. (res.body or "")
    end
    
    -- 解析响应
    local response_data
    if res.body and res.body ~= "" then
        local ok, data = pcall(cjson.decode, res.body)
        if ok then
            response_data = data
        else
            return nil, "Failed to parse JSON response: " .. data
        end
    end
    
    return response_data
end

-- GET请求
function _M.get(url, headers, timeout)
    return _M.request("GET", url, nil, headers, timeout)
end

-- POST请求
function _M.post(url, data, headers, timeout)
    return _M.request("POST", url, data, headers, timeout)
end

-- PUT请求
function _M.put(url, data, headers, timeout)
    return _M.request("PUT", url, data, headers, timeout)
end

-- DELETE请求
function _M.delete(url, headers, timeout)
    return _M.request("DELETE", url, nil, headers, timeout)
end

return _M 