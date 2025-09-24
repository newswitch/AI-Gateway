"""
上游服务器数据模型
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class UpstreamServerCreate(BaseModel):
    """创建上游服务器请求模型"""
    server_name: str
    server_type: str
    server_url: str
    api_key: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    load_balance_weight: int = 1
    max_connections: int = 100
    timeout_connect: int = 30
    timeout_read: int = 300
    timeout_write: int = 300
    health_check_url: Optional[str] = None
    health_check_interval: int = 30
    status: int = 1

class UpstreamServerUpdate(BaseModel):
    """更新上游服务器请求模型"""
    server_name: Optional[str] = None
    server_type: Optional[str] = None
    server_url: Optional[str] = None
    api_key: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    load_balance_weight: Optional[int] = None
    max_connections: Optional[int] = None
    timeout_connect: Optional[int] = None
    timeout_read: Optional[int] = None
    timeout_write: Optional[int] = None
    health_check_url: Optional[str] = None
    health_check_interval: Optional[int] = None
    status: Optional[int] = None

class UpstreamServerResponse(BaseModel):
    """上游服务器响应模型"""
    server_id: int
    server_name: str
    server_type: str
    server_url: str
    api_key: Optional[str]
    model_config: Optional[Dict[str, Any]]
    load_balance_weight: int
    max_connections: int
    timeout_connect: int
    timeout_read: int
    timeout_write: int
    health_check_url: Optional[str]
    health_check_interval: int
    status: int
    create_time: str
    update_time: str 