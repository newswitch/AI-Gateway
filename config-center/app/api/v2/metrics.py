"""
Prometheus指标查询API
用于替代MySQL中的监控数据查询
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.prometheus_query import get_prometheus_query_service, PrometheusQueryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Prometheus指标查询"])

# 安全认证
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户（简化版，直接返回用户信息）"""
    try:
        return {"user_id": "admin", "username": "admin"}
    except Exception as e:
        raise HTTPException(status_code=401, detail="认证失败")

@router.get("/metrics/namespaces/status-distribution")
async def get_namespace_status_distribution(
    query_service: PrometheusQueryService = Depends(get_prometheus_query_service)
):
    """获取命名空间状态分布 - 从Prometheus获取"""
    try:
        data = query_service.get_namespace_status_distribution()
        
        return {
            "code": 200,
            "message": "success",
            "data": data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取命名空间状态分布失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间状态分布失败: {str(e)}")

@router.get("/metrics/namespaces/request-trend")
async def get_namespace_request_trend(
    namespace: str = Query("all", description="命名空间"),
    timeRange: str = Query("today", description="时间范围"),
    query_service: PrometheusQueryService = Depends(get_prometheus_query_service)
):
    """获取命名空间请求趋势 - 从Prometheus获取"""
    try:
        data = query_service.get_namespace_request_trend(namespace, timeRange)
        
        return {
            "code": 200,
            "message": "success",
            "data": data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取命名空间请求趋势失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间请求趋势失败: {str(e)}")

@router.get("/metrics/namespaces/{namespace_id}/tokens")
async def get_namespace_token_usage(
    namespace_id: int,
    timeRange: str = Query("today", description="时间范围"),
    query_service: PrometheusQueryService = Depends(get_prometheus_query_service)
):
    """获取命名空间Token使用情况 - 从Prometheus获取"""
    try:
        # 这里需要根据namespace_id获取namespace名称
        # 暂时使用默认值，实际应该从数据库查询
        namespace = f"namespace_{namespace_id}"
        
        data = query_service.get_namespace_token_usage(namespace, timeRange)
        
        return {
            "code": 200,
            "message": "success",
            "data": data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取命名空间Token使用情况失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间Token使用情况失败: {str(e)}")

@router.get("/metrics/namespaces/{namespace_id}/stats")
async def get_namespace_metrics(
    namespace_id: int,
    query_service: PrometheusQueryService = Depends(get_prometheus_query_service)
):
    """获取命名空间详细指标 - 从Prometheus获取"""
    try:
        # 这里需要根据namespace_id获取namespace名称
        # 暂时使用默认值，实际应该从数据库查询
        namespace = f"namespace_{namespace_id}"
        
        data = query_service.get_namespace_metrics(namespace)
        
        return {
            "code": 200,
            "message": "success",
            "data": data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取命名空间指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间指标失败: {str(e)}")

@router.get("/metrics/system")
async def get_system_metrics(
    query_service: PrometheusQueryService = Depends(get_prometheus_query_service)
):
    """获取系统指标 - 从Prometheus获取"""
    try:
        data = query_service.get_system_metrics()
        
        return {
            "code": 200,
            "message": "success",
            "data": data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")

@router.get("/metrics/dashboard")
async def get_dashboard_metrics(
    query_service: PrometheusQueryService = Depends(get_prometheus_query_service)
):
    """获取仪表盘指标 - 从Prometheus获取"""
    try:
        # 获取系统指标
        system_metrics = query_service.get_system_metrics()
        
        # 获取命名空间状态分布
        status_distribution = query_service.get_namespace_status_distribution()
        
        # 获取请求趋势
        request_trend = query_service.get_namespace_request_trend("all", "today")
        
        data = {
            "system": system_metrics,
            "statusDistribution": status_distribution,
            "requestTrend": request_trend
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取仪表盘指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取仪表盘指标失败: {str(e)}")
