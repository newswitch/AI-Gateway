"""
Token服务中的Prometheus指标收集
用于收集大模型相关的指标数据
"""

import time
import logging
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY

logger = logging.getLogger(__name__)

class TokenServiceMetrics:
    """Token服务指标收集器"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self._init_metrics()
    
    def _init_metrics(self):
        """初始化所有指标"""
        
        # 模型请求指标
        self.model_requests_total = Counter(
            'model_requests_total',
            'Total model requests',
            ['model', 'namespace', 'status'],
            registry=self.registry
        )
        
        self.model_request_duration_seconds = Histogram(
            'model_request_duration_seconds',
            'Model request duration in seconds',
            ['model', 'namespace'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
            registry=self.registry
        )
        
        # Token使用指标
        self.model_tokens_input_total = Counter(
            'model_tokens_input_total',
            'Total input tokens',
            ['model', 'namespace'],
            registry=self.registry
        )
        
        self.model_tokens_output_total = Counter(
            'model_tokens_output_total',
            'Total output tokens',
            ['model', 'namespace'],
            registry=self.registry
        )
        
        self.model_tokens_per_second = Gauge(
            'model_tokens_per_second',
            'Tokens processed per second',
            ['model', 'namespace'],
            registry=self.registry
        )
        
        # 成本指标
        self.model_cost_usd_total = Counter(
            'model_cost_usd_total',
            'Total cost in USD',
            ['model', 'namespace'],
            registry=self.registry
        )
        
        # 性能指标
        self.model_throughput_requests_per_second = Gauge(
            'model_throughput_requests_per_second',
            'Requests processed per second',
            ['model', 'namespace'],
            registry=self.registry
        )
        
        # 错误指标
        self.model_errors_total = Counter(
            'model_errors_total',
            'Total model errors',
            ['model', 'namespace', 'error_type'],
            registry=self.registry
        )
        
        # 缓存指标
        self.model_cache_hits_total = Counter(
            'model_cache_hits_total',
            'Total model cache hits',
            ['model', 'namespace'],
            registry=self.registry
        )
        
        self.model_cache_misses_total = Counter(
            'model_cache_misses_total',
            'Total model cache misses',
            ['model', 'namespace'],
            registry=self.registry
        )
    
    def record_model_request(self, model: str, namespace: str, status: str = "success", duration: float = 0.0):
        """记录模型请求指标"""
        try:
            self.model_requests_total.labels(
                model=model,
                namespace=namespace,
                status=status
            ).inc()
            
            if duration > 0:
                self.model_request_duration_seconds.labels(
                    model=model,
                    namespace=namespace
                ).observe(duration)
                
        except Exception as e:
            logger.error(f"记录模型请求指标失败: {str(e)}")
    
    def record_tokens(self, model: str, namespace: str, input_tokens: int, output_tokens: int):
        """记录Token使用指标"""
        try:
            self.model_tokens_input_total.labels(
                model=model,
                namespace=namespace
            ).inc(input_tokens)
            
            self.model_tokens_output_total.labels(
                model=model,
                namespace=namespace
            ).inc(output_tokens)
                
        except Exception as e:
            logger.error(f"记录Token指标失败: {str(e)}")
    
    def record_cost(self, model: str, namespace: str, cost_usd: float):
        """记录成本指标"""
        try:
            self.model_cost_usd_total.labels(
                model=model,
                namespace=namespace
            ).inc(cost_usd)
                
        except Exception as e:
            logger.error(f"记录成本指标失败: {str(e)}")
    
    def record_throughput(self, model: str, namespace: str, requests_per_second: float):
        """记录吞吐量指标"""
        try:
            self.model_throughput_requests_per_second.labels(
                model=model,
                namespace=namespace
            ).set(requests_per_second)
                
        except Exception as e:
            logger.error(f"记录吞吐量指标失败: {str(e)}")
    
    def record_tokens_per_second(self, model: str, namespace: str, tokens_per_second: float):
        """记录每秒Token处理量"""
        try:
            self.model_tokens_per_second.labels(
                model=model,
                namespace=namespace
            ).set(tokens_per_second)
                
        except Exception as e:
            logger.error(f"记录Token处理速度指标失败: {str(e)}")
    
    def record_error(self, model: str, namespace: str, error_type: str):
        """记录错误指标"""
        try:
            self.model_errors_total.labels(
                model=model,
                namespace=namespace,
                error_type=error_type
            ).inc()
                
        except Exception as e:
            logger.error(f"记录错误指标失败: {str(e)}")
    
    def record_cache_hit(self, model: str, namespace: str):
        """记录缓存命中"""
        try:
            self.model_cache_hits_total.labels(
                model=model,
                namespace=namespace
            ).inc()
                
        except Exception as e:
            logger.error(f"记录缓存命中失败: {str(e)}")
    
    def record_cache_miss(self, model: str, namespace: str):
        """记录缓存未命中"""
        try:
            self.model_cache_misses_total.labels(
                model=model,
                namespace=namespace
            ).inc()
                
        except Exception as e:
            logger.error(f"记录缓存未命中失败: {str(e)}")
    
    def get_metrics(self) -> str:
        """获取所有指标的Prometheus格式"""
        try:
            return generate_latest(self.registry)
        except Exception as e:
            logger.error(f"获取指标失败: {str(e)}")
            return ""

# 全局指标收集器实例
metrics_collector = TokenServiceMetrics()

def get_metrics_collector() -> TokenServiceMetrics:
    """获取指标收集器实例"""
    return metrics_collector
