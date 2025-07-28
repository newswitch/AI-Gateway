-- 时间工具模块
-- 提供时间相关的实用函数

local _M = {}

-- 获取当前时间戳
function _M.get_current_time()
    return ngx.time()
end

-- 获取当前时间戳（毫秒）
function _M.get_current_time_ms()
    return ngx.now() * 1000
end

-- 获取当前时间戳（微秒）
function _M.get_current_time_us()
    return ngx.now() * 1000000
end

-- 格式化时间戳为日期字符串
function _M.format_time(timestamp, format)
    timestamp = timestamp or ngx.time()
    format = format or "%Y-%m-%d %H:%M:%S"
    
    local time_table = os.date("*t", timestamp)
    local formatted = os.date(format, timestamp)
    
    return formatted, time_table
end

-- 计算时间窗口开始时间
function _M.get_window_start(current_time, window_size)
    current_time = current_time or ngx.time()
    window_size = window_size or 3600  -- 默认1小时
    
    return math.floor(current_time / window_size) * window_size
end

-- 计算时间窗口结束时间
function _M.get_window_end(window_start, window_size)
    window_size = window_size or 3600
    return window_start + window_size - 1
end

-- 检查时间是否在指定窗口内
function _M.is_in_window(timestamp, window_start, window_size)
    local window_end = _M.get_window_end(window_start, window_size)
    return timestamp >= window_start and timestamp <= window_end
end

-- 计算时间差（秒）
function _M.time_diff(time1, time2)
    time1 = time1 or ngx.time()
    time2 = time2 or ngx.time()
    return math.abs(time2 - time1)
end

-- 计算时间差（分钟）
function _M.time_diff_minutes(time1, time2)
    return _M.time_diff(time1, time2) / 60
end

-- 计算时间差（小时）
function _M.time_diff_hours(time1, time2)
    return _M.time_diff(time1, time2) / 3600
end

-- 计算时间差（天）
function _M.time_diff_days(time1, time2)
    return _M.time_diff(time1, time2) / 86400
end

-- 获取今天的开始时间戳
function _M.get_today_start()
    local current_time = ngx.time()
    local time_table = os.date("*t", current_time)
    time_table.hour = 0
    time_table.min = 0
    time_table.sec = 0
    return os.time(time_table)
end

-- 获取本周的开始时间戳
function _M.get_week_start()
    local current_time = ngx.time()
    local time_table = os.date("*t", current_time)
    local days_since_monday = time_table.wday - 2  -- 周一是1，周日是7
    if days_since_monday < 0 then
        days_since_monday = 6  -- 如果是周日
    end
    
    time_table.day = time_table.day - days_since_monday
    time_table.hour = 0
    time_table.min = 0
    time_table.sec = 0
    return os.time(time_table)
end

-- 获取本月的开始时间戳
function _M.get_month_start()
    local current_time = ngx.time()
    local time_table = os.date("*t", current_time)
    time_table.day = 1
    time_table.hour = 0
    time_table.min = 0
    time_table.sec = 0
    return os.time(time_table)
end

-- 检查是否是工作时间（周一至周五 9:00-18:00）
function _M.is_work_time(timestamp)
    timestamp = timestamp or ngx.time()
    local time_table = os.date("*t", timestamp)
    
    -- 检查是否是工作日（周一到周五）
    if time_table.wday < 2 or time_table.wday > 6 then
        return false
    end
    
    -- 检查时间是否在工作时间内
    local hour = time_table.hour
    return hour >= 9 and hour < 18
end

-- 获取时间窗口的剩余时间
function _M.get_window_remaining(window_start, window_size)
    local current_time = ngx.time()
    local window_end = _M.get_window_end(window_start, window_size)
    
    if current_time >= window_end then
        return 0
    end
    
    return window_end - current_time
end

-- 计算下一个时间窗口的开始时间
function _M.get_next_window_start(current_window_start, window_size)
    return current_window_start + window_size
end

-- 计算上一个时间窗口的开始时间
function _M.get_prev_window_start(current_window_start, window_size)
    return current_window_start - window_size
end

-- 时间字符串解析（支持多种格式）
function _M.parse_time_string(time_str)
    if not time_str then
        return nil
    end
    
    -- 尝试解析ISO 8601格式
    local year, month, day, hour, min, sec = 
        time_str:match("(%d+)-(%d+)-(%d+)T(%d+):(%d+):(%d+)")
    
    if year then
        local time_table = {
            year = tonumber(year),
            month = tonumber(month),
            day = tonumber(day),
            hour = tonumber(hour),
            min = tonumber(min),
            sec = tonumber(sec)
        }
        return os.time(time_table)
    end
    
    -- 尝试解析标准日期时间格式
    year, month, day, hour, min, sec = 
        time_str:match("(%d+)-(%d+)-(%d+) (%d+):(%d+):(%d+)")
    
    if year then
        local time_table = {
            year = tonumber(year),
            month = tonumber(month),
            day = tonumber(day),
            hour = tonumber(hour),
            min = tonumber(min),
            sec = tonumber(sec)
        }
        return os.time(time_table)
    end
    
    -- 尝试解析纯数字时间戳
    local timestamp = tonumber(time_str)
    if timestamp then
        return timestamp
    end
    
    return nil
end

return _M 