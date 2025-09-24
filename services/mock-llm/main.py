#!/usr/bin/env python3
"""
模拟大模型服务
模拟vLLM的API接口，用于本地开发测试
"""

import asyncio
import json
import random
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import json

app = FastAPI(
    title="Mock LLM Service",
    description="模拟大模型服务，用于本地开发测试",
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

# 模拟的模型配置
MOCK_MODELS = {
    "qwen2.5-7b": {
        "id": "qwen2.5-7b",
        "object": "model",
        "created": int(time.time()),
        "owned_by": "mock-llm",
        "permission": [],
        "root": "qwen2.5-7b",
        "parent": None,
        "max_model_length": 32768,
        "context_length": 32768,
        "tokenizer": "qwen2.5-7b"
    },
    "qwen2.5-14b": {
        "id": "qwen2.5-14b",
        "object": "model",
        "created": int(time.time()),
        "owned_by": "mock-llm",
        "permission": [],
        "root": "qwen2.5-14b",
        "parent": None,
        "max_model_length": 32768,
        "context_length": 32768,
        "tokenizer": "qwen2.5-14b"
    },
    "Qwen3-8B": {
        "id": "Qwen3-8B",
        "object": "model",
        "created": int(time.time()),
        "owned_by": "mock-llm",
        "permission": [],
        "root": "Qwen3-8B",
        "parent": None,
        "max_model_length": 32768,
        "context_length": 32768,
        "tokenizer": "Qwen3-8B"
    },
    "deepseek-r1-7b": {
        "id": "deepseek-r1-7b",
        "object": "model",
        "created": int(time.time()),
        "owned_by": "mock-llm",
        "permission": [],
        "root": "deepseek-r1-7b",
        "parent": None,
        "max_model_length": 32768,
        "context_length": 32768,
        "tokenizer": "deepseek-r1-7b"
    }
}

# 模拟响应模板
MOCK_RESPONSES = [
    "这是一个模拟的AI回复。",
    "根据您的问题，我建议您考虑以下几个方面：",
    "这是一个很好的问题，让我来为您详细解答。",
    "基于我的理解，我认为应该这样处理：",
    "感谢您的提问，以下是我的建议：",
    "这个问题涉及到多个方面，让我逐一为您分析：",
    "根据当前的情况，我建议采用以下策略：",
    "这是一个复杂的问题，需要综合考虑多个因素：",
    "让我为您提供一个详细的解决方案：",
    "基于我的分析，我认为最佳的做法是："
]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    top_p: Optional[float] = 0.9
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop: Optional[List[str]] = None
    stream: Optional[bool] = False
    n: Optional[int] = 1

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    top_p: Optional[float] = 0.9
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop: Optional[List[str]] = None
    stream: Optional[bool] = False
    n: Optional[int] = 1

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class Choice(BaseModel):
    index: int
    message: Optional[ChatMessage] = None
    text: Optional[str] = None
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

class CompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

def generate_mock_response(prompt: str, max_tokens: int = 1000) -> str:
    """生成模拟回复 - 输入什么就输出什么"""
    return prompt

def generate_streaming_response(prompt: str, max_tokens: int = 1000):
    """生成流式回复 - 输入什么就输出什么"""
    # 逐字符输出输入内容
    full_response = prompt
    for i, char in enumerate(full_response):
        yield {
            "id": f"chatcmpl-{int(time.time())}-{random.randint(1000, 9999)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "mock-model",
            "choices": [{
                "index": 0,
                "delta": {"content": char},
                "finish_reason": None
            }]
        }
        time.sleep(0.05)  # 模拟打字效果
    
    # 发送结束标记
    yield {
        "id": f"chatcmpl-{int(time.time())}-{random.randint(1000, 9999)}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": "mock-model",
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }

def calculate_tokens(text: str) -> int:
    """简单的token计算（模拟）"""
    return len(text) // 4  # 粗略估算

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "mock-llm",
        "version": "1.0.0"
    }

@app.get("/v1/models")
async def list_models():
    """列出可用模型"""
    return {
        "object": "list",
        "data": list(MOCK_MODELS.values())
    }

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """获取特定模型信息"""
    if model_id not in MOCK_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    return MOCK_MODELS[model_id]

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    """创建聊天完成"""
    if request.model not in MOCK_MODELS:
        raise HTTPException(status_code=400, detail="Model not found")
    
    # 生成回复
    messages_text = " ".join([msg.content for msg in request.messages])
    
    # 如果启用流式输出
    if request.stream:
        def generate():
            for chunk in generate_streaming_response(messages_text, request.max_tokens or 1000):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    
    # 非流式输出
    # 模拟处理延迟
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    response_text = generate_mock_response(messages_text, request.max_tokens or 1000)
    
    # 计算token使用量
    prompt_tokens = calculate_tokens(messages_text)
    completion_tokens = calculate_tokens(response_text)
    
    # 生成多个选择（如果n>1）
    choices = []
    for i in range(request.n or 1):
        choice_text = response_text
        if i > 0:
            choice_text += f" (选择 {i+1})"
        
        choice = Choice(
            index=i,
            message=ChatMessage(role="assistant", content=choice_text),
            finish_reason="stop"
        )
        choices.append(choice)
    
    response = ChatCompletionResponse(
        id=f"chatcmpl-{int(time.time())}-{random.randint(1000, 9999)}",
        object="chat.completion",
        created=int(time.time()),
        model=request.model,
        choices=choices,
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
    )
    
    return response

@app.post("/v1/completions")
async def create_completion(request: CompletionRequest):
    """创建文本完成"""
    if request.model not in MOCK_MODELS:
        raise HTTPException(status_code=400, detail="Model not found")
    
    # 如果启用流式输出
    if request.stream:
        def generate():
            for chunk in generate_streaming_response(request.prompt, request.max_tokens or 1000):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    
    # 非流式输出
    # 模拟处理延迟
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    # 生成回复
    response_text = generate_mock_response(request.prompt, request.max_tokens or 1000)
    
    # 计算token使用量
    prompt_tokens = calculate_tokens(request.prompt)
    completion_tokens = calculate_tokens(response_text)
    
    # 生成多个选择（如果n>1）
    choices = []
    for i in range(request.n or 1):
        choice_text = response_text
        if i > 1:
            choice_text += f" (选择 {i+1})"
        
        choice = Choice(
            index=i,
            text=choice_text,
            finish_reason="stop"
        )
        choices.append(choice)
    
    response = CompletionResponse(
        id=f"cmpl-{int(time.time())}-{random.randint(1000, 9999)}",
        object="text_completion",
        created=int(time.time()),
        model=request.model,
        choices=choices,
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
    )
    
    return response

@app.get("/v1/engines")
async def list_engines():
    """列出引擎（兼容性接口）"""
    return await list_models()

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Mock LLM Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "models": "/v1/models",
            "chat_completions": "/v1/chat/completions",
            "completions": "/v1/completions"
        }
    }

if __name__ == "__main__":
    print("启动模拟大模型服务...")
    print("可用模型:", list(MOCK_MODELS.keys()))
    print("服务地址: http://localhost:8003")
    print("API文档: http://localhost:8003/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
