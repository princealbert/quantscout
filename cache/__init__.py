# utils package initialization
# 缓存系统工具包

import os
import sys
from .data_cache import StockDataCache

# 动态获取项目根目录
def get_project_root():
    """获取项目根目录"""
    cwd = os.getcwd()
    if cwd.endswith('ulti-para-seeker'):
        return os.path.dirname(cwd)
    elif cwd.endswith('cache'):
        # 从cache目录运行时，返回项目根目录
        return os.path.dirname(cwd)
    else:
        return cwd

# 创建全局缓存实例 - 使用动态项目根目录下的数据库，启用回测数据永久化存储
db_path = os.path.join(get_project_root(), "stock_data_cache.db")
# 配置：缓存过期天数为7天，回测数据永久化存储
stock_cache = StockDataCache(
    db_path=db_path,
    cache_expiry_days=7,
    permanent_storage_for_backtest=True
)

__all__ = ['StockDataCache', 'stock_cache']