-- JSON工具模块
-- 提供JSON处理功能

local _M = {}

local cjson = require "cjson"

-- 安全解码JSON
function _M.safe_decode(json_str)
    if not json_str or json_str == "" then
        return nil, "Empty JSON string"
    end
    
    local ok, result = pcall(cjson.decode, json_str)
    if ok then
        return result
    else
        return nil, "JSON decode failed: " .. tostring(result)
    end
end

-- 安全编码JSON
function _M.safe_encode(data)
    local ok, result = pcall(cjson.encode, data)
    if ok then
        return result
    else
        return nil, "JSON encode failed: " .. tostring(result)
    end
end

-- 检查是否为有效的JSON
function _M.is_valid_json(json_str)
    local ok, _ = pcall(cjson.decode, json_str)
    return ok
end

-- 合并JSON对象
function _M.merge_json(obj1, obj2)
    if not obj1 then
        return obj2
    end
    
    if not obj2 then
        return obj1
    end
    
    local result = {}
    
    -- 复制第一个对象
    for k, v in pairs(obj1) do
        result[k] = v
    end
    
    -- 合并第二个对象
    for k, v in pairs(obj2) do
        result[k] = v
    end
    
    return result
end

return _M 