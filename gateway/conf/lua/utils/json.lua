-- JSON工具模块
local cjson = require "cjson"

local _M = {}

-- 配置cjson以正确处理UTF-8编码
cjson.encode_empty_table_as_object(false)
cjson.encode_number_precision(14)
cjson.encode_keep_buffer(false)
cjson.encode_sparse_array(true)

-- 安全编码JSON
function _M.encode(data)
    local ok, result = pcall(cjson.encode, data)
    if not ok then
        ngx.log(ngx.ERR, "JSON encode failed: ", result)
        return nil, result
    end
    return result
end

-- 安全解码JSON - 支持UTF-8编码
function _M.decode(str)
    if not str or str == ngx.null then
        return nil, "empty string"
    end
    
    -- 确保字符串是UTF-8编码
    local utf8_str = str
    if type(str) == "string" then
        -- 检查是否为有效的UTF-8字符串
        local valid_utf8 = true
        for i = 1, #str do
            local byte = string.byte(str, i)
            if byte > 127 then
                -- 检查UTF-8多字节序列
                if byte >= 194 and byte <= 244 then
                    -- 这是一个有效的UTF-8起始字节
                    local next_bytes = 0
                    if byte >= 240 then next_bytes = 3
                    elseif byte >= 224 then next_bytes = 2
                    elseif byte >= 194 then next_bytes = 1
                    end
                    
                    -- 检查后续字节
                    for j = 1, next_bytes do
                        local next_byte = string.byte(str, i + j)
                        if not next_byte or next_byte < 128 or next_byte > 191 then
                            valid_utf8 = false
                            break
                        end
                    end
                    i = i + next_bytes
                else
                    valid_utf8 = false
                    break
                end
            end
        end
        
        if not valid_utf8 then
            ngx.log(ngx.NOTICE, "Invalid UTF-8 string detected, attempting to fix")
            -- 尝试修复UTF-8编码
            utf8_str = string.gsub(str, "[\128-\255]", function(c)
                return string.format("\\u%04x", string.byte(c))
            end)
        end
    end
    
    local ok, result = pcall(cjson.decode, utf8_str)
    if not ok then
        ngx.log(ngx.ERR, "JSON decode failed: ", result, " for string: ", string.sub(utf8_str, 1, 100))
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
