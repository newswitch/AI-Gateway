#!/bin/bash

# AI Gateway Kubernetes 卸载脚本

set -e

echo "🗑️ 开始卸载 AI Gateway..."

# 检查 kubectl 是否可用
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl 未安装或不在 PATH 中"
    exit 1
fi

# 删除 HPA
echo "📉 删除 HPA..."
kubectl delete -f 09-hpa.yaml --ignore-not-found=true

# 删除 Ingress
echo "🌍 删除 Ingress..."
kubectl delete -f 08-ingress.yaml --ignore-not-found=true

# 删除应用服务
echo "🚪 删除 Gateway 服务..."
kubectl delete -f 07-gateway.yaml --ignore-not-found=true

echo "🌐 删除前端服务..."
kubectl delete -f 06-frontend.yaml --ignore-not-found=true

echo "⚙️ 删除配置中心..."
kubectl delete -f 05-config-center.yaml --ignore-not-found=true

echo "🔧 删除 Token 服务..."
kubectl delete -f 04-token-service.yaml --ignore-not-found=true

# 删除数据库服务
echo "🔴 删除 Redis..."
kubectl delete -f 03-redis.yaml --ignore-not-found=true

echo "🗄️ 删除 MySQL..."
kubectl delete -f 02-mysql.yaml --ignore-not-found=true

# 删除配置和密钥
echo "🔧 删除配置和密钥..."
kubectl delete -f 01-config.yaml --ignore-not-found=true

# 删除命名空间
echo "📦 删除命名空间..."
kubectl delete -f 00-namespace.yaml --ignore-not-found=true

echo "✅ 卸载完成！"

# 清理持久化存储（可选）
read -p "是否删除持久化存储？这将删除所有数据！(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️ 删除持久化存储..."
    kubectl delete pvc --all -n ai-gateway --ignore-not-found=true
    kubectl delete pvc --all -n ai-gateway-monitoring --ignore-not-found=true
    echo "✅ 持久化存储已删除"
fi

echo "�� AI Gateway 已完全卸载！" 