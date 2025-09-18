"""
命名空间管理API适配层 - 适配新前端接口需求
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager, ConfigCache
from app.core.dependencies import get_db_manager, get_cache_manager
from app.schemas.namespace import NamespaceCreate, NamespaceUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["命名空间管理V2"])

# 安全认证
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户（简化版，直接返回用户信息）"""
    try:
        # 简化认证，实际项目中应该验证JWT token
        return {"user_id": "admin", "username": "admin"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_db() -> DatabaseManager:
    """获取数据库管理器"""
    return get_db_manager()

def get_cache() -> ConfigCache:
    """获取缓存管理器"""
    return get_cache_manager()

@router.get("/namespaces", response_model=Dict[str, Any])
async def get_namespaces(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    owner: Optional[str] = Query(None, description="所有者筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索")
):
    """
    获取命名空间列表 - 适配新前端接口格式
    支持分页、筛选和搜索
    """
    try:
        db = get_db()
        cache = get_cache()
        
        # 获取所有命名空间
        all_namespaces = await db.get_all_namespaces()
        
        # 应用筛选条件
        filtered_namespaces = []
        for ns in all_namespaces:
            # 状态筛选
            if status and status != "all":
                if status == "enabled" and ns.get('status') != 1:
                    continue
                elif status == "disabled" and ns.get('status') != 0:
                    continue
            
            # 关键词搜索
            if keyword:
                keyword_lower = keyword.lower()
                if not any(keyword_lower in str(ns.get(field, '')).lower() 
                          for field in ['namespace_code', 'namespace_name', 'description']):
                    continue
            
            # 获取匹配器信息
            matcher = None
            try:
                matchers = await db.get_matchers_by_namespace(ns.get('namespace_id'))
                if matchers and len(matchers) > 0:
                    matcher = matchers[0]  # 取第一个匹配器
            except Exception as e:
                logger.warning(f"获取命名空间 {ns.get('namespace_id')} 的匹配器失败: {str(e)}")
            
            # 转换为新前端期望的格式
            namespace_data = {
                "id": str(ns.get('namespace_id', '')),
                "code": ns.get('namespace_code', ''),
                "name": ns.get('namespace_name', ''),
                "owner": {
                    "name": "系统管理员",  # 暂时硬编码，后续可以从用户表获取
                    "avatar": "https://picsum.photos/id/1001/200/200"
                },
                "status": "enabled" if ns.get('status') == 1 else "disabled",
                "createdAt": ns.get('create_time', '')[:10] if ns.get('create_time') else '',
                "updatedAt": ns.get('update_time', '')[:10] if ns.get('update_time') else '',
                "matcher": matcher
            }
            
            filtered_namespaces.append(namespace_data)
        
        # 分页处理
        total = len(filtered_namespaces)
        start = (page - 1) * size
        end = start + size
        paginated_namespaces = filtered_namespaces[start:end]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": paginated_namespaces,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取命名空间列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间列表失败: {str(e)}")

