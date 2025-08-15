"""
Nginx配置管理API
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Nginx配置管理"])

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

@router.get("/nginx-configs", response_model=List[Dict[str, Any]])
async def list_nginx_configs(config_type: str | None = Query(None, description="可选：按类型过滤")):
    """获取所有nginx配置，支持可选类型过滤"""
    try:
        db = get_db()
        if config_type:
            return await db.get_nginx_configs_by_type(config_type)
        return await db.get_all_nginx_configs()
    except Exception as e:
        logger.error(f"获取nginx配置列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取nginx配置列表失败: {str(e)}")

@router.get("/nginx-configs/{config_type}", response_model=List[Dict[str, Any]])
async def get_nginx_configs_by_type(config_type: str):
    """根据类型获取nginx配置"""
    try:
        db = get_db()
        configs = await db.get_nginx_configs_by_type(config_type)
        return configs
    except Exception as e:
        logger.error(f"获取nginx配置列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取nginx配置列表失败: {str(e)}")

@router.get("/nginx-configs/{config_id}", response_model=Dict[str, Any])
async def get_nginx_config(config_id: int):
    """获取单个nginx配置"""
    try:
        db = get_db()
        config = await db.get_nginx_config(config_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="nginx配置不存在")
        
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取nginx配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取nginx配置失败: {str(e)}")

@router.post("/nginx-configs")
async def create_nginx_config(config_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """创建nginx配置"""
    try:
        db = get_db()
        
        # 创建nginx配置
        config_id = await db.create_nginx_config(config_data)
        
        # 获取创建的配置
        config = await db.get_nginx_config(config_id)
        
        logger.info(f"nginx配置创建成功，config_id={config_id}")
        return {"message": "nginx配置创建成功", "config_id": config_id, "config": config}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建nginx配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建nginx配置失败: {str(e)}")

@router.put("/nginx-configs/{config_id}")
async def update_nginx_config(config_id: int, config_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """更新nginx配置"""
    try:
        db = get_db()
        
        # 检查配置是否存在
        existing_config = await db.get_nginx_config(config_id)
        if not existing_config:
            raise HTTPException(status_code=404, detail="nginx配置不存在")
        
        # 更新配置
        success = await db.update_nginx_config(config_id, config_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="更新nginx配置失败")
        
        # 获取更新后的配置
        config = await db.get_nginx_config(config_id)
        
        logger.info(f"nginx配置更新成功，config_id={config_id}")
        return {"message": "nginx配置更新成功", "config": config}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新nginx配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新nginx配置失败: {str(e)}")

@router.delete("/nginx-configs/{config_id}")
async def delete_nginx_config(config_id: int, current_user: Dict = Depends(get_current_user)):
    """删除nginx配置"""
    try:
        db = get_db()
        
        # 检查配置是否存在
        config = await db.get_nginx_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="nginx配置不存在")
        
        # 删除配置
        success = await db.delete_nginx_config(config_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="删除nginx配置失败")
        
        logger.info(f"nginx配置删除成功，config_id={config_id}")
        return {"message": "nginx配置删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除nginx配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除nginx配置失败: {str(e)}") 