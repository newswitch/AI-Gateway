"""
报文匹配器管理API
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager, ConfigCache
from app.schemas.matcher import MatcherCreate, MatcherUpdate, MatcherResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["报文匹配器管理"])

# 安全认证
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户（直接返回用户信息）"""
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

@router.get("/matchers", response_model=List[Dict[str, Any]])
async def get_all_matchers():
    """获取所有报文匹配器"""
    try:
        db = get_db()
        matchers = await db.get_all_matchers()
        return matchers
    except Exception as e:
        logger.error(f"获取所有报文匹配器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取所有报文匹配器失败: {str(e)}")

@router.get("/matchers/{matcher_id}", response_model=Dict[str, Any])
async def get_matcher(matcher_id: int):
    """获取单个报文匹配器"""
    try:
        db = get_db()
        matcher = await db.get_matcher_by_id(matcher_id)
        
        if not matcher:
            raise HTTPException(status_code=404, detail="报文匹配器不存在")
        
        return matcher
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报文匹配器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取报文匹配器失败: {str(e)}")

@router.get("/namespaces/{namespace_id}/matchers", response_model=List[Dict[str, Any]])
async def get_matchers(namespace_id: int):
    """获取命名空间下的所有匹配器"""
    try:
        cache = get_cache()
        matchers = await cache.get_matchers(namespace_id)
        return matchers
    except Exception as e:
        logger.error(f"获取命名空间匹配器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间匹配器失败: {str(e)}")

@router.post("/namespaces/{namespace_id}/matchers")
async def create_matcher(namespace_id: int, matcher_data: MatcherCreate, current_user: Dict = Depends(get_current_user)):
    """创建报文匹配器"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 添加命名空间ID
        matcher_dict = matcher_data.dict()
        matcher_dict['namespace_id'] = namespace_id
        
        # 创建报文匹配器
        matcher_id = await db.create_matcher(matcher_dict)
        
        # 更新缓存
        matchers = await db.get_matchers_by_namespace(namespace_id)
        await cache.set_matchers(namespace_id, matchers)
        
        logger.info(f"报文匹配器创建成功，matcher_id={matcher_id}, namespace_id={namespace_id}")
        return {"message": "报文匹配器创建成功", "matcher_id": matcher_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建报文匹配器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建报文匹配器失败: {str(e)}")

@router.put("/matchers/{matcher_id}")
async def update_matcher(matcher_id: int, matcher_data: MatcherUpdate, current_user: Dict = Depends(get_current_user)):
    """更新报文匹配器"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查报文匹配器是否存在
        existing = await db.get_matcher_by_id(matcher_id)
        if not existing:
            raise HTTPException(status_code=404, detail="报文匹配器不存在")
        
        # 更新报文匹配器
        success = await db.update_matcher(matcher_id, matcher_data.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=500, detail="更新报文匹配器失败")
        
        # 更新缓存
        namespace_id = existing['namespace_id']
        matchers = await db.get_matchers_by_namespace(namespace_id)
        await cache.set_matchers(namespace_id, matchers)
        
        logger.info(f"报文匹配器更新成功，matcher_id={matcher_id}")
        return {"message": "报文匹配器更新成功", "matcher_id": matcher_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新报文匹配器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新报文匹配器失败: {str(e)}")

@router.delete("/matchers/{matcher_id}")
async def delete_matcher(matcher_id: int, current_user: Dict = Depends(get_current_user)):
    """删除报文匹配器"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查报文匹配器是否存在
        existing = await db.get_matcher_by_id(matcher_id)
        if not existing:
            raise HTTPException(status_code=404, detail="报文匹配器不存在")
        
        # 删除报文匹配器
        success = await db.delete_matcher(matcher_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除报文匹配器失败")
        
        # 更新缓存
        namespace_id = existing['namespace_id']
        matchers = await db.get_matchers_by_namespace(namespace_id)
        await cache.set_matchers(namespace_id, matchers)
        
        logger.info(f"报文匹配器删除成功，matcher_id={matcher_id}")
        return {"message": "报文匹配器删除成功", "matcher_id": matcher_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除报文匹配器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除报文匹配器失败: {str(e)}") 