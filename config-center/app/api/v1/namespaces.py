"""
命名空间管理API
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager, ConfigCache
from app.schemas.namespace import NamespaceCreate, NamespaceUpdate, NamespaceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["命名空间管理"])

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
    from app.core.dependencies import get_db_manager
    return get_db_manager()

def get_cache() -> ConfigCache:
    """获取缓存管理器"""
    from app.core.dependencies import get_cache_manager
    return get_cache_manager()

@router.get("/namespaces", response_model=List[Dict[str, Any]])
async def get_namespaces():
    """获取所有命名空间"""
    try:
        db = get_db()
        namespaces = await db.get_all_namespaces()
        return namespaces
    except Exception as e:
        logger.error(f"获取命名空间列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间列表失败: {str(e)}")

@router.get("/namespaces/{namespace_id}", response_model=Dict[str, Any])
async def get_namespace(namespace_id: int):
    """获取单个命名空间"""
    try:
        cache = get_cache()
        namespace = await cache.get_namespace(namespace_id)
        
        if not namespace:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        return namespace
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间失败: {str(e)}")

@router.post("/namespaces")
async def create_namespace(namespace_data: NamespaceCreate, current_user: Dict = Depends(get_current_user)):
    """创建命名空间 - 双写策略"""
    try:
        cache = get_cache()
        
        # 使用双写策略创建命名空间
        namespace_id = await cache.create_namespace_dual_write(namespace_data.dict())
        
        # 获取创建的命名空间
        namespace = await cache.get_namespace(namespace_id)
        
        logger.info(f"命名空间创建成功，namespace_id={namespace_id}")
        return {"message": "命名空间创建成功", "namespace_id": namespace_id, "namespace": namespace}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建命名空间失败: {str(e)}")

@router.put("/namespaces/{namespace_id}")
async def update_namespace(namespace_id: int, namespace_data: NamespaceUpdate, current_user: Dict = Depends(get_current_user)):
    """更新命名空间 - 双写策略"""
    try:
        cache = get_cache()
        
        # 检查命名空间是否存在
        existing = await cache.get_namespace(namespace_id)
        if not existing:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        # 使用双写策略更新命名空间
        success = await cache.update_namespace_dual_write(namespace_id, namespace_data.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=500, detail="更新命名空间失败")
        
        # 获取更新后的命名空间
        updated_namespace = await cache.get_namespace(namespace_id)
        
        logger.info(f"命名空间更新成功，namespace_id={namespace_id}")
        return {"message": "命名空间更新成功", "namespace_id": namespace_id, "namespace": updated_namespace}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新命名空间失败: {str(e)}")

@router.delete("/namespaces/{namespace_id}")
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
        return {"message": "命名空间删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除命名空间失败: {str(e)}")

# 命名空间路由管理API
@router.get("/namespaces/{namespace_id}/route")
async def get_namespace_route(namespace_id: int):
    """获取命名空间的路由规则"""
    try:
        db = get_db()
        route = await db.get_namespace_route(namespace_id)
        
        if not route:
            raise HTTPException(status_code=404, detail="命名空间路由规则不存在")
        
        return route
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取命名空间路由规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间路由规则失败: {str(e)}")

@router.post("/namespaces/{namespace_id}/route")
async def create_or_update_namespace_route(namespace_id: int, route_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """创建或更新命名空间路由规则"""
    try:
        db = get_db()
        
        # 检查命名空间是否存在
        namespace = await db.get_namespace(namespace_id)
        if not namespace:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        # 添加命名空间ID到路由数据
        route_data['namespace_id'] = namespace_id
        
        # 创建或更新路由规则
        route_id = await db.create_or_update_namespace_route(route_data)
        
        # 获取创建的路由规则
        route = await db.get_namespace_route(namespace_id)
        
        logger.info(f"命名空间路由规则保存成功，namespace_id={namespace_id}, route_id={route_id}")
        return {"message": "命名空间路由规则保存成功", "route_id": route_id, "route": route}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存命名空间路由规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存命名空间路由规则失败: {str(e)}")

@router.delete("/namespaces/{namespace_id}/route")
async def delete_namespace_route(namespace_id: int, current_user: Dict = Depends(get_current_user)):
    """删除命名空间路由规则"""
    try:
        db = get_db()
        
        # 检查命名空间是否存在
        namespace = await db.get_namespace(namespace_id)
        if not namespace:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        # 删除路由规则
        await db.delete_namespace_route(namespace_id)
        
        logger.info(f"命名空间路由规则删除成功，namespace_id={namespace_id}")
        return {"message": "命名空间路由规则删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除命名空间路由规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除命名空间路由规则失败: {str(e)}")

@router.post("/namespaces/{namespace_id}/validate")
async def validate_namespace_rules(namespace_id: int, request_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """验证命名空间规则"""
    try:
        db = get_db()
        
        # 检查命名空间是否存在
        namespace = await db.get_namespace(namespace_id)
        if not namespace:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        # 获取命名空间的所有规则
        rules = await db.get_rules_by_namespace(namespace_id)
        
        # 验证规则（这里简化处理，实际应该根据规则类型进行验证）
        validation_results = []
        allowed = True
        
        for rule in rules:
            if rule.get('status') == 1:  # 只验证启用的规则
                # 这里应该根据规则类型进行具体的验证逻辑
                # 暂时返回通过
                validation_results.append({
                    "rule_id": rule['rule_id'],
                    "rule_name": rule['rule_name'],
                    "rule_type": rule['rule_type'],
                    "passed": True,
                    "details": {"message": "规则验证通过"}
                })
        
        return {
            "allowed": allowed,
            "namespace_id": namespace_id,
            "namespace_code": namespace['namespace_code'],
            "namespace_name": namespace['namespace_name'],
            "rules": validation_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证命名空间规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证命名空间规则失败: {str(e)}")
    """删除命名空间"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查命名空间是否存在
        existing = await db.get_namespace(namespace_id)
        if not existing:
            raise HTTPException(status_code=404, detail="命名空间不存在")
        
        # 删除命名空间
        success = await db.delete_namespace(namespace_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除命名空间失败")
        
        # 清除缓存
        cache_key = cache._get_cache_key("namespace", str(namespace_id))
        await cache.redis_client.delete(cache_key)
        
        logger.info(f"命名空间删除成功，namespace_id={namespace_id}")
        return {"message": "命名空间删除成功", "namespace_id": namespace_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除命名空间失败: {str(e)}") 