@router.get("/namespaces/status-distribution")
async def get_namespace_status_distribution(
    timeRange: str = "all",
    db: DatabaseManager = Depends(get_db_manager)
):
    """获取命名空间状态分布数据 - 从Prometheus获取"""
    try:
        from app.services.prometheus_query import get_prometheus_query_service
        
        # 从Prometheus获取状态分布数据
        query_service = get_prometheus_query_service()
        data = query_service.get_namespace_status_distribution()
        
        return {
            "code": 200,
            "message": "success",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取命名空间状态分布失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间状态分布失败: {str(e)}")


@router.get("/namespaces/request-trend")
async def get_namespace_request_trend(
    timeRange: str = "today",
    db: DatabaseManager = Depends(get_db_manager)
):
    """获取命名空间请求趋势数据"""
    try:
        # 根据时间范围确定时间范围
        now = datetime.now()
        if timeRange == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now
            time_labels = ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
        elif timeRange == "week":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
            end_time = now
            time_labels = [f"{(start_time + timedelta(days=i)).strftime('%m-%d')}" for i in range(7)]
        else:  # month
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)
            end_time = now
            time_labels = [f"{(start_time + timedelta(days=i*5)).strftime('%m-%d')}" for i in range(6)]
        
        # 获取访问日志数据
        logs = await db.get_access_logs(
            filters={
                'start_time': start_time,
                'end_time': end_time
            },
            limit=10000  # 获取更多数据用于分析
        )
        
        # 获取所有命名空间
        namespaces = await db.get_all_namespaces()
        
        # 定义颜色数组
        colors = [
            {"border": "#165DFF", "background": "rgba(22, 93, 255, 0.1)"},
            {"border": "#722ED1", "background": "rgba(114, 46, 209, 0.1)"},
            {"border": "#00B42A", "background": "rgba(0, 180, 42, 0.1)"},
            {"border": "#F53F3F", "background": "rgba(245, 63, 63, 0.1)"},
            {"border": "#F7BA1E", "background": "rgba(247, 186, 30, 0.1)"},
            {"border": "#9FDB1D", "background": "rgba(159, 219, 29, 0.1)"},
            {"border": "#00D4AA", "background": "rgba(0, 212, 170, 0.1)"},
            {"border": "#1D2129", "background": "rgba(29, 33, 41, 0.1)"}
        ]
        
        # 基于真实访问日志数据生成趋势
        datasets = []
        
        # 按命名空间和时间段统计访问日志
        namespace_stats = {}
        for namespace in namespaces:
            namespace_id = namespace.get('namespace_id')
            namespace_stats[namespace_id] = {
                'name': namespace.get('namespace_name', f'命名空间{namespace_id}'),
                'data': [0] * len(time_labels)
            }
        
        # 统计每个时间段的访问量
        for log in logs:
            ns_id = log.get('namespace_id')
            if ns_id not in namespace_stats:
                continue
                
            # 根据时间范围计算时间段索引
            log_time = log.get('timestamp')
            if not log_time:
                continue
                
            try:
                if isinstance(log_time, str):
                    log_time = datetime.fromisoformat(log_time.replace('Z', '+00:00'))
                
                if timeRange == "today":
                    # 按3小时时间段统计
                    hour = log_time.hour
                    time_index = hour // 3
                    if time_index >= len(time_labels):
                        time_index = len(time_labels) - 1
                elif timeRange == "week":
                    # 按天统计
                    days_diff = (log_time.date() - start_time.date()).days
                    time_index = max(0, min(days_diff, len(time_labels) - 1))
                else:  # month
                    # 按5天统计
                    days_diff = (log_time.date() - start_time.date()).days
                    time_index = max(0, min(days_diff // 5, len(time_labels) - 1))
                
                namespace_stats[ns_id]['data'][time_index] += 1
            except Exception as e:
                logger.warning(f"解析日志时间失败: {e}")
                continue
        
        # 如果没有真实日志数据，使用基于命名空间特征的模拟数据
        has_real_data = any(sum(stats['data']) > 0 for stats in namespace_stats.values())
        
        for i, namespace in enumerate(namespaces):
            namespace_id = namespace.get('namespace_id')
            color = colors[i % len(colors)]
            
            if has_real_data:
                # 使用真实统计数据
                trend_data = namespace_stats[namespace_id]['data']
            else:
                # 没有日志数据时，生成基于命名空间特征的模拟数据
                # 根据命名空间名称生成不同的基础模式
                ns_name = namespace.get('namespace_name', '').lower()
                if 'wechat' in ns_name or '微信' in ns_name:
                    # 微信渠道：工作时间高峰
                    if timeRange == "today":
                        trend_data = [50, 20, 10, 80, 200, 350, 280, 120]
                    elif timeRange == "week":
                        trend_data = [1200, 1400, 1600, 1500, 1800, 2200, 2000]
                    else:
                        trend_data = [5000, 5500, 6000, 6500, 7000, 6800]
                elif 'alipay' in ns_name or '支付宝' in ns_name:
                    # 支付宝渠道：购物时间高峰
                    if timeRange == "today":
                        trend_data = [30, 15, 5, 60, 180, 320, 250, 100]
                    elif timeRange == "week":
                        trend_data = [1000, 1200, 1400, 1300, 1600, 2000, 1800]
                    else:
                        trend_data = [4500, 5000, 5500, 6000, 6500, 6200]
                else:
                    # Web渠道：全天均匀分布
                    if timeRange == "today":
                        trend_data = [40, 25, 15, 70, 190, 330, 260, 110]
                    elif timeRange == "week":
                        trend_data = [1100, 1300, 1500, 1400, 1700, 2100, 1900]
                    else:
                        trend_data = [4800, 5300, 5800, 6300, 6800, 6500]
            
            datasets.append({
                "label": namespace.get('namespace_name', f'命名空间{i+1}'),
                "data": trend_data,
                "borderColor": color["border"],
                "backgroundColor": color["background"],
                "fill": True,
                "tension": 0.4,
                "pointRadius": 4,
                "pointHoverRadius": 6
            })
        
        # 构建返回数据
        data = {
            "labels": time_labels,
            "datasets": datasets
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取命名空间请求趋势失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间请求趋势失败: {str(e)}")


@router.get("/namespaces/{namespace_id}", response_model=Dict[str, Any])
async def get_namespace(namespace_id: int):
    """获取单个命名空间详情"""
    try:
        cache = get_cache()
        namespace = await cache.get_namespace(namespace_id)
        
        if not namespace:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        # 转换为新前端期望的格式
        namespace_data = {
            "id": str(namespace.get('namespace_id', '')),
            "code": namespace.get('namespace_code', ''),
            "name": namespace.get('namespace_name', ''),
            "owner": {
                "name": "系统管理员",
                "avatar": "https://picsum.photos/id/1001/200/200"
            },
            "status": "enabled" if namespace.get('status') == 1 else "disabled",
            "createdAt": namespace.get('create_time', '')[:10] if namespace.get('create_time') else '',
            "updatedAt": namespace.get('update_time', '')[:10] if namespace.get('update_time') else ''
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": namespace_data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间失败: {str(e)}")

@router.post("/namespaces", response_model=Dict[str, Any])
async def create_namespace(namespace_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """创建命名空间 - 适配新前端数据格式"""
    try:
        cache = get_cache()
        
        # 转换新前端数据格式到后端格式
        create_data = {
            "namespace_code": namespace_data.get("code", ""),
            "namespace_name": namespace_data.get("name", ""),
            "description": namespace_data.get("description", ""),
            "status": 1 if namespace_data.get("status") == "enabled" else 0,
            "matcher_config": {
                "matcher_type": namespace_data.get("matcherType", "header"),
                "match_field": namespace_data.get("matchField", "channelcode"),
                "match_operator": namespace_data.get("matchOperator", "equals"),
                "match_value": namespace_data.get("matchValue", namespace_data.get("code", "")),
                "priority": namespace_data.get("priority", 100)
            }
        }
        
        # 使用双写策略创建命名空间
        namespace_id = await cache.create_namespace_dual_write(create_data)
        
        # 获取创建的命名空间
        namespace = await cache.get_namespace(namespace_id)
        
        logger.info(f"命名空间创建成功，namespace_id={namespace_id}")
        return {
            "code": 200,
            "message": "命名空间创建成功",
            "data": {
                "namespace_id": namespace_id,
                "namespace": namespace
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"创建命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建命名空间失败: {str(e)}")

@router.put("/namespaces/{namespace_id}", response_model=Dict[str, Any])
async def update_namespace(namespace_id: int, namespace_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """更新命名空间 - 适配新前端数据格式"""
    try:
        cache = get_cache()
        
        # 检查命名空间是否存在
        existing = await cache.get_namespace(namespace_id)
        if not existing:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        # 转换新前端数据格式到后端格式
        update_data = {}
        if "code" in namespace_data:
            update_data["namespace_code"] = namespace_data["code"]
        if "name" in namespace_data:
            update_data["namespace_name"] = namespace_data["name"]
        if "description" in namespace_data:
            update_data["description"] = namespace_data["description"]
        if "status" in namespace_data:
            update_data["status"] = 1 if namespace_data["status"] == "enabled" else 0
        
        # 使用双写策略更新命名空间
        success = await cache.update_namespace_dual_write(namespace_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="更新命名空间失败")
        
        # 更新匹配器配置
        if any(key in namespace_data for key in ["matcherType", "matchField", "matchOperator", "matchValue", "priority"]):
            await _update_namespace_matcher(namespace_id, namespace_data)
        
        # 获取更新后的命名空间
        updated_namespace = await cache.get_namespace(namespace_id)
        
        logger.info(f"命名空间更新成功，namespace_id={namespace_id}")
        return {
            "code": 200,
            "message": "命名空间更新成功",
            "data": {
                "namespace_id": namespace_id,
                "namespace": updated_namespace
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新命名空间失败: {str(e)}")

@router.delete("/namespaces/{namespace_id}", response_model=Dict[str, Any])
async def delete_namespace(namespace_id: int, current_user: Dict = Depends(get_current_user)):
    """删除命名空间"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查命名空间是否存在
        namespace = await db.get_namespace(namespace_id)
        if not namespace:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        # 删除命名空间
        await db.delete_namespace(namespace_id)
        
        # 清除缓存
        await cache.delete_namespace(namespace_id)
        
        logger.info(f"命名空间删除成功，namespace_id={namespace_id}")
        return {
            "code": 200,
            "message": "命名空间删除成功",
            "data": {
                "namespace_id": namespace_id
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除命名空间失败: {str(e)}")

@router.put("/namespaces/{namespace_id}/status", response_model=Dict[str, Any])
async def update_namespace_status(namespace_id: int, status_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """启用/禁用命名空间"""
    try:
        cache = get_cache()
        
        # 检查命名空间是否存在
        existing = await cache.get_namespace(namespace_id)
        if not existing:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        # 更新状态
        status_value = 1 if status_data.get("status") == "enabled" else 0
        success = await cache.update_namespace_dual_write(namespace_id, {"status": status_value})
        
        if not success:
            raise HTTPException(status_code=500, detail="更新命名空间状态失败")
        
        logger.info(f"命名空间状态更新成功，namespace_id={namespace_id}, status={status_value}")
        return {
            "code": 200,
            "message": "命名空间状态更新成功",
            "data": {
                "namespace_id": namespace_id,
                "status": status_data.get("status")
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新命名空间状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新命名空间状态失败: {str(e)}")

async def _update_namespace_matcher(namespace_id: int, namespace_data: Dict[str, Any]):
    """更新命名空间的匹配器配置"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 获取现有匹配器
        existing_matchers = await db.get_matchers_by_namespace(namespace_id)
        
        if existing_matchers and len(existing_matchers) > 0:
            # 更新现有匹配器
            matcher_id = existing_matchers[0]['matcher_id']
            matcher_data = {
                'matcher_type': namespace_data.get('matcherType', 'header'),
                'match_field': namespace_data.get('matchField', 'channelcode'),
                'match_operator': namespace_data.get('matchOperator', 'equals'),
                'match_value': namespace_data.get('matchValue', ''),
                'priority': namespace_data.get('priority', 100)
            }
            
            await db.update_matcher(matcher_id, matcher_data)
        else:
            # 创建新匹配器
            matcher_data = {
                'namespace_id': namespace_id,
                'matcher_name': f'{namespace_data.get("name", "命名空间")}渠道匹配',
                'matcher_type': namespace_data.get('matcherType', 'header'),
                'match_field': namespace_data.get('matchField', 'channelcode'),
                'match_operator': namespace_data.get('matchOperator', 'equals'),
                'match_value': namespace_data.get('matchValue', ''),
                'priority': namespace_data.get('priority', 100),
                'status': 1
            }
            
            await db.create_matcher(matcher_data)
        
        # 更新缓存
        matchers = await db.get_matchers_by_namespace(namespace_id)
        await cache.set_matchers(namespace_id, matchers)
        
        logger.info(f"命名空间 {namespace_id} 的匹配器更新成功")
        
    except Exception as e:
        logger.error(f"更新命名空间 {namespace_id} 的匹配器失败: {str(e)}")
        # 不抛出异常，避免影响命名空间更新

@router.get("/namespaces/{namespace_id}/stats", response_model=Dict[str, Any])
async def get_namespace_stats(namespace_id: int):
    """获取命名空间统计信息"""
    try:
        cache = get_cache()
        
        # 检查命名空间是否存在
        namespace = await cache.get_namespace(namespace_id)
        if not namespace:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        # 暂时返回模拟统计数据，后续可以从统计表获取
        stats_data = {
            "namespace_id": namespace_id,
            "requestCount": 5824,
            "successRate": "99.2%",
            "avgResponseTime": "1.2s",
            "inputTokens": 426835,
            "outputTokens": 241652,
            "avgInputTokensPerReq": 73.3,
            "avgOutputTokensPerReq": 41.5,
            "lastActive": "1分钟前"
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": stats_data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取命名空间统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间统计失败: {str(e)}")

