"""
统一配置管理API适配层 - 适配新前端接口需求
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager, ConfigCache
from app.core.dependencies import get_db_manager, get_cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["统一配置管理V2"])

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

@router.get("/config/nginx", response_model=Dict[str, Any])
async def get_nginx_config(db: DatabaseManager = Depends(get_db)):
    """获取Nginx配置 - 从数据库获取真实数据"""
    try:
        # 从数据库获取nginx配置
        nginx_configs = await db.get_all_nginx_configs()
        
        # 构建配置数据结构
        config_data = {
            "global": {
                "worker_processes": "auto",
                "worker_connections": 1024,
                "error_log": "/var/log/nginx/error.log",
                "pid": "/var/run/nginx.pid"
            },
            "events": {
                "use": "epoll",
                "worker_connections": 1024,
                "multi_accept": "on"
            },
            "http": {
                "include": "/etc/nginx/mime.types",
                "default_type": "application/octet-stream",
                "log_format": "main '$remote_addr - $remote_user [$time_local] \"$request\" $status $body_bytes_sent \"$http_referer\" \"$http_user_agent\" \"$http_x_forwarded_for\"'",
                "access_log": "/var/log/nginx/access.log main",
                "sendfile": "on",
                "tcp_nopush": "on",
                "tcp_nodelay": "on",
                "keepalive_timeout": 65,
                "gzip": "on",
                "gzip_vary": "on",
                "gzip_min_length": 1024,
                "gzip_types": "text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript"
            },
            "server": {
                "listen": 80,
                "server_name": "localhost",
                "location": {
                    "/": {
                        "root": "/usr/share/nginx/html",
                        "index": "index.html index.htm"
                    }
                }
            },
            "system": {
                "max_file_size": "100m",
                "client_max_body_size": "100m",
                "client_body_timeout": "60s",
                "client_header_timeout": "60s",
                "send_timeout": "60s"
            },
            "rate_limit": {
                "limit_req_zone": "llm zone=llm:10m rate=10r/s",
                "limit_conn_zone": "conn zone=conn:10m"
            }
        }
        
        # 如果有数据库配置，则使用数据库中的配置覆盖默认值
        if nginx_configs:
            for config in nginx_configs:
                config_type = config.get('config_type', '')
                config_name = config.get('config_name', '')
                config_value = config.get('config_value', '')
                
                try:
                    # 解析JSON配置值
                    if config_value:
                        parsed_value = json.loads(config_value) if isinstance(config_value, str) else config_value
                        
                        # 根据配置类型和名称更新配置
                        if config_type == 'global' and config_name in config_data['global']:
                            config_data['global'][config_name] = parsed_value
                        elif config_type == 'events' and config_name in config_data['events']:
                            config_data['events'][config_name] = parsed_value
                        elif config_type == 'http' and config_name in config_data['http']:
                            config_data['http'][config_name] = parsed_value
                        elif config_type == 'server' and config_name in config_data['server']:
                            config_data['server'][config_name] = parsed_value
                        elif config_type == 'system' and config_name in config_data['system']:
                            config_data['system'][config_name] = parsed_value
                        elif config_type == 'rate_limit' and config_name in config_data['rate_limit']:
                            config_data['rate_limit'][config_name] = parsed_value
                except json.JSONDecodeError:
                    # 如果JSON解析失败，使用原始值
                    if config_type == 'global' and config_name in config_data['global']:
                        config_data['global'][config_name] = config_value
                    elif config_type == 'events' and config_name in config_data['events']:
                        config_data['events'][config_name] = config_value
                    elif config_type == 'http' and config_name in config_data['http']:
                        config_data['http'][config_name] = config_value
                    elif config_type == 'server' and config_name in config_data['server']:
                        config_data['server'][config_name] = config_value
                    elif config_type == 'system' and config_name in config_data['system']:
                        config_data['system'][config_name] = config_value
                    elif config_type == 'rate_limit' and config_name in config_data['rate_limit']:
                        config_data['rate_limit'][config_name] = config_value
        
        return {
            "code": 200,
            "message": "success",
            "data": config_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取Nginx配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取Nginx配置失败: {str(e)}")

@router.put("/config/nginx", response_model=Dict[str, Any])
async def update_nginx_config(config_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """更新Nginx配置"""
    try:
        # 暂时返回成功响应，实际实现中需要保存配置到数据库
        logger.info(f"Nginx配置更新成功")
        return {
            "code": 200,
            "message": "Nginx配置更新成功",
            "data": {
                "config": config_data
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"更新Nginx配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新Nginx配置失败: {str(e)}")

@router.post("/config/validate", response_model=Dict[str, Any])
async def validate_config(config_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """验证配置"""
    try:
        # 暂时返回成功响应，实际实现中需要验证配置语法
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [
                "建议启用gzip压缩以提高性能",
                "建议设置适当的keepalive_timeout值"
            ],
            "suggestions": [
                "考虑添加SSL配置以提高安全性",
                "建议配置适当的日志级别"
            ]
        }
        
        return {
            "code": 200,
            "message": "配置验证完成",
            "data": validation_result,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"验证配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证配置失败: {str(e)}")

@router.post("/config/deploy", response_model=Dict[str, Any])
async def deploy_config(current_user: Dict = Depends(get_current_user)):
    """部署配置"""
    try:
        # 暂时返回成功响应，实际实现中需要部署配置到网关
        logger.info(f"配置部署成功")
        return {
            "code": 200,
            "message": "配置部署成功",
            "data": {
                "deploymentId": "deploy_123456789",
                "status": "success",
                "deployedAt": "2024-01-15T10:30:00Z"
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"部署配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"部署配置失败: {str(e)}")

@router.get("/config/history", response_model=Dict[str, Any])
async def get_config_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量")
):
    """获取配置历史"""
    try:
        # 暂时返回模拟数据，实际实现中需要从数据库获取
        all_history = [
            {
                "id": "1",
                "version": "v1.2.3",
                "description": "更新上游服务器配置",
                "configType": "nginx",
                "status": "deployed",
                "deployedBy": "admin",
                "deployedAt": "2024-01-15T10:30:00Z",
                "rollbackAvailable": True
            },
            {
                "id": "2",
                "version": "v1.2.2",
                "description": "修复路由规则问题",
                "configType": "nginx",
                "status": "deployed",
                "deployedBy": "admin",
                "deployedAt": "2024-01-15T09:15:00Z",
                "rollbackAvailable": True
            },
            {
                "id": "3",
                "version": "v1.2.1",
                "description": "添加新的上游服务器",
                "configType": "nginx",
                "status": "deployed",
                "deployedBy": "admin",
                "deployedAt": "2024-01-15T08:45:00Z",
                "rollbackAvailable": True
            },
            {
                "id": "4",
                "version": "v1.2.0",
                "description": "初始配置部署",
                "configType": "nginx",
                "status": "deployed",
                "deployedBy": "admin",
                "deployedAt": "2024-01-15T08:00:00Z",
                "rollbackAvailable": False
            }
        ]
        
        # 分页处理
        total = len(all_history)
        start = (page - 1) * size
        end = start + size
        paginated_history = all_history[start:end]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": paginated_history,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取配置历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置历史失败: {str(e)}")

@router.post("/config/rollback/{version_id}", response_model=Dict[str, Any])
async def rollback_config(version_id: str, current_user: Dict = Depends(get_current_user)):
    """回滚配置"""
    try:
        # 暂时返回成功响应，实际实现中需要回滚到指定版本
        logger.info(f"配置回滚成功，版本：{version_id}")
        return {
            "code": 200,
            "message": "配置回滚成功",
            "data": {
                "versionId": version_id,
                "status": "success",
                "rolledBackAt": "2024-01-15T10:30:00Z"
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"回滚配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"回滚配置失败: {str(e)}")

@router.get("/config/status", response_model=Dict[str, Any])
async def get_config_status():
    """获取配置状态"""
    try:
        # 暂时返回模拟数据，实际实现中需要检查配置状态
        status_data = {
            "currentVersion": "v1.2.3",
            "lastDeployed": "2024-01-15T10:30:00Z",
            "status": "active",
            "gatewayStatus": "running",
            "configValid": True,
            "lastValidation": "2024-01-15T10:30:00Z",
            "pendingChanges": False
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": status_data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取配置状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置状态失败: {str(e)}")

@router.get("/config/templates", response_model=Dict[str, Any])
async def get_config_templates():
    """获取配置模板"""
    try:
        # 返回预定义的配置模板
        templates = [
            {
                "id": "1",
                "name": "基础配置",
                "description": "适用于小型部署的基础Nginx配置",
                "config": {
                    "global": {
                        "worker_processes": "auto",
                        "worker_connections": 1024
                    },
                    "events": {
                        "use": "epoll",
                        "worker_connections": 1024
                    },
                    "http": {
                        "include": "/etc/nginx/mime.types",
                        "default_type": "application/octet-stream",
                        "sendfile": "on",
                        "keepalive_timeout": 65
                    }
                }
            },
            {
                "id": "2",
                "name": "高性能配置",
                "description": "适用于高并发场景的优化配置",
                "config": {
                    "global": {
                        "worker_processes": "auto",
                        "worker_connections": 2048
                    },
                    "events": {
                        "use": "epoll",
                        "worker_connections": 2048,
                        "multi_accept": "on"
                    },
                    "http": {
                        "include": "/etc/nginx/mime.types",
                        "default_type": "application/octet-stream",
                        "sendfile": "on",
                        "tcp_nopush": "on",
                        "tcp_nodelay": "on",
                        "keepalive_timeout": 65,
                        "gzip": "on",
                        "gzip_vary": "on"
                    }
                }
            },
            {
                "id": "3",
                "name": "安全配置",
                "description": "包含安全加固的配置模板",
                "config": {
                    "global": {
                        "worker_processes": "auto",
                        "worker_connections": 1024
                    },
                    "events": {
                        "use": "epoll",
                        "worker_connections": 1024
                    },
                    "http": {
                        "include": "/etc/nginx/mime.types",
                        "default_type": "application/octet-stream",
                        "sendfile": "on",
                        "keepalive_timeout": 65,
                        "client_max_body_size": "10m",
                        "client_body_timeout": "60s",
                        "client_header_timeout": "60s"
                    }
                }
            }
        ]
        
        return {
            "code": 200,
            "message": "success",
            "data": templates,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取配置模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置模板失败: {str(e)}")

@router.post("/config/import", response_model=Dict[str, Any])
async def import_config(
    config_file: str,
    current_user: Dict = Depends(get_current_user)
):
    """导入配置"""
    try:
        # 暂时返回成功响应，实际实现中需要解析导入的配置文件
        logger.info(f"配置导入成功，文件：{config_file}")
        return {
            "code": 200,
            "message": "配置导入成功",
            "data": {
                "importedAt": "2024-01-15T10:30:00Z",
                "configType": "nginx",
                "validationResult": {
                    "valid": True,
                    "errors": [],
                    "warnings": []
                }
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"导入配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入配置失败: {str(e)}")

@router.get("/config/export", response_model=Dict[str, Any])
async def export_config(
    format: str = Query("json", description="导出格式")
):
    """导出配置"""
    try:
        # 暂时返回成功响应，实际实现中需要生成导出文件
        logger.info(f"配置导出请求，格式：{format}")
        return {
            "code": 200,
            "message": "配置导出成功",
            "data": {
                "downloadUrl": "/api/config/download/nginx_config_20240115_103000.json",
                "filename": "nginx_config_20240115_103000.json",
                "size": "15.2KB",
                "expiresAt": "2024-01-15T11:30:00Z"
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"导出配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")
