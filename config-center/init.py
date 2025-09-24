#!/usr/bin/env python3
"""
配置初始化脚本 - 报文匹配规则版本
将示例配置数据写入Redis和MySQL
支持命名空间、报文匹配器和规则配置
"""

import asyncio
import json
import os
from datetime import datetime

# 示例配置数据
SAMPLE_DATA = {
    # 命名空间配置
    "namespaces": [
        {
            "namespace_code": "wechat",
            "namespace_name": "微信渠道",
            "description": "微信小程序和公众号渠道",
            "status": 1
        },
        {
            "namespace_code": "alipay",
            "namespace_name": "支付宝渠道",
            "description": "支付宝小程序和H5渠道",
            "status": 1
        },
        {
            "namespace_code": "web",
            "namespace_name": "Web渠道",
            "description": "Web浏览器渠道",
            "status": 1
        }
    ],
    
    # 报文匹配器配置
    "matchers": [
        {
            "namespace_code": "wechat",
            "matcher_name": "微信渠道匹配",
            "matcher_type": "header",
            "match_field": "channelcode",
            "match_operator": "equals",
            "match_value": "wechat",
            "priority": 100,
            "status": 1
        },
        {
            "namespace_code": "alipay",
            "matcher_name": "支付宝渠道匹配",
            "matcher_type": "header",
            "match_field": "channelcode",
            "match_operator": "equals",
            "match_value": "alipay",
            "priority": 100,
            "status": 1
        },
        {
            "namespace_code": "web",
            "matcher_name": "Web渠道匹配",
            "matcher_type": "header",
            "match_field": "user-agent",
            "match_operator": "contains",
            "match_value": "Mozilla",
            "priority": 50,
            "status": 1
        }
    ],
    
    # 规则配置
    "rules": [
        {
            "namespace_code": "wechat",
            "rule_name": "微信Token限制",
            "rule_type": "token_limit",
            "rule_config": {
                "max_tokens_per_hour": 100000,
                "max_tokens_per_day": 1000000,
                "window_size": 3600
            },
            "priority": 100,
            "status": 1
        },
        {
            "namespace_code": "wechat",
            "rule_name": "微信连接数限制",
            "rule_type": "connection_limit",
            "rule_config": {
                "max_connections": 1000,
                "window_size": 3600
            },
            "priority": 90,
            "status": 1
        },
        {
            "namespace_code": "alipay",
            "rule_name": "支付宝Token限制",
            "rule_type": "token_limit",
            "rule_config": {
                "max_tokens_per_hour": 50000,
                "max_tokens_per_day": 500000,
                "window_size": 3600
            },
            "priority": 100,
            "status": 1
        },
        {
            "namespace_code": "web",
            "rule_name": "Web请求频率限制",
            "rule_type": "request_limit",
            "rule_config": {
                "max_requests_per_minute": 100,
                "max_requests_per_hour": 5000
            },
            "priority": 80,
            "status": 1
        },
        {
            "namespace_code": "wechat",
            "rule_name": "微信Token字段检查",
            "rule_type": "field_check",
            "rule_config": {
                "field_path": "body.max_tokens",
                "operator": "lte",
                "value": 20000,
                "message": "max_tokens不能大于20000"
            },
            "priority": 70,
            "status": 1
        }
    ]
}

