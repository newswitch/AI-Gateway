-- 定时任务调度器模块
-- 负责管理所有定时任务的创建和执行

local _M = {}

-- 配置同步任务
local function sync_config()
    local http = require "utils.http"
    local config = require "core.init"
    
    -- 调用Config Center的同步接口
    local config_center_url = "http://" .. config.config_center.host .. ":" .. config.config_center.port .. "/sync"
    
    ngx.log(ngx.INFO, "Syncing config from Config Center: ", config_center_url)
    
    local res, err = http.post(config_center_url, "", {
        ["Content-Type"] = "application/json"
    })
    
    if res and res.status == 200 then
        ngx.log(ngx.INFO, "Config sync completed successfully")
        return true
    else
        ngx.log(ngx.ERR, "Config sync failed: ", err or "Unknown error, status: " .. (res and res.status or "nil"))
        return false
    end
end

-- 健康检查任务
local function health_check()
    local health = require "monitoring.health"
    local health_status = health.check_health()
    
    if health_status.status == "healthy" then
        ngx.log(ngx.INFO, "Health check passed")
    else
        ngx.log(ngx.WARN, "Health check failed: ", health_status.status)
    end
end

-- 清理过期数据任务
local function cleanup_data()
    -- 清理过期的限流数据
    local ngx_shared = ngx.shared.rate_limit
    ngx_shared:flush_expired()
    
    -- 清理过期指标
    local metrics = require "monitoring.metrics"
    metrics.cleanup_expired_metrics()
    
    ngx.log(ngx.INFO, "Data cleanup completed")
end

-- 定时更新指标数据任务
local function update_metrics()
    local metrics = require "monitoring.metrics"
    metrics.update_metrics_data()
end

-- 系统状态报告任务
local function system_status_report()
    local health = require "monitoring.health"
    local metrics = require "monitoring.metrics"
    
    local health_status = health.check_health()
    local global_metrics = metrics.get_global_metrics()
    
    ngx.log(ngx.INFO, "System Status Report:")
    ngx.log(ngx.INFO, "  Health: ", health_status.status)
    ngx.log(ngx.INFO, "  Total Requests: ", global_metrics.total_requests or 0)
    ngx.log(ngx.INFO, "  Total Namespaces: ", global_metrics.total_namespaces or 0)
    ngx.log(ngx.INFO, "  Total Upstreams: ", global_metrics.total_upstreams or 0)
end

-- 任务配置
local TASK_CONFIG = {
    {
        name = "config_sync",
        func = sync_config,
        interval = 30,  -- 30秒
        description = "配置同步任务"
    },
    {
        name = "health_check",
        func = health_check,
        interval = 60,  -- 60秒
        description = "健康检查任务"
    },
    {
        name = "metrics_update",
        func = update_metrics,
        interval = 60,  -- 60秒
        description = "指标数据更新任务"
    },
    {
        name = "data_cleanup",
        func = cleanup_data,
        interval = 300, -- 5分钟
        description = "数据清理任务"
    },
    {
        name = "status_report",
        func = system_status_report,
        interval = 600, -- 10分钟
        description = "系统状态报告任务"
    }
}

-- 启动所有定时任务
function _M.start_all_tasks()
    ngx.log(ngx.INFO, "Starting scheduled tasks...")
    
    for _, task in ipairs(TASK_CONFIG) do
        local ok, err = ngx.timer.every(task.interval, task.func)
        
        if ok then
            ngx.log(ngx.INFO, "Started task: ", task.name, " (", task.description, ") - interval: ", task.interval, "s")
        else
            ngx.log(ngx.ERR, "Failed to start task: ", task.name, " - error: ", err)
        end
    end
    
    ngx.log(ngx.INFO, "All scheduled tasks started")
end

-- 启动单个任务（仅用于调试）
function _M.start_task(task_name)
    for _, task in ipairs(TASK_CONFIG) do
        if task.name == task_name then
            local ok, err = ngx.timer.every(task.interval, task.func)
            
            if ok then
                ngx.log(ngx.INFO, "Started task: ", task.name, " (", task.description, ")")
                return true
            else
                ngx.log(ngx.ERR, "Failed to start task: ", task.name, " - error: ", err)
                return false
            end
        end
    end
    
    ngx.log(ngx.ERR, "Task not found: ", task_name)
    return false
end

-- 获取任务列表
function _M.get_task_list()
    local tasks = {}
    for _, task in ipairs(TASK_CONFIG) do
        table.insert(tasks, {
            name = task.name,
            interval = task.interval,
            description = task.description
        })
    end
    return tasks
end

-- 手动执行任务（仅用于调试）
function _M.execute_task(task_name)
    for _, task in ipairs(TASK_CONFIG) do
        if task.name == task_name then
            ngx.log(ngx.INFO, "Manually executing task: ", task.name)
            local ok, err = pcall(task.func)
            
            if ok then
                ngx.log(ngx.INFO, "Task executed successfully: ", task.name)
                return true
            else
                ngx.log(ngx.ERR, "Task execution failed: ", task.name, " - error: ", err)
                return false
            end
        end
    end
    
    ngx.log(ngx.ERR, "Task not found: ", task_name)
    return false
end

-- 获取任务状态
function _M.get_task_status()
    local status = {
        total_tasks = #TASK_CONFIG,
        tasks = {}
    }
    
    for _, task in ipairs(TASK_CONFIG) do
        table.insert(status.tasks, {
            name = task.name,
            interval = task.interval,
            description = task.description,
            status = "running"  -- 这里可以添加更详细的状态检查
        })
    end
    
    return status
end

return _M
