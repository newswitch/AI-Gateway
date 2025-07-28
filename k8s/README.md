# AI Gateway Kubernetes 部署指南

## 📋 概述

本目录包含了将 AI Gateway 部署到 Kubernetes 集群的完整配置文件。

## 🏗️ 架构组件

### 核心服务
- **MySQL**: 主数据库，存储配置和规则数据
- **Redis**: 缓存和会话存储
- **Token Service**: Token计算服务
- **Config Center**: 配置中心服务
- **Frontend**: 前端管理界面
- **Gateway**: 智能网关服务

### 扩展功能
- **Ingress**: 外部访问入口
- **HPA**: 水平Pod自动扩缩容
- **ConfigMap/Secret**: 配置管理

## 📁 文件结构

```
k8s/
├── 00-namespace.yaml          # 命名空间定义
├── 01-config.yaml            # ConfigMap和Secret
├── 02-mysql.yaml             # MySQL部署
├── 03-redis.yaml             # Redis部署
├── 04-token-service.yaml     # Token服务部署
├── 05-config-center.yaml     # 配置中心部署
├── 06-frontend.yaml          # 前端服务部署
├── 07-gateway.yaml           # Gateway服务部署
├── 08-ingress.yaml           # Ingress配置
├── 09-hpa.yaml              # HPA配置
├── deploy.sh                 # 部署脚本
├── undeploy.sh               # 卸载脚本
└── README.md                 # 说明文档
```

## 🚀 快速部署

### 前置要求

1. **Kubernetes 集群**
   - 版本: 1.20+
   - 支持 Ingress Controller
   - 支持 HPA

2. **镜像准备**
   ```bash
   # 构建镜像
   docker build -t ai-gateway-token-service:latest ./services/token-count
   docker build -t ai-gateway-config-center:latest ./config-center
   docker build -t ai-gateway-frontend:latest ./frontend
   docker build -t ai-gateway-nginx:latest ./gateway
   
   # 推送到镜像仓库（可选）
   docker tag ai-gateway-token-service:latest your-registry/ai-gateway-token-service:latest
   docker push your-registry/ai-gateway-token-service:latest
   ```

3. **存储类**
   ```bash
   # 检查可用的存储类
   kubectl get storageclass
   ```

### 部署步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd AI-Gateway-2.0/k8s
   ```

2. **修改配置**
   - 根据需要修改 `01-config.yaml` 中的配置
   - 调整资源限制和副本数
   - 配置域名和TLS证书

3. **执行部署**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

4. **验证部署**
   ```bash
   kubectl get pods -n ai-gateway
   kubectl get svc -n ai-gateway
   kubectl get ingress -n ai-gateway
   ```

## 🌐 访问地址

部署完成后，可以通过以下地址访问：

- **前端界面**: http://ai-gateway.local
- **API 接口**: http://api.ai-gateway.local

## ⚙️ 配置说明

### Token计算服务配置

项目支持精确的token计算功能，相关配置如下：

- `TOKEN_SERVICE_URL`: Token计算服务地址（默认：http://ai-gateway-token-service:8000）
- `USE_PRECISE_TOKEN_CALCULATION`: 是否启用精确token计算（默认：true）
- `TOKEN_CALCULATION_TIMEOUT`: Token计算超时时间，单位毫秒（默认：3000）
- `TOKEN_CACHE_TTL`: Token缓存时间，单位秒（默认：300）

### 配置示例

```yaml
# 在 01-config.yaml 中配置
data:
  TOKEN_SERVICE_URL: "http://ai-gateway-token-service:8000"
  USE_PRECISE_TOKEN_CALCULATION: "true"
  TOKEN_CALCULATION_TIMEOUT: "3000"
  TOKEN_CACHE_TTL: "300"
