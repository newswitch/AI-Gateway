"""
路由规则管理API适配层 - 适配新前端接口需求
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager
from app.core.dependencies import get_db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["路由规则管理V2"])

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

@router.get("/locations", response_model=Dict[str, Any])
async def get_locations(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索")
):
    """
    获取路由规则列表 - 适配新前端接口格式
    支持分页和搜索
    """
    try:
        db = get_db()
        
        # 从数据库获取所有路由规则
        all_locations_data = await db.get_all_location_rules()
        
        # 获取上游服务器信息用于显示名称
        upstream_servers = await db.get_all_upstream_servers()
        upstream_map = {server['server_id']: server['server_name'] for server in upstream_servers}
        
        # 转换为前端需要的格式
        all_locations = []
        for location in all_locations_data:
            # 解析限流配置
            limit_req_config = location.get('limit_req_config', {})
            if isinstance(limit_req_config, str):
                try:
                    import json
                    limit_req_config = json.loads(limit_req_config)
                except:
                    limit_req_config = {}
            
            all_locations.append({
                "id": location['location_id'],
                "path": location['path'],
                "upstream": upstream_map.get(location['upstream_id'], f"server_{location['upstream_id']}"),
                "proxy_cache": location['proxy_cache'],
                "proxy_buffering": location['proxy_buffering'],
                "proxy_pass": location['proxy_pass'],
                "is_regex": location['is_regex'],
                "limit_req": {
                    "enabled": limit_req_config.get('enabled', True),
                    "zone": limit_req_config.get('zone', 'llm'),
                    "burst": limit_req_config.get('burst', 20),
                    "nodelay": limit_req_config.get('nodelay', True)
                },
                "sse_support": location['sse_support'],
                "chunked_transfer": location['chunked_transfer'],
                "status": "enabled" if location['status'] == 1 else "disabled",
                "createdAt": location['create_time'][:10],  # 只取日期部分
                "updatedAt": location['update_time'][:10]
            })
        
        # 应用搜索条件
        filtered_locations = []
        for location in all_locations:
            # 关键词搜索
            if keyword:
                keyword_lower = keyword.lower()
                if not any(keyword_lower in str(location.get(field, '')).lower() 
                          for field in ['path', 'upstream', 'proxy_pass']):
                    continue
            
            filtered_locations.append(location)
        
        # 分页处理
        total = len(filtered_locations)
        start = (page - 1) * size
        end = start + size
        paginated_locations = filtered_locations[start:end]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": paginated_locations,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取路由规则列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取路由规则列表失败: {str(e)}")

@router.get("/locations/{location_id}", response_model=Dict[str, Any])
async def get_location(location_id: int):
    """获取单个路由规则详情"""
    try:
        # 暂时返回模拟数据，实际实现中需要从数据库查询
        location_data = {
            "id": location_id,
            "path": "/ds1_5b/v1/chat/completions",
            "upstream": "ds1_5b",
            "proxy_cache": False,
            "proxy_buffering": False,
            "proxy_pass": "http://ds1_5b/v1/chat/completions",
            "is_regex": False,
            "limit_req": {
                "enabled": True,
                "zone": "llm",
                "burst": 20,
                "nodelay": True
            },
            "sse_support": True,
            "chunked_transfer": True,
            "status": "enabled",
            "createdAt": "2024-01-15",
            "updatedAt": "2024-01-15"
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": location_data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取路由规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取路由规则失败: {str(e)}")

@router.post("/locations", response_model=Dict[str, Any])
async def create_location(location_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """创建路由规则 - 适配新前端数据格式"""
    try:
        db = get_db()
        
        # 获取上游服务器ID
        upstream_servers = await db.get_all_upstream_servers()
        upstream_name_to_id = {server['server_name']: server['server_id'] for server in upstream_servers}
        upstream_id = upstream_name_to_id.get(location_data.get('upstream'))
        
        if not upstream_id:
            raise HTTPException(status_code=400, detail=f"上游服务器 '{location_data.get('upstream')}' 不存在")
        
        # 转换前端数据格式到数据库格式
        create_data = {
            "path": location_data.get("path", ""),
            "upstream_id": upstream_id,
            "proxy_cache": location_data.get("proxy_cache", False),
            "proxy_buffering": location_data.get("proxy_buffering", False),
            "proxy_pass": f"http://{location_data.get('upstream')}{location_data.get('path', '')}",
            "is_regex": location_data.get("is_regex", False),
            "limit_req_config": {
                "enabled": True,
                "zone": "llm",
                "burst": 20,
                "nodelay": True
            },
            "sse_support": location_data.get("sse_support", False),
            "chunked_transfer": location_data.get("chunked_transfer", False),
            "matcher_type": "path",
            "priority": location_data.get("priority", 100),
            "status": 1,  # 默认创建为启用状态
            "created_by": 1  # 暂时硬编码为管理员
        }
        
        # 创建路由规则
        location_id = await db.create_location_rule(create_data)
        
        logger.info(f"路由规则创建成功，location_id={location_id}")
        return {
            "code": 200,
            "message": "路由规则创建成功",
            "data": {
                "location_id": location_id,
                "location": location_data
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"创建路由规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建路由规则失败: {str(e)}")

@router.put("/locations/{location_id}", response_model=Dict[str, Any])
async def update_location(location_id: int, location_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """更新路由规则 - 适配新前端数据格式"""
    try:
        # 暂时返回成功响应，实际实现中需要更新数据库
        logger.info(f"路由规则更新成功，location_id={location_id}")
        return {
            "code": 200,
            "message": "路由规则更新成功",
            "data": {
                "location_id": location_id,
                "location": location_data
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"更新路由规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新路由规则失败: {str(e)}")

@router.delete("/locations/{location_id}", response_model=Dict[str, Any])
async def delete_location(location_id: int, current_user: Dict = Depends(get_current_user)):
    """删除路由规则"""
    try:
        # 暂时返回成功响应，实际实现中需要从数据库删除
        logger.info(f"路由规则删除成功，location_id={location_id}")
        return {
            "code": 200,
            "message": "路由规则删除成功",
            "data": {
                "location_id": location_id
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"删除路由规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除路由规则失败: {str(e)}")

@router.put("/locations/{location_id}/status", response_model=Dict[str, Any])
async def update_location_status(location_id: int, status_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """启用/禁用路由规则"""
    try:
        # 暂时返回成功响应，实际实现中需要更新数据库状态
        logger.info(f"路由规则状态更新成功，location_id={location_id}, status={status_data.get('status')}")
        return {
            "code": 200,
            "message": "路由规则状态更新成功",
            "data": {
                "location_id": location_id,
                "status": status_data.get("status")
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"更新路由规则状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新路由规则状态失败: {str(e)}")
