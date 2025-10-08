"""
数据库管理器 - MySQL操作
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, Boolean, select, insert, update, delete, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器 - MySQL操作"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.metadata = MetaData()
        
        # 定义表结构
        self._define_tables()
    
    def _define_tables(self):
        """定义数据库表结构"""
        # 命名空间表
        self.namespaces = Table(
            'namespaces', self.metadata,
            Column('namespace_id', Integer, primary_key=True, autoincrement=True),
            Column('namespace_code', String(50), unique=True, nullable=False, comment='命名空间代码'),
            Column('namespace_name', String(100), nullable=False, comment='命名空间名称'),
            Column('description', Text, comment='描述'),
            Column('status', Integer, default=1, comment='状态：1-启用，0-禁用'),
            Column('create_time', DateTime, default=datetime.now, comment='创建时间'),
            Column('update_time', DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
        )
        
        # 报文匹配器表
        self.message_matchers = Table(
            'message_matchers', self.metadata,
            Column('matcher_id', Integer, primary_key=True, autoincrement=True),
            Column('namespace_id', Integer, nullable=False, comment='命名空间ID'),
            Column('matcher_name', String(100), nullable=False, comment='匹配器名称'),
            Column('matcher_type', String(20), nullable=False, comment='匹配类型：header/body'),
            Column('match_field', String(100), nullable=False, comment='匹配字段'),
            Column('match_operator', String(20), nullable=False, comment='匹配操作符'),
            Column('match_value', Text, nullable=False, comment='匹配值'),
            Column('priority', Integer, default=100, comment='优先级'),
            Column('status', Integer, default=1, comment='状态：1-启用，0-禁用'),
            Column('create_time', DateTime, default=datetime.now, comment='创建时间'),
            Column('update_time', DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
        )
        
        # 通用规则表（合并所有规则类型）
        self.rules = Table(
            'rules', self.metadata,
            Column('rule_id', Integer, primary_key=True, autoincrement=True),
            Column('namespace_id', Integer, nullable=False, comment='命名空间ID'),
            Column('rule_name', String(100), nullable=False, comment='规则名称'),
            Column('rule_type', String(50), nullable=False, comment='规则类型：matcher/token_limit/concurrent_limit/rate_limit'),
            Column('rule_config', Text, nullable=False, comment='规则配置(JSON)'),
            Column('priority', Integer, default=100, comment='优先级'),
            Column('status', Integer, default=1, comment='状态：1-启用，0-禁用'),
            Column('create_time', DateTime, default=datetime.now, comment='创建时间'),
            Column('update_time', DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
        )
        
        # 策略表
        self.policies = Table(
            'policies', self.metadata,
            Column('policy_id', Integer, primary_key=True, autoincrement=True),
            Column('policy_name', String(100), nullable=False, comment='策略名称'),
            Column('policy_type', String(50), nullable=False, comment='策略类型：token-limit/concurrency-limit/qps-limit/message-matching'),
            Column('description', Text, comment='策略描述'),
            Column('namespace_id', Integer, comment='命名空间ID'),
            Column('namespaces', Text, comment='关联命名空间(JSON)'),
            Column('rules', Text, nullable=False, comment='规则列表(JSON)'),
            Column('rule_type', String(50), comment='规则类型'),
            Column('rule_config', Text, comment='规则配置(JSON)'),
            Column('priority', Integer, default=100, comment='优先级'),
            Column('status', Integer, default=1, comment='状态：1-启用，0-禁用'),
            Column('created_by', Integer, comment='创建者ID'),
            Column('create_time', DateTime, default=datetime.now, comment='创建时间'),
            Column('update_time', DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
        )
        
        # Nginx上游服务器配置表
        self.upstream_servers = Table(
            'upstream_servers', self.metadata,
            Column('server_id', Integer, primary_key=True, autoincrement=True),
            Column('server_name', String(100), nullable=False, comment='服务器名称'),
            Column('server_type', String(50), nullable=False, comment='服务器类型：openai/azure/claude/anthropic/custom'),
            Column('server_url', String(500), nullable=False, comment='服务器地址'),
            Column('api_key', String(500), comment='API密钥'),
            Column('model_config', Text, comment='模型配置(JSON)'),
            Column('load_balance_weight', Integer, default=1, comment='负载均衡权重'),
            Column('max_connections', Integer, default=100, comment='最大连接数'),
            Column('timeout_connect', Integer, default=30, comment='连接超时(秒)'),
            Column('timeout_read', Integer, default=300, comment='读取超时(秒)'),
            Column('timeout_write', Integer, default=300, comment='写入超时(秒)'),
            Column('health_check_url', String(500), comment='健康检查URL'),
            Column('health_check_interval', Integer, default=30, comment='健康检查间隔(秒)'),
            Column('status', Integer, default=1, comment='状态：1-启用，0-禁用'),
            Column('create_time', DateTime, default=datetime.now, comment='创建时间'),
            Column('update_time', DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
        )
        
        # 路由规则表（location_rules）
        self.location_rules = Table(
            'location_rules', self.metadata,
            Column('location_id', Integer, primary_key=True, autoincrement=True),
            Column('path', String(500), nullable=False, comment='路径'),
            Column('upstream_id', Integer, nullable=False, comment='上游服务器ID'),
            Column('proxy_cache', Boolean, default=False, comment='代理缓存'),
            Column('proxy_buffering', Boolean, default=False, comment='代理缓冲'),
            Column('proxy_pass', String(500), comment='代理转发地址'),
            Column('is_regex', Boolean, default=False, comment='是否正则表达式'),
            Column('limit_req_config', Text, comment='限流配置(JSON)'),
            Column('sse_support', Boolean, default=False, comment='SSE支持'),
            Column('chunked_transfer', Boolean, default=False, comment='分块传输'),
            Column('matcher_type', String(20), default='path', comment='匹配器类型'),
            Column('match_field', String(100), comment='匹配字段'),
            Column('match_operator', String(20), comment='匹配操作符'),
            Column('match_value', Text, comment='匹配值'),
            Column('add_headers', Text, comment='添加的请求头(JSON)'),
            Column('rewrite_path', String(200), comment='路径重写'),
            Column('path_rewrite_config', Text, comment='路径重写配置(JSON)'),
            Column('priority', Integer, default=100, comment='优先级'),
            Column('status', Integer, default=1, comment='状态：1-启用，0-禁用'),
            Column('created_by', Integer, comment='创建者ID'),
            Column('create_time', DateTime, default=datetime.now, comment='创建时间'),
            Column('update_time', DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
        )
        
        # Nginx代理规则配置表
        self.proxy_rules = Table(
            'proxy_rules', self.metadata,
            Column('rule_id', Integer, primary_key=True, autoincrement=True),
            Column('rule_name', String(100), nullable=False, comment='规则名称'),
            Column('rule_type', String(50), nullable=False, comment='规则类型：path_match/header_match/model_match'),
            Column('match_pattern', String(200), nullable=False, comment='匹配模式'),
            Column('target_server_id', Integer, nullable=False, comment='目标服务器ID'),
            Column('rewrite_path', String(200), comment='路径重写'),
            Column('add_headers', Text, comment='添加的请求头(JSON)'),
            Column('priority', Integer, default=100, comment='优先级'),
            Column('status', Integer, default=1, comment='状态：1-启用，0-禁用'),
            Column('create_time', DateTime, default=datetime.now, comment='创建时间'),
            Column('update_time', DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
        )
        
        # 访问日志表
        self.access_logs = Table(
            'access_logs', self.metadata,
            Column('log_id', Integer, primary_key=True, autoincrement=True),
            Column('request_id', String(100), comment='请求ID'),
            Column('namespace_id', Integer, comment='命名空间ID'),
            Column('upstream_id', Integer, comment='上游服务器ID'),
            Column('client_ip', String(45), comment='客户端IP'),
            Column('user_agent', Text, comment='用户代理'),
            Column('method', String(10), comment='请求方法'),
            Column('path', String(500), comment='请求路径'),
            Column('status_code', Integer, comment='状态码'),
            Column('response_time', Integer, comment='响应时间(ms)'),
            Column('request_size', Integer, comment='请求大小'),
            Column('response_size', Integer, comment='响应大小'),
            Column('input_tokens', Integer, comment='输入Token数'),
            Column('output_tokens', Integer, comment='输出Token数'),
            Column('api_key', String(100), comment='API密钥'),
            Column('error_message', Text, comment='错误信息'),
            Column('timestamp', DateTime, nullable=False, comment='时间戳'),
            Column('create_time', DateTime, default=datetime.now, comment='创建时间')
        )
        
        # 监控指标表
        self.monitoring_metrics = Table(
            'monitoring_metrics', self.metadata,
            Column('metric_id', Integer, primary_key=True, autoincrement=True),
            Column('namespace_id', Integer, comment='命名空间ID'),
            Column('metric_name', String(100), nullable=False, comment='指标名称'),
            Column('metric_value', String(20), nullable=False, comment='指标值'),
            Column('metric_unit', String(20), comment='指标单位'),
            Column('tags', Text, comment='标签(JSON)'),
            Column('timestamp', DateTime, nullable=False, comment='时间戳'),
            Column('create_time', DateTime, default=datetime.now, comment='创建时间')
        )
        
        # Nginx全局配置表
        self.nginx_config = Table(
            'nginx_config', self.metadata,
            Column('config_id', Integer, primary_key=True, autoincrement=True),
            Column('config_type', String(50), nullable=False, comment='配置类型：global/http/server'),
            Column('config_name', String(100), nullable=False, comment='配置名称'),
            Column('config_value', Text, comment='配置值(JSON)'),
            Column('description', String(500), comment='配置描述'),
            Column('status', Integer, default=1, comment='状态：1-启用，0-禁用'),
            Column('create_time', DateTime, default=datetime.now, comment='创建时间'),
            Column('update_time', DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
        )
    
    async def connect(self):
        """连接数据库"""
        try:
            # 添加字符集配置
            connect_args = {
                "charset": "utf8mb4",
                "use_unicode": True,
                "init_command": "SET NAMES utf8mb4"
            }
            self.engine = create_async_engine(self.database_url, echo=False, connect_args=connect_args)
            self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
            
            # 创建表
            async with self.engine.begin() as conn:
                await conn.run_sync(self.metadata.create_all)
            
            logger.info("MySQL数据库连接成功")
        except Exception as e:
            logger.error(f"MySQL数据库连接失败: {str(e)}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            await self.engine.dispose()
    
    def get_session(self):
        """获取数据库会话上下文管理器"""
        if not self.session_factory:
            raise RuntimeError("数据库未连接")
        return self.session_factory()
    
    # 命名空间管理
    async def create_namespace(self, namespace_data: Dict[str, Any]) -> int:
        """创建命名空间"""
        try:
            async with self.get_session() as session:
                stmt = insert(self.namespaces).values(
                    namespace_code=namespace_data['namespace_code'],
                    namespace_name=namespace_data['namespace_name'],
                    description=namespace_data.get('description', ''),
                    status=namespace_data.get('status', 1),
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )
                
                result = await session.execute(stmt)
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建命名空间失败: {str(e)}")
            raise
    
    async def get_namespace(self, namespace_id: int) -> Optional[Dict[str, Any]]:
        """获取命名空间"""
        try:
            async with self.get_session() as session:
                stmt = select(self.namespaces).where(
                    self.namespaces.c.namespace_id == namespace_id,
                    self.namespaces.c.status == 1
                )
                result = await session.execute(stmt)
                row = result.first()
                
                if row:
                    return {
                        'namespace_id': row.namespace_id,
                        'namespace_code': row.namespace_code,
                        'namespace_name': row.namespace_name,
                        'description': row.description,
                        'status': row.status,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    }
                return None
        except Exception as e:
            logger.error(f"获取命名空间失败: {str(e)}")
            return None
    
    async def get_all_namespaces(self) -> List[Dict[str, Any]]:
        """获取所有命名空间"""
        try:
            async with self.get_session() as session:
                stmt = select(self.namespaces).where(self.namespaces.c.status == 1)
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                return [{
                    'namespace_id': row.namespace_id,
                    'namespace_code': row.namespace_code,
                    'namespace_name': row.namespace_name,
                    'description': row.description,
                    'status': row.status,
                    'create_time': row.create_time.isoformat(),
                    'update_time': row.update_time.isoformat()
                } for row in rows]
        except Exception as e:
            logger.error(f"获取所有命名空间失败: {str(e)}")
            return []
    
    async def update_namespace(self, namespace_id: int, namespace_data: Dict[str, Any]) -> bool:
        """更新命名空间"""
        try:
            async with self.get_session() as session:
                stmt = update(self.namespaces).where(
                    self.namespaces.c.namespace_id == namespace_id
                ).values(
                    namespace_code=namespace_data.get('namespace_code'),
                    namespace_name=namespace_data.get('namespace_name'),
                    description=namespace_data.get('description'),
                    status=namespace_data.get('status'),
                    update_time=datetime.now()
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"更新命名空间失败: {str(e)}")
            return False
    
    async def delete_namespace(self, namespace_id: int) -> bool:
        """删除命名空间（硬删除）"""
        try:
            async with self.get_session() as session:
                stmt = self.namespaces.delete().where(
                    self.namespaces.c.namespace_id == namespace_id
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"删除命名空间失败: {str(e)}")
            return False
    
    # 报文匹配器管理
    async def create_matcher(self, matcher_data: Dict[str, Any]) -> int:
        """创建报文匹配器"""
        try:
            async with self.get_session() as session:
                stmt = insert(self.message_matchers).values(
                    namespace_id=matcher_data['namespace_id'],
                    matcher_name=matcher_data['matcher_name'],
                    matcher_type=matcher_data['matcher_type'],
                    match_field=matcher_data['match_field'],
                    match_operator=matcher_data['match_operator'],
                    match_value=matcher_data['match_value'],
                    priority=matcher_data.get('priority', 100),
                    status=matcher_data.get('status', 1),
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )
                
                result = await session.execute(stmt)
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建报文匹配器失败: {str(e)}")
            raise
    
    async def get_matchers_by_namespace(self, namespace_id: int) -> List[Dict[str, Any]]:
        """获取命名空间下的所有匹配器"""
        try:
            async with self.get_session() as session:
                stmt = select(self.message_matchers).where(
                    self.message_matchers.c.namespace_id == namespace_id,
                    self.message_matchers.c.status == 1
                ).order_by(self.message_matchers.c.priority.asc())
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                return [{
                    'matcher_id': row.matcher_id,
                    'namespace_id': row.namespace_id,
                    'matcher_name': row.matcher_name,
                    'matcher_type': row.matcher_type,
                    'match_field': row.match_field,
                    'match_operator': row.match_operator,
                    'match_value': row.match_value,
                    'priority': row.priority,
                    'status': row.status,
                    'create_time': row.create_time.isoformat(),
                    'update_time': row.update_time.isoformat()
                } for row in rows]
        except Exception as e:
            logger.error(f"获取命名空间匹配器失败: {str(e)}")
            return []
    
    async def get_all_matchers(self) -> List[Dict[str, Any]]:
        """获取所有报文匹配器"""
        try:
            async with self.get_session() as session:
                stmt = select(self.message_matchers).where(self.message_matchers.c.status == 1)
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                return [{
                    'matcher_id': row.matcher_id,
                    'namespace_id': row.namespace_id,
                    'matcher_name': row.matcher_name,
                    'matcher_type': row.matcher_type,
                    'match_field': row.match_field,
                    'match_operator': row.match_operator,
                    'match_value': row.match_value,
                    'priority': row.priority,
                    'status': row.status,
                    'create_time': row.create_time.isoformat(),
                    'update_time': row.update_time.isoformat()
                } for row in rows]
        except Exception as e:
            logger.error(f"获取所有报文匹配器失败: {str(e)}")
            return []
    
    async def get_matcher_by_id(self, matcher_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取报文匹配器"""
        try:
            async with self.get_session() as session:
                stmt = select(self.message_matchers).where(
                    self.message_matchers.c.matcher_id == matcher_id,
                    self.message_matchers.c.status == 1
                )
                result = await session.execute(stmt)
                row = result.first()
                
                if row:
                    return {
                        'matcher_id': row.matcher_id,
                        'namespace_id': row.namespace_id,
                        'matcher_name': row.matcher_name,
                        'matcher_type': row.matcher_type,
                        'match_field': row.match_field,
                        'match_operator': row.match_operator,
                        'match_value': row.match_value,
                        'priority': row.priority if row.priority is not None else 100,
                        'status': row.status if row.status is not None else 1,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    }
                return None
        except Exception as e:
            logger.error(f"获取报文匹配器失败: {str(e)}")
            return None
    
    async def update_matcher(self, matcher_id: int, matcher_data: Dict[str, Any]) -> bool:
        """更新报文匹配器"""
        try:
            async with self.get_session() as session:
                stmt = update(self.message_matchers).where(
                    self.message_matchers.c.matcher_id == matcher_id
                ).values(
                    matcher_name=matcher_data.get('matcher_name'),
                    matcher_type=matcher_data.get('matcher_type'),
                    match_field=matcher_data.get('match_field'),
                    match_operator=matcher_data.get('match_operator'),
                    match_value=matcher_data.get('match_value'),
                    priority=matcher_data.get('priority'),
                    status=matcher_data.get('status'),
                    update_time=datetime.now()
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"更新报文匹配器失败: {str(e)}")
            return False
    
    async def delete_matcher(self, matcher_id: int) -> bool:
        """删除报文匹配器（硬删除）"""
        try:
            async with self.get_session() as session:
                stmt = self.message_matchers.delete().where(
                    self.message_matchers.c.matcher_id == matcher_id
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"删除报文匹配器失败: {str(e)}")
            return False
    
    # 通用规则管理
    async def create_rule(self, rule_data: Dict[str, Any]) -> int:
        """创建通用规则"""
        try:
            async with self.get_session() as session:
                stmt = insert(self.rules).values(
                    namespace_id=rule_data['namespace_id'],
                    rule_name=rule_data['rule_name'],
                    rule_type=rule_data['rule_type'],
                    rule_config=json.dumps(rule_data['rule_config']) if isinstance(rule_data['rule_config'], dict) else rule_data['rule_config'],
                    priority=rule_data.get('priority', 100),
                    status=rule_data.get('status', 1),
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )
                
                result = await session.execute(stmt)
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建通用规则失败: {str(e)}")
            raise
    
    async def get_rules_by_namespace(self, namespace_id: int, rule_type: str = None) -> List[Dict[str, Any]]:
        """获取命名空间下的所有规则"""
        try:
            async with self.get_session() as session:
                stmt = select(self.rules).where(
                    self.rules.c.namespace_id == namespace_id,
                    self.rules.c.status == 1
                )
                
                if rule_type:
                    stmt = stmt.where(self.rules.c.rule_type == rule_type)
                
                stmt = stmt.order_by(self.rules.c.priority.asc())
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                return [{
                    'rule_id': row.rule_id,
                    'namespace_id': row.namespace_id,
                    'rule_name': row.rule_name,
                    'rule_type': row.rule_type,
                    'rule_config': row.rule_config,
                    'priority': row.priority,
                    'status': row.status,
                    'create_time': row.create_time.isoformat(),
                    'update_time': row.update_time.isoformat()
                } for row in rows]
        except Exception as e:
            logger.error(f"获取命名空间规则失败: {str(e)}")
            return []
    
    async def get_all_rules(self, rule_type: str = None) -> List[Dict[str, Any]]:
        """获取所有规则"""
        try:
            async with self.get_session() as session:
                stmt = select(self.rules).where(self.rules.c.status == 1)
                
                if rule_type:
                    stmt = stmt.where(self.rules.c.rule_type == rule_type)
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                return [{
                    'rule_id': row.rule_id,
                    'namespace_id': row.namespace_id,
                    'rule_name': row.rule_name,
                    'rule_type': row.rule_type,
                    'rule_config': row.rule_config,
                    'priority': row.priority,
                    'status': row.status,
                    'create_time': row.create_time.isoformat(),
                    'update_time': row.update_time.isoformat()
                } for row in rows]
        except Exception as e:
            logger.error(f"获取所有规则失败: {str(e)}")
            return []
    
    async def get_rule_by_id(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取规则"""
        try:
            async with self.get_session() as session:
                stmt = select(self.rules).where(
                    self.rules.c.rule_id == rule_id,
                    self.rules.c.status == 1
                )
                result = await session.execute(stmt)
                row = result.first()
                
                if row:
                    return {
                        'rule_id': row.rule_id,
                        'namespace_id': row.namespace_id,
                        'rule_name': row.rule_name,
                        'rule_type': row.rule_type,
                        'rule_config': row.rule_config,
                        'priority': row.priority if row.priority is not None else 100,
                        'status': row.status if row.status is not None else 1,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    }
                return None
        except Exception as e:
            logger.error(f"获取规则失败: {str(e)}")
            return None
    
    async def update_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> bool:
        """更新规则"""
        try:
            async with self.get_session() as session:
                stmt = update(self.rules).where(
                    self.rules.c.rule_id == rule_id
                ).values(
                    rule_name=rule_data.get('rule_name'),
                    rule_type=rule_data.get('rule_type'),
                    rule_config=json.dumps(rule_data['rule_config']) if 'rule_config' in rule_data and isinstance(rule_data['rule_config'], dict) else rule_data.get('rule_config'),
                    priority=rule_data.get('priority'),
                    status=rule_data.get('status'),
                    update_time=datetime.now()
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"更新规则失败: {str(e)}")
            return False
    
    async def delete_rule(self, rule_id: int) -> bool:
        """删除命名空间规则（硬删除）"""
        try:
            async with self.get_session() as session:
                stmt = self.rules.delete().where(
                    self.rules.c.rule_id == rule_id
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"删除命名空间规则失败: {str(e)}")
            return False
    
    # 通用限制规则管理
    async def create_limit_rule(self, rule_data: Dict[str, Any]) -> int:
        """创建限制规则"""
        try:
            async with self.get_session() as session:
                stmt = insert(self.limit_rules).values(
                    namespace_id=rule_data['namespace_id'],
                    rule_name=rule_data['rule_name'],
                    rule_type=rule_data['rule_type'],
                    rule_config=json.dumps(rule_data['rule_config']) if isinstance(rule_data['rule_config'], dict) else rule_data['rule_config'],
                    priority=rule_data.get('priority', 100),
                    status=rule_data.get('status', 1),
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )
                
                result = await session.execute(stmt)
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建限制规则失败: {str(e)}")
            raise
    
    async def get_limit_rules_by_namespace(self, namespace_id: int, rule_type: str = None) -> List[Dict[str, Any]]:
        """获取命名空间下的所有限制规则"""
        try:
            async with self.get_session() as session:
                stmt = select(self.limit_rules).where(
                    self.limit_rules.c.namespace_id == namespace_id,
                    self.limit_rules.c.status == 1
                )
                
                if rule_type:
                    stmt = stmt.where(self.limit_rules.c.rule_type == rule_type)
                
                stmt = stmt.order_by(self.limit_rules.c.priority.asc())
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                return [{
                    'rule_id': row.rule_id,
                    'namespace_id': row.namespace_id,
                    'rule_name': row.rule_name,
                    'rule_type': row.rule_type,
                    'rule_config': row.rule_config,
                    'priority': row.priority,
                    'status': row.status,
                    'create_time': row.create_time.isoformat(),
                    'update_time': row.update_time.isoformat()
                } for row in rows]
        except Exception as e:
            logger.error(f"获取命名空间限制规则失败: {str(e)}")
            return []
    
    async def get_all_limit_rules(self, rule_type: str = None) -> List[Dict[str, Any]]:
        """获取所有限制规则"""
        try:
            async with self.get_session() as session:
                stmt = select(self.limit_rules).where(self.limit_rules.c.status == 1)
                
                if rule_type:
                    stmt = stmt.where(self.limit_rules.c.rule_type == rule_type)
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                return [{
                    'rule_id': row.rule_id,
                    'namespace_id': row.namespace_id,
                    'rule_name': row.rule_name,
                    'rule_type': row.rule_type,
                    'rule_config': row.rule_config,
                    'priority': row.priority,
                    'status': row.status,
                    'create_time': row.create_time.isoformat(),
                    'update_time': row.update_time.isoformat()
                } for row in rows]
        except Exception as e:
            logger.error(f"获取所有限制规则失败: {str(e)}")
            return []
    
    async def get_limit_rule_by_id(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取限制规则"""
        try:
            async with self.get_session() as session:
                stmt = select(self.limit_rules).where(
                    self.limit_rules.c.rule_id == rule_id,
                    self.limit_rules.c.status == 1
                )
                result = await session.execute(stmt)
                row = result.first()
                
                if row:
                    return {
                        'rule_id': row.rule_id,
                        'namespace_id': row.namespace_id,
                        'rule_name': row.rule_name,
                        'rule_type': row.rule_type,
                        'rule_config': row.rule_config,
                        'priority': row.priority if row.priority is not None else 100,
                        'status': row.status if row.status is not None else 1,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    }
                return None
        except Exception as e:
            logger.error(f"获取限制规则失败: {str(e)}")
            return None
    
    async def update_limit_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> bool:
        """更新限制规则"""
        try:
            async with self.get_session() as session:
                stmt = update(self.limit_rules).where(
                    self.limit_rules.c.rule_id == rule_id
                ).values(
                    rule_name=rule_data.get('rule_name'),
                    rule_type=rule_data.get('rule_type'),
                    rule_config=json.dumps(rule_data['rule_config']) if 'rule_config' in rule_data and isinstance(rule_data['rule_config'], dict) else rule_data.get('rule_config'),
                    priority=rule_data.get('priority'),
                    status=rule_data.get('status'),
                    update_time=datetime.now()
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"更新限制规则失败: {str(e)}")
            return False
    
    async def delete_token_rule(self, rule_id: int) -> bool:
        """删除Token限制规则（硬删除）"""
        try:
            async with self.get_session() as session:
                stmt = self.token_limit_rules.delete().where(
                    self.token_limit_rules.c.rule_id == rule_id
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"删除Token限制规则失败: {str(e)}")
            return False
    
    # Token时间窗口计数器管理
    async def get_token_window_counter(self, namespace_id: int, rule_id: int, window_start: datetime) -> Optional[Dict[str, Any]]:
        """获取Token时间窗口计数器"""
        try:
            async with self.get_session() as session:
                stmt = select(self.token_window_counters).where(
                    self.token_window_counters.c.namespace_id == namespace_id,
                    self.token_window_counters.c.rule_id == rule_id,
                    self.token_window_counters.c.window_start == window_start
                )
                result = await session.execute(stmt)
                row = result.first()
                
                if row:
                    return {
                        'counter_id': row.counter_id,
                        'namespace_id': row.namespace_id,
                        'rule_id': row.rule_id,
                        'window_start': row.window_start.isoformat(),
                        'window_end': row.window_end.isoformat(),
                        'token_count': row.token_count,
                        'request_count': row.request_count,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    }
                return None
        except Exception as e:
            logger.error(f"获取Token时间窗口计数器失败: {str(e)}")
            return None
    
    async def create_token_window_counter(self, namespace_id: int, rule_id: int, window_start: datetime, window_end: datetime) -> int:
        """创建Token时间窗口计数器"""
        try:
            async with self.get_session() as session:
                stmt = insert(self.token_window_counters).values(
                    namespace_id=namespace_id,
                    rule_id=rule_id,
                    window_start=window_start,
                    window_end=window_end,
                    token_count=0,
                    request_count=0,
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )
                
                result = await session.execute(stmt)
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建Token时间窗口计数器失败: {str(e)}")
            raise
    
    async def update_token_window_counter(self, counter_id: int, token_count: int, request_count: int = 1) -> bool:
        """更新Token时间窗口计数器"""
        try:
            async with self.get_session() as session:
                stmt = update(self.token_window_counters).where(
                    self.token_window_counters.c.counter_id == counter_id
                ).values(
                    token_count=self.token_window_counters.c.token_count + token_count,
                    request_count=self.token_window_counters.c.request_count + request_count,
                    update_time=datetime.now()
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"更新Token时间窗口计数器失败: {str(e)}")
            return False
    
    async def cleanup_expired_token_counters(self) -> int:
        """清理过期的Token时间窗口计数器"""
        try:
            async with self.get_session() as session:
                stmt = self.token_window_counters.delete().where(
                    self.token_window_counters.c.window_end < datetime.now()
                )
                
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"清理过期Token计数器失败: {str(e)}")
            return 0

    # 命名空间路由相关方法
    async def get_namespace_route(self, namespace_id: int) -> Optional[Dict[str, Any]]:
        """获取命名空间的路由规则"""
        try:
            async with self.get_session() as session:
                # 从message_matchers表中查找该命名空间的路由规则
                result = await session.execute(
                    select(self.message_matchers).where(
                        self.message_matchers.c.namespace_id == namespace_id
                    ).order_by(self.message_matchers.c.priority.asc())
                )
                
                matchers = result.fetchall()
                if not matchers:
                    return None
                
                # 返回第一个匹配器作为路由规则
                matcher = matchers[0]
                return {
                    'route_id': matcher.matcher_id,
                    'namespace_id': matcher.namespace_id,
                    'matcher_type': matcher.matcher_type,
                    'match_field': matcher.match_field,
                    'match_operator': matcher.match_operator,
                    'match_value': matcher.match_value,
                    'status': matcher.status,
                    'create_time': matcher.create_time.isoformat() if matcher.create_time else None,
                    'update_time': matcher.update_time.isoformat() if matcher.update_time else None
                }
                
        except Exception as e:
            logger.error(f"获取命名空间路由规则失败: {str(e)}")
            raise

    async def create_or_update_namespace_route(self, route_data: Dict[str, Any]) -> int:
        """创建或更新命名空间路由规则"""
        try:
            async with self.get_session() as session:
                namespace_id = route_data['namespace_id']
                
                # 检查是否已存在路由规则
                existing_result = await session.execute(
                    select(self.message_matchers).where(
                        self.message_matchers.c.namespace_id == namespace_id
                    )
                )
                existing_matcher = existing_result.fetchone()
                
                if existing_matcher:
                    # 更新现有路由规则
                    await session.execute(
                        update(self.message_matchers).where(
                            self.message_matchers.c.matcher_id == existing_matcher.matcher_id
                        ).values(
                            matcher_type=route_data.get('matcher_type', 'header'),
                            match_field=route_data['match_field'],
                            match_operator=route_data['match_operator'],
                            match_value=route_data['match_value'],
                            update_time=datetime.now()
                        )
                    )
                    await session.commit()
                    return existing_matcher.matcher_id
                else:
                    # 创建新的路由规则
                    result = await session.execute(
                        insert(self.message_matchers).values(
                            namespace_id=namespace_id,
                            matcher_name=f"路由规则-{namespace_id}",
                            matcher_type=route_data.get('matcher_type', 'header'),
                            match_field=route_data['match_field'],
                            match_operator=route_data['match_operator'],
                            match_value=route_data['match_value'],
                            priority=100,
                            status=1
                        )
                    )
                    await session.commit()
                    return result.inserted_primary_key[0]
                
        except Exception as e:
            logger.error(f"创建或更新命名空间路由规则失败: {str(e)}")
            raise

    async def delete_namespace_route(self, namespace_id: int) -> bool:
        """删除命名空间路由规则"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    self.message_matchers.delete().where(
                        self.message_matchers.c.namespace_id == namespace_id
                    )
                )
                await session.commit()
                
                deleted_count = result.rowcount
                logger.info(f"删除了 {deleted_count} 个命名空间路由规则")
                return deleted_count > 0
                
        except Exception as e:
            logger.error(f"删除命名空间路由规则失败: {str(e)}")
            raise

    # Nginx上游服务器管理方法
    async def create_upstream_server(self, server_data: Dict[str, Any]) -> int:
        """创建上游服务器"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    insert(self.upstream_servers).values(
                        server_name=server_data['server_name'],
                        server_type=server_data['server_type'],
                        server_url=server_data['server_url'],
                        api_key=server_data.get('api_key'),
                        model_config=json.dumps(server_data.get('model_config', {})) if server_data.get('model_config') else None,
                        load_balance_weight=server_data.get('load_balance_weight', 1),
                        max_connections=server_data.get('max_connections', 100),
                        timeout_connect=server_data.get('timeout_connect', 30),
                        timeout_read=server_data.get('timeout_read', 300),
                        timeout_write=server_data.get('timeout_write', 300),
                        health_check_url=server_data.get('health_check_url'),
                        health_check_interval=server_data.get('health_check_interval', 30),
                        status=server_data.get('status', 1)
                    )
                )
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建上游服务器失败: {str(e)}")
            raise

    async def get_upstream_server(self, server_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取上游服务器"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(self.upstream_servers).where(
                        self.upstream_servers.c.server_id == server_id
                    )
                )
                row = result.first()
                
                if row:
                    model_config = None
                    if row.model_config:
                        try:
                            model_config = json.loads(row.model_config)
                        except json.JSONDecodeError:
                            pass
                    
                    return {
                        'server_id': row.server_id,
                        'server_name': row.server_name,
                        'server_type': row.server_type,
                        'server_url': row.server_url,
                        'api_key': row.api_key,
                        'model_config': model_config,
                        'load_balance_weight': row.load_balance_weight,
                        'max_connections': row.max_connections,
                        'timeout_connect': row.timeout_connect,
                        'timeout_read': row.timeout_read,
                        'timeout_write': row.timeout_write,
                        'health_check_url': row.health_check_url,
                        'health_check_interval': row.health_check_interval,
                        'status': row.status,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    }
                return None
        except Exception as e:
            logger.error(f"获取上游服务器失败: {str(e)}")
            return None

    async def get_all_upstream_servers(self) -> List[Dict[str, Any]]:
        """获取所有上游服务器"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(self.upstream_servers).order_by(self.upstream_servers.c.server_id.asc())
                )
                rows = result.fetchall()
                
                servers = []
                for row in rows:
                    model_config = None
                    if row.model_config:
                        try:
                            model_config = json.loads(row.model_config)
                        except json.JSONDecodeError:
                            pass
                    
                    servers.append({
                        'server_id': row.server_id,
                        'server_name': row.server_name,
                        'server_type': row.server_type,
                        'server_url': row.server_url,
                        'api_key': row.api_key,
                        'model_config': model_config,
                        'load_balance_weight': row.load_balance_weight,
                        'max_connections': row.max_connections,
                        'timeout_connect': row.timeout_connect,
                        'timeout_read': row.timeout_read,
                        'timeout_write': row.timeout_write,
                        'health_check_url': row.health_check_url,
                        'health_check_interval': row.health_check_interval,
                        'status': row.status,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    })
                return servers
        except Exception as e:
            logger.error(f"获取所有上游服务器失败: {str(e)}")
            return []

    async def update_upstream_server(self, server_id: int, server_data: Dict[str, Any]) -> bool:
        """更新上游服务器"""
        try:
            async with self.get_session() as session:
                stmt = update(self.upstream_servers).where(
                    self.upstream_servers.c.server_id == server_id
                ).values(
                    server_name=server_data.get('server_name'),
                    server_type=server_data.get('server_type'),
                    server_url=server_data.get('server_url'),
                    api_key=server_data.get('api_key'),
                    model_config=json.dumps(server_data.get('model_config', {})) if server_data.get('model_config') else None,
                    load_balance_weight=server_data.get('load_balance_weight'),
                    max_connections=server_data.get('max_connections'),
                    timeout_connect=server_data.get('timeout_connect'),
                    timeout_read=server_data.get('timeout_read'),
                    timeout_write=server_data.get('timeout_write'),
                    health_check_url=server_data.get('health_check_url'),
                    health_check_interval=server_data.get('health_check_interval'),
                    status=server_data.get('status'),
                    update_time=datetime.now()
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"更新上游服务器失败: {str(e)}")
            return False

    async def delete_upstream_server(self, server_id: int) -> bool:
        """删除上游服务器"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    self.upstream_servers.delete().where(
                        self.upstream_servers.c.server_id == server_id
                    )
                )
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"删除上游服务器失败: {str(e)}")
            return False

    # Nginx代理规则管理方法
    async def create_proxy_rule(self, rule_data: Dict[str, Any]) -> int:
        """创建代理规则"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    insert(self.proxy_rules).values(
                        rule_name=rule_data['rule_name'],
                        rule_type=rule_data['rule_type'],
                        match_pattern=rule_data['match_pattern'],
                        target_server_id=rule_data['target_server_id'],
                        rewrite_path=rule_data.get('rewrite_path'),
                        add_headers=json.dumps(rule_data.get('add_headers', {})) if rule_data.get('add_headers') else None,
                        priority=rule_data.get('priority', 100),
                        status=rule_data.get('status', 1)
                    )
                )
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建代理规则失败: {str(e)}")
            raise

    async def get_proxy_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取代理规则"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(self.proxy_rules).where(
                        self.proxy_rules.c.rule_id == rule_id
                    )
                )
                row = result.first()
                
                if row:
                    add_headers = None
                    if row.add_headers:
                        try:
                            add_headers = json.loads(row.add_headers)
                        except json.JSONDecodeError:
                            pass
                    
                    return {
                        'rule_id': row.rule_id,
                        'rule_name': row.rule_name,
                        'rule_type': row.rule_type,
                        'match_pattern': row.match_pattern,
                        'target_server_id': row.target_server_id,
                        'rewrite_path': row.rewrite_path,
                        'add_headers': add_headers,
                        'priority': row.priority if row.priority is not None else 100,
                        'status': row.status if row.status is not None else 1,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    }
                return None
        except Exception as e:
            logger.error(f"获取代理规则失败: {str(e)}")
            return None

    async def get_all_proxy_rules(self) -> List[Dict[str, Any]]:
        """获取所有代理规则"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(self.proxy_rules).order_by(self.proxy_rules.c.priority.asc())
                )
                rows = result.fetchall()
                
                rules = []
                for row in rows:
                    add_headers = None
                    if row.add_headers:
                        try:
                            add_headers = json.loads(row.add_headers)
                        except json.JSONDecodeError:
                            pass
                    
                    rules.append({
                        'rule_id': row.rule_id,
                        'rule_name': row.rule_name,
                        'rule_type': row.rule_type,
                        'match_pattern': row.match_pattern,
                        'target_server_id': row.target_server_id,
                        'rewrite_path': row.rewrite_path,
                        'add_headers': add_headers,
                        'priority': row.priority if row.priority is not None else 100,
                        'status': row.status if row.status is not None else 1,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    })
                return rules
        except Exception as e:
            logger.error(f"获取所有代理规则失败: {str(e)}")
            return []

    async def update_proxy_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> bool:
        """更新代理规则"""
        try:
            async with self.get_session() as session:
                stmt = update(self.proxy_rules).where(
                    self.proxy_rules.c.rule_id == rule_id
                ).values(
                    rule_name=rule_data.get('rule_name'),
                    rule_type=rule_data.get('rule_type'),
                    match_pattern=rule_data.get('match_pattern'),
                    target_server_id=rule_data.get('target_server_id'),
                    rewrite_path=rule_data.get('rewrite_path'),
                    add_headers=json.dumps(rule_data.get('add_headers', {})) if rule_data.get('add_headers') else None,
                    priority=rule_data.get('priority'),
                    status=rule_data.get('status'),
                    update_time=datetime.now()
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"更新代理规则失败: {str(e)}")
            return False

    async def delete_proxy_rule(self, rule_id: int) -> bool:
        """删除代理规则"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    self.proxy_rules.delete().where(
                        self.proxy_rules.c.rule_id == rule_id
                    )
                )
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"删除代理规则失败: {str(e)}")
            return False

    # Nginx全局配置管理方法
    async def create_nginx_config(self, config_data: Dict[str, Any]) -> int:
        """创建nginx配置"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    insert(self.nginx_config).values(
                        config_type=config_data['config_type'],
                        config_name=config_data['config_name'],
                        config_value=json.dumps(config_data.get('config_value', {})) if config_data.get('config_value') else None,
                        description=config_data.get('description'),
                        status=config_data.get('status', 1)
                    )
                )
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建nginx配置失败: {str(e)}")
            raise

    async def get_nginx_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取nginx配置"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(self.nginx_config).where(
                        self.nginx_config.c.config_id == config_id
                    )
                )
                row = result.first()
                
                if row:
                    config_value = None
                    if row.config_value:
                        try:
                            config_value = json.loads(row.config_value)
                        except json.JSONDecodeError:
                            pass
                    
                    return {
                        'config_id': row.config_id,
                        'config_type': row.config_type,
                        'config_name': row.config_name,
                        'config_value': config_value,
                        'description': row.description,
                        'status': row.status,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    }
                return None
        except Exception as e:
            logger.error(f"获取nginx配置失败: {str(e)}")
            return None

    async def get_nginx_configs_by_type(self, config_type: str) -> List[Dict[str, Any]]:
        """根据类型获取nginx配置"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(self.nginx_config).where(
                        self.nginx_config.c.config_type == config_type,
                        self.nginx_config.c.status == 1
                    ).order_by(self.nginx_config.c.config_id.asc())
                )
                rows = result.fetchall()
                
                configs = []
                for row in rows:
                    config_value = None
                    if row.config_value:
                        try:
                            config_value = json.loads(row.config_value)
                        except json.JSONDecodeError:
                            pass
                    
                    configs.append({
                        'config_id': row.config_id,
                        'config_type': row.config_type,
                        'config_name': row.config_name,
                        'config_value': config_value,
                        'description': row.description,
                        'status': row.status,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    })
                return configs
        except Exception as e:
            logger.error(f"获取nginx配置失败: {str(e)}")
            return []

    async def get_all_nginx_configs(self) -> List[Dict[str, Any]]:
        """获取所有nginx配置（默认仅返回启用状态）"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(self.nginx_config)
                    .where(self.nginx_config.c.status == 1)
                    .order_by(self.nginx_config.c.config_type.asc(), self.nginx_config.c.config_id.asc())
                )
                rows = result.fetchall()

                configs = []
                for row in rows:
                    config_value = None
                    if row.config_value:
                        try:
                            config_value = json.loads(row.config_value)
                        except json.JSONDecodeError:
                            pass

                    configs.append({
                        'config_id': row.config_id,
                        'config_type': row.config_type,
                        'config_name': row.config_name,
                        'config_value': config_value,
                        'description': row.description,
                        'status': row.status,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    })
                return configs
        except Exception as e:
            logger.error(f"获取nginx配置失败: {str(e)}")
            return []

    async def update_nginx_config(self, config_id: int, config_data: Dict[str, Any]) -> bool:
        """更新nginx配置"""
        try:
            async with self.get_session() as session:
                stmt = update(self.nginx_config).where(
                    self.nginx_config.c.config_id == config_id
                ).values(
                    config_type=config_data.get('config_type'),
                    config_name=config_data.get('config_name'),
                    config_value=json.dumps(config_data.get('config_value', {})) if config_data.get('config_value') else None,
                    description=config_data.get('description'),
                    status=config_data.get('status'),
                    update_time=datetime.now()
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"更新nginx配置失败: {str(e)}")
            return False

    async def delete_nginx_config(self, config_id: int) -> bool:
        """删除nginx配置"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    self.nginx_config.delete().where(
                        self.nginx_config.c.config_id == config_id
                    )
                )
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"删除nginx配置失败: {str(e)}")
            return False

    # ==================== 路由规则管理 ====================
    
    async def create_location_rule(self, location_data: Dict[str, Any]) -> int:
        """创建路由规则"""
        try:
            async with self.get_session() as session:
                stmt = insert(self.location_rules).values(
                    path=location_data['path'],
                    upstream_id=location_data['upstream_id'],
                    proxy_cache=location_data.get('proxy_cache', False),
                    proxy_buffering=location_data.get('proxy_buffering', False),
                    proxy_pass=location_data.get('proxy_pass'),
                    is_regex=location_data.get('is_regex', False),
                    limit_req_config=json.dumps(location_data.get('limit_req_config', {})) if location_data.get('limit_req_config') else None,
                    sse_support=location_data.get('sse_support', False),
                    chunked_transfer=location_data.get('chunked_transfer', False),
                    matcher_type=location_data.get('matcher_type', 'path'),
                    match_field=location_data.get('match_field'),
                    match_operator=location_data.get('match_operator'),
                    match_value=location_data.get('match_value'),
                    add_headers=json.dumps(location_data.get('add_headers', {})) if location_data.get('add_headers') else None,
                    rewrite_path=location_data.get('rewrite_path'),
                    path_rewrite_config=json.dumps(location_data.get('path_rewrite_config', {})) if location_data.get('path_rewrite_config') else None,
                    priority=location_data.get('priority', 100),
                    status=location_data.get('status', 1),
                    created_by=location_data.get('created_by'),
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )
                
                result = await session.execute(stmt)
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建路由规则失败: {str(e)}")
            raise
    
    async def get_location_rule(self, location_id: int) -> Optional[Dict[str, Any]]:
        """获取路由规则"""
        try:
            async with self.get_session() as session:
                stmt = select(self.location_rules).where(
                    self.location_rules.c.location_id == location_id,
                    self.location_rules.c.status == 1
                )
                result = await session.execute(stmt)
                row = result.first()
                
                if row:
                    limit_req_config = None
                    if row.limit_req_config:
                        try:
                            limit_req_config = json.loads(row.limit_req_config)
                        except json.JSONDecodeError:
                            pass
                    
                    add_headers = None
                    if row.add_headers:
                        try:
                            add_headers = json.loads(row.add_headers)
                        except json.JSONDecodeError:
                            pass
                    
                    return {
                        'location_id': row.location_id,
                        'path': row.path,
                        'upstream_id': row.upstream_id,
                        'proxy_cache': row.proxy_cache,
                        'proxy_buffering': row.proxy_buffering,
                        'proxy_pass': row.proxy_pass,
                        'is_regex': row.is_regex,
                        'limit_req_config': limit_req_config,
                        'sse_support': row.sse_support,
                        'chunked_transfer': row.chunked_transfer,
                        'matcher_type': row.matcher_type,
                        'match_field': row.match_field,
                        'match_operator': row.match_operator,
                        'match_value': row.match_value,
                        'add_headers': add_headers,
                        'rewrite_path': row.rewrite_path,
                        'priority': row.priority if row.priority is not None else 100,
                        'status': row.status if row.status is not None else 1,
                        'created_by': row.created_by,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    }
                return None
        except Exception as e:
            logger.error(f"获取路由规则失败: {str(e)}")
            return None
    
    async def get_all_location_rules(self) -> List[Dict[str, Any]]:
        """获取所有路由规则"""
        try:
            async with self.get_session() as session:
                stmt = select(self.location_rules).where(self.location_rules.c.status == 1)
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                location_rules = []
                for row in rows:
                    limit_req_config = None
                    if row.limit_req_config:
                        try:
                            limit_req_config = json.loads(row.limit_req_config)
                        except json.JSONDecodeError:
                            pass
                    
                    add_headers = None
                    if row.add_headers:
                        try:
                            add_headers = json.loads(row.add_headers)
                        except json.JSONDecodeError:
                            pass
                    
                    path_rewrite_config = {}
                    if row.path_rewrite_config:
                        try:
                            path_rewrite_config = json.loads(row.path_rewrite_config)
                        except json.JSONDecodeError:
                            path_rewrite_config = {}
                    
                    location_rules.append({
                        'location_id': row.location_id,
                        'path': row.path,
                        'upstream_id': row.upstream_id,
                        'proxy_cache': row.proxy_cache,
                        'proxy_buffering': row.proxy_buffering,
                        'proxy_pass': row.proxy_pass,
                        'is_regex': row.is_regex,
                        'limit_req_config': limit_req_config,
                        'sse_support': row.sse_support,
                        'chunked_transfer': row.chunked_transfer,
                        'matcher_type': row.matcher_type,
                        'match_field': row.match_field,
                        'match_operator': row.match_operator,
                        'match_value': row.match_value,
                        'add_headers': add_headers,
                        'rewrite_path': row.rewrite_path,
                        'path_rewrite_config': path_rewrite_config,
                        'priority': row.priority if row.priority is not None else 100,
                        'status': row.status if row.status is not None else 1,
                        'created_by': row.created_by,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    })
                
                return location_rules
        except Exception as e:
            logger.error(f"获取所有路由规则失败: {str(e)}")
            return []
    
    async def update_location_rule(self, location_id: int, location_data: Dict[str, Any]) -> bool:
        """更新路由规则"""
        try:
            print(f"DEBUG: Updating location {location_id} with data: {location_data}")
            async with self.get_session() as session:
                stmt = update(self.location_rules).where(
                    self.location_rules.c.location_id == location_id
                ).values(
                    path=location_data.get('path'),
                    upstream_id=location_data.get('upstream_id'),
                    proxy_cache=location_data.get('proxy_cache'),
                    proxy_buffering=location_data.get('proxy_buffering'),
                    proxy_pass=location_data.get('proxy_pass'),
                    is_regex=location_data.get('is_regex'),
                    limit_req_config=json.dumps(location_data.get('limit_req_config', {})) if location_data.get('limit_req_config') else None,
                    sse_support=location_data.get('sse_support'),
                    chunked_transfer=location_data.get('chunked_transfer'),
                    matcher_type=location_data.get('matcher_type'),
                    match_field=location_data.get('match_field'),
                    match_operator=location_data.get('match_operator'),
                    match_value=location_data.get('match_value'),
                    add_headers=json.dumps(location_data.get('add_headers', {})) if location_data.get('add_headers') else None,
                    rewrite_path=location_data.get('rewrite_path'),
                    path_rewrite_config=json.dumps(location_data.get('path_rewrite_config', {})) if location_data.get('path_rewrite_config') else None,
                    priority=location_data.get('priority'),
                    status=location_data.get('status'),
                    update_time=datetime.now()
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"更新路由规则失败: {str(e)}")
            return False
    
    async def delete_location_rule(self, location_id: int) -> bool:
        """删除路由规则（硬删除）"""
        try:
            async with self.get_session() as session:
                stmt = self.location_rules.delete().where(
                    self.location_rules.c.location_id == location_id
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"删除路由规则失败: {str(e)}")
            return False

    # ==================== 访问日志管理 ====================
    
    async def get_access_logs(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取访问日志"""
        try:
            async with self.get_session() as session:
                stmt = select(self.access_logs)
                
                # 应用筛选条件
                if filters:
                    if filters.get('start_time'):
                        stmt = stmt.where(self.access_logs.c.timestamp >= filters['start_time'])
                    if filters.get('end_time'):
                        stmt = stmt.where(self.access_logs.c.timestamp <= filters['end_time'])
                    if filters.get('level'):
                        stmt = stmt.where(self.access_logs.c.status_code >= 400 if filters['level'] == 'error' else self.access_logs.c.status_code < 400)
                    if filters.get('namespace_id'):
                        stmt = stmt.where(self.access_logs.c.namespace_id == filters['namespace_id'])
                    if filters.get('search'):
                        search_term = f"%{filters['search']}%"
                        stmt = stmt.where(
                            (self.access_logs.c.path.like(search_term)) |
                            (self.access_logs.c.client_ip.like(search_term)) |
                            (self.access_logs.c.error_message.like(search_term))
                        )
                
                # 排序和分页
                stmt = stmt.order_by(self.access_logs.c.timestamp.desc()).limit(limit).offset(offset)
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                logs = []
                for row in rows:
                    logs.append({
                        'log_id': row.log_id,
                        'request_id': row.request_id,
                        'namespace_id': row.namespace_id,
                        'upstream_id': row.upstream_id,
                        'client_ip': row.client_ip,
                        'user_agent': row.user_agent,
                        'method': row.method,
                        'path': row.path,
                        'status_code': row.status_code,
                        'response_time': row.response_time,
                        'request_size': row.request_size,
                        'response_size': row.response_size,
                        'input_tokens': row.input_tokens,
                        'output_tokens': row.output_tokens,
                        'api_key': row.api_key,
                        'error_message': row.error_message,
                        'timestamp': row.timestamp.isoformat(),
                        'create_time': row.create_time.isoformat()
                    })
                
                return logs
        except Exception as e:
            logger.error(f"获取访问日志失败: {str(e)}")
            return []
    
    async def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计"""
        try:
            async with self.get_session() as session:
                # 总日志数
                total_stmt = select(func.count(self.access_logs.c.log_id))
                total_result = await session.execute(total_stmt)
                total_logs = total_result.scalar() or 0
                
                # 错误日志数
                error_stmt = select(func.count(self.access_logs.c.log_id)).where(self.access_logs.c.status_code >= 400)
                error_result = await session.execute(error_stmt)
                error_count = error_result.scalar() or 0
                
                # 警告日志数（2xx-3xx但有错误信息）
                warning_stmt = select(func.count(self.access_logs.c.log_id)).where(
                    (self.access_logs.c.status_code < 400) & 
                    (self.access_logs.c.error_message.isnot(None))
                )
                warning_result = await session.execute(warning_stmt)
                warning_count = warning_result.scalar() or 0
                
                # 信息日志数
                info_count = total_logs - error_count - warning_count
                
                # 错误率
                error_rate = f"{(error_count / total_logs * 100):.1f}%" if total_logs > 0 else "0%"
                
                # 平均响应时间
                avg_response_stmt = select(self.access_logs.c.response_time).where(
                    self.access_logs.c.response_time.isnot(None)
                )
                avg_response_result = await session.execute(avg_response_stmt)
                response_times = [row[0] for row in avg_response_result.fetchall() if row[0] is not None]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                return {
                    'total_logs': total_logs,
                    'error_count': error_count,
                    'warning_count': warning_count,
                    'info_count': info_count,
                    'debug_count': 0,  # 暂时设为0
                    'error_rate': error_rate,
                    'avg_response_time': int(avg_response_time)
                }
        except Exception as e:
            logger.error(f"获取日志统计失败: {str(e)}")
            return {
                'total_logs': 0,
                'error_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'debug_count': 0,
                'error_rate': '0%',
                'avg_response_time': 0
            }
    
    async def create_access_log(self, log_data: Dict[str, Any]) -> int:
        """创建访问日志"""
        try:
            async with self.get_session() as session:
                stmt = insert(self.access_logs).values(
                    request_id=log_data.get('request_id'),
                    namespace_id=log_data.get('namespace_id'),
                    upstream_id=log_data.get('upstream_id'),
                    client_ip=log_data.get('client_ip'),
                    user_agent=log_data.get('user_agent'),
                    method=log_data.get('method'),
                    path=log_data.get('path'),
                    status_code=log_data.get('status_code'),
                    response_time=log_data.get('response_time'),
                    request_size=log_data.get('request_size'),
                    response_size=log_data.get('response_size'),
                    input_tokens=log_data.get('input_tokens'),
                    output_tokens=log_data.get('output_tokens'),
                    api_key=log_data.get('api_key'),
                    error_message=log_data.get('error_message'),
                    timestamp=log_data.get('timestamp', datetime.now())
                )
                
                result = await session.execute(stmt)
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建访问日志失败: {str(e)}")
            raise 

    # ==================== 策略管理 ====================
    
    async def create_policy(self, policy_data: Dict[str, Any]) -> int:
        """创建策略"""
        try:
            async with self.get_session() as session:
                stmt = insert(self.policies).values(
                    policy_name=policy_data['policy_name'],
                    policy_type=policy_data['policy_type'],
                    description=policy_data.get('description', ''),
                    namespace_id=policy_data.get('namespace_id'),
                    namespaces=json.dumps(policy_data.get('namespaces', [])),
                    rules=json.dumps(policy_data.get('rules', [])),
                    rule_type=policy_data.get('rule_type'),
                    rule_config=json.dumps(policy_data.get('rule_config', {})) if isinstance(policy_data.get('rule_config'), dict) else policy_data.get('rule_config'),
                    priority=policy_data.get('priority', 100),
                    status=policy_data.get('status', 1),
                    created_by=policy_data.get('created_by'),
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )
                
                result = await session.execute(stmt)
                await session.commit()
                return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"创建策略失败: {str(e)}")
            raise
    
    async def get_policy_by_id(self, policy_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取策略"""
        try:
            async with self.get_session() as session:
                # 查询 status = 1 或 status IS NULL 的记录（NULL 视为启用状态）
                stmt = select(self.policies).where(
                    self.policies.c.policy_id == policy_id,
                    (self.policies.c.status == 1) | (self.policies.c.status.is_(None))
                )
                result = await session.execute(stmt)
                row = result.first()
                
                if row:
                    return {
                        'policy_id': row.policy_id,
                        'policy_name': row.policy_name,
                        'policy_type': row.policy_type,
                        'description': row.description,
                        'namespace_id': row.namespace_id,
                        'namespaces': json.loads(row.namespaces) if row.namespaces else [],
                        'rules': json.loads(row.rules) if row.rules else [],
                        'rule_type': row.rule_type,
                        'rule_config': json.loads(row.rule_config) if row.rule_config else {},
                        'priority': row.priority if row.priority is not None else 100,
                        'status': row.status if row.status is not None else 1,
                        'created_by': row.created_by,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    }
                return None
        except Exception as e:
            logger.error(f"获取策略失败: {str(e)}")
            return None
    
    async def get_all_policies(self, policy_type: str = None, status_filter: str = None) -> List[Dict[str, Any]]:
        """获取所有策略，支持状态过滤"""
        try:
            async with self.get_session() as session:
                # 构建基础查询
                stmt = select(self.policies)
                
                # 应用状态过滤
                if status_filter == "enabled":
                    # 只返回启用状态的策略
                    stmt = stmt.where(
                        (self.policies.c.status == 1) | (self.policies.c.status.is_(None))
                    )
                elif status_filter == "disabled":
                    # 只返回禁用状态的策略
                    stmt = stmt.where(self.policies.c.status == 0)
                # 如果 status_filter 为 None 或 "all"，则返回所有策略
                
                if policy_type:
                    stmt = stmt.where(self.policies.c.policy_type == policy_type)
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                policies = []
                for row in rows:
                    policies.append({
                        'policy_id': row.policy_id,
                        'policy_name': row.policy_name,
                        'policy_type': row.policy_type,
                        'description': row.description,
                        'namespace_id': row.namespace_id,
                        'namespaces': json.loads(row.namespaces) if row.namespaces else [],
                        'rules': json.loads(row.rules) if row.rules else [],
                        'rule_type': row.rule_type,
                        'rule_config': json.loads(row.rule_config) if row.rule_config else {},
                        'priority': row.priority if row.priority is not None else 100,
                        'status': row.status if row.status is not None else 1,
                        'created_by': row.created_by,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    })
                return policies
        except Exception as e:
            logger.error(f"获取所有策略失败: {str(e)}")
            return []
    
    async def get_policies_by_namespace(self, namespace_id: int, policy_type: str = None) -> List[Dict[str, Any]]:
        """获取命名空间下的所有策略"""
        try:
            async with self.get_session() as session:
                stmt = select(self.policies).where(
                    self.policies.c.namespace_id == namespace_id,
                    (self.policies.c.status == 1) | (self.policies.c.status.is_(None))
                )
                
                if policy_type:
                    stmt = stmt.where(self.policies.c.policy_type == policy_type)
                
                stmt = stmt.order_by(self.policies.c.priority.asc())
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                policies = []
                for row in rows:
                    policies.append({
                        'policy_id': row.policy_id,
                        'policy_name': row.policy_name,
                        'policy_type': row.policy_type,
                        'description': row.description,
                        'namespace_id': row.namespace_id,
                        'namespaces': json.loads(row.namespaces) if row.namespaces else [],
                        'rules': json.loads(row.rules) if row.rules else [],
                        'rule_type': row.rule_type,
                        'rule_config': json.loads(row.rule_config) if row.rule_config else {},
                        'priority': row.priority if row.priority is not None else 100,
                        'status': row.status if row.status is not None else 1,
                        'created_by': row.created_by,
                        'create_time': row.create_time.isoformat(),
                        'update_time': row.update_time.isoformat()
                    })
                return policies
        except Exception as e:
            logger.error(f"获取命名空间策略失败: {str(e)}")
            return []
    
    async def update_policy(self, policy_id: int, policy_data: Dict[str, Any]) -> bool:
        """更新策略"""
        try:
            async with self.get_session() as session:
                stmt = update(self.policies).where(
                    self.policies.c.policy_id == policy_id
                ).values(
                    policy_name=policy_data.get('policy_name'),
                    policy_type=policy_data.get('policy_type'),
                    description=policy_data.get('description'),
                    namespace_id=policy_data.get('namespace_id'),
                    namespaces=json.dumps(policy_data.get('namespaces', [])) if 'namespaces' in policy_data else None,
                    rules=json.dumps(policy_data.get('rules', [])) if 'rules' in policy_data else None,
                    rule_type=policy_data.get('rule_type'),
                    rule_config=json.dumps(policy_data['rule_config']) if 'rule_config' in policy_data and isinstance(policy_data['rule_config'], dict) else policy_data.get('rule_config'),
                    priority=policy_data.get('priority', 100) if 'priority' in policy_data else None,
                    status=policy_data.get('status', 1) if 'status' in policy_data else None,
                    update_time=datetime.now()
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"更新策略失败: {str(e)}")
            return False
    
    async def delete_policy(self, policy_id: int) -> bool:
        """删除策略（硬删除）"""
        try:
            async with self.get_session() as session:
                stmt = self.policies.delete().where(
                    self.policies.c.policy_id == policy_id
                )
                
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"删除策略失败: {str(e)}")
            return False