```

### 功能特性

1. **精确Token计算**: 使用专业的token计算服务，支持多种大模型
2. **智能缓存**: 避免重复计算相同文本的token数量
3. **降级机制**: 当token服务不可用时，自动降级到简单估算
4. **可配置性**: 支持通过环境变量动态配置
- **Gateway**: http://gateway.ai-gateway.local

### 本地测试

在 `/etc/hosts` 中添加：
```
127.0.0.1 ai-gateway.local
127.0.0.1 api.ai-gateway.local
127.0.0.1 gateway.ai-gateway.local
```

## ⚙️ 配置说明

### 资源配置

| 服务 | CPU请求 | CPU限制 | 内存请求 | 内存限制 | 副本数 |
|------|---------|---------|----------|----------|--------|
| MySQL | 250m | 500m | 512Mi | 1Gi | 1 |
| Redis | 100m | 200m | 256Mi | 512Mi | 1 |
| Token Service | 500m | 1000m | 1Gi | 2Gi | 2 |
| Config Center | 250m | 500m | 512Mi | 1Gi | 2 |
| Frontend | 100m | 200m | 128Mi | 256Mi | 2 |
| Gateway | 250m | 500m | 512Mi | 1Gi | 3 |

### HPA 配置

| 服务 | 最小副本 | 最大副本 | CPU阈值 | 内存阈值 |
|------|----------|----------|---------|----------|
| Config Center | 2 | 10 | 70% | 80% |
| Token Service | 2 | 10 | 70% | 80% |
| Gateway | 3 | 20 | 70% | 80% |

## 🔧 自定义配置

### 修改镜像仓库

如果使用私有镜像仓库，修改部署文件中的镜像地址：

```yaml
image: your-registry/ai-gateway-token-service:latest
imagePullPolicy: Always
imagePullSecrets:
- name: your-registry-secret
```

### 配置持久化存储

修改 PVC 的存储类：

```yaml
storageClassName: your-storage-class
```

### 启用 HTTPS

1. 安装 cert-manager
2. 取消注释 `08-ingress.yaml` 中的 TLS 配置
3. 配置证书颁发者

## 📊 监控和日志

### 查看日志
```bash
# 查看特定服务的日志
kubectl logs -f deployment/ai-gateway-config-center -n ai-gateway

# 查看所有Pod的日志
kubectl logs -f -l app=ai-gateway-config-center -n ai-gateway
```

### 查看资源使用
```bash
# 查看Pod资源使用
kubectl top pods -n ai-gateway

# 查看HPA状态
kubectl get hpa -n ai-gateway
```

### 端口转发（调试用）
```bash
# 转发前端服务
kubectl port-forward svc/ai-gateway-frontend 8080:80 -n ai-gateway

# 转发API服务
kubectl port-forward svc/ai-gateway-config-center 8001:8000 -n ai-gateway
```

## 🗑️ 卸载

```bash
chmod +x undeploy.sh
./undeploy.sh
```

## 🔍 故障排除

### 常见问题

1. **Pod 启动失败**
   ```bash
   kubectl describe pod <pod-name> -n ai-gateway
   kubectl logs <pod-name> -n ai-gateway
   ```

2. **服务无法访问**
   ```bash
   kubectl get endpoints -n ai-gateway
   kubectl describe svc <service-name> -n ai-gateway
   ```

3. **Ingress 不工作**
   ```bash
   kubectl get ingress -n ai-gateway
   kubectl describe ingress ai-gateway-ingress -n ai-gateway
   ```

4. **存储问题**
   ```bash
   kubectl get pvc -n ai-gateway
   kubectl describe pvc <pvc-name> -n ai-gateway
   ```

### 性能调优

1. **调整资源限制**
   - 根据实际负载调整 CPU 和内存限制
   - 监控资源使用情况

2. **优化副本数**
   - 根据流量调整 HPA 配置
   - 设置合适的扩缩容阈值

3. **缓存优化**
   - 调整 Redis 内存配置
   - 优化缓存策略

## 📞 支持

如遇到问题，请检查：
1. Kubernetes 集群状态
2. 镜像是否正确构建
3. 配置文件是否正确
4. 网络和存储配置

## �� 许可证

MIT License 