"""
命名空间规则数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class RuleBase(BaseModel):
    """命名空间规则基础模型"""
    rule_name: str = Field(..., description="规则名称", max_length=100)
    rule_type: str = Field(..., description="规则类型", max_length=30)
    rule_config: Dict[str, Any] = Field(..., description="规则配置")
    priority: int = Field(100, description="优先级", ge=0)
    status: int = Field(1, description="状态：1-启用，0-禁用", ge=0, le=1)

class RuleCreate(RuleBase):
    """创建命名空间规则模型"""
    pass

class RuleUpdate(BaseModel):
    """更新命名空间规则模型"""
    rule_name: Optional[str] = Field(None, description="规则名称", max_length=100)
    rule_type: Optional[str] = Field(None, description="规则类型", max_length=30)
    rule_config: Optional[Dict[str, Any]] = Field(None, description="规则配置")
    priority: Optional[int] = Field(None, description="优先级", ge=0)
    status: Optional[int] = Field(None, description="状态：1-启用，0-禁用", ge=0, le=1)

class RuleResponse(RuleBase):
    """命名空间规则响应模型"""
    rule_id: int = Field(..., description="规则ID")
    namespace_id: int = Field(..., description="命名空间ID")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True 