"""
指标收集中间件
用于在API请求时自动收集指标到Prometheus
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    """指标收集中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并收集指标"""
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        
        # 从请求头或路径中提取命名空间信息
        namespace = self._extract_namespace(request)
        upstream = self._extract_upstream(request)
        
        # 处理请求
        try:
            response = await call_next(request)
            status_code = response.status_code
            status = "success" if status_code < 400 else "error"
            
        except Exception as e:
            logger.error(f"请求处理失败: {str(e)}")
            status_code = 500
            status = "error"
            raise
        
        finally:
            # 计算响应时间
            duration = time.time() - start_time
            
            # 收集指标
            try:
                self.metrics_collector.record_http_request(
                    method=method,
                    endpoint=path,
                    status_code=status_code,
                    namespace=namespace,
                    upstream=upstream,
                    duration=duration
                )
                
                # 记录命名空间请求
                self.metrics_collector.record_namespace_request(namespace, status)
                
                # 记录上游服务器请求
                self.metrics_collector.record_upstream_request(upstream, status)
                
                # 记录错误
                if status_code >= 400:
                    error_type = self._get_error_type(status_code)
                    self.metrics_collector.record_error(error_type, namespace, upstream)
                
            except Exception as e:
                logger.error(f"收集指标失败: {str(e)}")
        
        return response
    
    def _extract_namespace(self, request: Request) -> str:
        """从请求中提取命名空间信息"""
        try:
            # 从请求头中获取
            namespace = request.headers.get("X-Namespace")
            if namespace:
                return namespace
            
            # 从路径中提取
            path = request.url.path
            if "/api/namespaces/" in path:
                # 从路径中提取namespace_id
                parts = path.split("/")
                if len(parts) > 3:
                    return f"namespace_{parts[3]}"
            
            # 从查询参数中获取
            namespace = request.query_params.get("namespace")
            if namespace:
                return namespace
            
            return "default"
            
        except Exception as e:
            logger.error(f"提取命名空间失败: {str(e)}")
            return "default"
    
    def _extract_upstream(self, request: Request) -> str:
        """从请求中提取上游服务器信息"""
        try:
            # 从请求头中获取
            upstream = request.headers.get("X-Upstream")
            if upstream:
                return upstream
            
            # 从路径中提取
            path = request.url.path
            if "/api/upstreams/" in path:
                # 从路径中提取upstream_id
                parts = path.split("/")
                if len(parts) > 3:
                    return f"upstream_{parts[3]}"
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"提取上游服务器失败: {str(e)}")
            return "unknown"
    
    def _get_error_type(self, status_code: int) -> str:
        """根据状态码获取错误类型"""
        if 400 <= status_code < 500:
            return "client_error"
        elif 500 <= status_code < 600:
            return "server_error"
        else:
            return "unknown_error"
