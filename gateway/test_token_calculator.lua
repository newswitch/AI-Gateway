-- 测试token计算器模块
-- 用于验证子请求方式的token计算是否正常工作

local token_calculator = require "utils.token_calculator"
local json = require "utils.json"

-- 测试文本
local test_texts = {
    "Hello, world!",
    "你好，世界！",
    "这是一个测试文本，用于验证token计算功能。",
    "This is a longer test text that contains both English and Chinese characters to test the token calculation accuracy.",
    "混合文本测试：Hello 世界！This is a mixed language test. 中文和English混合。"
}

local test_models = {
    "Qwen3-8B",
    "Qwen3-32B", 
    "Deepseek-R1-7B"
}

print("=== Token计算器测试 ===")
print()

-- 测试估算功能
print("1. 测试估算功能:")
for i, text in ipairs(test_texts) do
    local estimated = token_calculator.estimate_tokens(text, "Qwen3-8B")
    print(string.format("文本 %d: %s", i, text:sub(1, 50) .. (text:len() > 50 and "..." or "")))
    print(string.format("估算token数: %d", estimated))
    print()
end

-- 测试子请求功能（如果可用）
print("2. 测试子请求功能:")
for i, text in ipairs(test_texts) do
    print(string.format("测试文本 %d: %s", i, text:sub(1, 50) .. (text:len() > 50 and "..." or "")))
    
    for _, model in ipairs(test_models) do
        local tokens = token_calculator.calculate_tokens_with_subrequest(text, model)
        print(string.format("模型 %s: %d tokens", model, tokens))
    end
    print()
end

-- 测试批量计算
print("3. 测试批量计算:")
local batch_tokens = token_calculator.calculate_tokens_batch(test_texts, "Qwen3-8B")
print(string.format("批量计算总token数: %d", batch_tokens))
print()

-- 测试混合模式
print("4. 测试混合模式:")
for i, text in ipairs(test_texts) do
    local subrequest_tokens = token_calculator.calculate_tokens_hybrid(text, "Qwen3-8B", true)
    local estimated_tokens = token_calculator.calculate_tokens_hybrid(text, "Qwen3-8B", false)
    print(string.format("文本 %d: 子请求=%d, 估算=%d", i, subrequest_tokens, estimated_tokens))
end

print()
print("=== 测试完成 ===")
