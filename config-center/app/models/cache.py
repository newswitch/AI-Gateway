"""
缓存管理器 - Redis操作
"""

import json
import logging
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

def safe_json_dumps(data, **kwargs):
    """安全的JSON序列化，确保中文字符正确编码"""
    json_str = json.dumps(data, indent=2, ensure_ascii=False, **kwargs)
    return json_str.encode('utf-8')
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class ConfigCache:
    """配置缓存管理器 - Redis + MySQL双写"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self.db_manager = None  # 数据库管理器引用
        
        # 缓存配置
        self.cache_ttl = {
            'namespace': 3600,           # 命名空间缓存1小时
            'matchers': 3600,            # 匹配器缓存1小时
            'location_rules': 1800,      # 路由规则缓存30分钟（原 matchers + proxy_rules）
            'policies': 1800,            # 策略配置缓存30分钟（原 rules）
            'upstream_servers': 1800,    # 上游服务器缓存30分钟（原 upstream）
            'system_configs': 7200,      # 系统配置缓存2小时（原 nginx_config）
            'monitoring_metrics': 300,   # 监控指标缓存5分钟（新增）
            'access_logs': 600,          # 访问日志缓存10分钟
            'dashboard': 60,             # 仪表盘数据缓存1分钟
            'auth': 3600,                # 认证信息缓存1小时
            'stats': 300                 # 统计数据缓存5分钟
        }
    
    async def connect(self):
        """连接Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            raise
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _get_cache_key(self, data_type: str, data_id: str) -> str:
        """生成缓存键"""
        return f"config:{data_type}:{data_id}"
    
    def _get_list_cache_key(self, data_type: str, filters: Dict = None) -> str:
        """生成列表缓存键"""
        if filters:
            filter_str = ":".join([f"{k}={v}" for k, v in sorted(filters.items())])
            return f"config:{data_type}:list:{filter_str}"
        return f"config:{data_type}:list"
    
    async def set_namespace(self, namespace_id: int, namespace_data: Dict, ttl: int = None):
        """设置命名空间缓存"""
        try:
            cache_key = self._get_cache_key("namespaces", str(namespace_id))
            await self.redis_client.set(cache_key, json.dumps(namespace_data, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['namespace'])
            
            # 异步写入MySQL（如果数据库管理器可用）
            if self.db_manager:
                asyncio.create_task(self._write_namespace_to_mysql(namespace_data))
                
        except Exception as e:
            logger.error(f"设置命名空间缓存失败: {str(e)}")
    
    async def get_namespace(self, namespace_id: int) -> Optional[Dict]:
        """获取命名空间缓存 - 缓存优先策略"""
        try:
            cache_key = self._get_cache_key("namespaces", str(namespace_id))
            data = await self.redis_client.get(cache_key)
            
            if data:
                return json.loads(data)
            
            # 缓存未命中，从MySQL读取
            if self.db_manager:
                namespace = await self.db_manager.get_namespace(namespace_id)
                if namespace:
                    # 异步更新缓存
                    asyncio.create_task(self.set_namespace(namespace_id, namespace))
                    return namespace
            
            return None
            
        except Exception as e:
            logger.error(f"获取命名空间缓存失败: {str(e)}")
            # 降级到MySQL
            if self.db_manager:
                return await self.db_manager.get_namespace(namespace_id)
            return None
    
    async def _write_namespace_to_mysql(self, namespace_data: Dict):
        """异步写入命名空间到MySQL"""
        try:
            if 'namespace_id' in namespace_data:
                # 更新现有命名空间
                await self.db_manager.update_namespace(namespace_data['namespace_id'], namespace_data)
            else:
                # 创建新命名空间
                await self.db_manager.create_namespace(namespace_data)
        except Exception as e:
            logger.error(f"异步写入命名空间到MySQL失败: {str(e)}")
    
    async def set_matchers(self, namespace_id: int, matchers: List[Dict], ttl: int = None):
        """设置报文匹配器缓存"""
        try:
            cache_key = self._get_cache_key("matchers", str(namespace_id))
            # 使用安全的JSON编码
            await self.redis_client.set(cache_key, safe_json_dumps(matchers), ex=ttl or self.cache_ttl['matchers'])
            
        except Exception as e:
            logger.error(f"设置报文匹配器缓存失败: {str(e)}")
    
    async def get_matchers(self, namespace_id: int) -> List[Dict]:
        """获取报文匹配器缓存 - 缓存优先策略"""
        try:
            cache_key = self._get_cache_key("matchers", str(namespace_id))
            data = await self.redis_client.get(cache_key)
            
            if data:
                return json.loads(data)
            
            # 缓存未命中，从MySQL读取
            if self.db_manager:
                matchers = await self.db_manager.get_matchers_by_namespace(namespace_id)
                if matchers:
                    # 异步更新缓存
                    asyncio.create_task(self.set_matchers(namespace_id, matchers))
                    return matchers
            
            return []
            
        except Exception as e:
            logger.error(f"获取报文匹配器缓存失败: {str(e)}")
            # 降级到MySQL
            if self.db_manager:
                return await self.db_manager.get_matchers_by_namespace(namespace_id)
            return []
    
    async def set_rules(self, namespace_id: int, rules: List[Dict], ttl: int = None):
        """设置命名空间规则缓存 - 支持配置变更时重置计数器"""
        try:
            cache_key = self._get_cache_key("rules", str(namespace_id))
            
            # 检查配置是否发生变化
            old_rules = await self.get_rules(namespace_id)
            config_changed = await self._detect_config_changes(old_rules, rules)
            
            # 更新规则缓存
            await self.redis_client.set(cache_key, json.dumps(rules, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['policies'])
            
            # 如果配置发生变化，重置相关计数器
            if config_changed:
                await self._reset_counters_on_config_change(namespace_id, rules)
                logger.info(f"配置变更检测到，已重置命名空间 {namespace_id} 的计数器")
            
        except Exception as e:
            logger.error(f"设置命名空间规则缓存失败: {str(e)}")
    
    async def _detect_config_changes(self, old_rules: List[Dict], new_rules: List[Dict]) -> bool:
        """检测配置是否发生变化"""
        try:
            if not old_rules:
                return True  # 新规则，视为配置变更
            
            # 创建规则映射，便于比较
            old_rules_map = {rule['rule_id']: rule for rule in old_rules}
            new_rules_map = {rule['rule_id']: rule for rule in new_rules}
            
            # 检查规则数量变化
            if len(old_rules) != len(new_rules):
                return True
            
            # 检查每个规则的变化
            for rule_id, new_rule in new_rules_map.items():
                old_rule = old_rules_map.get(rule_id)
                if not old_rule:
                    return True  # 新规则
                
                # 比较规则配置
                if (old_rule.get('rule_config') != new_rule.get('rule_config') or
                    old_rule.get('priority') != new_rule.get('priority') or
                    old_rule.get('status') != new_rule.get('status')):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"检测配置变更失败: {str(e)}")
            return False
    
    async def _reset_counters_on_config_change(self, namespace_id: int, rules: List[Dict]):
        """配置变更时重置计数器"""
        try:
            current_time = int(time.time())
            
            for rule in rules:
                if rule.get('rule_type') in ['token_limit', 'qps_limit', 'concurrent_limit']:
                    rule_id = rule['rule_id']
                    
                    # 重置Token计数器
                    if rule['rule_type'] == 'token_limit':
                        await self._reset_token_counters(namespace_id, rule_id, current_time)
                    
                    # 重置QPS计数器
                    if rule['rule_type'] == 'qps_limit':
                        await self._reset_qps_counters(namespace_id, rule_id, current_time)
                    
                    # 重置并发计数器
                    if rule['rule_type'] == 'concurrent_limit':
                        await self._reset_concurrent_counters(namespace_id, rule_id, current_time)
            
            logger.info(f"命名空间 {namespace_id} 的计数器重置完成")
            
        except Exception as e:
            logger.error(f"重置计数器失败: {str(e)}")
    
    async def _reset_token_counters(self, namespace_id: int, rule_id: int, current_time: int):
        """重置Token计数器"""
        try:
            # 创建新的Token计数器键
            hour_key = f"rate_limit:{namespace_id}:{rule_id}:hour:{current_time}"
            day_key = f"rate_limit:{namespace_id}:{rule_id}:day:{current_time}"
            
            # 重置计数器
            await self.redis_client.set(hour_key, "0")
            await self.redis_client.set(day_key, "0")
            
            # 设置过期时间
            await self.redis_client.expire(hour_key, 7200)  # 2小时
            await self.redis_client.expire(day_key, 172800)  # 2天
            
            # 清理旧的Token计数器
            await self._cleanup_old_counters(f"rate_limit:{namespace_id}:{rule_id}:hour:*", [hour_key])
            await self._cleanup_old_counters(f"rate_limit:{namespace_id}:{rule_id}:day:*", [day_key])
            
        except Exception as e:
            logger.error(f"重置Token计数器失败: {str(e)}")
    
    async def _reset_qps_counters(self, namespace_id: int, rule_id: int, current_time: int):
        """重置QPS计数器"""
        try:
            # 创建新的QPS计数器键（使用新的格式，支持配置变更重置）
            minute_key = f"rate_limit:{namespace_id}:qps:{current_time}"
            
            # 重置计数器
            await self.redis_client.set(minute_key, "0")
            
            # 设置过期时间
            await self.redis_client.expire(minute_key, 120)  # 2分钟
            
            # 清理旧的QPS计数器
            await self._cleanup_old_counters(f"rate_limit:{namespace_id}:*:minute:*", [minute_key])
            await self._cleanup_old_counters(f"rate_limit:{namespace_id}:*:qps:*", [minute_key])
            
        except Exception as e:
            logger.error(f"重置QPS计数器失败: {str(e)}")
    
    async def _reset_concurrent_counters(self, namespace_id: int, rule_id: int, current_time: int):
        """重置并发计数器"""
        try:
            # 创建新的并发计数器键
            concurrent_key = f"concurrent:{namespace_id}:current"
            
            # 重置计数器
            await self.redis_client.set(concurrent_key, "0")
            
            # 清理旧的并发计数器
            await self._cleanup_old_counters(f"concurrent:{namespace_id}:*", [concurrent_key])
            
        except Exception as e:
            logger.error(f"重置并发计数器失败: {str(e)}")
    
    async def _cleanup_old_counters(self, pattern: str, exclude_keys: List[str]):
        """清理旧的计数器"""
        try:
            exclude_set = set(exclude_keys)
            
            # 获取匹配的键
            keys = await self.redis_client.keys(pattern)
            for key in keys:
                if key not in exclude_set:
                    await self.redis_client.delete(key)
                    
        except Exception as e:
            logger.error(f"清理旧计数器失败: {str(e)}")
    
    async def get_rules(self, namespace_id: int) -> List[Dict]:
        """获取命名空间规则缓存 - 缓存优先策略"""
        try:
            cache_key = self._get_cache_key("rules", str(namespace_id))
            data = await self.redis_client.get(cache_key)
            
            if data:
                return json.loads(data)
            
            # 缓存未命中，从MySQL读取
            if self.db_manager:
                rules = await self.db_manager.get_rules_by_namespace(namespace_id)
                if rules:
                    # 异步更新缓存
                    asyncio.create_task(self.set_rules(namespace_id, rules))
                    return rules
            
            return []
            
        except Exception as e:
            logger.error(f"获取命名空间规则缓存失败: {str(e)}")
            # 降级到MySQL
            if self.db_manager:
                return await self.db_manager.get_rules_by_namespace(namespace_id)
            return []
    
    async def set_upstream_server(self, server_id: int, server_data: Dict, ttl: int = None):
        """设置上游服务器缓存"""
        try:
            cache_key = self._get_cache_key("upstream", str(server_id))
            await self.redis_client.set(cache_key, json.dumps(server_data, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['upstream_servers'])
        except Exception as e:
            logger.error(f"设置上游服务器缓存失败: {str(e)}")
    
    async def get_upstream_server(self, server_id: int) -> Optional[Dict]:
        """获取上游服务器缓存 - 缓存优先策略"""
        try:
            cache_key = self._get_cache_key("upstream", str(server_id))
            data = await self.redis_client.get(cache_key)
            
            if data:
                return json.loads(data)
            
            # 缓存未命中，从MySQL读取
            if self.db_manager:
                server = await self.db_manager.get_upstream_server(server_id)
                if server:
                    # 异步更新缓存
                    asyncio.create_task(self.set_upstream_server(server_id, server))
                    return server
            
            return None
            
        except Exception as e:
            logger.error(f"获取上游服务器缓存失败: {str(e)}")
            # 降级到MySQL
            if self.db_manager:
                return await self.db_manager.get_upstream_server(server_id)
            return None
    
    async def preload_namespace_data(self, namespace_id: int):
        """预加载命名空间的所有相关数据"""
        """预加载命名空间的所有相关数据"""
        try:
            if not self.db_manager:
                return
            
            # 并行加载所有相关数据
            tasks = []
            
            # 加载命名空间
            namespace_task = self.db_manager.get_namespace(namespace_id)
            tasks.append(namespace_task)
            
            # 加载匹配器
            matchers_task = self.db_manager.get_matchers_by_namespace(namespace_id)
            tasks.append(matchers_task)
            
            # 加载规则
            rules_task = self.db_manager.get_rules_by_namespace(namespace_id)
            tasks.append(rules_task)
            
            # 并行执行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 更新缓存
            cache_tasks = []
            
            if not isinstance(results[0], Exception) and results[0]:
                cache_tasks.append(self.set_namespace(namespace_id, results[0]))
            
            if not isinstance(results[1], Exception) and results[1]:
                cache_tasks.append(self.set_matchers(namespace_id, results[1]))
            
            if not isinstance(results[2], Exception) and results[2]:
                cache_tasks.append(self.set_rules(namespace_id, results[2]))
            
            if cache_tasks:
                await asyncio.gather(*cache_tasks, return_exceptions=True)
            
            logger.info(f"命名空间 {namespace_id} 数据预加载完成")
            
        except Exception as e:
            logger.error(f"预加载命名空间数据失败: {str(e)}")
    
    async def batch_get_namespaces(self, namespace_ids: List[int]) -> Dict[int, Dict]:
        """批量获取命名空间数据"""
        try:
            # 批量从Redis获取
            cache_keys = [self._get_cache_key("namespaces", str(ns_id)) for ns_id in namespace_ids]
            cache_results = await self.redis_client.mget(cache_keys)
            
            result = {}
            missing_ids = []
            
            # 处理缓存结果
            for i, (ns_id, cache_data) in enumerate(zip(namespace_ids, cache_results)):
                if cache_data:
                    result[ns_id] = json.loads(cache_data)
                else:
                    missing_ids.append(ns_id)
            
            # 从MySQL获取缺失的数据
            if missing_ids and self.db_manager:
                for ns_id in missing_ids:
                    namespace = await self.db_manager.get_namespace(ns_id)
                    if namespace:
                        result[ns_id] = namespace
                        # 异步更新缓存
                        asyncio.create_task(self.set_namespace(ns_id, namespace))
            
            return result
            
        except Exception as e:
            logger.error(f"批量获取命名空间失败: {str(e)}")
            return {}
    
    async def increment_counter(self, counter_key: str, ttl: int = 3600) -> int:
        """增加计数器"""
        try:
            # 使用Redis的INCR命令
            value = await self.redis_client.incr(counter_key)
            
            # 设置过期时间（如果还没有设置）
            await self.redis_client.expire(counter_key, ttl)
            
            return value
            
        except Exception as e:
            logger.error(f"增加计数器失败: {str(e)}")
            return 0
    
    async def get_counter(self, counter_key: str) -> int:
        """获取计数器值"""
        try:
            value = await self.redis_client.get(counter_key)
            return int(value) if value else 0
            
        except Exception as e:
            logger.error(f"获取计数器失败: {str(e)}")
            return 0
    
    async def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        try:
            info = await self.redis_client.info()
            return {
                'redis_version': info.get('redis_version'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'uptime_in_seconds': info.get('uptime_in_seconds')
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {str(e)}")
            return {}
    
    async def sync_from_mysql(self) -> bool:
        """从MySQL同步数据到Redis"""
        if not self.db_manager:
            logger.warning("数据库管理器未初始化，无法同步")
            return False
        
        try:
            logger.info("开始同步数据库配置到Redis...")
            
            # 获取命名空间和匹配器数据（不单独缓存）
            namespaces = await self.db_manager.get_all_namespaces()
            matchers = await self.db_manager.get_all_matchers()
            
            # 获取其他配置数据（不单独缓存）
            rules = await self.db_manager.get_all_rules()
            upstream_servers = await self.db_manager.get_all_upstream_servers()
            location_rules = await self.db_manager.get_all_location_rules()
            policies = await self.db_manager.get_all_policies()
            
            # 存储配置数据（网关需要的格式）
            if upstream_servers:
                await self.redis_client.set("config:upstreams:all", json.dumps(upstream_servers, indent=2, ensure_ascii=False), ex=self.cache_ttl['upstream_servers'])
            
            if location_rules:
                await self.redis_client.set("config:locations:all", json.dumps(location_rules, indent=2, ensure_ascii=False), ex=self.cache_ttl['location_rules'])
            
            if policies:
                await self.redis_client.set("config:policies:all", json.dumps(policies, indent=2, ensure_ascii=False), ex=self.cache_ttl['policies'])
                
                # 为每个策略创建基于namespace_code的单独key
                for policy in policies:
                    namespace_id = policy.get('namespace_id')
                    if namespace_id:
                        # 根据namespace_id找到对应的namespace_code
                        namespace_code = None
                        for namespace in namespaces:
                            if namespace['namespace_id'] == namespace_id:
                                namespace_code = namespace.get('namespace_code')
                                break
                        
                        if namespace_code:
                            key = f"config:policies:{namespace_code}"
                            await self.redis_client.set(key, json.dumps(policy, indent=2, ensure_ascii=False), ex=self.cache_ttl['policies'])
            
            # 将匹配器信息嵌入到命名空间数据中，并创建基于匹配值的键
            if namespaces and matchers:
                # 创建匹配器映射
                matchers_by_namespace = {}
                for matcher in matchers:
                    namespace_id = matcher['namespace_id']
                    if namespace_id not in matchers_by_namespace:
                        matchers_by_namespace[namespace_id] = []
                    matchers_by_namespace[namespace_id].append(matcher)
                
                # 为每个命名空间添加匹配器信息
                for namespace in namespaces:
                    namespace_id = namespace['namespace_id']
                    if namespace_id in matchers_by_namespace:
                        # 取第一个匹配器（一对一关系）
                        namespace['matcher'] = matchers_by_namespace[namespace_id][0]
                    else:
                        namespace['matcher'] = None
                
                # 存储合并后的命名空间列表（网关需要的格式）
                await self.redis_client.set("config:namespaces:all", json.dumps(namespaces, indent=2, ensure_ascii=False), ex=self.cache_ttl['namespace'])
                
                # 为每个命名空间创建基于namespace_code的单独key
                for namespace in namespaces:
                    namespace_code = namespace.get('namespace_code')
                    if namespace_code:
                        key = f"config:namespaces:{namespace_code}"
                        await self.redis_client.set(key, json.dumps(namespace, indent=2, ensure_ascii=False), ex=self.cache_ttl['namespace'])
                
            elif namespaces:
                # 如果没有匹配器，也要存储命名空间
                for namespace in namespaces:
                    namespace['matcher'] = None
                await self.redis_client.set("config:namespaces:all", json.dumps(namespaces, indent=2, ensure_ascii=False), ex=self.cache_ttl['namespace'])
                
                # 为每个命名空间创建基于namespace_code的单独key
                for namespace in namespaces:
                    namespace_code = namespace.get('namespace_code')
                    if namespace_code:
                        key = f"config:namespaces:{namespace_code}"
                        await self.redis_client.set(key, json.dumps(namespace, indent=2, ensure_ascii=False), ex=self.cache_ttl['namespace'])
            
            logger.info(f"成功同步 {len(namespaces)} 个命名空间, {len(matchers)} 个匹配器, {len(rules)} 个规则, {len(upstream_servers)} 个上游服务器, {len(location_rules)} 个路由规则, {len(policies)} 个策略到Redis")
            return True
            
        except Exception as e:
            logger.error(f"同步数据库配置到Redis失败: {str(e)}")
            return False
    

    async def create_namespace_dual_write(self, namespace_data: Dict[str, Any]) -> int:
        """双写创建命名空间 - Redis和MySQL并行写入"""
        try:
            # 并行执行Redis和MySQL写入
            tasks = []
            
            # MySQL写入任务
            if self.db_manager:
                mysql_task = self.db_manager.create_namespace(namespace_data)
                tasks.append(mysql_task)
            
            # Redis写入任务（临时存储，等待MySQL返回ID）
            temp_key = f"temp:namespace:{datetime.now().timestamp()}"
            redis_task = self.redis_client.set(temp_key, json.dumps(namespace_data, indent=2, ensure_ascii=False), ex=60)
            tasks.append(redis_task)
            
            # 并行执行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            namespace_id = None
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"写入失败: {str(result)}")
                elif i == 0 and self.db_manager:  # MySQL结果
                    namespace_id = result
                elif i == 1:  # Redis结果
                    # Redis写入成功，删除临时键
                    await self.redis_client.delete(temp_key)
            
            if namespace_id:
                # 使用MySQL返回的ID更新Redis
                namespace_data['namespace_id'] = namespace_id
                await self.set_namespace(namespace_id, namespace_data)
                
                # 自动创建默认的消息匹配器
                await self._create_default_matcher(namespace_id, namespace_data)
                
                return namespace_id
            else:
                raise Exception("MySQL写入失败")
                
        except Exception as e:
            logger.error(f"双写创建命名空间失败: {str(e)}")
            raise
    
    async def _create_default_matcher(self, namespace_id: int, namespace_data: Dict[str, Any]):
        """为命名空间创建默认的消息匹配器"""
        try:
            if not self.db_manager:
                return
                
            # 根据命名空间代码创建默认匹配器
            namespace_code = namespace_data.get('namespace_code', '')
            namespace_name = namespace_data.get('namespace_name', '')
            
            # 检查是否有前端传递的匹配器配置
            matcher_config = namespace_data.get('matcher_config', {})
            
            # 创建基于命名空间代码的默认匹配器
            matcher_data = {
                'namespace_id': namespace_id,
                'matcher_name': f'{namespace_name}渠道匹配',
                'matcher_type': matcher_config.get('matcher_type', 'header'),
                'match_field': matcher_config.get('match_field', 'channelcode'),
                'match_operator': matcher_config.get('match_operator', 'equals'),
                'match_value': matcher_config.get('match_value', namespace_code),
                'priority': matcher_config.get('priority', 100),
                'status': 1
            }
            
            # 创建匹配器
            matcher_id = await self.db_manager.create_matcher(matcher_data)
            
            # 更新缓存
            matchers = await self.db_manager.get_matchers_by_namespace(namespace_id)
            await self.set_matchers(namespace_id, matchers)
            
            logger.info(f"为命名空间 {namespace_id} 创建默认匹配器成功，matcher_id={matcher_id}")
            
        except Exception as e:
            logger.error(f"创建默认匹配器失败: {str(e)}")
            # 不抛出异常，避免影响命名空间创建
    
    async def update_namespace_dual_write(self, namespace_id: int, namespace_data: Dict[str, Any]) -> bool:
        """双写更新命名空间 - Redis和MySQL并行更新"""
        try:
            # 添加ID到数据中
            namespace_data['namespace_id'] = namespace_id
            
            # 并行执行Redis和MySQL更新
            tasks = []
            
            # MySQL更新任务
            if self.db_manager:
                mysql_task = self.db_manager.update_namespace(namespace_id, namespace_data)
                tasks.append(mysql_task)
            
            # Redis更新任务
            redis_task = self.set_namespace(namespace_id, namespace_data)
            tasks.append(redis_task)
            
            # 并行执行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查结果
            mysql_success = True
            redis_success = True
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"更新失败: {str(result)}")
                    if i == 0:  # MySQL
                        mysql_success = False
                    elif i == 1:  # Redis
                        redis_success = False
            
            # 如果MySQL成功但Redis失败，重试Redis
            if mysql_success and not redis_success:
                logger.warning("MySQL更新成功但Redis更新失败，重试Redis更新")
                try:
                    await self.set_namespace(namespace_id, namespace_data)
                    redis_success = True
                except Exception as e:
                    logger.error(f"Redis重试更新失败: {str(e)}")
            
            return mysql_success and redis_success
            
        except Exception as e:
            logger.error(f"双写更新命名空间失败: {str(e)}")
            return False
    
    async def delete_namespace(self, namespace_id: int) -> bool:
        """删除命名空间（硬删除）"""
        try:
            # 先删除MySQL中的数据
            if self.db_manager:
                success = await self.db_manager.delete_namespace(namespace_id)
                if not success:
                    logger.error(f"MySQL删除命名空间失败: namespace_id={namespace_id}")
                    return False
            
            # 删除Redis缓存
            cache_key = self._get_cache_key("namespaces", str(namespace_id))
            await self.redis_client.delete(cache_key)
            
            # 删除相关的匹配器和规则缓存
            matcher_cache_key = self._get_cache_key("matchers", str(namespace_id))
            await self.redis_client.delete(matcher_cache_key)
            
            rules_cache_key = self._get_cache_key("rules", str(namespace_id))
            await self.redis_client.delete(rules_cache_key)
            
            logger.info(f"命名空间删除成功: namespace_id={namespace_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除命名空间失败: {str(e)}")
            return False
    
    async def create_rule_dual_write(self, rule_data: Dict[str, Any]) -> int:
        """双写创建规则 - Redis和MySQL并行写入"""
        try:
            # 并行执行Redis和MySQL写入
            tasks = []
            
            # MySQL写入任务
            if self.db_manager:
                mysql_task = self.db_manager.create_rule(rule_data)
                tasks.append(mysql_task)
            
            # Redis写入任务（临时存储）
            temp_key = f"temp:rule:{datetime.now().timestamp()}"
            redis_task = self.redis_client.set(temp_key, json.dumps(rule_data, indent=2, ensure_ascii=False), ex=60)
            tasks.append(redis_task)
            
            # 并行执行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            rule_id = None
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"写入失败: {str(result)}")
                elif i == 0 and self.db_manager:  # MySQL结果
                    rule_id = result
                elif i == 1:  # Redis结果
                    # Redis写入成功，删除临时键
                    await self.redis_client.delete(temp_key)
            
            if rule_id:
                # 更新相关缓存
                namespace_id = rule_data.get('namespace_id')
                if namespace_id and self.db_manager:
                    # 异步更新命名空间规则缓存
                    asyncio.create_task(self._update_rules_cache(namespace_id))
                return rule_id
            else:
                raise Exception("MySQL写入失败")
                
        except Exception as e:
            logger.error(f"双写创建规则失败: {str(e)}")
            raise
    
    async def _update_rules_cache(self, namespace_id: int):
        """更新规则缓存"""
        try:
            if self.db_manager:
                rules = await self.db_manager.get_rules_by_namespace(namespace_id)
                await self.set_rules(namespace_id, rules)
        except Exception as e:
            logger.error(f"更新规则缓存失败: {str(e)}")
    
    async def batch_dual_write(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量双写操作"""
        try:
            results = {
                'success': [],
                'failed': [],
                'mysql_only': [],
                'redis_only': []
            }
            
            for operation in operations:
                op_type = operation.get('type')
                data = operation.get('data')
                
                try:
                    if op_type == 'create_namespace':
                        namespace_id = await self.create_namespace_dual_write(data)
                        results['success'].append({'type': op_type, 'id': namespace_id})
                    elif op_type == 'update_namespace':
                        success = await self.update_namespace_dual_write(data['namespace_id'], data)
                        if success:
                            results['success'].append({'type': op_type, 'id': data['namespace_id']})
                        else:
                            results['failed'].append({'type': op_type, 'data': data})
                    elif op_type == 'create_rule':
                        rule_id = await self.create_rule_dual_write(data)
                        results['success'].append({'type': op_type, 'id': rule_id})
                    else:
                        results['failed'].append({'type': op_type, 'data': data, 'error': 'Unknown operation type'})
                        
                except Exception as e:
                    results['failed'].append({'type': op_type, 'data': data, 'error': str(e)})
            
            return results
            
        except Exception as e:
            logger.error(f"批量双写操作失败: {str(e)}")
            return {'error': str(e)}
    
    async def get_namespace_usage(self, namespace_id: int, time_window: str = "30m") -> Dict[str, Any]:
        """获取命名空间的使用情况"""
        try:
            # 解析时间窗口
            window_minutes = self._parse_time_window(time_window)
            
            # 获取命名空间信息
            namespace = await self.get_namespace(namespace_id)
            if not namespace:
                return {"error": "Namespace not found"}
            
            # 获取规则配置
            rules = await self.get_rules(namespace_id)
            
            # 获取当前时间
            current_time = int(time.time())
            
            usage_data = {
                "namespace_id": namespace_id,
                "namespace_name": namespace.get("namespace_name", ""),
                "namespace_code": namespace.get("namespace_code", ""),
                "current_time": current_time,
                "time_window": time_window,
                "window_minutes": window_minutes,
                "metrics": {}
            }
            
            # 获取各种指标的使用情况
            for rule in rules:
                rule_type = rule.get("rule_type")
                rule_config = rule.get("rule_config", {})
                
                if isinstance(rule_config, str):
                    try:
                        rule_config = json.loads(rule_config)
                    except:
                        rule_config = {}
                
                if rule_type == "token_limit":
                    token_usage = await self._get_token_usage(namespace_id, rule_config, current_time, window_minutes)
                    usage_data["metrics"]["token_usage"] = token_usage
                
                elif rule_type == "qps_limit":
                    qps_usage = await self._get_qps_usage(namespace_id, rule_config, current_time, window_minutes)
                    usage_data["metrics"]["qps_usage"] = qps_usage
                
                elif rule_type == "concurrent_limit":
                    concurrent_usage = await self._get_concurrent_usage(namespace_id, rule_config, current_time)
                    usage_data["metrics"]["concurrent_usage"] = concurrent_usage
            
            return usage_data
            
        except Exception as e:
            logger.error(f"获取命名空间使用情况失败: {str(e)}")
            return {"error": str(e)}
    
    async def get_namespaces_usage_overview(self) -> Dict[str, Any]:
        """获取所有命名空间的使用情况概览"""
        try:
            # 获取所有命名空间
            if self.db_manager:
                namespaces = await self.db_manager.get_all_namespaces()
            else:
                return {"error": "Database manager not available"}
            
            overview = {
                "total_namespaces": len(namespaces),
                "namespaces": []
            }
            
            for namespace in namespaces:
                namespace_id = namespace.get("namespace_id")
                if namespace_id:
                    usage = await self.get_namespace_usage(namespace_id, "30m")
                    overview["namespaces"].append({
                        "namespace_id": namespace_id,
                        "namespace_name": namespace.get("namespace_name", ""),
                        "namespace_code": namespace.get("namespace_code", ""),
                        "usage": usage
                    })
            
            return overview
            
        except Exception as e:
            logger.error(f"获取命名空间使用情况概览失败: {str(e)}")
            return {"error": str(e)}
    
    async def get_namespace_monitoring(self, namespace_id: int, metric_type: str = "all") -> Dict[str, Any]:
        """获取命名空间的实时监控数据"""
        try:
            current_time = int(time.time())
            
            monitoring_data = {
                "namespace_id": namespace_id,
                "current_time": current_time,
                "metrics": {}
            }
            
            if metric_type in ["all", "token"]:
                # 获取token使用情况的时间序列数据
                token_timeline = await self._get_token_timeline(namespace_id, current_time)
                monitoring_data["metrics"]["token_timeline"] = token_timeline
            
            if metric_type in ["all", "qps"]:
                # 获取QPS使用情况的时间序列数据
                qps_timeline = await self._get_qps_timeline(namespace_id, current_time)
                monitoring_data["metrics"]["qps_timeline"] = qps_timeline
            
            if metric_type in ["all", "concurrent"]:
                # 获取并发使用情况的时间序列数据
                concurrent_timeline = await self._get_concurrent_timeline(namespace_id, current_time)
                monitoring_data["metrics"]["concurrent_timeline"] = concurrent_timeline
            
            return monitoring_data
            
        except Exception as e:
            logger.error(f"获取命名空间监控数据失败: {str(e)}")
            return {"error": str(e)}
    
    def _parse_time_window(self, time_window: str) -> int:
        """解析时间窗口字符串"""
        if time_window.endswith("m"):
            return int(time_window[:-1])
        elif time_window.endswith("h"):
            return int(time_window[:-1]) * 60
        elif time_window.endswith("d"):
            return int(time_window[:-1]) * 24 * 60
        else:
            return 30  # 默认30分钟
    
    async def _get_token_usage(self, namespace_id: int, rule_config: Dict, current_time: int, window_minutes: int) -> Dict[str, Any]:
        """获取token使用情况"""
        try:
            # 计算时间窗口
            window_size = window_minutes * 60
            window_start = (current_time // window_size) * window_size
            
            # 构建Redis键
            counter_key = f"rate_limit:{namespace_id}:token:{window_start}"
            
            # 获取当前使用量
            current_usage = await self.get_counter(counter_key)
            
            # 获取限制值
            max_tokens = rule_config.get("max_tokens_per_hour") or rule_config.get("max_tokens_per_window", 0)
            
            return {
                "current_usage": current_usage,
                "max_limit": max_tokens,
                "usage_percentage": (current_usage / max_tokens * 100) if max_tokens > 0 else 0,
                "window_start": window_start,
                "window_end": window_start + window_size,
                "remaining": max_tokens - current_usage if max_tokens > current_usage else 0
            }
            
        except Exception as e:
            logger.error(f"获取token使用情况失败: {str(e)}")
            return {"error": str(e)}
    
    async def _get_qps_usage(self, namespace_id: int, rule_config: Dict, current_time: int, window_minutes: int) -> Dict[str, Any]:
        """获取QPS使用情况"""
        try:
            # 计算时间窗口
            window_size = window_minutes * 60
            window_start = (current_time // window_size) * window_size
            
            # 构建Redis键
            counter_key = f"rate_limit:{namespace_id}:qps:{window_start}"
            
            # 获取当前使用量
            current_usage = await self.get_counter(counter_key)
            
            # 获取限制值
            max_requests = rule_config.get("max_requests_per_minute", 0) * window_minutes
            
            return {
                "current_usage": current_usage,
                "max_limit": max_requests,
                "usage_percentage": (current_usage / max_requests * 100) if max_requests > 0 else 0,
                "window_start": window_start,
                "window_end": window_start + window_size,
                "remaining": max_requests - current_usage if max_requests > current_usage else 0
            }
            
        except Exception as e:
            logger.error(f"获取QPS使用情况失败: {str(e)}")
            return {"error": str(e)}
    
    async def _get_concurrent_usage(self, namespace_id: int, rule_config: Dict, current_time: int) -> Dict[str, Any]:
        """获取并发使用情况"""
        try:
            # 构建Redis键
            counter_key = f"concurrent:{namespace_id}:current"
            
            # 获取当前使用量
            current_usage = await self.get_counter(counter_key)
            
            # 获取限制值
            max_connections = rule_config.get("max_connections", 0)
            
            return {
                "current_usage": current_usage,
                "max_limit": max_connections,
                "usage_percentage": (current_usage / max_connections * 100) if max_connections > 0 else 0,
                "remaining": max_connections - current_usage if max_connections > current_usage else 0
            }
            
        except Exception as e:
            logger.error(f"获取并发使用情况失败: {str(e)}")
            return {"error": str(e)}
    
    async def _get_token_timeline(self, namespace_id: int, current_time: int) -> List[Dict[str, Any]]:
        """获取token使用情况的时间序列数据"""
        try:
            timeline = []
            
            # 获取最近24小时的数据，每小时一个点
            for i in range(24):
                timestamp = current_time - (i * 3600)
                window_start = (timestamp // 3600) * 3600
                
                counter_key = f"rate_limit:{namespace_id}:token:{window_start}"
                usage = await self.get_counter(counter_key)
                
                timeline.append({
                    "timestamp": window_start,
                    "usage": usage,
                    "time": time.strftime("%H:%M", time.localtime(window_start))
                })
            
            # 反转时间序列，使其按时间顺序排列
            timeline.reverse()
            return timeline
            
        except Exception as e:
            logger.error(f"获取token时间序列失败: {str(e)}")
            return []
    
    async def _get_qps_timeline(self, namespace_id: int, current_time: int) -> List[Dict[str, Any]]:
        """获取QPS使用情况的时间序列数据"""
        try:
            timeline = []
            
            # 获取最近60分钟的数据，每分钟一个点
            for i in range(60):
                timestamp = current_time - (i * 60)
                window_start = (timestamp // 60) * 60
                
                counter_key = f"rate_limit:{namespace_id}:qps:{window_start}"
                usage = await self.get_counter(counter_key)
                
                timeline.append({
                    "timestamp": window_start,
                    "usage": usage,
                    "time": time.strftime("%H:%M", time.localtime(window_start))
                })
            
            # 反转时间序列，使其按时间顺序排列
            timeline.reverse()
            return timeline
            
        except Exception as e:
            logger.error(f"获取QPS时间序列失败: {str(e)}")
            return []
    
    async def _get_concurrent_timeline(self, namespace_id: int, current_time: int) -> List[Dict[str, Any]]:
        """获取并发使用情况的时间序列数据"""
        try:
            timeline = []
            
            # 获取最近60分钟的数据，每分钟一个点
            for i in range(60):
                timestamp = current_time - (i * 60)
                
                counter_key = f"concurrent:{namespace_id}:current"
                usage = await self.get_counter(counter_key)
                
                timeline.append({
                    "timestamp": timestamp,
                    "usage": usage,
                    "time": time.strftime("%H:%M", time.localtime(timestamp))
                })
            
            # 反转时间序列，使其按时间顺序排列
            timeline.reverse()
            return timeline
            
        except Exception as e:
            logger.error(f"获取并发时间序列失败: {str(e)}")
            return []

    # ==================== 策略配置缓存 ====================
    
    async def set_policy(self, policy_id: int, policy_data: Dict, ttl: int = None):
        """设置策略配置缓存"""
        try:
            cache_key = self._get_cache_key("policies", str(policy_id))
            await self.redis_client.set(cache_key, json.dumps(policy_data, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['policies'])
        except Exception as e:
            logger.error(f"设置策略配置缓存失败: {str(e)}")
    
    async def get_policy(self, policy_id: int) -> Optional[Dict]:
        """获取策略配置缓存"""
        try:
            cache_key = self._get_cache_key("policies", str(policy_id))
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"获取策略配置缓存失败: {str(e)}")
            return None
    
    async def set_policies_list(self, policies: List[Dict], filters: Dict = None, ttl: int = None):
        """设置策略列表缓存"""
        try:
            cache_key = self._get_list_cache_key("policies", filters)
            await self.redis_client.set(cache_key, json.dumps(policies, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['policies'])
        except Exception as e:
            logger.error(f"设置策略列表缓存失败: {str(e)}")
    
    async def get_policies_list(self, filters: Dict = None) -> List[Dict]:
        """获取策略列表缓存"""
        try:
            cache_key = self._get_list_cache_key("policies", filters)
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else []
        except Exception as e:
            logger.error(f"获取策略列表缓存失败: {str(e)}")
            return []
    
    async def delete_policy(self, policy_id: int):
        """删除策略配置缓存"""
        try:
            cache_key = self._get_cache_key("policies", str(policy_id))
            await self.redis_client.delete(cache_key)
            # 清除相关列表缓存
            await self.redis_client.delete(self._get_list_cache_key("policies"))
        except Exception as e:
            logger.error(f"删除策略配置缓存失败: {str(e)}")

    # ==================== 流量监控缓存 ====================
    
    async def set_traffic_metrics(self, metrics: Dict, ttl: int = None):
        """设置流量监控指标缓存"""
        try:
            cache_key = "traffic:metrics"
            await self.redis_client.set(cache_key, json.dumps(metrics, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['traffic'])
        except Exception as e:
            logger.error(f"设置流量监控指标缓存失败: {str(e)}")
    
    async def get_traffic_metrics(self) -> Optional[Dict]:
        """获取流量监控指标缓存"""
        try:
            cache_key = "traffic:metrics"
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"获取流量监控指标缓存失败: {str(e)}")
            return None
    
    async def set_alerts(self, alerts: List[Dict], ttl: int = None):
        """设置告警信息缓存"""
        try:
            cache_key = "traffic:alerts"
            await self.redis_client.set(cache_key, json.dumps(alerts, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['alerts'])
        except Exception as e:
            logger.error(f"设置告警信息缓存失败: {str(e)}")
    
    async def get_alerts(self) -> List[Dict]:
        """获取告警信息缓存"""
        try:
            cache_key = "traffic:alerts"
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else []
        except Exception as e:
            logger.error(f"获取告警信息缓存失败: {str(e)}")
            return []
    
    async def set_alert(self, alert_id: str, alert_data: Dict, ttl: int = None):
        """设置单个告警缓存"""
        try:
            cache_key = f"traffic:alert:{alert_id}"
            await self.redis_client.set(cache_key, json.dumps(alert_data, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['alerts'])
        except Exception as e:
            logger.error(f"设置告警缓存失败: {str(e)}")
    
    async def get_alert(self, alert_id: str) -> Optional[Dict]:
        """获取单个告警缓存"""
        try:
            cache_key = f"traffic:alert:{alert_id}"
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"获取告警缓存失败: {str(e)}")
            return None

    # ==================== 访问日志缓存 ====================
    
    async def set_logs(self, logs: List[Dict], filters: Dict = None, ttl: int = None):
        """设置访问日志缓存"""
        try:
            cache_key = self._get_list_cache_key("logs", filters)
            await self.redis_client.set(cache_key, json.dumps(logs, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['logs'])
        except Exception as e:
            logger.error(f"设置访问日志缓存失败: {str(e)}")
    
    async def get_logs(self, filters: Dict = None) -> List[Dict]:
        """获取访问日志缓存"""
        try:
            cache_key = self._get_list_cache_key("logs", filters)
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else []
        except Exception as e:
            logger.error(f"获取访问日志缓存失败: {str(e)}")
            return []
    
    async def set_log_stats(self, stats: Dict, ttl: int = None):
        """设置日志统计缓存"""
        try:
            cache_key = "logs:stats"
            await self.redis_client.set(cache_key, json.dumps(stats, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['stats'])
        except Exception as e:
            logger.error(f"设置日志统计缓存失败: {str(e)}")
    
    async def get_log_stats(self) -> Optional[Dict]:
        """获取日志统计缓存"""
        try:
            cache_key = "logs:stats"
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"获取日志统计缓存失败: {str(e)}")
            return None

    # ==================== 仪表盘数据缓存 ====================
    
    async def set_dashboard_metrics(self, metrics: Dict, ttl: int = None):
        """设置仪表盘指标缓存"""
        try:
            cache_key = "dashboard:metrics"
            await self.redis_client.set(cache_key, json.dumps(metrics, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['dashboard'])
        except Exception as e:
            logger.error(f"设置仪表盘指标缓存失败: {str(e)}")
    
    async def get_dashboard_metrics(self) -> Optional[Dict]:
        """获取仪表盘指标缓存"""
        try:
            cache_key = "dashboard:metrics"
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"获取仪表盘指标缓存失败: {str(e)}")
            return None
    
    async def set_dashboard_realtime(self, realtime_data: Dict, ttl: int = None):
        """设置仪表盘实时数据缓存"""
        try:
            cache_key = "dashboard:realtime"
            await self.redis_client.set(cache_key, json.dumps(realtime_data, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['dashboard'])
        except Exception as e:
            logger.error(f"设置仪表盘实时数据缓存失败: {str(e)}")
    
    async def get_dashboard_realtime(self) -> Optional[Dict]:
        """获取仪表盘实时数据缓存"""
        try:
            cache_key = "dashboard:realtime"
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"获取仪表盘实时数据缓存失败: {str(e)}")
            return None

    # ==================== 路由规则缓存 ====================
    
    async def set_location(self, location_id: int, location_data: Dict, ttl: int = None):
        """设置路由规则缓存"""
        try:
            cache_key = self._get_cache_key("locations", str(location_id))
            await self.redis_client.set(cache_key, json.dumps(location_data, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['location_rules'])
        except Exception as e:
            logger.error(f"设置路由规则缓存失败: {str(e)}")
    
    async def get_location(self, location_id: int) -> Optional[Dict]:
        """获取路由规则缓存"""
        try:
            cache_key = self._get_cache_key("locations", str(location_id))
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"获取路由规则缓存失败: {str(e)}")
            return None
    
    async def set_locations_list(self, locations: List[Dict], ttl: int = None):
        """设置路由规则列表缓存"""
        try:
            cache_key = self._get_list_cache_key("locations")
            await self.redis_client.set(cache_key, json.dumps(locations, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['locations'])
        except Exception as e:
            logger.error(f"设置路由规则列表缓存失败: {str(e)}")
    
    async def get_locations_list(self) -> List[Dict]:
        """获取路由规则列表缓存"""
        try:
            cache_key = self._get_list_cache_key("locations")
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else []
        except Exception as e:
            logger.error(f"获取路由规则列表缓存失败: {str(e)}")
            return []
    
    async def delete_location(self, location_id: int):
        """删除路由规则缓存"""
        try:
            cache_key = self._get_cache_key("locations", str(location_id))
            await self.redis_client.delete(cache_key)
            # 清除相关列表缓存
            await self.redis_client.delete(self._get_list_cache_key("locations"))
        except Exception as e:
            logger.error(f"删除路由规则缓存失败: {str(e)}")

    # ==================== 认证信息缓存 ====================
    
    async def set_auth_token(self, token: str, user_data: Dict, ttl: int = None):
        """设置认证令牌缓存"""
        try:
            cache_key = f"auth:token:{token}"
            await self.redis_client.set(cache_key, json.dumps(user_data, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['auth'])
        except Exception as e:
            logger.error(f"设置认证令牌缓存失败: {str(e)}")
    
    async def get_auth_token(self, token: str) -> Optional[Dict]:
        """获取认证令牌缓存"""
        try:
            cache_key = f"auth:token:{token}"
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"获取认证令牌缓存失败: {str(e)}")
            return None
    
    async def delete_auth_token(self, token: str):
        """删除认证令牌缓存"""
        try:
            cache_key = f"auth:token:{token}"
            await self.redis_client.delete(cache_key)
        except Exception as e:
            logger.error(f"删除认证令牌缓存失败: {str(e)}")
    
    async def set_user_permissions(self, user_id: str, permissions: List[str], ttl: int = None):
        """设置用户权限缓存"""
        try:
            cache_key = f"auth:permissions:{user_id}"
            await self.redis_client.set(cache_key, json.dumps(permissions, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['auth'])
        except Exception as e:
            logger.error(f"设置用户权限缓存失败: {str(e)}")
    
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限缓存"""
        try:
            cache_key = f"auth:permissions:{user_id}"
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else []
        except Exception as e:
            logger.error(f"获取用户权限缓存失败: {str(e)}")
            return []

    # ==================== 统计数据缓存 ====================
    
    async def set_stats(self, stats_type: str, stats_data: Dict, ttl: int = None):
        """设置统计数据缓存"""
        try:
            cache_key = f"stats:{stats_type}"
            await self.redis_client.set(cache_key, json.dumps(stats_data, indent=2, ensure_ascii=False), ex=ttl or self.cache_ttl['stats'])
        except Exception as e:
            logger.error(f"设置统计数据缓存失败: {str(e)}")
    
    async def get_stats(self, stats_type: str) -> Optional[Dict]:
        """获取统计数据缓存"""
        try:
            cache_key = f"stats:{stats_type}"
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"获取统计数据缓存失败: {str(e)}")
            return None 
    
    # ==================== 策略缓存管理 ====================
    
    async def set_policies(self, namespace_id: int, policies: List[Dict], ttl: int = None):
        """设置命名空间策略缓存"""
        try:
            cache_key = f"namespace:{namespace_id}:policies"
            await self.redis_client.setex(
                cache_key, 
                ttl or self.cache_ttl['policies'], 
                json.dumps(policies, indent=2, ensure_ascii=False)
            )
            logger.info(f"设置命名空间策略缓存成功: {namespace_id}")
        except Exception as e:
            logger.error(f"设置命名空间策略缓存失败: {str(e)}")
    
    async def get_policies(self, namespace_id: int) -> List[Dict]:
        """获取命名空间策略缓存"""
        try:
            cache_key = f"namespace:{namespace_id}:policies"
            data = await self.redis_client.get(cache_key)
            
            if data:
                return json.loads(data)
            
            # 缓存未命中，从MySQL读取
            if self.db_manager:
                policies = await self.db_manager.get_policies_by_namespace(namespace_id)
                if policies:
                    # 异步更新缓存
                    asyncio.create_task(self.set_policies(namespace_id, policies))
                    return policies
            
            return []
            
        except Exception as e:
            logger.error(f"获取命名空间策略缓存失败: {str(e)}")
            # 降级到MySQL
            if self.db_manager:
                return await self.db_manager.get_policies_by_namespace(namespace_id)
            return []