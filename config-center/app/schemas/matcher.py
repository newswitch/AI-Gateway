"""
报文匹配器数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MatcherBase(BaseModel):
    """报文匹配器基础模型"""
    matcher_name: str = Field(..., description="匹配器名称", max_length=100)
    matcher_type: str = Field(..., description="匹配类型：header/body", max_length=20)
    match_field: str = Field(..., description="匹配字段", max_length=100)
    match_operator: str = Field(..., description="匹配操作符", max_length=20)
    match_value: str = Field(..., description="匹配值")
    priority: int = Field(100, description="优先级", ge=0)
    status: int = Field(1, description="状态：1-启用，0-禁用", ge=0, le=1)

class MatcherCreate(MatcherBase):
    """创建报文匹配器模型"""
    pass

class MatcherUpdate(BaseModel):
    """更新报文匹配器模型"""
    matcher_name: Optional[str] = Field(None, description="匹配器名称", max_length=100)
    matcher_type: Optional[str] = Field(None, description="匹配类型：header/body", max_length=20)
    match_field: Optional[str] = Field(None, description="匹配字段", max_length=100)
    match_operator: Optional[str] = Field(None, description="匹配操作符", max_length=20)
    match_value: Optional[str] = Field(None, description="匹配值")
    priority: Optional[int] = Field(None, description="优先级", ge=0)
    status: Optional[int] = Field(None, description="状态：1-启用，0-禁用", ge=0, le=1)

class MatcherResponse(MatcherBase):
    """报文匹配器响应模型"""
    matcher_id: int = Field(..., description="匹配器ID")
    namespace_id: int = Field(..., description="命名空间ID")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True 