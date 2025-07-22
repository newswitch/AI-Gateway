from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
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

# 请求模型
class TokenRequest(BaseModel):
    text: str
    model_name: str

class BatchTokenRequest(BaseModel):
    texts: List[str]
    model_name: str

class DownloadModelRequest(BaseModel):
    model_name: str

# 响应模型
class TokenResponse(BaseModel):
    success: bool
    model_name: Optional[str] = None
    text: Optional[str] = None
    token_count: int
    sample_tokens: Optional[List[int]] = None
    sample_text: Optional[str] = None
    text_length: Optional[int] = None
    error: Optional[str] = None

class ModelInfo(BaseModel):
    name: str
    description: str
    downloaded: bool
    url: str

@app.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "message": "Token计算服务",
        "version": "1.0.0",
        "endpoints": {
            "计算单个文本token": "/calculate",
            "批量计算token": "/batch-calculate", 
            "获取可用模型": "/models",
            "下载模型": "/download-model",
            "健康检查": "/health"
        }
    }

@app.post("/calculate", response_model=TokenResponse)
async def calculate_tokens(request: TokenRequest):
    """
    计算单个文本的token数量
    
    Args:
        request: 包含文本和模型名称的请求
        
    Returns:
        TokenResponse: token计算结果
    """
    try:
        result = token_service.calculate_tokens(request.text, request.model_name)
        return TokenResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")

@app.post("/batch-calculate", response_model=List[TokenResponse])
async def batch_calculate_tokens(request: BatchTokenRequest):
    """
    批量计算多个文本的token数量
    
    Args:
        request: 包含文本列表和模型名称的请求
        
    Returns:
        List[TokenResponse]: 每个文本的token计算结果
    """
    try:
        results = token_service.batch_calculate_tokens(request.texts, request.model_name)
        return [TokenResponse(**result) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量计算失败: {str(e)}")

@app.get("/models", response_model=List[ModelInfo])
async def get_models():
    """
    获取可用的模型列表
    
    Returns:
        List[ModelInfo]: 可用模型信息列表
    """
    try:
        models = token_service.get_available_models()
        return [ModelInfo(**model) for model in models]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@app.post("/download-model")
async def download_model(request: DownloadModelRequest):
    """
    下载指定模型到本地
    
    Args:
        request: 包含模型名称的请求
        
    Returns:
        dict: 下载结果
    """
    try:
        success = token_service.download_model(request.model_name)
        if success:
            return {
                "success": True,
                "message": f"模型 {request.model_name} 下载成功"
            }
        else:
            raise HTTPException(status_code=400, detail=f"模型 {request.model_name} 下载失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "token-calculator",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower()
    ) 