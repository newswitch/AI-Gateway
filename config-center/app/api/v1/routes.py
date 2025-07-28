"""
命名空间路由API
"""

import logging
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager, ConfigCache
from app.core.dependencies import get_db_manager, get_cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["命名空间路由"])

# 安全认证
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户（直接返回用户信息）"""
    try:
        # 简化认证，实际项目中应该验证JWT token
        return {"user_id": "admin", "username": "admin"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_db():
    """获取数据库管理器"""
    return get_db_manager()

def get_cache():
    """获取缓存管理器"""
    return get_cache_manager()

@router.post("/route/namespace")
async def route_to_namespace(request_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """
    根据报文内容路由到目标命名空间
    
    请求格式：
    {
        "headers": {"X-Service-Type": "chatgpt", "Content-Type": "application/json"},
        "query_params": {"model": "gpt-4"},
        "body": {"prompt": "Hello world"},
        "path": "/v1/chat/completions"
    }
    """
    try:
        db = get_db()
        cache = get_cache()
        
        # 获取所有命名空间的匹配器规则
        all_rules = await db.get_all_rules()
        matcher_rules = [rule for rule in all_rules if rule.get('rule_type') == 'matcher']
        
        # 按优先级排序
        matcher_rules.sort(key=lambda x: x.get('priority', 100))
        
        # 遍历匹配器规则，找到第一个匹配的
        for rule in matcher_rules:
            if rule.get('status') != 1:  # 跳过禁用的规则
                continue
                
            rule_config = rule.get('rule_config')
            if isinstance(rule_config, str):
                try:
                    rule_config = json.loads(rule_config)
                except json.JSONDecodeError:
                    continue
            
            if not rule_config:
                continue
            
            # 检查是否匹配
            if _match_request(rule_config, request_data):
                target_namespace = rule_config.get('target_namespace')
                if target_namespace:
                    # 获取目标命名空间信息
                    namespace_info = await _get_namespace_by_code(db, target_namespace)
                    if namespace_info:
                        return {
                            "matched": True,
                            "rule_id": rule.get('rule_id'),
                            "rule_name": rule.get('rule_name'),
                            "target_namespace": target_namespace,
                            "namespace_info": namespace_info,
                            "matched_config": rule_config
                        }
        
        # 没有找到匹配的规则，返回默认命名空间
        default_namespace = await _get_default_namespace(db)
        return {
            "matched": False,
            "target_namespace": "default",
            "namespace_info": default_namespace,
            "message": "未找到匹配的规则，使用默认命名空间"
        }
        
    except Exception as e:
        logger.error(f"路由到命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"路由失败: {str(e)}")

@router.post("/route/validate")
async def validate_routing(request_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """
    验证报文路由规则（用于测试）
    """
    try:
        db = get_db()
        
        # 获取所有匹配器规则
        all_rules = await db.get_all_rules()
        matcher_rules = [rule for rule in all_rules if rule.get('rule_type') == 'matcher']
        
        # 按优先级排序（数字越小越优先）
        matcher_rules.sort(key=lambda x: x.get('priority', 100))
        
        results = []
        for rule in matcher_rules:
            rule_config = rule.get('rule_config')
            if isinstance(rule_config, str):
                try:
                    rule_config = json.loads(rule_config)
                except json.JSONDecodeError:
                    continue
            
            is_matched = _match_request(rule_config, request_data) if rule_config else False
            
            results.append({
                "rule_id": rule.get('rule_id'),
                "rule_name": rule.get('rule_name'),
                "priority": rule.get('priority'),
                "status": rule.get('status'),
                "matched": is_matched,
                "config": rule_config
            })
        
        return {
            "request_data": request_data,
            "rules": results
        }
        
    except Exception as e:
        logger.error(f"验证路由规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")

def _match_request(rule_config: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
    """检查请求是否匹配规则"""
    try:
        matcher_type = rule_config.get('matcher_type', 'header')
        match_field = rule_config.get('match_field')
        match_operator = rule_config.get('match_operator', 'equals')
        match_value = rule_config.get('match_value')
        
        if not match_field or not match_value:
            return False
        
        # 根据匹配类型获取要检查的数据
        if matcher_type == 'header':
            data_to_check = request_data.get('headers', {})
        elif matcher_type == 'query':
            data_to_check = request_data.get('query_params', {})
        elif matcher_type == 'body':
            data_to_check = request_data.get('body', {})
        elif matcher_type == 'path':
            data_to_check = request_data.get('path', '')
        else:
            return False
        
        # 获取字段值
        if matcher_type == 'path':
            field_value = data_to_check
        else:
            field_value = data_to_check.get(match_field)
        
        if field_value is None:
            return False
        
        # 根据操作符进行匹配
        if match_operator == 'equals':
            return str(field_value) == str(match_value)
        elif match_operator == 'contains':
            return str(match_value) in str(field_value)
        elif match_operator == 'starts_with':
            return str(field_value).startswith(str(match_value))
        elif match_operator == 'ends_with':
            return str(field_value).endswith(str(match_value))
        elif match_operator == 'regex':
            import re
            try:
                return bool(re.search(str(match_value), str(field_value)))
            except:
                return False
        
        return False
        
    except Exception as e:
        logger.error(f"匹配请求失败: {str(e)}")
        return False

async def _get_namespace_by_code(db: DatabaseManager, namespace_code: str) -> Optional[Dict[str, Any]]:
    """根据命名空间代码获取命名空间信息"""
    try:
        # 这里需要实现根据namespace_code查询命名空间的方法
        # 暂时返回模拟数据
        return {
            "namespace_id": 1,
            "namespace_code": namespace_code,
            "namespace_name": f"{namespace_code} Service",
            "description": f"Namespace for {namespace_code}",
            "status": 1
        }
    except Exception as e:
        logger.error(f"获取命名空间信息失败: {str(e)}")
        return None

async def _get_default_namespace(db: DatabaseManager) -> Optional[Dict[str, Any]]:
    """获取默认命名空间"""
    try:
        # 这里需要实现获取默认命名空间的方法
        return {
            "namespace_id": 1,
            "namespace_code": "default",
            "namespace_name": "Default Service",
            "description": "Default namespace",
            "status": 1
        }
    except Exception as e:
        logger.error(f"获取默认命名空间失败: {str(e)}")
        return None 