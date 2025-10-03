"""
配置中心主应用
"""

import os
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import List, Dict, Any

from app.models import DatabaseManager, ConfigCache
from app.core.dependencies import set_db_manager, set_cache_manager
from app.api.v1 import namespaces, matchers, rules, routes, upstream, proxy, nginx_config
from app.api.v2 import namespaces as namespaces_v2, upstreams, locations, dashboard, policies, traffic, logs, config, auth, metrics
from app.middleware.metrics_middleware import MetricsMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def periodic_sync(cache_manager):
    """定时同步任务 - 每15秒同步一次数据到Redis"""
    while True:
        try:
            await asyncio.sleep(15)  # 等待15秒
            logger.info("执行定时数据同步...")
            success = await cache_manager.sync_from_mysql()
            if success:
                logger.info("定时数据同步完成")
            else:
                logger.warning("定时数据同步失败")
        except Exception as e:
            logger.error(f"定时同步任务出错: {str(e)}")
            await asyncio.sleep(15)  # 出错后等待15秒再重试

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("配置中心服务启动中...")
    
    # 初始化MySQL数据库
    database_url = os.getenv("DATABASE_URL", "mysql+aiomysql://ai_gateway:ai_gateway_pass@mysql:3306/ai_gateway_config?charset=utf8mb4&use_unicode=1&init_command=SET NAMES utf8mb4")
    db_manager = DatabaseManager(database_url)
    try:
        await db_manager.connect()
        set_db_manager(db_manager)
        logger.info("MySQL数据库连接成功")
    except Exception as e:
        logger.error(f"MySQL数据库连接失败: {str(e)}")
        # 重试连接
        try:
            await asyncio.sleep(5)  # 等待5秒
            await db_manager.connect()
            set_db_manager(db_manager)
            logger.info("MySQL数据库重连成功")
        except Exception as retry_e:
            logger.error(f"MySQL数据库重连失败: {str(retry_e)}")
            # 如果重连失败，创建一个模拟的数据库管理器
            set_db_manager(None)
    
    # 初始化Redis连接
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    cache_manager = ConfigCache(redis_url)
    await cache_manager.connect()
    
    # 设置数据库管理器引用
    cache_manager.db_manager = db_manager
    set_cache_manager(cache_manager)
    
    # 启动时同步数据到Redis
    if db_manager:
        try:
            await cache_manager.sync_from_mysql()
            logger.info("数据同步到Redis完成")
        except Exception as e:
            logger.warning(f"数据同步到Redis失败: {str(e)}")
    
    # 启动定时同步任务
    if db_manager:
        asyncio.create_task(periodic_sync(cache_manager))
        logger.info("定时同步任务已启动")
    
    logger.info("Redis连接初始化完成")
    
    yield
    
    # 关闭时
    logger.info("配置中心服务关闭中...")
    await cache_manager.disconnect()
    if db_manager:
        await db_manager.disconnect()
    logger.info("配置中心服务已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="AI智能网关配置中心",
    description="基于Redis + MySQL双写的高性能报文匹配规则配置管理服务",
    version="2.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(namespaces.router)
app.include_router(matchers.router)
app.include_router(rules.router)
app.include_router(routes.router)
app.include_router(upstream.router)
app.include_router(proxy.router)
app.include_router(nginx_config.router)

# 注册V2适配层路由
app.include_router(namespaces_v2.router)
app.include_router(upstreams.router)
app.include_router(locations.router)
app.include_router(dashboard.router)
app.include_router(policies.router)
app.include_router(traffic.router)
app.include_router(logs.router)
app.include_router(config.router)
app.include_router(auth.router)
app.include_router(metrics.router)

# 添加指标收集中间件
app.add_middleware(MetricsMiddleware)

# Prometheus指标端点
@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    from app.services.metrics_collector import get_metrics_collector
    metrics_collector = get_metrics_collector()
    return Response(metrics_collector.get_metrics(), media_type="text/plain")

# Redis指标导出端点
@app.get("/redis-metrics")
async def redis_metrics():
    """从Redis导出监控指标"""
    from app.services.redis_metrics_exporter import redis_exporter
    return Response(redis_exporter.get_metrics(), media_type="text/plain")

# 健康检查
@app.get("/health")
@app.head("/health")
async def health_check():
    """健康检查"""
    try:
        from app.core.dependencies import get_cache_manager, get_db_manager
        
        # 检查Redis连接
        cache = get_cache_manager()
        await cache.redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis健康检查失败: {str(e)}")
        redis_status = "unhealthy"
    
    # 检查MySQL连接
    try:
        db = get_db_manager()
        async with db.get_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        mysql_status = "healthy"
    except Exception as e:
        logger.error(f"MySQL健康检查失败: {str(e)}")
        mysql_status = "unhealthy"
    
    # 判断整体健康状态
    overall_status = "healthy" if redis_status == "healthy" and mysql_status == "healthy" else "unhealthy"
    

    
    # GET请求返回完整的健康状态信息
    return {
        "status": overall_status,
        "storage": {
            "redis": redis_status,
            "mysql": mysql_status
        },
        "timestamp": datetime.now().isoformat()
    }

# 兼容前端：系统状态
@app.get("/api/v1/status")
async def system_status():
    """兼容前端期望的状态接口，复用 /health 输出"""
    return await health_check()

# 缓存统计
@app.get("/stats")
async def cache_stats():
    """获取缓存统计信息"""
    try:
        from app.core.dependencies import get_cache_manager
        cache = get_cache_manager()
        stats = await cache.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"获取缓存统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")

