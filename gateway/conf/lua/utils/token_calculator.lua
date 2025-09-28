-- Token计算工具模块 - 使用子请求方式
-- 解决body_filter_by_lua_block阶段无法发送HTTP请求的问题

local json = require "utils.json"
local core = require "core.init"

local _M = {}

-- 使用子请求计算token数量
function _M.calculate_tokens_with_subrequest(text, model)
    -- 使用内部token计算location
    local query_string = "text=" .. ngx.escape_uri(text) .. 
                        "&model=" .. ngx.escape_uri(model or "Qwen3-8B")
    
    -- 发送子请求到内部token计算服务
    local res = ngx.location.capture("/_token_calc?" .. query_string, {
        method = ngx.HTTP_GET
    })
    
    if not res then
        ngx.log(ngx.WARN, "Token calculation subrequest failed")
        return _M.estimate_tokens(text, model)  -- 降级到估算
    end
    
    if res.status ~= 200 then
        ngx.log(ngx.WARN, "Token calculation subrequest failed with status: ", res.status)
        return _M.estimate_tokens(text, model)  -- 降级到估算
    end
    
    -- 解析响应
    local response_data, parse_err = json.decode(res.body)
    if not response_data then
        ngx.log(ngx.WARN, "Failed to parse token calculation response: ", parse_err)
        return _M.estimate_tokens(text, model)  -- 降级到估算
    end
    
    if response_data.success then
        return response_data.token_count or 0
    else
        ngx.log(ngx.WARN, "Token calculation failed: ", response_data.error or "Unknown error")
        return _M.estimate_tokens(text, model)  -- 降级到估算
    end
end

-- 批量计算多个文本块的token数量
function _M.calculate_tokens_batch(texts, model)
    local total_tokens = 0
    for _, text in ipairs(texts) do
        total_tokens = total_tokens + _M.calculate_tokens_with_subrequest(text, model)
    end
    return total_tokens
end

-- 快速估算token数量（用于高频调用场景）
function _M.estimate_tokens(text, model)
    -- 根据模型类型使用不同的估算策略
    local model_type = model or "Qwen3-8B"
    
    if model_type:match("Qwen") then
        -- Qwen模型：中文字符按1.5个token计算，英文按0.25个token计算
        local chinese_chars = 0
        local english_chars = 0
        
        for char in text:gmatch(".") do
            local byte = string.byte(char)
            if byte >= 0x4E00 and byte <= 0x9FFF then
                chinese_chars = chinese_chars + 1
            else
                english_chars = english_chars + 1
            end
        end
        
        return math.ceil(chinese_chars * 1.5 + english_chars * 0.25)
    else
        -- 默认估算：每4个字符约1个token
        return math.ceil(string.len(text) / 4)
    end
end

-- 混合模式：结合子请求和估算
function _M.calculate_tokens_hybrid(text, model, use_subrequest)
    if use_subrequest then
        return _M.calculate_tokens_with_subrequest(text, model)
    else
        return _M.estimate_tokens(text, model)
    end
end

return _M
