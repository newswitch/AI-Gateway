-- Trie树（前缀树）实现
-- 用于高效的字符串匹配和查找

local _M = {}

-- Trie树节点
local function create_node()
    return {
        children = {},           -- 子节点映射
        namespace_id = nil,      -- 命名空间ID（叶子节点）
        is_end = false,         -- 是否为结束节点
        data = nil              -- 额外数据
    }
end

-- 创建Trie树
function _M.create()
    return create_node()
end

-- 插入数据到Trie树
function _M.insert(trie, key, namespace_id, data)
    local node = trie
    
    -- 遍历key的每个字符
    for i = 1, #key do
        local char = key:sub(i, i)
        
        -- 如果子节点不存在，创建新的
        if not node.children[char] then
            node.children[char] = create_node()
        end
        
        node = node.children[char]
    end
    
    -- 标记为结束节点
    node.is_end = true
    node.namespace_id = namespace_id
    node.data = data
    
    return true
end

-- 查找数据
function _M.search(trie, key)
    local node = trie
    
    -- 遍历key的每个字符
    for i = 1, #key do
        local char = key:sub(i, i)
        
        -- 如果子节点不存在，返回nil
        if not node.children[char] then
            return nil
        end
        
        node = node.children[char]
    end
    
    -- 检查是否为结束节点
    if node.is_end then
        return {
            namespace_id = node.namespace_id,
            data = node.data
        }
    end
    
    return nil
end

-- 查找前缀匹配
function _M.search_prefix(trie, prefix)
    local node = trie
    local results = {}
    
    -- 遍历到前缀的最后一个字符
    for i = 1, #prefix do
        local char = prefix:sub(i, i)
        
        if not node.children[char] then
            return results
        end
        
        node = node.children[char]
    end
    
    -- 收集所有以该前缀开头的键
    _M._collect_keys(node, prefix, results)
    
    return results
end

-- 递归收集所有键
function _M._collect_keys(node, current_key, results)
    if node.is_end then
        table.insert(results, {
            key = current_key,
            namespace_id = node.namespace_id,
            data = node.data
        })
    end
    
    for char, child_node in pairs(node.children) do
        _M._collect_keys(child_node, current_key .. char, results)
    end
end

-- 删除数据
function _M.delete(trie, key)
    local node = trie
    local path = {}
    
    -- 遍历到目标节点
    for i = 1, #key do
        local char = key:sub(i, i)
        
        if not node.children[char] then
            return false  -- 键不存在
        end
        
        table.insert(path, {node = node, char = char})
        node = node.children[char]
    end
    
    -- 如果不是结束节点，返回false
    if not node.is_end then
        return false
    end
    
    -- 标记为非结束节点
    node.is_end = false
    node.namespace_id = nil
    node.data = nil
    
    -- 清理空的父节点
    for i = #path, 1, -1 do
        local path_item = path[i]
        local parent = path_item.node
        local char = path_item.char
        
        -- 如果子节点没有子节点且不是结束节点，删除它
        if not node.is_end and next(node.children) == nil then
            parent.children[char] = nil
            node = parent
        else
            break
        end
    end
    
    return true
end

-- 获取树的大小
function _M.size(trie)
    local count = 0
    _M._count_nodes(trie, count)
    return count
end

-- 递归计算节点数量
function _M._count_nodes(node, count)
    if node.is_end then
        count = count + 1
    end
    
    for _, child_node in pairs(node.children) do
        _M._count_nodes(child_node, count)
    end
end

-- 清空树
function _M.clear(trie)
    trie.children = {}
    trie.namespace_id = nil
    trie.is_end = false
    trie.data = nil
end

-- 打印树结构（调试用）
function _M.print(trie, indent)
    indent = indent or 0
    local spaces = string.rep("  ", indent)
    
    for char, child_node in pairs(trie.children) do
        local info = ""
        if child_node.is_end then
            info = " [namespace_id=" .. (child_node.namespace_id or "nil") .. "]"
        end
        ngx.log(ngx.INFO, spaces .. char .. info)
        _M.print(child_node, indent + 1)
    end
end

return _M
