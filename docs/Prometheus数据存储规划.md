# Prometheus数据存储规划

## 📊 Prometheus特性

### **什么是Prometheus**
- **时间序列数据库(TSDB)**：专门存储带时间戳的数值数据
- **拉取模式**：主动从目标服务拉取指标数据
- **标签系统**：通过标签进行数据分类和查询
- **PromQL查询**：强大的时间序列查询语言

### **数据模型**
```prometheus
# 指标名称{标签1="值1", 标签2="值2"} 数值 时间戳
http_requests_total{method="GET", endpoint="/api/namespaces", namespace="wechat"} 150 1642234567
```

## 🎯 数据分类规划

### **1. 系统监控指标**
```prometheus
# 系统资源
node_cpu_usage_percent{instance="server1"} 75.5
node_memory_usage_bytes{instance="server1"} 8589934592
node_disk_usage_percent{instance="server1", device="/dev/sda1"} 45.2

# 网络指标
node_network_receive_bytes{instance="server1", device="eth0"} 1024000
node_network_transmit_bytes{instance="server1", device="eth0"} 2048000
```

### **2. 应用监控指标**
```prometheus
# HTTP请求指标
http_requests_total{method="GET", endpoint="/api/namespaces", status_code="200", namespace="wechat"}
http_request_duration_seconds{method="GET", endpoint="/api/namespaces", namespace="wechat"}

# 业务指标
namespace_requests_total{namespace="wechat", status="success"}
namespace_tokens_total{namespace="wechat", token_type="input"}
namespace_tokens_total{namespace="wechat", token_type="output"}

# 错误指标
errors_total{error_type="client_error", namespace="wechat", upstream="openai"}
```

### **3. 大模型指标**
```prometheus
# 模型调用指标
model_requests_total{model="gpt-4", namespace="wechat", status="success"}
model_tokens_input_total{model="gpt-4", namespace="wechat"}
model_tokens_output_total{model="gpt-4", namespace="wechat"}
model_request_duration_seconds{model="gpt-4", namespace="wechat"}

# 模型性能指标
model_throughput_tokens_per_second{model="gpt-4", namespace="wechat"}
model_cost_usd_total{model="gpt-4", namespace="wechat"}
model_accuracy_percent{model="gpt-4", task_type="classification"}
```

### **4. 网关指标**
```prometheus
# 网关请求指标
gateway_requests_total{method="POST", path="/v1/chat/completions", namespace="wechat"}
gateway_request_duration_seconds{method="POST", path="/v1/chat/completions", namespace="wechat"}

# 限流指标
rate_limit_hits_total{namespace="wechat", rule_type="token_limit"}
rate_limit_violations_total{namespace="wechat", rule_type="token_limit"}

# 缓存指标
cache_hits_total{cache_type="namespace_config"}
cache_misses_total{cache_type="namespace_config"}
```

## 🔧 数据收集方案

### **1. 从Lua脚本收集数据**

#### **方案A：HTTP推送**
```lua
-- 在Lua脚本中推送指标到Prometheus
local function push_metric(metric_name, value, labels)
    local http = require "resty.http"
    local httpc = http.new()
    
    local url = "http://prometheus:9090/api/v1/push"
    local body = string.format('%s{%s} %s', metric_name, labels, value)
    
    local res, err = httpc:request_uri(url, {
        method = "POST",
        body = body,
        headers = {
            ["Content-Type"] = "text/plain"
        }
    })
end

-- 使用示例
push_metric("gateway_requests_total", "1", 'method="POST",path="/v1/chat/completions",namespace="wechat"')
```

#### **方案B：通过配置中心代理**
```lua
-- Lua脚本发送数据到配置中心，由配置中心推送到Prometheus
local function send_metric_to_config_center(metric_data)
    local http = require "resty.http"
    local httpc = http.new()
    
    local url = "http://config-center:8000/api/metrics/push"
    local body = cjson.encode(metric_data)
    
    local res, err = httpc:request_uri(url, {
        method = "POST",
        body = body,
        headers = {
            ["Content-Type"] = "application/json"
        }
    })
end
```

### **2. 从大模型服务收集数据**

