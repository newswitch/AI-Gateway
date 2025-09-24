#!/bin/bash

# AI Gateway Kubernetes 部署脚本

set -e

echo "🚀 开始部署 AI Gateway 到 Kubernetes..."

# 检查 kubectl 是否可用
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl 未安装或不在 PATH 中"
    exit 1
fi

# 检查集群连接
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ 无法连接到 Kubernetes 集群"
    exit 1
fi

echo "✅ Kubernetes 集群连接正常"

# 创建命名空间
echo "📦 创建命名空间..."
kubectl apply -f 00-namespace.yaml

# 创建配置和密钥
echo "🔧 创建配置和密钥..."
kubectl apply -f 01-config.yaml

# 部署数据库服务
echo "🗄️ 部署 MySQL..."
kubectl apply -f 02-mysql.yaml

echo "🔴 部署 Redis..."
kubectl apply -f 03-redis.yaml

# 等待数据库服务就绪
echo "⏳ 等待数据库服务就绪..."
kubectl wait --for=condition=ready pod -l app=ai-gateway-mysql -n ai-gateway --timeout=300s
kubectl wait --for=condition=ready pod -l app=ai-gateway-redis -n ai-gateway --timeout=300s

# 部署应用服务
echo "🔧 部署 Token 服务..."
kubectl apply -f 04-token-service.yaml

echo "⚙️ 部署配置中心..."
kubectl apply -f 05-config-center.yaml

echo "🌐 部署前端服务..."
kubectl apply -f 06-frontend.yaml

echo "🚪 部署 Gateway 服务..."
kubectl apply -f 07-gateway.yaml

# 等待应用服务就绪
echo "⏳ 等待应用服务就绪..."
kubectl wait --for=condition=ready pod -l app=ai-gateway-token-service -n ai-gateway --timeout=300s
kubectl wait --for=condition=ready pod -l app=ai-gateway-config-center -n ai-gateway --timeout=300s
kubectl wait --for=condition=ready pod -l app=ai-gateway-frontend -n ai-gateway --timeout=300s
kubectl wait --for=condition=ready pod -l app=ai-gateway-nginx -n ai-gateway --timeout=300s

# 部署 Ingress
echo "🌍 部署 Ingress..."
kubectl apply -f 08-ingress.yaml

# 部署 HPA
echo "📈 部署 HPA..."
kubectl apply -f 09-hpa.yaml

echo "✅ 部署完成！"

# 显示服务状态
echo "📊 服务状态："
kubectl get pods -n ai-gateway
echo ""
echo "🌐 服务端点："
kubectl get svc -n ai-gateway
echo ""
echo "🚪 Ingress 状态："
kubectl get ingress -n ai-gateway

echo ""
echo "🎉 AI Gateway 已成功部署到 Kubernetes！"
echo ""
echo "访问地址："
echo "  前端界面: http://ai-gateway.local"
echo "  API 接口: http://api.ai-gateway.local"
echo "  Gateway: http://gateway.ai-gateway.local"
echo ""
echo "注意：请确保在 /etc/hosts 中添加相应的域名映射" 