"""
代理规则数据模型
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ProxyRuleCreate(BaseModel):
    """创建代理规则请求模型"""
    rule_name: str
    rule_type: str
    match_pattern: str
    target_server_id: int
    rewrite_path: Optional[str] = None
    add_headers: Optional[Dict[str, str]] = None
    priority: int = 100
    status: int = 1

class ProxyRuleUpdate(BaseModel):
    """更新代理规则请求模型"""
    rule_name: Optional[str] = None
    rule_type: Optional[str] = None
    match_pattern: Optional[str] = None
    target_server_id: Optional[int] = None
    rewrite_path: Optional[str] = None
    add_headers: Optional[Dict[str, str]] = None
    priority: Optional[int] = None
    status: Optional[int] = None

class ProxyRuleResponse(BaseModel):
    """代理规则响应模型"""
    rule_id: int
    rule_name: str
    rule_type: str
    match_pattern: str
    target_server_id: int
    rewrite_path: Optional[str]
    add_headers: Optional[Dict[str, str]]
    priority: int
    status: int
    create_time: str
    update_time: str 