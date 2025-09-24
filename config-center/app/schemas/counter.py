"""
计数器数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional

class CounterIncrement(BaseModel):
    """计数器增加模型"""
    amount: int = Field(1, description="增加数量", ge=1)

class CounterResponse(BaseModel):
    """计数器响应模型"""
    counter_key: str = Field(..., description="计数器键")
    value: int = Field(..., description="计数器值")
    
    class Config:
        from_attributes = True 