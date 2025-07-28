"""
上游服务器管理API
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager
from app.schemas.upstream import UpstreamServerCreate, UpstreamServerUpdate, UpstreamServerResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["上游服务器管理"])

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

@router.get("/upstream-servers", response_model=List[Dict[str, Any]])
async def get_upstream_servers():
    """获取所有上游服务器"""
    try:
        db = get_db()
        servers = await db.get_all_upstream_servers()
        return servers
    except Exception as e:
        logger.error(f"获取上游服务器列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取上游服务器列表失败: {str(e)}")

@router.get("/upstream-servers/{server_id}", response_model=Dict[str, Any])
async def get_upstream_server(server_id: int):
    """获取单个上游服务器"""
    try:
        db = get_db()
        server = await db.get_upstream_server(server_id)
        
        if not server:
            raise HTTPException(status_code=404, detail="上游服务器不存在")
        
        return server
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取上游服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取上游服务器失败: {str(e)}")

@router.post("/upstream-servers")
async def create_upstream_server(server_data: UpstreamServerCreate, current_user: Dict = Depends(get_current_user)):
    """创建上游服务器"""
    try:
        db = get_db()
        
        # 创建上游服务器
        server_id = await db.create_upstream_server(server_data.dict())
        
        # 获取创建的上游服务器
        server = await db.get_upstream_server(server_id)
        
        logger.info(f"上游服务器创建成功，server_id={server_id}")
        return {"message": "上游服务器创建成功", "server_id": server_id, "server": server}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建上游服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建上游服务器失败: {str(e)}")

@router.put("/upstream-servers/{server_id}")
async def update_upstream_server(server_id: int, server_data: UpstreamServerUpdate, current_user: Dict = Depends(get_current_user)):
    """更新上游服务器"""
    try:
        db = get_db()
        
        # 检查上游服务器是否存在
        existing_server = await db.get_upstream_server(server_id)
        if not existing_server:
            raise HTTPException(status_code=404, detail="上游服务器不存在")
        
        # 更新上游服务器
        success = await db.update_upstream_server(server_id, server_data.dict(exclude_unset=True))
        
        if not success:
            raise HTTPException(status_code=500, detail="更新上游服务器失败")
        
        # 获取更新后的上游服务器
        server = await db.get_upstream_server(server_id)
        
        logger.info(f"上游服务器更新成功，server_id={server_id}")
        return {"message": "上游服务器更新成功", "server": server}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新上游服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新上游服务器失败: {str(e)}")

@router.delete("/upstream-servers/{server_id}")
async def delete_upstream_server(server_id: int, current_user: Dict = Depends(get_current_user)):
    """删除上游服务器"""
    try:
        db = get_db()
        
        # 检查上游服务器是否存在
        server = await db.get_upstream_server(server_id)
        if not server:
            raise HTTPException(status_code=404, detail="上游服务器不存在")
        
        # 删除上游服务器
        success = await db.delete_upstream_server(server_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="删除上游服务器失败")
        
        logger.info(f"上游服务器删除成功，server_id={server_id}")
        return {"message": "上游服务器删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除上游服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除上游服务器失败: {str(e)}") 