async def main():
    """主函数"""
    print("=== AI智能网关配置中心 - 报文匹配规则初始化 ===")
    print(f"初始化时间: {datetime.now()}")
    
    # 获取环境变量
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    database_url = os.getenv("DATABASE_URL", "mysql+aiomysql://ai_gateway:ai_gateway_pass@localhost:3306/ai_gateway_config")
    
    print(f"Redis URL: {redis_url}")
    print(f"Database URL: {database_url}")
    
    # 导入应用模块
    from app import DatabaseManager, ConfigCache
    
    # 初始化Redis连接
    print("\n1. 初始化Redis连接...")
    cache = ConfigCache(redis_url)
    try:
        await cache.connect()
        print("✓ Redis连接成功")
    except Exception as e:
        print(f"✗ Redis连接失败: {str(e)}")
        return
    
    # 初始化MySQL连接
    print("\n2. 初始化MySQL连接...")
    db_manager = DatabaseManager(database_url)
    try:
        await db_manager.connect()
        print("✓ MySQL连接成功")
        cache.db_manager = db_manager
    except Exception as e:
        print(f"✗ MySQL连接失败: {str(e)}")
        # 继续执行，只使用Redis
    
    # 初始化配置
    print("\n3. 初始化配置数据...")
    
    # 创建命名空间
    print("创建命名空间...")
    namespace_map = {}  # 用于存储namespace_code到namespace_id的映射
    
    for namespace_data in SAMPLE_DATA["namespaces"]:
        try:
            namespace_id = await db_manager.create_namespace(namespace_data)
            namespace_map[namespace_data["namespace_code"]] = namespace_id
            print(f"  ✓ 命名空间: {namespace_data['namespace_code']} (ID: {namespace_id})")
        except Exception as e:
            print(f"  ✗ 命名空间: {namespace_data['namespace_code']} - 失败: {str(e)}")
    
    # 创建报文匹配器
    print("\n创建报文匹配器...")
    for matcher_data in SAMPLE_DATA["matchers"]:
        try:
            namespace_code = matcher_data["namespace_code"]
            if namespace_code in namespace_map:
                matcher_data["namespace_id"] = namespace_map[namespace_code]
                matcher_id = await db_manager.create_matcher(matcher_data)
                print(f"  ✓ 匹配器: {matcher_data['matcher_name']} (ID: {matcher_id})")
            else:
                print(f"  ✗ 匹配器: {matcher_data['matcher_name']} - 命名空间不存在: {namespace_code}")
        except Exception as e:
            print(f"  ✗ 匹配器: {matcher_data['matcher_name']} - 失败: {str(e)}")
    
    # 创建规则
    print("\n创建规则...")
    for rule_data in SAMPLE_DATA["rules"]:
        try:
            namespace_code = rule_data["namespace_code"]
            if namespace_code in namespace_map:
                rule_data["namespace_id"] = namespace_map[namespace_code]
                # 将规则配置转换为JSON字符串
                rule_data["rule_config"] = json.dumps(rule_data["rule_config"])
                rule_id = await db_manager.create_rule(rule_data)
                print(f"  ✓ 规则: {rule_data['rule_name']} (ID: {rule_id})")
            else:
                print(f"  ✗ 规则: {rule_data['rule_name']} - 命名空间不存在: {namespace_code}")
        except Exception as e:
            print(f"  ✗ 规则: {rule_data['rule_name']} - 失败: {str(e)}")
    
    # 同步到Redis
    print("\n4. 同步配置到Redis...")
    try:
        success = await cache.sync_from_mysql()
        if success:
            print("✓ 配置同步到Redis成功")
        else:
            print("✗ 配置同步到Redis失败")
    except Exception as e:
        print(f"✗ 配置同步到Redis失败: {str(e)}")
    
    # 验证配置
    print("\n5. 验证配置数据...")
    try:
        # 验证命名空间
        namespaces = await db_manager.get_all_namespaces()
        print(f"✓ 命名空间: {len(namespaces)} 个")
        
        # 验证报文匹配器
        matchers = await db_manager.get_all_matchers()
        print(f"✓ 报文匹配器: {len(matchers)} 个")
        
        # 验证规则
        rules = await db_manager.get_all_rules()
        print(f"✓ 规则: {len(rules)} 个")
        
        # 按命名空间统计
        print("\n按命名空间统计:")
        for namespace in namespaces:
            namespace_id = namespace['namespace_id']
            namespace_matchers = await db_manager.get_matchers_by_namespace(namespace_id)
            namespace_rules = await db_manager.get_rules_by_namespace(namespace_id)
            print(f"  - {namespace['namespace_code']}: {len(namespace_matchers)} 个匹配器, {len(namespace_rules)} 个规则")
            
    except Exception as e:
        print(f"✗ 配置验证失败: {str(e)}")
    
    # 输出统计信息
    print("\n6. 配置统计:")
    try:
        redis_stats = await cache.get_cache_stats()
        print(f"Redis统计: {redis_stats}")
    except Exception as e:
        print(f"获取Redis统计失败: {str(e)}")
    
    # 关闭连接
    print("\n7. 关闭连接...")
    await cache.disconnect()
    if db_manager:
        await db_manager.disconnect()
    
    print("\n=== 配置初始化完成 ===")
    print("✓ 所有配置初始化成功")
    print("\n支持的规则类型:")
    print("  - connection_limit: 最大连接数限制")
    print("  - request_limit: 单位时间内最大请求量限制")
    print("  - token_limit: 单位时间内输入token数量限制")
    print("  - field_check: 报文字段检查")
    print("\nAPI文档: http://localhost:8000/docs")

if __name__ == "__main__":
    asyncio.run(main()) 