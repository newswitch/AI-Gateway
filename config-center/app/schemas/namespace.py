"""
命名空间数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NamespaceBase(BaseModel):
    """命名空间基础模型"""
    namespace_code: str = Field(..., description="命名空间代码", max_length=50)
    namespace_name: str = Field(..., description="命名空间名称", max_length=100)
    description: Optional[str] = Field(None, description="描述")
    status: int = Field(1, description="状态：1-启用，0-禁用", ge=0, le=1)

class NamespaceCreate(NamespaceBase):
    """创建命名空间模型"""
    pass

class NamespaceUpdate(BaseModel):
    """更新命名空间模型"""
    namespace_code: Optional[str] = Field(None, description="命名空间代码", max_length=50)
    namespace_name: Optional[str] = Field(None, description="命名空间名称", max_length=100)
    description: Optional[str] = Field(None, description="描述")
    status: Optional[int] = Field(None, description="状态：1-启用，0-禁用", ge=0, le=1)

class NamespaceResponse(NamespaceBase):
    """命名空间响应模型"""
    namespace_id: int = Field(..., description="命名空间ID")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True 