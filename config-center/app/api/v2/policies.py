"""
策略配置管理API适配层 - 适配新前端接口需求
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models import DatabaseManager, ConfigCache
from app.core.dependencies import get_db_manager, get_cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["策略配置管理V2"])

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

@router.get("/policies", response_model=Dict[str, Any])
async def get_policies(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    policy_type: Optional[str] = Query(None, description="策略类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选")
):
    """
    获取策略列表 - 适配新前端接口格式
    支持分页、搜索和筛选
    """
    try:
        db = get_db()
        
        # 获取所有策略规则
        all_rules = await db.get_all_rules()
        
        # 应用搜索和筛选条件
        filtered_policies = []
        for rule in all_rules:
            # 关键词搜索
            if keyword:
                keyword_lower = keyword.lower()
                if not any(keyword_lower in str(rule.get(field, '')).lower() 
                          for field in ['rule_name', 'rule_type', 'description']):
                    continue
            
            # 策略类型筛选
            if policy_type and rule.get('rule_type') != policy_type:
                continue
            
            # 状态筛选
            if status:
                rule_status = "enabled" if rule.get('status') == 1 else "disabled"
                if rule_status != status:
                    continue
            
            # 转换为新前端期望的格式
            policy_data = {
                "id": str(rule.get('rule_id', '')),
                "name": rule.get('rule_name', ''),
                "type": rule.get('rule_type', ''),
                "description": rule.get('description', ''),
                "config": rule.get('rule_config', {}),
                "status": "enabled" if rule.get('status') == 1 else "disabled",
                "priority": rule.get('priority', 100),
                "namespace_id": str(rule.get('namespace_id', '')),
                "createdAt": rule.get('create_time', '')[:10] if rule.get('create_time') else '',
                "updatedAt": rule.get('update_time', '')[:10] if rule.get('update_time') else ''
            }
            
            filtered_policies.append(policy_data)
        
        # 分页处理
        total = len(filtered_policies)
        start = (page - 1) * size
        end = start + size
        paginated_policies = filtered_policies[start:end]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": paginated_policies,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")

@router.get("/policies/{policy_id}", response_model=Dict[str, Any])
async def get_policy(policy_id: int):
    """获取单个策略详情"""
    try:
        db = get_db()
        rule = await db.get_rule_by_id(policy_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 转换为新前端期望的格式
        policy_data = {
            "id": str(rule.get('rule_id', '')),
            "name": rule.get('rule_name', ''),
            "type": rule.get('rule_type', ''),
            "description": rule.get('description', ''),
            "config": rule.get('rule_config', {}),
            "status": "enabled" if rule.get('status') == 1 else "disabled",
            "priority": rule.get('priority', 100),
            "namespace_id": str(rule.get('namespace_id', '')),
            "createdAt": rule.get('create_time', '')[:10] if rule.get('create_time') else '',
            "updatedAt": rule.get('update_time', '')[:10] if rule.get('update_time') else ''
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": policy_data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取策略失败: {str(e)}")

@router.post("/policies", response_model=Dict[str, Any])
async def create_policy(policy_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """创建策略 - 适配新前端数据格式"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 转换新前端数据格式到后端格式
        create_data = {
            "rule_name": policy_data.get("name", ""),
            "rule_type": policy_data.get("type", ""),
            "description": policy_data.get("description", ""),
            "rule_config": policy_data.get("config", {}),
            "priority": policy_data.get("priority", 100),
            "namespace_id": int(policy_data.get("namespace_id", 0)),
            "status": 1 if policy_data.get("status") == "enabled" else 0
        }
        
        # 创建策略
        rule_id = await db.create_rule(create_data)
        
        # 更新缓存
        namespace_id = create_data["namespace_id"]
        rules = await db.get_rules_by_namespace(namespace_id)
        await cache.set_rules(namespace_id, rules)
        
        logger.info(f"策略创建成功，rule_id={rule_id}")
        return {
            "code": 200,
            "message": "策略创建成功",
            "data": {
                "policy_id": rule_id,
                "policy": policy_data
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"创建策略失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建策略失败: {str(e)}")

@router.put("/policies/{policy_id}", response_model=Dict[str, Any])
async def update_policy(policy_id: int, policy_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """更新策略 - 适配新前端数据格式"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查策略是否存在
        existing = await db.get_rule_by_id(policy_id)
        if not existing:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 转换新前端数据格式到后端格式
        update_data = {}
        if "name" in policy_data:
            update_data["rule_name"] = policy_data["name"]
        if "type" in policy_data:
            update_data["rule_type"] = policy_data["type"]
        if "description" in policy_data:
            update_data["description"] = policy_data["description"]
        if "config" in policy_data:
            update_data["rule_config"] = policy_data["config"]
        if "priority" in policy_data:
            update_data["priority"] = policy_data["priority"]
        if "status" in policy_data:
            update_data["status"] = 1 if policy_data["status"] == "enabled" else 0
        
        # 更新策略
        success = await db.update_rule(policy_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="更新策略失败")
        
        # 更新缓存
        namespace_id = existing['namespace_id']
        rules = await db.get_rules_by_namespace(namespace_id)
        await cache.set_rules(namespace_id, rules)
        
        logger.info(f"策略更新成功，policy_id={policy_id}")
        return {
            "code": 200,
            "message": "策略更新成功",
            "data": {
                "policy_id": policy_id,
                "policy": policy_data
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新策略失败: {str(e)}")

@router.delete("/policies/{policy_id}", response_model=Dict[str, Any])
async def delete_policy(policy_id: int, current_user: Dict = Depends(get_current_user)):
    """删除策略"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查策略是否存在
        existing = await db.get_rule_by_id(policy_id)
        if not existing:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 删除策略
        success = await db.delete_rule(policy_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除策略失败")
        
        # 更新缓存
        namespace_id = existing['namespace_id']
        rules = await db.get_rules_by_namespace(namespace_id)
        await cache.set_rules(namespace_id, rules)
        
        logger.info(f"策略删除成功，policy_id={policy_id}")
        return {
            "code": 200,
            "message": "策略删除成功",
            "data": {
                "policy_id": policy_id
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除策略失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除策略失败: {str(e)}")

@router.put("/policies/{policy_id}/status", response_model=Dict[str, Any])
async def update_policy_status(policy_id: int, status_data: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """启用/禁用策略"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查策略是否存在
        existing = await db.get_rule_by_id(policy_id)
        if not existing:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 更新状态
        status_value = 1 if status_data.get("status") == "enabled" else 0
        success = await db.update_rule(policy_id, {"status": status_value})
        if not success:
            raise HTTPException(status_code=500, detail="更新策略状态失败")
        
        # 更新缓存
        namespace_id = existing['namespace_id']
        rules = await db.get_rules_by_namespace(namespace_id)
        await cache.set_rules(namespace_id, rules)
        
        logger.info(f"策略状态更新成功，policy_id={policy_id}, status={status_value}")
        return {
            "code": 200,
            "message": "策略状态更新成功",
            "data": {
                "policy_id": policy_id,
                "status": status_data.get("status")
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新策略状态失败: {str(e)}")

@router.get("/policy-templates", response_model=Dict[str, Any])
async def get_policy_templates():
    """获取策略模板列表"""
    try:
        # 返回预定义的策略模板
        templates = [
            {
                "id": "1",
                "name": "消息匹配策略",
                "type": "matcher",
                "description": "基于消息内容进行匹配的策略模板",
                "config_schema": {
                    "matcher_type": {
                        "type": "string",
                        "enum": ["header", "body", "query", "path"],
                        "description": "匹配字段来源"
                    },
                    "match_field": {
                        "type": "string",
                        "description": "匹配字段名称"
                    },
                    "match_operator": {
                        "type": "string",
                        "enum": ["eq", "ne", "gt", "gte", "lt", "lte", "contains", "regex"],
                        "description": "匹配操作符"
                    },
                    "match_value": {
                        "type": "string",
                        "description": "匹配值"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["allow", "deny"],
                        "description": "匹配动作"
                    }
                }
            },
            {
                "id": "2",
                "name": "Token限制策略",
                "type": "token_limit",
                "description": "限制请求Token数量的策略模板",
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
                "id": "3",
                "name": "并发限制策略",
                "type": "concurrent_limit",
                "description": "限制并发连接数的策略模板",
                "config_schema": {
                    "max_concurrent": {
                        "type": "number",
                        "description": "最大并发连接数"
                    }
                }
            },
            {
                "id": "4",
                "name": "QPS限制策略",
                "type": "rate_limit",
                "description": "限制每秒请求数的策略模板",
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
        
        return {
            "code": 200,
            "message": "success",
            "data": templates,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取策略模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取策略模板失败: {str(e)}")

@router.get("/policies/stats", response_model=Dict[str, Any])
async def get_policy_stats():
    """获取策略统计信息"""
    try:
        db = get_db()
        
        # 获取策略统计
        all_rules = await db.get_all_rules()
        
        # 按类型统计
        type_stats = {}
        status_stats = {"enabled": 0, "disabled": 0}
        
        for rule in all_rules:
            rule_type = rule.get('rule_type', 'unknown')
            rule_status = "enabled" if rule.get('status') == 1 else "disabled"
            
            type_stats[rule_type] = type_stats.get(rule_type, 0) + 1
            status_stats[rule_status] += 1
        
        stats_data = {
            "total": len(all_rules),
            "by_type": type_stats,
            "by_status": status_stats,
            "enabled_rate": f"{status_stats['enabled'] / len(all_rules) * 100:.1f}%" if all_rules else "0%"
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": stats_data,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"获取策略统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取策略统计失败: {str(e)}")
