#!/usr/bin/env python3
# coding=utf-8
"""
检查连接池状态的脚本
用于分析数据库锁定问题
"""

import time
import threading
from cache.data_cache import StockDataCache


def test_connection_pool():
    """测试连接池状态"""
    # 创建缓存实例
    cache = StockDataCache()
    
    # 监控连接池状态
    def monitor_pool():
        while True:
            try:
                with cache._pool_lock:
                    pool_size = len(cache._conn_pool)
                    print(f"连接池状态: {pool_size}/{cache._max_connections} 可用连接")
                time.sleep(2)
            except Exception as e:
                print(f"监控连接池失败: {e}")
                break
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_pool, daemon=True)
    monitor_thread.start()
    
    print("连接池监控已启动，按Ctrl+C退出...")
    
    try:
        # 保持脚本运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n退出监控")


if __name__ == "__main__":
    test_connection_pool()
