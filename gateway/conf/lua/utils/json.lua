-- JSON工具模块
local cjson = require "cjson"

local _M = {}

-- 安全编码JSON
function _M.encode(data)
    local ok, result = pcall(cjson.encode, data)
    if not ok then
        ngx.log(ngx.ERR, "JSON encode failed: ", result)
        return nil, result
    end
    return result
end

-- 安全解码JSON
function _M.decode(str)
    if not str or str == ngx.null then
        return nil, "empty string"
    end
    
    local ok, result = pcall(cjson.decode, str)
    if not ok then
        ngx.log(ngx.ERR, "JSON decode failed: ", result)
        return nil, result
    end
    return result
end

-- 检查是否为有效JSON
function _M.is_valid(str)
    local ok, _ = pcall(cjson.decode, str)
    return ok
end

return _M