#### **在Token服务中添加指标收集**
```python
# 在token-service中添加Prometheus指标
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
model_requests_total = Counter('model_requests_total', 'Total model requests', ['model', 'namespace', 'status'])
model_tokens_input_total = Counter('model_tokens_input_total', 'Total input tokens', ['model', 'namespace'])
model_tokens_output_total = Counter('model_tokens_output_total', 'Total output tokens', ['model', 'namespace'])
model_request_duration_seconds = Histogram('model_request_duration_seconds', 'Model request duration', ['model', 'namespace'])

# 在API处理函数中记录指标
@app.post("/count_tokens")
async def count_tokens(request: TokenCountRequest):
    start_time = time.time()
    
    try:
        # 处理请求
        result = await process_tokens(request)
        
        # 记录成功指标
        model_requests_total.labels(
            model=request.model, 
            namespace=request.namespace, 
            status="success"
        ).inc()
        
        model_tokens_input_total.labels(
            model=request.model, 
            namespace=request.namespace
        ).inc(request.input_tokens)
        
        model_tokens_output_total.labels(
            model=request.model, 
            namespace=request.namespace
        ).inc(request.output_tokens)
        
    except Exception as e:
        # 记录错误指标
        model_requests_total.labels(
            model=request.model, 
            namespace=request.namespace, 
            status="error"
        ).inc()
        raise
    
    finally:
        # 记录响应时间
        duration = time.time() - start_time
        model_request_duration_seconds.labels(
            model=request.model, 
            namespace=request.namespace
        ).observe(duration)
    
    return result
```

## 📈 数据查询和展示

### **1. 在现有前端页面展示**

#### **总览页面**
```javascript
// 获取系统指标
const systemMetrics = await api.get('/api/metrics/system');

// 获取命名空间指标
const namespaceMetrics = await api.get('/api/metrics/namespaces/status-distribution');

// 获取请求趋势
const requestTrend = await api.get('/api/metrics/namespaces/request-trend?timeRange=today');
```

#### **命名空间管理页面**
```javascript
// 获取命名空间详细指标
const namespaceStats = await api.get(`/api/metrics/namespaces/${namespaceId}/stats`);

// 获取Token使用情况
const tokenUsage = await api.get(`/api/metrics/namespaces/${namespaceId}/tokens?timeRange=today`);
```

### **2. PromQL查询示例**

#### **系统指标查询**
```promql
# 获取CPU使用率
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 获取内存使用率
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# 获取磁盘使用率
(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100
```

#### **业务指标查询**
```promql
# 获取请求率
rate(http_requests_total[5m])

# 获取成功率
sum(rate(http_requests_total{status_code=~"2.."}[5m])) / sum(rate(http_requests_total[5m])) * 100

# 获取95分位响应时间
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### **大模型指标查询**
```promql
# 获取模型调用次数
sum(model_requests_total) by (model, namespace)

# 获取Token使用量
sum(model_tokens_input_total) by (model, namespace)
sum(model_tokens_output_total) by (model, namespace)

# 获取模型成本
sum(model_cost_usd_total) by (model, namespace)
```

## ⚠️ 注意事项

### **1. 标签设计原则**
- **避免高基数标签**：不要使用用户ID、请求ID等作为标签
- **标签值要稳定**：避免频繁变化的标签值
- **标签数量适中**：一般不超过10个标签

### **2. 数据保留策略**
- **开发环境**：30天
- **生产环境**：90天-1年
- **重要指标**：可以配置更长的保留时间

### **3. 性能优化**
- **采集间隔**：根据业务需求设置，一般15秒-1分钟
- **查询优化**：使用合适的查询范围和聚合函数
- **存储优化**：定期清理不需要的指标

## 🚀 实施步骤

### **阶段1：基础指标收集**
1. 配置Prometheus收集配置中心指标
2. 在现有API中添加指标收集
3. 验证指标数据正常收集

### **阶段2：Lua脚本集成**
1. 在Lua脚本中添加指标推送
2. 配置网关指标收集
3. 测试Lua到Prometheus的数据流

### **阶段3：大模型指标收集**
1. 在Token服务中添加指标收集
2. 配置大模型相关指标
3. 验证模型指标数据

### **阶段4：前端集成**
1. 修改现有API使用Prometheus数据
2. 更新前端页面显示实时指标
3. 添加图表和可视化组件
