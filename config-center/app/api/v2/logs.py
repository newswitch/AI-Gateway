"""
访问日志API适配层 - 适配新前端接口需求
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager, ConfigCache
from app.core.dependencies import get_db_manager, get_cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["访问日志V2"])

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

@router.get("/logs", response_model=Dict[str, Any])
async def get_logs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    startTime: Optional[str] = Query(None, description="开始时间"),
    endTime: Optional[str] = Query(None, description="结束时间"),
    level: Optional[str] = Query(None, description="日志级别筛选"),
    model: Optional[str] = Query(None, description="模型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取访问日志列表"""
    try:
        # 从数据库获取真实数据
        db = get_db()
        
        # 构建筛选条件
        filters = {}
        if startTime:
            filters['start_time'] = startTime
        if endTime:
            filters['end_time'] = endTime
        if level:
            filters['level'] = level
        if search:
            filters['search'] = search
        
        # 获取访问日志
        all_logs_data = await db.get_access_logs(filters, limit=size, offset=(page-1)*size)
        
        # 获取命名空间和上游服务器信息用于显示名称
        namespaces = await db.get_all_namespaces()
        namespace_map = {ns['namespace_id']: ns['namespace_name'] for ns in namespaces}
        
        upstreams = await db.get_all_upstream_servers()
        upstream_map = {up['server_id']: up['server_name'] for up in upstreams}
        
        # 转换为前端需要的格式
        all_logs = []
        for log in all_logs_data:
            # 确定日志级别
            if log['status_code'] >= 400:
                log_level = "error"
            elif log['error_message']:
                log_level = "warning"
            else:
                log_level = "info"
            
            all_logs.append({
                "id": str(log['log_id']),
                "timestamp": log['timestamp'],
                "level": log_level,
                "message": log['error_message'] or "Request processed successfully",
                "model": "gpt-4",  # 暂时硬编码，后续可以从配置获取
                "status": str(log['status_code']),
                "method": log['method'] or "POST",
                "path": log['path'] or "/v1/chat/completions",
                "ip": log['client_ip'],
                "userAgent": log['user_agent'] or "Unknown",
                "responseTime": log['response_time'] or 0,
                "inputTokens": log['input_tokens'] or 0,
                "outputTokens": log['output_tokens'] or 0,
                "namespace": namespace_map.get(log['namespace_id'], f"ns_{log['namespace_id']}"),
                "upstream": upstream_map.get(log['upstream_id'], f"upstream_{log['upstream_id']}"),
                "requestId": log['request_id'] or f"req_{log['log_id']}"
            })
        
        # 应用筛选条件
        filtered_logs = []
        for log in all_logs:
            # 时间范围筛选
            if startTime and log.get('timestamp') < startTime:
                continue
            if endTime and log.get('timestamp') > endTime:
                continue
            
            # 级别筛选
            if level and log.get('level') != level:
                continue
            
            # 模型筛选
            if model and log.get('model') != model:
                continue
            
            # 状态筛选
            if status and log.get('status') != status:
                continue
            
            # 搜索关键词
            if search:
                search_lower = search.lower()
                if not any(search_lower in str(log.get(field, '')).lower() 
                          for field in ['message', 'model', 'path', 'ip', 'requestId']):
                    continue
            
            filtered_logs.append(log)
        
        # 分页处理
        total = len(filtered_logs)
        start = (page - 1) * size
        end = start + size
        paginated_logs = filtered_logs[start:end]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": paginated_logs,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取访问日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取访问日志失败: {str(e)}")

@router.get("/logs/stats", response_model=Dict[str, Any])
async def get_log_stats(
    startTime: Optional[str] = Query(None, description="开始时间"),
    endTime: Optional[str] = Query(None, description="结束时间")
):
    """获取日志统计信息"""
    try:
        # 暂时返回模拟数据，实际实现中需要从日志系统获取
        stats_data = {
            "total": 12856,
            "error": 167,
            "warn": 23,
            "info": 12666,
            "storage": "2.3GB",
            "byLevel": {
                "info": 12666,
                "warn": 23,
                "error": 167,
                "debug": 0
            },
            "byModel": {
                "gpt-4": 8562,
                "gpt-3.5-turbo": 2341,
                "claude-3": 1234,
                "other": 719
            },
            "byStatus": {
                "200": 12666,
                "400": 45,
                "401": 23,
                "403": 12,
                "429": 34,
                "500": 45,
                "502": 23,
                "503": 8
            },
            "trends": {
                "timestamps": [
                    "2024-01-15T10:00:00Z",
                    "2024-01-15T10:01:00Z",
                    "2024-01-15T10:02:00Z",
                    "2024-01-15T10:03:00Z",
                    "2024-01-15T10:04:00Z"
                ],
                "counts": [245, 231, 256, 218, 224],
                "errors": [3, 2, 4, 2, 3],
                "warnings": [1, 0, 2, 1, 1]
            }
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": stats_data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取日志统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取日志统计失败: {str(e)}")

