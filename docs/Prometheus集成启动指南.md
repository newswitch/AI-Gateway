# Prometheus集成启动指南

## 🚀 快速启动

### **1. 启动所有服务**
```bash
# 启动包含Prometheus的完整服务栈
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps
```

### **2. 验证服务状态**
```bash
# 检查Prometheus
curl http://localhost:9090/-/healthy

# 检查Grafana
curl http://localhost:3001/api/health

# 检查配置中心指标
curl http://localhost:8001/metrics
```

## 📊 服务端口映射

| 服务 | 端口 | 访问地址 | 说明 |
|------|------|----------|------|
| 前端 | 3000 | http://localhost:3000 | React前端界面 |
| 配置中心 | 8001 | http://localhost:8001 | FastAPI后端服务 |
| Token服务 | 8002 | http://localhost:8002 | Token计算服务 |
| 网关 | 8080 | http://localhost:8080 | OpenResty网关 |
| Prometheus | 9090 | http://localhost:9090 | 时间序列数据库 |
| Grafana | 3001 | http://localhost:3001 | 监控可视化面板 |
| MySQL | 3307 | localhost:3307 | 数据库 |
| Redis | 6379 | localhost:6379 | 缓存 |

## 🔧 配置说明

### **Prometheus配置**
- **配置文件**：`monitoring/prometheus.yml`
- **数据保留**：30天
- **采集间隔**：10-15秒
- **存储路径**：`prometheus_data_dev` 数据卷

### **Grafana配置**
- **默认用户**：admin
- **默认密码**：admin123
- **数据源**：自动配置Prometheus
- **仪表盘**：AI Gateway Overview

### **指标收集**
- **中间件**：自动收集HTTP请求指标
- **端点**：`/metrics` 暴露Prometheus格式指标
- **标签**：method, endpoint, status_code, namespace, upstream

## 📈 监控指标

### **HTTP请求指标**
```prometheus
# 请求总数
http_requests_total{method="GET", endpoint="/api/namespaces", status_code="200", namespace="wechat", upstream="openai"}

# 请求持续时间
http_request_duration_seconds{method="GET", endpoint="/api/namespaces", namespace="wechat", upstream="openai"}
```

### **业务指标**
```prometheus
# 命名空间请求
namespace_requests_total{namespace="wechat", status="success"}

# 命名空间Token使用
namespace_tokens_total{namespace="wechat", token_type="input"}
namespace_tokens_total{namespace="wechat", token_type="output"}

# 上游服务器请求
upstream_requests_total{upstream="openai", status="success"}
```

### **系统指标**
```prometheus
# 活跃连接数
active_connections{namespace="wechat"}

# 错误率
errors_total{error_type="client_error", namespace="wechat", upstream="openai"}
```

## 🔍 查询示例

### **PromQL查询**
```promql
# 获取最近5分钟的请求率
rate(http_requests_total[5m])

# 获取命名空间请求分布
sum by (namespace) (namespace_requests_total)

# 获取95分位响应时间
histogram_quantile(0.95, http_request_duration_seconds)

# 获取错误率
sum(rate(errors_total[5m])) by (namespace)
```

### **API查询**
```bash
# 获取命名空间状态分布
curl "http://localhost:8001/api/metrics/namespaces/status-distribution"

# 获取请求趋势
curl "http://localhost:8001/api/metrics/namespaces/request-trend?namespace=wechat&timeRange=today"

# 获取Token使用情况
curl "http://localhost:8001/api/metrics/namespaces/1/tokens?timeRange=today"

# 获取系统指标
curl "http://localhost:8001/api/metrics/system"
```

## 🎯 使用Grafana

### **访问Grafana**
1. 打开浏览器访问：http://localhost:3001
2. 使用用户名：admin，密码：admin123登录
3. 查看预配置的"AI Gateway Overview"仪表盘

### **仪表盘功能**
- **总请求数**：实时显示系统总请求数
- **成功率**：显示请求成功率百分比
- **平均响应时间**：显示平均响应时间
- **QPS**：显示每秒查询数
- **命名空间请求趋势**：按命名空间显示请求趋势
- **Token使用情况**：显示输入/输出Token使用量

## ⚠️ 注意事项

### **数据迁移**
1. **MySQL数据保留**：配置数据继续存储在MySQL
2. **指标数据迁移**：监控数据迁移到Prometheus
3. **缓存数据**：实时数据继续使用Redis缓存

### **性能优化**
1. **指标标签**：避免高基数标签影响性能
2. **采集间隔**：根据业务需求调整采集频率
3. **存储空间**：监控Prometheus存储使用情况

### **故障排查**
1. **服务健康检查**：所有服务都有健康检查端点
2. **日志查看**：使用 `docker-compose logs <service_name>` 查看日志
3. **指标验证**：访问 `/metrics` 端点验证指标收集

## 🔄 停止服务

```bash
# 停止所有服务
docker-compose -f docker-compose.dev.yml down

# 停止并删除数据卷（谨慎使用）
docker-compose -f docker-compose.dev.yml down -v
```

## 📚 相关文档

- [Prometheus官方文档](https://prometheus.io/docs/)
- [Grafana官方文档](https://grafana.com/docs/)
- [PromQL查询语言](https://prometheus.io/docs/prometheus/latest/querying/basics/)
