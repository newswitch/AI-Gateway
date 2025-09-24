"""
依赖注入管理
"""

from typing import Optional
from app.models import DatabaseManager, ConfigCache

# 全局实例
_db_manager: Optional[DatabaseManager] = None
_cache_manager: Optional[ConfigCache] = None

def get_db_manager() -> DatabaseManager:
    """获取数据库管理器"""
    global _db_manager
    if not _db_manager:
        raise RuntimeError("数据库管理器未初始化")
    return _db_manager

def get_cache_manager() -> ConfigCache:
    """获取缓存管理器"""
    global _cache_manager
    if not _cache_manager:
        raise RuntimeError("缓存管理器未初始化")
    return _cache_manager

def set_db_manager(db_manager: DatabaseManager):
    """设置数据库管理器"""
    global _db_manager
    _db_manager = db_manager

def set_cache_manager(cache_manager: ConfigCache):
    """设置缓存管理器"""
    global _cache_manager
    _cache_manager = cache_manager 