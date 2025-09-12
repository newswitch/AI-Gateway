"""
Prometheus查询服务
用于从Prometheus获取指标数据，替代MySQL中的监控数据查询
"""

import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class PrometheusQueryService:
    """Prometheus查询服务"""
    
    def __init__(self, prometheus_url: str = "http://prometheus:9090"):
        self.prometheus_url = prometheus_url
    
    def _query_prometheus(self, query: str, start_time: Optional[str] = None, 
                         end_time: Optional[str] = None, step: str = "1m") -> Dict[str, Any]:
        """查询Prometheus"""
        try:
            params = {
                'query': query
            }
            
            if start_time and end_time:
                params['start'] = start_time
                params['end'] = end_time
                params['step'] = step
            
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Prometheus查询失败: {response.status_code}")
                return {"status": "error", "data": {"result": []}}
                
        except Exception as e:
            logger.error(f"查询Prometheus失败: {str(e)}")
            return {"status": "error", "data": {"result": []}}
    
    def get_namespace_request_trend(self, namespace: str = "all", 
                                   time_range: str = "today") -> Dict[str, Any]:
        """获取命名空间请求趋势"""
        try:
            # 计算时间范围
            now = datetime.now()
            if time_range == "today":
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = now
                step = "1h"
            elif time_range == "week":
                start_time = now - timedelta(days=7)
                end_time = now
                step = "1d"
            else:  # month
                start_time = now - timedelta(days=30)
                end_time = now
                step = "1d"
            
            # 构建查询语句
            if namespace == "all":
                query = 'sum(rate(namespace_requests_total[5m])) by (namespace)'
            else:
                query = f'rate(namespace_requests_total{{namespace="{namespace}"}}[5m])'
            
            result = self._query_prometheus(
                query,
                start_time.isoformat(),
                end_time.isoformat(),
                step
            )
            
            return self._format_trend_data(result, time_range)
            
        except Exception as e:
            logger.error(f"获取命名空间请求趋势失败: {str(e)}")
            return {"labels": [], "datasets": []}
    
    def get_namespace_token_usage(self, namespace: str, time_range: str = "today") -> Dict[str, Any]:
        """获取命名空间Token使用情况"""
        try:
            # 计算时间范围
            now = datetime.now()
            if time_range == "today":
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = now
                step = "1h"
            elif time_range == "week":
                start_time = now - timedelta(days=7)
                end_time = now
                step = "1d"
            else:  # month
                start_time = now - timedelta(days=30)
                end_time = now
                step = "1d"
            
            # 查询输入Token
            input_query = f'namespace_tokens_total{{namespace="{namespace}", token_type="input"}}'
            input_result = self._query_prometheus(
                input_query,
                start_time.isoformat(),
                end_time.isoformat(),
                step
            )
            
            # 查询输出Token
            output_query = f'namespace_tokens_total{{namespace="{namespace}", token_type="output"}}'
            output_result = self._query_prometheus(
                output_query,
                start_time.isoformat(),
                end_time.isoformat(),
                step
            )
            
            return self._format_token_data(input_result, output_result, time_range)
            
        except Exception as e:
            logger.error(f"获取命名空间Token使用情况失败: {str(e)}")
            return {"labels": [], "datasets": []}
    
    def get_namespace_status_distribution(self) -> Dict[str, Any]:
        """获取命名空间状态分布"""
        try:
            # 查询启用的命名空间
            enabled_query = 'sum(namespace_requests_total{status="success"}) by (namespace)'
            enabled_result = self._query_prometheus(enabled_query)
            
            # 查询禁用的命名空间
            disabled_query = 'sum(namespace_requests_total{status="error"}) by (namespace)'
            disabled_result = self._query_prometheus(disabled_query)
            
            return self._format_status_distribution(enabled_result, disabled_result)
            
        except Exception as e:
            logger.error(f"获取命名空间状态分布失败: {str(e)}")
            return {"labels": [], "data": []}
    
    def get_namespace_metrics(self, namespace: str) -> Dict[str, Any]:
        """获取命名空间详细指标"""
        try:
            # 查询请求总数
            requests_query = f'sum(namespace_requests_total{{namespace="{namespace}"}})'
            requests_result = self._query_prometheus(requests_query)
            
            # 查询成功率
            success_rate_query = f'sum(namespace_requests_total{{namespace="{namespace}", status="success"}}) / sum(namespace_requests_total{{namespace="{namespace}"}}) * 100'
            success_rate_result = self._query_prometheus(success_rate_query)
            
            # 查询平均响应时间
            response_time_query = f'avg(http_request_duration_seconds{{namespace="{namespace}"}})'
            response_time_result = self._query_prometheus(response_time_query)
            
            # 查询Token使用量
            input_tokens_query = f'sum(namespace_tokens_total{{namespace="{namespace}", token_type="input"}})'
            input_tokens_result = self._query_prometheus(input_tokens_query)
            
            output_tokens_query = f'sum(namespace_tokens_total{{namespace="{namespace}", token_type="output"}})'
            output_tokens_result = self._query_prometheus(output_tokens_query)
            
            return {
                "requestCount": self._extract_value(requests_result, 0),
                "successRate": f"{self._extract_value(success_rate_result, 0):.1f}%",
                "avgResponseTime": f"{self._extract_value(response_time_result, 0):.2f}s",
                "inputTokens": int(self._extract_value(input_tokens_result, 0)),
                "outputTokens": int(self._extract_value(output_tokens_result, 0))
            }
            
        except Exception as e:
            logger.error(f"获取命名空间指标失败: {str(e)}")
            return {}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            # 查询总请求数
            total_requests_query = 'sum(http_requests_total)'
            total_requests_result = self._query_prometheus(total_requests_query)
            
            # 查询错误率
            error_rate_query = 'sum(http_requests_total{status_code=~"5.."}) / sum(http_requests_total) * 100'
            error_rate_result = self._query_prometheus(error_rate_query)
            
            # 查询平均响应时间
            avg_response_time_query = 'avg(http_request_duration_seconds)'
            avg_response_time_result = self._query_prometheus(avg_response_time_query)
            
            # 查询QPS
            qps_query = 'sum(rate(http_requests_total[1m]))'
            qps_result = self._query_prometheus(qps_query)
            
            return {
                "totalRequests": int(self._extract_value(total_requests_result, 0)),
                "errorRate": f"{self._extract_value(error_rate_result, 0):.2f}%",
                "avgResponseTime": f"{self._extract_value(avg_response_time_result, 0):.2f}s",
                "qps": f"{self._extract_value(qps_result, 0):.1f}"
            }
            
        except Exception as e:
            logger.error(f"获取系统指标失败: {str(e)}")
            return {}
    
    def _format_trend_data(self, result: Dict[str, Any], time_range: str) -> Dict[str, Any]:
        """格式化趋势数据"""
        try:
            if result.get("status") != "success":
                return {"labels": [], "datasets": []}
            
            data = result.get("data", {})
            result_list = data.get("result", [])
            
            if not result_list:
                return {"labels": [], "datasets": []}
            
            # 生成时间标签
            if time_range == "today":
                labels = [f"{i:02d}:00" for i in range(0, 24, 3)]
            elif time_range == "week":
                labels = [(datetime.now() - timedelta(days=6-i)).strftime("%m-%d") for i in range(7)]
            else:  # month
                labels = [(datetime.now() - timedelta(days=29-i)).strftime("%m-%d") for i in range(0, 30, 5)]
            
            # 处理数据
            datasets = []
            for item in result_list:
                metric = item.get("metric", {})
                values = item.get("values", [])
                
                namespace = metric.get("namespace", "unknown")
                data_points = [float(v[1]) if v[1] != "NaN" else 0 for v in values]
                
                datasets.append({
                    "label": namespace,
                    "data": data_points,
                    "borderColor": self._get_color(len(datasets)),
                    "backgroundColor": self._get_color(len(datasets), alpha=0.1)
                })
            
            return {
                "labels": labels,
                "datasets": datasets
            }
            
        except Exception as e:
            logger.error(f"格式化趋势数据失败: {str(e)}")
            return {"labels": [], "datasets": []}
    
    def _format_token_data(self, input_result: Dict[str, Any], output_result: Dict[str, Any], 
                          time_range: str) -> Dict[str, Any]:
        """格式化Token数据"""
        try:
            # 生成时间标签
            if time_range == "today":
                labels = [f"{i:02d}:00" for i in range(0, 24, 3)]
            elif time_range == "week":
                labels = [(datetime.now() - timedelta(days=6-i)).strftime("%m-%d") for i in range(7)]
            else:  # month
                labels = [(datetime.now() - timedelta(days=29-i)).strftime("%m-%d") for i in range(0, 30, 5)]
            
            # 处理输入Token数据
            input_data = self._extract_time_series_data(input_result)
            output_data = self._extract_time_series_data(output_result)
            
            datasets = [
                {
                    "label": "输入Token",
                    "data": input_data,
                    "borderColor": "#3b82f6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)"
                },
                {
                    "label": "输出Token",
                    "data": output_data,
                    "borderColor": "#10b981",
                    "backgroundColor": "rgba(16, 185, 129, 0.1)"
                }
            ]
            
            return {
                "labels": labels,
                "datasets": datasets
            }
            
        except Exception as e:
            logger.error(f"格式化Token数据失败: {str(e)}")
            return {"labels": [], "datasets": []}
    
    def _format_status_distribution(self, enabled_result: Dict[str, Any], 
                                   disabled_result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化状态分布数据"""
        try:
            enabled_count = len(enabled_result.get("data", {}).get("result", []))
            disabled_count = len(disabled_result.get("data", {}).get("result", []))
            
            return {
                "labels": ["启用", "禁用"],
                "data": [enabled_count, disabled_count]
            }
            
        except Exception as e:
            logger.error(f"格式化状态分布数据失败: {str(e)}")
            return {"labels": [], "data": []}
    
    def _extract_value(self, result: Dict[str, Any], default: float = 0) -> float:
        """从Prometheus结果中提取数值"""
        try:
            if result.get("status") != "success":
                return default
            
            data = result.get("data", {})
            result_list = data.get("result", [])
            
            if not result_list:
                return default
            
            # 对于即时查询，取第一个值
            if "value" in result_list[0]:
                return float(result_list[0]["value"][1])
            
            # 对于范围查询，取最后一个值
            if "values" in result_list[0]:
                values = result_list[0]["values"]
                if values:
                    return float(values[-1][1])
            
            return default
            
        except Exception as e:
            logger.error(f"提取数值失败: {str(e)}")
            return default
    
    def _extract_time_series_data(self, result: Dict[str, Any]) -> List[float]:
        """提取时间序列数据"""
        try:
            if result.get("status") != "success":
                return [0] * 8  # 默认8个数据点
            
            data = result.get("data", {})
            result_list = data.get("result", [])
            
            if not result_list:
                return [0] * 8
            
            values = result_list[0].get("values", [])
            return [float(v[1]) if v[1] != "NaN" else 0 for v in values]
            
        except Exception as e:
            logger.error(f"提取时间序列数据失败: {str(e)}")
            return [0] * 8
    
    def _get_color(self, index: int, alpha: float = 1.0) -> str:
        """获取颜色"""
        colors = [
            "#3b82f6",  # blue
            "#10b981",  # green
            "#f59e0b",  # yellow
            "#ef4444",  # red
            "#8b5cf6",  # purple
            "#06b6d4",  # cyan
            "#f97316",  # orange
            "#84cc16"   # lime
        ]
        
        color = colors[index % len(colors)]
        if alpha < 1.0:
            return f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, {alpha})"
        return color

# 全局查询服务实例
query_service = PrometheusQueryService()

def get_prometheus_query_service() -> PrometheusQueryService:
    """获取Prometheus查询服务实例"""
    return query_service
