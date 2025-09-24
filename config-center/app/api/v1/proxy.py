"""
代理规则管理API
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager
from app.schemas.proxy import ProxyRuleCreate, ProxyRuleUpdate, ProxyRuleResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["代理规则管理"])

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

@router.get("/proxy-rules", response_model=List[Dict[str, Any]])
async def get_proxy_rules():
    """获取所有代理规则"""
    try:
        db = get_db()
        rules = await db.get_all_proxy_rules()
        return rules
    except Exception as e:
        logger.error(f"获取代理规则列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取代理规则列表失败: {str(e)}")

@router.get("/proxy-rules/{rule_id}", response_model=Dict[str, Any])
async def get_proxy_rule(rule_id: int):
    """获取单个代理规则"""
    try:
        db = get_db()
        rule = await db.get_proxy_rule(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail="代理规则不存在")
        
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代理规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取代理规则失败: {str(e)}")

@router.post("/proxy-rules")
async def create_proxy_rule(rule_data: ProxyRuleCreate, current_user: Dict = Depends(get_current_user)):
    """创建代理规则"""
    try:
        db = get_db()
        
        # 验证目标服务器是否存在
        target_server = await db.get_upstream_server(rule_data.target_server_id)
        if not target_server:
            raise HTTPException(status_code=400, detail="目标服务器不存在")
        
        # 创建代理规则
        rule_id = await db.create_proxy_rule(rule_data.dict())
        
        # 获取创建的代理规则
        rule = await db.get_proxy_rule(rule_id)
        
        logger.info(f"代理规则创建成功，rule_id={rule_id}")
        return {"message": "代理规则创建成功", "rule_id": rule_id, "rule": rule}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建代理规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建代理规则失败: {str(e)}")

@router.put("/proxy-rules/{rule_id}")
async def update_proxy_rule(rule_id: int, rule_data: ProxyRuleUpdate, current_user: Dict = Depends(get_current_user)):
    """更新代理规则"""
    try:
        db = get_db()
        
        # 检查代理规则是否存在
        existing_rule = await db.get_proxy_rule(rule_id)
        if not existing_rule:
            raise HTTPException(status_code=404, detail="代理规则不存在")
        
        # 如果更新了目标服务器，验证服务器是否存在
        if rule_data.target_server_id:
            target_server = await db.get_upstream_server(rule_data.target_server_id)
            if not target_server:
                raise HTTPException(status_code=400, detail="目标服务器不存在")
        
        # 更新代理规则
        success = await db.update_proxy_rule(rule_id, rule_data.dict(exclude_unset=True))
        
        if not success:
            raise HTTPException(status_code=500, detail="更新代理规则失败")
        
        # 获取更新后的代理规则
        rule = await db.get_proxy_rule(rule_id)
        
        logger.info(f"代理规则更新成功，rule_id={rule_id}")
        return {"message": "代理规则更新成功", "rule": rule}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新代理规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新代理规则失败: {str(e)}")

@router.delete("/proxy-rules/{rule_id}")
async def delete_proxy_rule(rule_id: int, current_user: Dict = Depends(get_current_user)):
    """删除代理规则"""
    try:
        db = get_db()
        
        # 检查代理规则是否存在
        rule = await db.get_proxy_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="代理规则不存在")
        
        # 删除代理规则
        success = await db.delete_proxy_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="删除代理规则失败")
        
        logger.info(f"代理规则删除成功，rule_id={rule_id}")
        return {"message": "代理规则删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除代理规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除代理规则失败: {str(e)}") 