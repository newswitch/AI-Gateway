#!/usr/bin/env python3
"""
检查数据库数据
"""
import asyncio
import os
from app.models.database import DatabaseManager

async def check_data():
    db_url = os.getenv('DATABASE_URL', 'mysql+aiomysql://ai_gateway:ai_gateway_pass@mysql:3306/ai_gateway_config')
    db = DatabaseManager(db_url)
    try:
        await db.connect()
        print("数据库连接成功！")
        
        # 检查命名空间数据
        namespaces = await db.get_all_namespaces()
        print(f'命名空间数量: {len(namespaces)}')
        for ns in namespaces:
            print(f'  - {ns["namespace_name"]} ({ns["namespace_code"]})')
        
        # 检查上游服务器数据
        upstreams = await db.get_all_upstream_servers()
        print(f'上游服务器数量: {len(upstreams)}')
        for up in upstreams:
            print(f'  - {up["server_name"]} ({up["server_type"]})')
        
        # 检查路由规则数据
        locations = await db.get_all_location_rules()
        print(f'路由规则数量: {len(locations)}')
        for loc in locations:
            print(f'  - {loc["path"]} -> upstream_{loc["upstream_id"]}')
        
        # 检查访问日志数据
        logs = await db.get_access_logs(limit=5)
        print(f'访问日志数量: {len(logs)}')
        
        # 检查日志统计
        stats = await db.get_log_stats()
        print(f'日志统计: {stats}')
        
    except Exception as e:
        print(f'数据库连接失败: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_data())
