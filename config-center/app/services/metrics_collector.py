"""
Prometheus指标收集服务
用于收集和存储访问日志、性能指标等时间序列数据
"""

import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class PrometheusMetricsCollector:
    """Prometheus指标收集器"""
    
    def __init__(self, prometheus_url: str = "http://prometheus:9090"):
        self.prometheus_url = prometheus_url
        self.registry = CollectorRegistry()
        self._init_metrics()
    
    def _init_metrics(self):
        """初始化所有指标"""
        
        # HTTP请求指标
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code', 'namespace', 'upstream'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'namespace', 'upstream'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
            registry=self.registry
        )
        
        # 业务指标
        self.namespace_requests_total = Counter(
            'namespace_requests_total',
            'Total number of requests per namespace',
            ['namespace', 'status'],
            registry=self.registry
        )
        
        self.namespace_tokens_total = Counter(
            'namespace_tokens_total',
            'Total tokens per namespace',
            ['namespace', 'token_type'],  # token_type: input/output
            registry=self.registry
        )
        
        self.upstream_requests_total = Counter(
            'upstream_requests_total',
            'Total number of requests per upstream',
            ['upstream', 'status'],
            registry=self.registry
        )
        
        self.policy_violations_total = Counter(
            'policy_violations_total',
            'Total number of policy violations',
            ['policy_type', 'namespace'],
            registry=self.registry
        )
        
        # 系统指标
        self.active_connections = Gauge(
            'active_connections',
            'Number of active connections',
            ['namespace'],
            registry=self.registry
        )
        
        self.response_time_p95 = Summary(
            'response_time_p95_seconds',
            '95th percentile response time',
            ['namespace'],
            registry=self.registry
        )
        
        # 缓存指标
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total number of cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total number of cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # 限流指标
        self.rate_limit_hits_total = Counter(
            'rate_limit_hits_total',
            'Total number of rate limit hits',
            ['namespace', 'rule_type'],
            registry=self.registry
        )
        
        self.rate_limit_violations_total = Counter(
            'rate_limit_violations_total',
            'Total number of rate limit violations',
            ['namespace', 'rule_type'],
            registry=self.registry
        )
        
        # 错误指标
        self.errors_total = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type', 'namespace', 'upstream'],
            registry=self.registry
        )
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, 
                           namespace: str = "default", upstream: str = "unknown", 
                           duration: float = 0.0):
        """记录HTTP请求指标"""
        try:
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code),
                namespace=namespace,
                upstream=upstream
            ).inc()
            
            if duration > 0:
                self.http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint,
                    namespace=namespace,
                    upstream=upstream
                ).observe(duration)
                
        except Exception as e:
            logger.error(f"记录HTTP请求指标失败: {str(e)}")
    
    def record_namespace_request(self, namespace: str, status: str = "success"):
        """记录命名空间请求指标"""
        try:
            self.namespace_requests_total.labels(
                namespace=namespace,
                status=status
            ).inc()
        except Exception as e:
            logger.error(f"记录命名空间请求指标失败: {str(e)}")
    
    def record_namespace_tokens(self, namespace: str, token_type: str, count: int):
        """记录命名空间Token指标"""
        try:
            self.namespace_tokens_total.labels(
                namespace=namespace,
                token_type=token_type
            ).inc(count)
        except Exception as e:
            logger.error(f"记录命名空间Token指标失败: {str(e)}")
    
    def record_upstream_request(self, upstream: str, status: str = "success"):
        """记录上游服务器请求指标"""
        try:
            self.upstream_requests_total.labels(
                upstream=upstream,
                status=status
            ).inc()
        except Exception as e:
            logger.error(f"记录上游服务器请求指标失败: {str(e)}")
    
    def record_policy_violation(self, policy_type: str, namespace: str):
        """记录策略违规指标"""
        try:
            self.policy_violations_total.labels(
                policy_type=policy_type,
                namespace=namespace
            ).inc()
        except Exception as e:
            logger.error(f"记录策略违规指标失败: {str(e)}")
    
    def set_active_connections(self, namespace: str, count: int):
        """设置活跃连接数"""
        try:
            self.active_connections.labels(namespace=namespace).set(count)
        except Exception as e:
            logger.error(f"设置活跃连接数失败: {str(e)}")
    
    def record_response_time_p95(self, namespace: str, response_time: float):
        """记录95分位响应时间"""
        try:
            self.response_time_p95.labels(namespace=namespace).observe(response_time)
        except Exception as e:
            logger.error(f"记录响应时间指标失败: {str(e)}")
    
    def record_cache_hit(self, cache_type: str):
        """记录缓存命中"""
        try:
            self.cache_hits_total.labels(cache_type=cache_type).inc()
        except Exception as e:
            logger.error(f"记录缓存命中失败: {str(e)}")
    
    def record_cache_miss(self, cache_type: str):
        """记录缓存未命中"""
        try:
            self.cache_misses_total.labels(cache_type=cache_type).inc()
        except Exception as e:
            logger.error(f"记录缓存未命中失败: {str(e)}")
    
    def record_rate_limit_hit(self, namespace: str, rule_type: str):
        """记录限流命中"""
        try:
            self.rate_limit_hits_total.labels(
                namespace=namespace,
                rule_type=rule_type
            ).inc()
        except Exception as e:
            logger.error(f"记录限流命中失败: {str(e)}")
    
    def record_rate_limit_violation(self, namespace: str, rule_type: str):
        """记录限流违规"""
        try:
            self.rate_limit_violations_total.labels(
                namespace=namespace,
                rule_type=rule_type
            ).inc()
        except Exception as e:
            logger.error(f"记录限流违规失败: {str(e)}")
    
    def record_error(self, error_type: str, namespace: str = "default", upstream: str = "unknown"):
        """记录错误指标"""
        try:
            self.errors_total.labels(
                error_type=error_type,
                namespace=namespace,
                upstream=upstream
            ).inc()
        except Exception as e:
            logger.error(f"记录错误指标失败: {str(e)}")
    
    def get_metrics(self) -> str:
        """获取所有指标的Prometheus格式"""
        try:
            return generate_latest(self.registry)
        except Exception as e:
            logger.error(f"获取指标失败: {str(e)}")
            return ""
    
    def push_metrics_to_prometheus(self):
        """推送指标到Prometheus"""
        try:
            metrics_data = self.get_metrics()
            if not metrics_data:
                return False
            
            response = requests.post(
                f"{self.prometheus_url}/api/v1/push",
                data=metrics_data,
                headers={'Content-Type': 'text/plain'},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug("指标推送成功")
                return True
            else:
                logger.error(f"指标推送失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"推送指标到Prometheus失败: {str(e)}")
            return False

# 全局指标收集器实例
metrics_collector = PrometheusMetricsCollector()

def get_metrics_collector() -> PrometheusMetricsCollector:
    """获取指标收集器实例"""
    return metrics_collector
