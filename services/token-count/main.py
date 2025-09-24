from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Union, Dict
import uvicorn
import time
from token_service import TokenService
from config import Config

# 创建FastAPI应用
app = FastAPI(
    title="Token计算服务",
    description="基于Hugging Face的大模型Token计算服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化Token服务
token_service = TokenService()

# 基础请求模型
class TokenRequest(BaseModel):
    text: str
    model_name: str

# OpenAI 格式请求模型
class OpenAIToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Dict[str, str]  # name 和 arguments

class OpenAIMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[OpenAIToolCall]] = None
    tool_call_id: Optional[str] = None

class OpenAIRequest(BaseModel):
    model: str
    messages: List[OpenAIMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop: Optional[List[str]] = None

# 统一请求模型（支持两种格式）
class UnifiedTokenRequest(BaseModel):
    # 基础格式字段
    text: Optional[str] = None
    model_name: Optional[str] = None
    
    # OpenAI 格式字段
    model: Optional[str] = None
    messages: Optional[List[OpenAIMessage]] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop: Optional[List[str]] = None
    
    class Config:
        # 允许任意字段，不进行严格验证
        extra = "allow"

# 基础响应模型
class TokenResponse(BaseModel):
    success: bool
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    text: Optional[str] = None
    token_count: int
    sample_tokens: Optional[list] = None
    sample_text: Optional[str] = None
    text_length: Optional[int] = None
    tokenizer_type: Optional[str] = None
    error: Optional[str] = None

# OpenAI 格式响应模型
class OpenAIChoice(BaseModel):
    index: int
    message: OpenAIMessage
    finish_reason: str

class OpenAIUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class OpenAIResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[OpenAIChoice]
    usage: OpenAIUsage

@app.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "message": "Token计算服务",
        "version": "1.0.0",
        "endpoints": {
            "计算单个文本token": "/calculate",
            "支持格式": ["基础格式", "OpenAI格式"]
        },
        "支持的请求格式": {
            "基础格式": {
                "text": "要计算的文本",
                "model_name": "模型名称"
            },
            "OpenAI格式": {
                "model": "模型名称",
                "messages": [{"role": "user", "content": "消息内容"}]
            }
        },
        "响应格式": {
            "token_count": "token数量",
            "model": "使用的模型名称",
            "success": "是否成功"
        }
    }

@app.get("/health")
@app.head("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "token-calculator",
        "version": "1.0.0"
    }

@app.post("/calculate")
async def calculate_tokens(request: UnifiedTokenRequest):
    """
    计算文本的token数量，支持基础格式和OpenAI格式
    
    Args:
        request: 统一请求格式，支持两种输入方式
        
    Returns:
        dict: 简化的响应格式，只包含token数量
    """
    try:
        # 判断请求格式
        is_openai_format = request.messages is not None and request.model is not None
        
        if is_openai_format:
            # OpenAI 格式处理
            # 提取消息内容，包括工具调用
            messages_text = ""
            for message in request.messages:
                # 处理普通消息内容
                if message.content:
                    messages_text += message.content + "\n"
                
                # 处理工具调用
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        messages_text += f"Tool Call: {tool_call.function.get('name', 'unknown')}\n"
                        messages_text += f"Arguments: {tool_call.function.get('arguments', '')}\n"
            
            # 计算token
            result = token_service.calculate_tokens(messages_text, request.model)
            
            if not result["success"]:
                raise HTTPException(status_code=400, detail=f"Token计算失败: {result['error']}")
            
            # 返回简化的响应
            return {
                "token_count": result["token_count"],
                "model": request.model,
                "success": True
            }
        else:
            # 基础格式处理
            if not request.text or not request.model_name:
                raise HTTPException(status_code=400, detail="基础格式需要提供text和model_name字段")
            
            result = token_service.calculate_tokens(request.text, request.model_name)
            
            if not result["success"]:
                raise HTTPException(status_code=400, detail=f"Token计算失败: {result['error']}")
            
            # 返回简化的响应
            return {
                "token_count": result["token_count"],
                "model": request.model_name,
                "success": True
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower()
    ) 