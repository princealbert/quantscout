# utils package initialization
# 缓存系统工具包

import os
import sys
from .data_cache import StockDataCache

# 获取项目根目录 - 强制使用固定路径，确保所有应用使用相同的数据库位置
# 固定项目根目录：c:\Users\Administrator\.emgm3\projects\1593121d-dda9-11f0-8409-e89c2599a417
FIXED_PROJECT_ROOT = "c:\\Users\\Administrator\\.emgm3\\projects\\1593121d-dda9-11f0-8409-e89c2599a417"

# 创建全局缓存实例 - 使用固定项目根目录下的数据库，启用回测数据永久化存储
db_path = os.path.join(FIXED_PROJECT_ROOT, "stock_data_cache.db")
# 配置：缓存过期天数为7天，回测数据永久化存储
stock_cache = StockDataCache(
    db_path=db_path,
    cache_expiry_days=7,
    permanent_storage_for_backtest=True
)

__all__ = ['StockDataCache', 'stock_cache']