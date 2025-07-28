-- OpenSSL X509 Chain 模块占位符
-- 这个文件用于避免lua-resty-http加载SSL模块时的错误

local _M = {}

-- 提供基本的占位符函数
function _M.new()
    return {
        verify = function() return true end,
        add = function() return true end,
        set_verify_flags = function() return true end,
        set_verify_depth = function() return true end
    }
end

return _M 