# 数据同步
@app.post("/sync")
async def sync_data():
    """同步数据库到Redis"""
    try:
        from app.core.dependencies import get_cache_manager
        cache = get_cache_manager()
        success = await cache.sync_from_mysql()
        
        if success:
            return {"message": "数据同步成功"}
        else:
            raise HTTPException(status_code=500, detail="数据同步失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"数据同步失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据同步失败: {str(e)}")

# 预加载命名空间数据
@app.post("/preload/{namespace_id}")
async def preload_namespace_data(namespace_id: int):
    """预加载命名空间的所有相关数据到缓存"""
    try:
        from app.core.dependencies import get_cache_manager
        cache = get_cache_manager()
        await cache.preload_namespace_data(namespace_id)
        return {"message": f"命名空间 {namespace_id} 数据预加载完成"}
    except Exception as e:
        logger.error(f"预加载命名空间数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预加载失败: {str(e)}")

# 缓存统计
@app.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    try:
        from app.core.dependencies import get_cache_manager
        cache = get_cache_manager()
        stats = await cache.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"获取缓存统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")

# 批量获取命名空间
@app.post("/namespaces/batch")
async def batch_get_namespaces(namespace_ids: List[int]):
    """批量获取命名空间数据"""
    try:
        from app.core.dependencies import get_cache_manager
        cache = get_cache_manager()
        result = await cache.batch_get_namespaces(namespace_ids)
        return result
    except Exception as e:
        logger.error(f"批量获取命名空间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量获取失败: {str(e)}")

# 批量双写操作
@app.post("/batch-dual-write")
async def batch_dual_write(operations: List[Dict[str, Any]]):
    """批量双写操作"""
    try:
        from app.core.dependencies import get_cache_manager
        cache = get_cache_manager()
        result = await cache.batch_dual_write(operations)
        return result
    except Exception as e:
        logger.error(f"批量双写操作失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量双写失败: {str(e)}")

# 获取命名空间使用情况
@app.get("/api/v1/namespaces/{namespace_id}/usage")
async def get_namespace_usage(namespace_id: int, time_window: str = "30m"):
    """获取命名空间的使用情况（并发数、token使用量等）"""
    try:
        from app.core.dependencies import get_cache_manager
        cache = get_cache_manager()
        usage_data = await cache.get_namespace_usage(namespace_id, time_window)
        return usage_data
    except Exception as e:
        logger.error(f"获取命名空间使用情况失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取使用情况失败: {str(e)}")

# 获取所有命名空间使用情况概览
@app.get("/api/v1/namespaces/usage/overview")
async def get_namespaces_usage_overview():
    """获取所有命名空间的使用情况概览"""
    try:
        from app.core.dependencies import get_cache_manager
        cache = get_cache_manager()
        overview = await cache.get_namespaces_usage_overview()
        return overview
    except Exception as e:
        logger.error(f"获取命名空间使用情况概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取概览失败: {str(e)}")

# 获取命名空间实时监控数据
@app.get("/api/v1/namespaces/{namespace_id}/monitoring")
async def get_namespace_monitoring(namespace_id: int, metric_type: str = "all"):
    """获取命名空间的实时监控数据"""
    try:
        from app.core.dependencies import get_cache_manager
        cache = get_cache_manager()
        monitoring_data = await cache.get_namespace_monitoring(namespace_id, metric_type)
        return monitoring_data
    except Exception as e:
        logger.error(f"获取命名空间监控数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取监控数据失败: {str(e)}")

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI智能网关配置中心",
        "version": "2.0.0",
        "description": "基于Redis + MySQL双写的高性能报文匹配规则配置管理服务",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 