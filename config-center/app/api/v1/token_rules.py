"""
Token限制规则管理API
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager, ConfigCache
from app.schemas.token_rule import TokenRuleCreate, TokenRuleUpdate, TokenRuleResponse
from app.services.token_window_service import TokenWindowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Token限制规则管理"])

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

@router.get("/token-rules/{rule_id}", response_model=Dict[str, Any])
async def get_token_rule(rule_id: int):
    """获取单个Token限制规则"""
    try:
        db = get_db()
        rule = await db.get_token_rule_by_id(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail="Token限制规则不存在")
        
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Token限制规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取Token限制规则失败: {str(e)}")

@router.get("/namespaces/{namespace_id}/token-rules", response_model=List[Dict[str, Any]])
async def get_token_rules(namespace_id: int):
    """获取命名空间下的所有Token限制规则"""
    try:
        db = get_db()
        rules = await db.get_token_rules_by_namespace(namespace_id)
        return rules
    except Exception as e:
        logger.error(f"获取命名空间Token限制规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间Token限制规则失败: {str(e)}")

@router.post("/namespaces/{namespace_id}/token-rules")
async def create_token_rule(namespace_id: int, rule_data: TokenRuleCreate, current_user: Dict = Depends(get_current_user)):
    """创建Token限制规则"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 添加命名空间ID
        rule_dict = rule_data.dict()
        rule_dict['namespace_id'] = namespace_id
        
        # 创建Token限制规则
        rule_id = await db.create_token_rule(rule_dict)
        
        # 更新缓存
        rules = await db.get_token_rules_by_namespace(namespace_id)
        await cache.set_token_rules(namespace_id, rules)
        
        logger.info(f"Token限制规则创建成功，rule_id={rule_id}, namespace_id={namespace_id}")
        return {"message": "Token限制规则创建成功", "rule_id": rule_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建Token限制规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建Token限制规则失败: {str(e)}")

@router.put("/token-rules/{rule_id}")
async def update_token_rule(rule_id: int, rule_data: TokenRuleUpdate, current_user: Dict = Depends(get_current_user)):
    """更新Token限制规则"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查Token限制规则是否存在
        existing = await db.get_token_rule_by_id(rule_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Token限制规则不存在")
        
        # 更新Token限制规则
        success = await db.update_token_rule(rule_id, rule_data.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=500, detail="更新Token限制规则失败")
        
        # 更新缓存
        namespace_id = existing['namespace_id']
        rules = await db.get_token_rules_by_namespace(namespace_id)
        await cache.set_token_rules(namespace_id, rules)
        
        logger.info(f"Token限制规则更新成功，rule_id={rule_id}")
        return {"message": "Token限制规则更新成功", "rule_id": rule_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新Token限制规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新Token限制规则失败: {str(e)}")

@router.delete("/token-rules/{rule_id}")
async def delete_token_rule(rule_id: int, current_user: Dict = Depends(get_current_user)):
    """删除Token限制规则"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查Token限制规则是否存在
        existing = await db.get_token_rule_by_id(rule_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Token限制规则不存在")
        
        # 删除Token限制规则
        success = await db.delete_token_rule(rule_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除Token限制规则失败")
        
        # 更新缓存
        namespace_id = existing['namespace_id']
        rules = await db.get_token_rules_by_namespace(namespace_id)
        await cache.set_token_rules(namespace_id, rules)
        
        logger.info(f"Token限制规则删除成功，rule_id={rule_id}")
        return {"message": "Token限制规则删除成功", "rule_id": rule_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除Token限制规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除Token限制规则失败: {str(e)}")

@router.get("/token-rules", response_model=List[Dict[str, Any]])
async def get_all_token_rules():
    """获取所有Token限制规则（供nginx lua查询）"""
    try:
        db = get_db()
        rules = await db.get_all_token_rules()
        return rules
    except Exception as e:
        logger.error(f"获取所有Token限制规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取所有Token限制规则失败: {str(e)}")

@router.post("/token-rules/{rule_id}/validate-window")
async def validate_token_window(rule_id: int, token_count: int, namespace_id: int):
    """验证Token时间窗口限制（供nginx lua调用）"""
    try:
        db = get_db()
        window_service = TokenWindowService(db)
        
        # 获取规则配置
        rule = await db.get_token_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Token限制规则不存在")
        
        # 验证时间窗口限制
        result = await window_service.validate_token_window_limit(
            namespace_id, rule_id, token_count, rule
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证Token时间窗口限制失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证Token时间窗口限制失败: {str(e)}")

@router.get("/token-rules/{rule_id}/window-stats")
async def get_window_statistics(rule_id: int, namespace_id: int):
    """获取Token时间窗口统计信息"""
    try:
        db = get_db()
        window_service = TokenWindowService(db)
        
        stats = await window_service.get_window_statistics(namespace_id, rule_id)
        
        if 'error' in stats:
            raise HTTPException(status_code=400, detail=stats['error'])
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取时间窗口统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取时间窗口统计信息失败: {str(e)}")

@router.post("/token-rules/cleanup-counters")
async def cleanup_expired_counters(current_user: Dict = Depends(get_current_user)):
    """清理过期的Token计数器"""
    try:
        db = get_db()
        window_service = TokenWindowService(db)
        
        cleaned_count = await window_service.cleanup_expired_counters()
        
        return {
            "message": f"成功清理 {cleaned_count} 个过期计数器",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"清理过期计数器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理过期计数器失败: {str(e)}") 