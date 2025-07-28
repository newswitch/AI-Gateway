"""
通用规则管理API
"""

import logging
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager, ConfigCache
from app.core.dependencies import get_db_manager, get_cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["通用规则管理"])

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

@router.get("/rules/types")
async def get_rule_types(current_user: Dict = Depends(get_current_user)):
    """获取支持的规则类型"""
    return {
        "rule_types": [
            {
                "type": "matcher",
                "name": "报文匹配",
                "description": "基于字段匹配的访问控制规则",
                "config_schema": {
                    "matcher_type": {
                        "type": "string",
                        "enum": ["header", "body", "query", "path"],
                        "description": "匹配字段来源：header-报文头，body-请求体，query-查询参数，path-路径参数"
                    },
                    "match_field": {
                        "type": "string",
                        "description": "匹配字段名称"
                    },
                    "match_operator": {
                        "type": "string",
                        "enum": ["eq", "ne", "gt", "gte", "lt", "lte", "contains", "regex"],
                        "description": "匹配操作符：eq-等于，ne-不等于，gt-大于，gte-大于等于，lt-小于，lte-小于等于，contains-包含，regex-正则匹配"
                    },
                    "match_value": {
                        "type": "string",
                        "description": "匹配值"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["allow", "deny"],
                        "description": "匹配动作：allow-允许通过，deny-拒绝请求"
                    }
                }
            },
            {
                "type": "token_limit",
                "name": "Token限制",
                "description": "限制请求的Token数量",
                "config_schema": {
                    "model_name": {
                        "type": "string",
                        "description": "模型名称"
                    },
                    "max_tokens": {
                        "type": "number",
                        "description": "最大Token数量"
                    },
                    "time_window_enabled": {
                        "type": "boolean",
                        "description": "是否启用时间窗口"
                    },
                    "time_window_minutes": {
                        "type": "number",
                        "description": "时间窗口分钟数"
                    },
                    "max_tokens_per_window": {
                        "type": "number",
                        "description": "时间窗口内最大Token数量"
                    }
                }
            },
            {
                "type": "concurrent_limit", 
                "name": "并发限制",
                "description": "限制并发连接数",
                "config_schema": {
                    "max_concurrent": {
                        "type": "number",
                        "description": "最大并发连接数"
                    }
                }
            },
            {
                "type": "rate_limit",
                "name": "QPS限制", 
                "description": "限制每秒请求数",
                "config_schema": {
                    "max_qps": {
                        "type": "number",
                        "description": "最大QPS"
                    },
                    "time_window_seconds": {
                        "type": "number",
                        "description": "时间窗口秒数"
                    }
                }
            }
        ]
    }

@router.get("/rules/{rule_id}", response_model=Dict[str, Any])
async def get_rule(rule_id: int):
    """获取单个规则"""
    try:
        db = get_db()
        rule = await db.get_rule_by_id(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        # 解析rule_config
        if rule.get('rule_config'):
            try:
                rule['rule_config'] = json.loads(rule['rule_config'])
            except json.JSONDecodeError:
                pass
        
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取规则失败: {str(e)}")

@router.get("/namespaces/{namespace_id}/rules", response_model=List[Dict[str, Any]])
async def get_rules_by_namespace(
    namespace_id: int, 
    rule_type: Optional[str] = Query(None, description="规则类型过滤")
):
    """获取命名空间下的所有规则 - 缓存优先策略"""
    try:
        cache = get_cache()
        rules = await cache.get_rules(namespace_id)
        
        # 如果指定了规则类型，进行过滤
        if rule_type:
            rules = [rule for rule in rules if rule.get('rule_type') == rule_type]
        
        # 解析每个规则的rule_config
        for rule in rules:
            if rule.get('rule_config'):
                try:
                    rule['rule_config'] = json.loads(rule['rule_config'])
                except json.JSONDecodeError:
                    pass
        
        return rules
    except Exception as e:
        logger.error(f"获取命名空间规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取命名空间规则失败: {str(e)}")

@router.get("/rules", response_model=List[Dict[str, Any]])
async def get_all_rules(rule_type: Optional[str] = Query(None, description="规则类型过滤")):
    """获取所有规则"""
    try:
        db = get_db()
        rules = await db.get_all_rules()
        
        # 如果指定了规则类型，进行过滤
        if rule_type:
            rules = [rule for rule in rules if rule.get('rule_type') == rule_type]
        
        # 解析每个规则的rule_config
        for rule in rules:
            if rule.get('rule_config'):
                try:
                    rule['rule_config'] = json.loads(rule['rule_config'])
                except json.JSONDecodeError:
                    pass
        
        return rules
    except Exception as e:
        logger.error(f"获取所有规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取所有规则失败: {str(e)}")

@router.post("/namespaces/{namespace_id}/rules")
async def create_rule(namespace_id: int, rule_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """创建规则 - 双写策略"""
    try:
        cache = get_cache()
        
        # 验证必要字段
        required_fields = ['rule_name', 'rule_type', 'rule_config']
        for field in required_fields:
            if field not in rule_data:
                raise HTTPException(status_code=400, detail=f"缺少必要字段: {field}")
        
        # 添加命名空间ID
        rule_data['namespace_id'] = namespace_id
        
        # 确保rule_config是JSON字符串
        if isinstance(rule_data['rule_config'], dict):
            rule_data['rule_config'] = json.dumps(rule_data['rule_config'])
        
        # 使用双写策略创建规则
        rule_id = await cache.create_rule_dual_write(rule_data)
        
        logger.info(f"规则创建成功，rule_id={rule_id}, namespace_id={namespace_id}, rule_type={rule_data['rule_type']}")
        return {"message": "规则创建成功", "rule_id": rule_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建规则失败: {str(e)}")

@router.put("/rules/{rule_id}")
async def update_rule(rule_id: int, rule_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """更新规则"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查规则是否存在
        existing = await db.get_rule_by_id(rule_id)
        if not existing:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        # 确保rule_config是JSON字符串
        if 'rule_config' in rule_data and isinstance(rule_data['rule_config'], dict):
            rule_data['rule_config'] = json.dumps(rule_data['rule_config'])
        
        # 更新规则
        success = await db.update_rule(rule_id, rule_data)
        if not success:
            raise HTTPException(status_code=500, detail="更新规则失败")
        
        # 更新缓存
        namespace_id = existing['namespace_id']
        rules = await db.get_rules_by_namespace(namespace_id)
        await cache.set_rules(namespace_id, rules)
        
        logger.info(f"规则更新成功，rule_id={rule_id}")
        return {"message": "规则更新成功", "rule_id": rule_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新规则失败: {str(e)}")

@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int, current_user: Dict = Depends(get_current_user)):
    """删除规则"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查规则是否存在
        existing = await db.get_rule_by_id(rule_id)
        if not existing:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        # 删除规则
        success = await db.delete_rule(rule_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除规则失败")
        
        # 更新缓存
        namespace_id = existing['namespace_id']
        rules = await db.get_rules_by_namespace(namespace_id)
        await cache.set_rules(namespace_id, rules)
        
        logger.info(f"规则删除成功，rule_id={rule_id}")
        return {"message": "规则删除成功", "rule_id": rule_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除规则失败: {str(e)}") 