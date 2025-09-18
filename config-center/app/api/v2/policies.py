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
        
        # 获取所有策略
        all_policies = await db.get_all_policies()
        
        # 应用搜索和筛选条件
        filtered_policies = []
        for policy in all_policies:
            # 关键词搜索
            if keyword:
                keyword_lower = keyword.lower()
                if not any(keyword_lower in str(policy.get(field, '')).lower() 
                          for field in ['policy_name', 'policy_type', 'description']):
                    continue
            
            # 策略类型筛选
            if policy_type and policy.get('policy_type') != policy_type:
                continue
            
            # 状态筛选
            if status:
                policy_status = "enabled" if policy.get('status') == 1 else "disabled"
                if policy_status != status:
                    continue
            
            # 获取命名空间信息 - 优先使用存储的 namespaces 字段
            namespace_info = None
            # 添加调试日志
            logger.info(f"策略 {policy.get('policy_id')} 的 namespaces 字段: {policy.get('namespaces')}")
            logger.info(f"namespaces 类型: {type(policy.get('namespaces'))}")
            
            if policy.get('namespaces') and len(policy.get('namespaces', [])) > 0:
                # 使用存储的 namespaces 字段
                namespace_info = policy['namespaces'][0]
                logger.info(f"使用存储的 namespaces: {namespace_info}")
            else:
                # 如果 namespaces 字段为空，则动态查询
                namespace_id = policy.get('namespace_id')
                if namespace_id:
                    try:
                        namespace = await db.get_namespace(int(namespace_id))
                        if namespace:
                            namespace_info = {
                                "id": str(namespace.get('namespace_id', '')),
                                "code": namespace.get('namespace_code', ''),
                                "name": namespace.get('namespace_name', '')
                            }
                    except:
                        pass
            
            # 转换为新前端期望的格式
            policy_data = {
                "id": str(policy.get('policy_id', '')),
                "name": policy.get('policy_name', ''),
                "type": policy.get('policy_type', ''),
                "description": policy.get('description', ''),
                "config": policy.get('rule_config', {}),
                "status": "enabled" if policy.get('status') == 1 else "disabled",
                "priority": policy.get('priority', 100),
                "namespace_id": str(policy.get('namespace_id', '')),
                "namespaces": [namespace_info] if namespace_info else [],
                "rules": policy.get('rules', []),
                "createdAt": policy.get('create_time', '')[:10] if policy.get('create_time') else '',
                "updatedAt": policy.get('update_time', '')[:10] if policy.get('update_time') else ''
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
        policy = await db.get_policy_by_id(policy_id)
        
        if not policy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 转换为新前端期望的格式
        policy_data = {
            "id": str(policy.get('policy_id', '')),
            "name": policy.get('policy_name', ''),
            "type": policy.get('policy_type', ''),
            "description": policy.get('description', ''),
            "config": policy.get('rule_config', {}),
            "status": "enabled" if policy.get('status') == 1 else "disabled",
            "priority": policy.get('priority', 100),
            "namespace_id": str(policy.get('namespace_id', '')),
            "createdAt": policy.get('create_time', '')[:10] if policy.get('create_time') else '',
            "updatedAt": policy.get('update_time', '')[:10] if policy.get('update_time') else ''
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
        namespace_id = policy_data.get("namespace_id")
        if namespace_id:
            # 如果namespace_id是字符串，需要转换为数字
            if isinstance(namespace_id, str):
                # 从命名空间代码或名称获取ID
                all_namespaces = await db.get_all_namespaces()
                for ns in all_namespaces:
                    if ns.get('namespace_code') == namespace_id or ns.get('namespace_name') == namespace_id:
                        namespace_id = ns.get('namespace_id')
                        break
                else:
                    namespace_id = None  # 设置为 NULL 而不是 0
            else:
                namespace_id = int(namespace_id) if namespace_id > 0 else None
        else:
            namespace_id = None  # 设置为 NULL 而不是 0
            
        # 生成规则描述
        rules = []
        config = policy_data.get("config", {})
        policy_type = policy_data.get("type", "")
        
        if policy_type == "token-limit":
            max_input = config.get("maxInputTokenCount", "未设置")
            max_output = config.get("maxOutputTokenCount", "未设置")
            rules.append(f"输入{max_input}，输出{max_output}")
        elif policy_type == "concurrency-limit":
            max_concurrent = config.get("maxConcurrentConnections", "未设置")
            rules.append(f"最大并发{max_concurrent}个连接")
        elif policy_type == "qps-limit":
            max_qps = config.get("maxQPS", "未设置")
            time_window = config.get("timeWindow", "未设置")
            rules.append(f"每秒最多{max_qps}个请求，{time_window}秒窗口")
        elif policy_type == "message-matching":
            field_source = config.get("matchingFieldSource", "未设置")
            field_name = config.get("matchingFieldName", "未设置")
            operator = config.get("matchingOperator", "未设置")
            value = config.get("matchingValue", "未设置")
            action = config.get("matchingAction", "未设置")
            rules.append(f"{field_source}.{field_name} {operator} \"{value}\" → {action}")
        
        # 处理 namespaces 字段 - 现在前端发送的是单个值或数组
        namespaces = policy_data.get("namespaces", [])
        # 如果是单个值，转换为数组
        if not isinstance(namespaces, list):
            namespaces = [namespaces] if namespaces else []
        
        if namespaces and len(namespaces) > 0:
            # 如果 namespaces 包含完整的对象信息，直接使用
            if isinstance(namespaces[0], dict) and 'id' in namespaces[0]:
                processed_namespaces = namespaces
            else:
                # 如果 namespaces 只包含 ID，需要查询完整的命名空间信息
                processed_namespaces = []
                for ns_id in namespaces:
                    try:
                        ns_id_int = int(ns_id) if isinstance(ns_id, str) else ns_id
                        if ns_id_int > 0:
                            namespace = await db.get_namespace(ns_id_int)
                            if namespace:
                                processed_namespaces.append({
                                    "id": str(namespace.get('namespace_id', '')),
                                    "code": namespace.get('namespace_code', ''),
                                    "name": namespace.get('namespace_name', '')
                                })
                    except (ValueError, TypeError):
                        continue
        else:
            processed_namespaces = []
        
        create_data = {
            "policy_name": policy_data.get("name", ""),
            "policy_type": policy_data.get("type", ""),
            "description": policy_data.get("description", ""),
            "rule_config": config,
            "rule_type": policy_data.get("type", ""),  # rule_type 使用与 policy_type 相同的值
            "priority": policy_data.get("priority", 100),
            "namespace_id": namespace_id,
            "namespaces": processed_namespaces,
            "rules": rules,
            "status": 1  # 始终为启用状态，因为只有启用的策略才会被创建
        }
        
        # 创建策略
        policy_id = await db.create_policy(create_data)
        
        # 更新策略的 namespaces 字段
        if namespace_id and namespace_id > 0:
            namespace = await db.get_namespace(namespace_id)
            if namespace:
                namespace_info = {
                    "id": str(namespace.get('namespace_id', '')),
                    "code": namespace.get('namespace_code', ''),
                    "name": namespace.get('namespace_name', '')
                }
                await db.update_policy(policy_id, {"namespaces": [namespace_info]})
        
        # 更新缓存
        if namespace_id:
            policies = await db.get_policies_by_namespace(namespace_id)
            await cache.set_policies(namespace_id, policies)
        
        logger.info(f"策略创建成功，policy_id={policy_id}")
        return {
            "code": 200,
            "message": "策略创建成功",
            "data": {
                "policy_id": policy_id,
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
        existing = await db.get_policy_by_id(policy_id)
        if not existing:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 添加调试日志
        logger.info(f"更新策略 {policy_id} 接收到的数据: {policy_data}")
        
        # 转换新前端数据格式到后端格式
        update_data = {}
        if "name" in policy_data:
            update_data["policy_name"] = policy_data["name"]
        if "type" in policy_data:
            update_data["policy_type"] = policy_data["type"]
            update_data["rule_type"] = policy_data["type"]  # rule_type 使用与 policy_type 相同的值
        if "description" in policy_data:
            update_data["description"] = policy_data["description"]
        if "config" in policy_data:
            update_data["rule_config"] = policy_data["config"]
            # 生成规则描述
            rules = []
            config = policy_data["config"]
            policy_type = policy_data.get("type", existing.get("policy_type", ""))
            
            if policy_type == "token-limit":
                max_input = config.get("maxInputTokenCount", "未设置")
                max_output = config.get("maxOutputTokenCount", "未设置")
                rules.append(f"输入{max_input}，输出{max_output}")
            elif policy_type == "concurrency-limit":
                max_concurrent = config.get("maxConcurrentConnections", "未设置")
                rules.append(f"最大并发{max_concurrent}个连接")
            elif policy_type == "qps-limit":
                max_qps = config.get("maxQPS", "未设置")
                time_window = config.get("timeWindow", "未设置")
                rules.append(f"每秒最多{max_qps}个请求，{time_window}秒窗口")
            elif policy_type == "message-matching":
                field_source = config.get("matchingFieldSource", "未设置")
                field_name = config.get("matchingFieldName", "未设置")
                operator = config.get("matchingOperator", "未设置")
                value = config.get("matchingValue", "未设置")
                action = config.get("matchingAction", "未设置")
                rules.append(f"{field_source}.{field_name} {operator} \"{value}\" → {action}")
            
            update_data["rules"] = rules
        if "priority" in policy_data:
            update_data["priority"] = policy_data["priority"]
            logger.info(f"priority 字段: {policy_data['priority']}")
        if "rules" in policy_data:
            update_data["rules"] = policy_data["rules"]
        if "namespaces" in policy_data:
            # 处理前端发送的 namespaces 字段 - 现在前端发送的是单个值或数组
            namespaces = policy_data["namespaces"]
            # 如果是单个值，转换为数组
            if not isinstance(namespaces, list):
                namespaces = [namespaces] if namespaces else []
            
            if namespaces and len(namespaces) > 0:
                # 如果 namespaces 包含完整的对象信息，直接使用
                if isinstance(namespaces[0], dict) and 'id' in namespaces[0]:
                    update_data["namespaces"] = namespaces
                else:
                    # 如果 namespaces 只包含 ID，需要查询完整的命名空间信息
                    namespace_infos = []
                    for ns_id in namespaces:
                        try:
                            ns_id_int = int(ns_id) if isinstance(ns_id, str) else ns_id
                            if ns_id_int > 0:
                                namespace = await db.get_namespace(ns_id_int)
                                if namespace:
                                    namespace_infos.append({
                                        "id": str(namespace.get('namespace_id', '')),
                                        "code": namespace.get('namespace_code', ''),
                                        "name": namespace.get('namespace_name', '')
                                    })
                        except (ValueError, TypeError):
                            continue
                    update_data["namespaces"] = namespace_infos
            else:
                update_data["namespaces"] = []
        
        logger.info(f"转换后的更新数据: {update_data}")
        if "namespace_id" in policy_data:
            # 处理 namespace_id 类型转换
            namespace_id = policy_data["namespace_id"]
            if namespace_id:
                try:
                    namespace_id_int = int(namespace_id)
                    if namespace_id_int > 0:
                        update_data["namespace_id"] = namespace_id_int
                    else:
                        update_data["namespace_id"] = None  # 设置为 NULL 而不是 0
                except (ValueError, TypeError):
                    logger.warning(f"无效的 namespace_id: {namespace_id}")
                    # 如果转换失败，尝试从命名空间代码或名称获取ID
                    all_namespaces = await db.get_all_namespaces()
                    for ns in all_namespaces:
                        if ns.get('namespace_code') == str(namespace_id) or ns.get('namespace_name') == str(namespace_id):
                            update_data["namespace_id"] = ns.get('namespace_id')
                            break
                    else:
                        update_data["namespace_id"] = None  # 设置为 NULL 而不是 0
            else:
                update_data["namespace_id"] = None  # 设置为 NULL 而不是 0
        # 处理 status 字段
        if "status" in policy_data:
            update_data["status"] = 1 if policy_data["status"] == "enabled" else 0
        
        # 更新策略
        success = await db.update_policy(policy_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="更新策略失败")
        
        # 如果更新了 namespace_id，同步更新 namespaces 字段
        if "namespace_id" in policy_data:
            namespace_id = policy_data["namespace_id"]
            # 确保 namespace_id 是整数类型
            if namespace_id:
                try:
                    namespace_id = int(namespace_id)
                    if namespace_id > 0:
                        namespace = await db.get_namespace(namespace_id)
                        if namespace:
                            namespace_info = {
                                "id": str(namespace.get('namespace_id', '')),
                                "code": namespace.get('namespace_code', ''),
                                "name": namespace.get('namespace_name', '')
                            }
                            await db.update_policy(policy_id, {"namespaces": [namespace_info]})
                except (ValueError, TypeError):
                    logger.warning(f"无效的 namespace_id: {namespace_id}")
                    pass
        
        # 更新缓存
        namespace_id = existing.get('namespace_id')
        if namespace_id:
            policies = await db.get_policies_by_namespace(namespace_id)
            await cache.set_policies(namespace_id, policies)
        
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
        existing = await db.get_policy_by_id(policy_id)
        if not existing:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 删除策略
        success = await db.delete_policy(policy_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除策略失败")
        
        # 更新缓存
        namespace_id = existing.get('namespace_id')
        if namespace_id:
            policies = await db.get_policies_by_namespace(namespace_id)
            await cache.set_policies(namespace_id, policies)
        
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
    """启用/禁用策略 - 禁用时直接删除策略"""
    try:
        db = get_db()
        cache = get_cache()
        
        # 检查策略是否存在
        existing = await db.get_policy_by_id(policy_id)
        if not existing:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        status = status_data.get("status")
        
        if status == "enabled":
            # 启用策略：确保状态为1（实际上所有策略都是启用状态）
            success = await db.update_policy(policy_id, {"status": 1})
            if not success:
                raise HTTPException(status_code=500, detail="启用策略失败")
            
            message = "策略已启用"
        elif status == "disabled":
            # 禁用策略：直接删除策略
            success = await db.delete_policy(policy_id)
            if not success:
                raise HTTPException(status_code=500, detail="禁用策略失败")
            
            message = "策略已禁用（删除）"
        else:
            raise HTTPException(status_code=400, detail="无效的状态值")
        
        # 更新缓存
        namespace_id = existing.get('namespace_id')
        if namespace_id and status == "enabled":
            policies = await db.get_policies_by_namespace(namespace_id)
            await cache.set_policies(namespace_id, policies)
        elif namespace_id and status == "disabled":
            # 删除策略时，清除相关缓存
            await cache.delete_policy(policy_id)
        
        logger.info(f"策略状态更新成功，policy_id={policy_id}, status={status}")
        return {
            "code": 200,
            "message": message,
            "data": {
                "policy_id": policy_id,
                "status": status
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
        all_policies = await db.get_all_policies()
        
        # 按类型统计
        type_stats = {}
        status_stats = {"enabled": 0, "disabled": 0}
        
        for policy in all_policies:
            policy_type = policy.get('policy_type', 'unknown')
            policy_status = "enabled" if policy.get('status') == 1 else "disabled"
            
            type_stats[policy_type] = type_stats.get(policy_type, 0) + 1
            status_stats[policy_status] += 1
        
        stats_data = {
            "total": len(all_policies),
            "by_type": type_stats,
            "by_status": status_stats,
            "enabled_rate": f"{status_stats['enabled'] / len(all_policies) * 100:.1f}%" if all_policies else "0%"
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
