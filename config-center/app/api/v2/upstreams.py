"""
上游服务器管理API适配层 - 适配新前端接口需求
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager
from app.core.dependencies import get_db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["上游服务器管理V2"])

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

@router.get("/upstreams", response_model=Dict[str, Any])
async def get_upstreams(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索")
):
    """
    获取上游服务器列表 - 适配新前端接口格式
    支持分页和搜索
    """
    try:
        db = get_db()
        
        # 获取所有上游服务器
        all_servers = await db.get_all_upstream_servers()
        
        # 应用搜索条件
        filtered_servers = []
        for server in all_servers:
            # 关键词搜索
            if keyword:
                keyword_lower = keyword.lower()
                if not any(keyword_lower in str(server.get(field, '')).lower() 
                          for field in ['server_name', 'server_type', 'server_url']):
                    continue
            
            # 转换为新前端期望的格式
            server_data = {
                "id": str(server.get('server_id', '')),
                "name": server.get('server_name', ''),
                "servers": [
                    {
                        "address": _extract_address(server.get('server_url', '')),
                        "port": _extract_port(server.get('server_url', '')),
                        "weight": server.get('load_balance_weight', 1)
                    }
                ],
                "keepalive": server.get('max_connections', 64),
                "health_check": {
                    "enabled": bool(server.get('health_check_url')),
                    "path": server.get('health_check_url', '/health'),
                    "interval": server.get('health_check_interval', 30)
                },
                "server_type": server.get('server_type', 'openai'),
                "api_key": server.get('api_key', ''),
                "model_config": server.get('model_config', {}),
                "timeout_connect": server.get('timeout_connect', 30),
                "timeout_read": server.get('timeout_read', 300),
                "timeout_write": server.get('timeout_write', 300),
                "status": "enabled" if server.get('status') == 1 else "disabled",
                "createdAt": server.get('create_time', '')[:10] if server.get('create_time') else '',
                "updatedAt": server.get('update_time', '')[:10] if server.get('update_time') else ''
            }
            
            filtered_servers.append(server_data)
        
        # 分页处理
        total = len(filtered_servers)
        start = (page - 1) * size
        end = start + size
        paginated_servers = filtered_servers[start:end]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": paginated_servers,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取上游服务器列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取上游服务器列表失败: {str(e)}")

@router.get("/upstreams/{server_id}", response_model=Dict[str, Any])
async def get_upstream(server_id: int):
    """获取单个上游服务器详情"""
    try:
        db = get_db()
        server = await db.get_upstream_server(server_id)
        
        if not server:
            raise HTTPException(status_code=404, detail="上游服务器不存在")
        
        # 转换为新前端期望的格式
        server_data = {
            "id": str(server.get('server_id', '')),
            "name": server.get('server_name', ''),
            "servers": [
                {
                    "address": _extract_address(server.get('server_url', '')),
                    "port": _extract_port(server.get('server_url', '')),
                    "weight": server.get('load_balance_weight', 1)
                }
            ],
            "keepalive": server.get('max_connections', 64),
            "health_check": {
                "enabled": bool(server.get('health_check_url')),
                "path": server.get('health_check_url', '/health'),
                "interval": server.get('health_check_interval', 30)
            },
            "server_type": server.get('server_type', 'openai'),
            "api_key": server.get('api_key', ''),
            "model_config": server.get('model_config', {}),
            "timeout_connect": server.get('timeout_connect', 30),
            "timeout_read": server.get('timeout_read', 300),
            "timeout_write": server.get('timeout_write', 300),
            "status": "enabled" if server.get('status') == 1 else "disabled",
            "createdAt": server.get('create_time', '')[:10] if server.get('create_time') else '',
            "updatedAt": server.get('update_time', '')[:10] if server.get('update_time') else ''
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": server_data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取上游服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取上游服务器失败: {str(e)}")

@router.post("/upstreams", response_model=Dict[str, Any])
async def create_upstream(upstream_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """创建上游服务器 - 适配新前端数据格式"""
    try:
        db = get_db()
        
        # 转换新前端数据格式到后端格式
        create_data = {
            "server_name": upstream_data.get("name", ""),
            "server_type": upstream_data.get("server_type", "openai"),
            "server_url": _build_server_url(upstream_data),
            "api_key": upstream_data.get("api_key", ""),
            "model_config": upstream_data.get("model_config", {}),
            "load_balance_weight": upstream_data.get("servers", [{}])[0].get("weight", 1),
            "max_connections": upstream_data.get("keepalive", 64),
            "timeout_connect": upstream_data.get("timeout_connect", 30),
            "timeout_read": upstream_data.get("timeout_read", 300),
            "timeout_write": upstream_data.get("timeout_write", 300),
            "health_check_url": upstream_data.get("health_check", {}).get("path", "/health"),
            "health_check_interval": upstream_data.get("health_check", {}).get("interval", 30),
            "status": 1 if upstream_data.get("status") == "enabled" else 0
        }
        
        # 创建上游服务器
        server_id = await db.create_upstream_server(create_data)
        
        # 获取创建的上游服务器
        server = await db.get_upstream_server(server_id)
        
        logger.info(f"上游服务器创建成功，server_id={server_id}")
        return {
            "code": 200,
            "message": "上游服务器创建成功",
            "data": {
                "server_id": server_id,
                "server": server
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"创建上游服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建上游服务器失败: {str(e)}")

@router.put("/upstreams/{server_id}", response_model=Dict[str, Any])
async def update_upstream(server_id: int, upstream_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """更新上游服务器 - 适配新前端数据格式"""
    try:
        db = get_db()
        
        # 检查上游服务器是否存在
        existing_server = await db.get_upstream_server(server_id)
        if not existing_server:
            raise HTTPException(status_code=404, detail="上游服务器不存在")
        
        # 转换新前端数据格式到后端格式
        update_data = {}
        if "name" in upstream_data:
            update_data["server_name"] = upstream_data["name"]
        if "server_type" in upstream_data:
            update_data["server_type"] = upstream_data["server_type"]
        if "servers" in upstream_data:
            update_data["server_url"] = _build_server_url(upstream_data)
        if "api_key" in upstream_data:
            update_data["api_key"] = upstream_data["api_key"]
        if "model_config" in upstream_data:
            update_data["model_config"] = upstream_data["model_config"]
        if "keepalive" in upstream_data:
            update_data["max_connections"] = upstream_data["keepalive"]
        if "timeout_connect" in upstream_data:
            update_data["timeout_connect"] = upstream_data["timeout_connect"]
        if "timeout_read" in upstream_data:
            update_data["timeout_read"] = upstream_data["timeout_read"]
        if "timeout_write" in upstream_data:
            update_data["timeout_write"] = upstream_data["timeout_write"]
        if "health_check" in upstream_data:
            health_check = upstream_data["health_check"]
            update_data["health_check_url"] = health_check.get("path", "/health")
            update_data["health_check_interval"] = health_check.get("interval", 30)
        if "status" in upstream_data:
            update_data["status"] = 1 if upstream_data["status"] == "enabled" else 0
        
        # 更新上游服务器
        success = await db.update_upstream_server(server_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="更新上游服务器失败")
        
        # 获取更新后的上游服务器
        server = await db.get_upstream_server(server_id)
        
        logger.info(f"上游服务器更新成功，server_id={server_id}")
        return {
            "code": 200,
            "message": "上游服务器更新成功",
            "data": {
                "server_id": server_id,
                "server": server
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新上游服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新上游服务器失败: {str(e)}")

@router.delete("/upstreams/{server_id}", response_model=Dict[str, Any])
async def delete_upstream(server_id: int, current_user: Dict = Depends(get_current_user)):
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
        return {
            "code": 200,
            "message": "上游服务器删除成功",
            "data": {
                "server_id": server_id
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除上游服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除上游服务器失败: {str(e)}")

@router.put("/upstreams/{server_id}/status", response_model=Dict[str, Any])
async def update_upstream_status(server_id: int, status_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """启用/禁用上游服务器"""
    try:
        db = get_db()
        
        # 检查上游服务器是否存在
        existing_server = await db.get_upstream_server(server_id)
        if not existing_server:
            raise HTTPException(status_code=404, detail="上游服务器不存在")
        
        # 更新状态
        status_value = 1 if status_data.get("status") == "enabled" else 0
        success = await db.update_upstream_server(server_id, {"status": status_value})
        
        if not success:
            raise HTTPException(status_code=500, detail="更新上游服务器状态失败")
        
        logger.info(f"上游服务器状态更新成功，server_id={server_id}, status={status_value}")
        return {
            "code": 200,
            "message": "上游服务器状态更新成功",
            "data": {
                "server_id": server_id,
                "status": status_data.get("status")
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新上游服务器状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新上游服务器状态失败: {str(e)}")

def _extract_address(server_url: str) -> str:
    """从服务器URL中提取地址"""
    try:
        if not server_url:
            return ''
        
        # 移除协议部分
        if '://' in server_url:
            url_without_protocol = server_url.split('://')[-1]
        else:
            url_without_protocol = server_url
        
        # 移除路径部分
        host_part = url_without_protocol.split('/')[0]
        
        # 移除端口部分
        if ':' in host_part:
            return host_part.split(':')[0]
        return host_part
    except (ValueError, IndexError):
        return ''

def _extract_port(server_url: str) -> int:
    """从服务器URL中提取端口号"""
    try:
        if not server_url or ':' not in server_url:
            return 80
        
        # 提取端口部分
        port_part = server_url.split(':')[-1].split('/')[0]
        if port_part and port_part.isdigit():
            return int(port_part)
        return 80
    except (ValueError, IndexError):
        return 80

def _build_server_url(upstream_data: Dict[str, Any]) -> str:
    """根据新前端数据构建服务器URL"""
    servers = upstream_data.get("servers", [])
    if not servers:
        return ""
    
    server = servers[0]
    address = server.get("address", "")
    port = server.get("port", 80)
    
    # 根据服务器类型构建URL
    server_type = upstream_data.get("server_type", "openai")
    if server_type == "openai":
        return f"https://{address}:{port}"
    elif server_type == "azure":
        return f"https://{address}:{port}"
    elif server_type == "claude":
        return f"https://{address}:{port}"
    else:
        return f"http://{address}:{port}"