@router.get("/logs/export", response_model=Dict[str, Any])
async def export_logs(
    startTime: Optional[str] = Query(None, description="开始时间"),
    endTime: Optional[str] = Query(None, description="结束时间"),
    level: Optional[str] = Query(None, description="日志级别筛选"),
    model: Optional[str] = Query(None, description="模型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    format: str = Query("json", description="导出格式")
):
    """导出访问日志"""
    try:
        # 暂时返回成功响应，实际实现中需要生成导出文件
        logger.info(f"日志导出请求，格式：{format}")
        return {
            "code": 200,
            "message": "日志导出成功",
            "data": {
                "downloadUrl": "/api/logs/download/export_20240115_103000.json",
                "filename": "export_20240115_103000.json",
                "size": "2.3MB",
                "expiresAt": "2024-01-15T11:30:00Z"
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"导出日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出日志失败: {str(e)}")

@router.get("/logs/filters", response_model=Dict[str, Any])
async def get_log_filters():
    """获取日志筛选选项"""
    try:
        # 返回可用的筛选选项
        filters_data = {
            "levels": [
                {"value": "debug", "label": "调试"},
                {"value": "info", "label": "信息"},
                {"value": "warn", "label": "警告"},
                {"value": "error", "label": "错误"}
            ],
            "models": [
                {"value": "gpt-4", "label": "GPT-4"},
                {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"},
                {"value": "claude-3", "label": "Claude-3"},
                {"value": "qwen-72b", "label": "Qwen-72B"},
                {"value": "deepseek-7b", "label": "DeepSeek-7B"}
            ],
            "statuses": [
                {"value": "200", "label": "200 - 成功"},
                {"value": "400", "label": "400 - 请求错误"},
                {"value": "401", "label": "401 - 未授权"},
                {"value": "403", "label": "403 - 禁止访问"},
                {"value": "429", "label": "429 - 请求过多"},
                {"value": "500", "label": "500 - 服务器错误"},
                {"value": "502", "label": "502 - 网关错误"},
                {"value": "503", "label": "503 - 服务不可用"}
            ],
            "formats": [
                {"value": "json", "label": "JSON"},
                {"value": "csv", "label": "CSV"},
                {"value": "txt", "label": "TXT"}
            ]
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": filters_data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取日志筛选选项失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取日志筛选选项失败: {str(e)}")

@router.get("/logs/{log_id}", response_model=Dict[str, Any])
async def get_log_detail(log_id: str):
    """获取单个日志详情"""
    try:
        # 暂时返回模拟数据，实际实现中需要从日志系统获取
        log_data = {
            "id": log_id,
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "info",
            "message": "Request processed successfully",
            "model": "gpt-4",
            "status": "200",
            "method": "POST",
            "path": "/v1/chat/completions",
            "ip": "192.168.1.100",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "responseTime": 1250,
            "inputTokens": 150,
            "outputTokens": 75,
            "namespace": "ns-enterprise-001",
            "upstream": "ds1_5b",
            "requestId": "req_123456789",
            "requestBody": {
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, how are you?"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 100
            },
            "responseBody": {
                "id": "chatcmpl-123456789",
                "object": "chat.completion",
                "created": 1705312200,
                "model": "gpt-4",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 75,
                    "total_tokens": 225
                }
            },
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer sk-...",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": log_data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取日志详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取日志详情失败: {str(e)}")

@router.delete("/logs", response_model=Dict[str, Any])
async def clear_logs(
    startTime: Optional[str] = Query(None, description="开始时间"),
    endTime: Optional[str] = Query(None, description="结束时间"),
    level: Optional[str] = Query(None, description="日志级别筛选"),
    current_user: Dict = Depends(get_current_user)
):
    """清理日志"""
    try:
        # 暂时返回成功响应，实际实现中需要清理日志数据
        logger.info(f"日志清理请求，时间范围：{startTime} - {endTime}")
        return {
            "code": 200,
            "message": "日志清理成功",
            "data": {
                "clearedCount": 1000,
                "clearedSize": "500MB"
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"清理日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理日志失败: {str(e)}")
