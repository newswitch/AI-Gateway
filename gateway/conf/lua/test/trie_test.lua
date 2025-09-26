-- Trie树测试模块
-- 用于测试Trie树的功能

local trie = require "utils.trie"
local namespace_matcher = require "auth.namespace_matcher"

local _M = {}

-- 测试Trie树基本功能
function _M.test_trie_basic()
    ngx.log(ngx.INFO, "=== Testing Trie Basic Functions ===")
    
    local t = trie.create()
    
    -- 插入测试数据
    trie.insert(t, "channelcode:web", 1, {name = "Web渠道"})
    trie.insert(t, "channelcode:wechat", 2, {name = "微信渠道"})
    trie.insert(t, "channel:mobile", 3, {name = "移动渠道"})
    
    -- 测试查找
    local result1 = trie.search(t, "channelcode:web")
    ngx.log(ngx.INFO, "Search 'channelcode:web': ", json.encode(result1))
    
    local result2 = trie.search(t, "channelcode:wechat")
    ngx.log(ngx.INFO, "Search 'channelcode:wechat': ", json.encode(result2))
    
    local result3 = trie.search(t, "channel:mobile")
    ngx.log(ngx.INFO, "Search 'channel:mobile': ", json.encode(result3))
    
    -- 测试不存在的键
    local result4 = trie.search(t, "channelcode:app")
    ngx.log(ngx.INFO, "Search 'channelcode:app': ", json.encode(result4))
    
    -- 测试前缀搜索
    local prefix_results = trie.search_prefix(t, "channelcode:")
    ngx.log(ngx.INFO, "Prefix search 'channelcode:': ", json.encode(prefix_results))
    
    -- 打印树结构
    ngx.log(ngx.INFO, "Trie structure:")
    trie.print(t)
    
    ngx.log(ngx.INFO, "Trie size: ", trie.size(t))
end

-- 测试命名空间匹配器
function _M.test_namespace_matcher()
    ngx.log(ngx.INFO, "=== Testing Namespace Trie Matcher ===")
    
    -- 模拟请求
    local request_info = {
        headers = {
            ["channelcode"] = "web",
            ["Content-Type"] = "application/json"
        },
        body = '{"user_id": "12345"}',
        query_params = {
            ["version"] = "v2"
        }
    }
    
    -- 测试匹配
    local namespace = namespace_matcher.find_matching_namespace(request_info)
    if namespace then
        ngx.log(ngx.INFO, "Found namespace: ", namespace.code, " (", namespace.name, ")")
    else
        ngx.log(ngx.INFO, "No namespace found")
    end
    
    -- 获取缓存统计
    local stats = namespace_matcher.get_cache_stats()
    ngx.log(ngx.INFO, "Cache stats: ", json.encode(stats))
end

-- 性能测试
function _M.test_performance()
    ngx.log(ngx.INFO, "=== Testing Trie Performance ===")
    
    local t = trie.create()
    
    -- 插入大量数据
    local start_time = ngx.now()
    for i = 1, 1000 do
        trie.insert(t, "field" .. i .. ":value" .. i, i, {id = i})
    end
    local insert_time = ngx.now() - start_time
    ngx.log(ngx.INFO, "Insert 1000 items time: ", insert_time, "s")
    
    -- 测试查找性能
    start_time = ngx.now()
    for i = 1, 1000 do
        local result = trie.search(t, "field" .. i .. ":value" .. i)
        if not result then
            ngx.log(ngx.ERR, "Search failed for item ", i)
        end
    end
    local search_time = ngx.now() - start_time
    ngx.log(ngx.INFO, "Search 1000 items time: ", search_time, "s")
    
    ngx.log(ngx.INFO, "Trie size: ", trie.size(t))
end

-- 运行所有测试
function _M.run_all_tests()
    ngx.log(ngx.INFO, "=== Starting Trie Tests ===")
    
    _M.test_trie_basic()
    _M.test_namespace_matcher()
    _M.test_performance()
    
    ngx.log(ngx.INFO, "=== Trie Tests Completed ===")
end

return _M
