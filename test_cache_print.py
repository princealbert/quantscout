# coding=utf-8
"""
测试数据缓存模块的打印输出是否在多线程环境下正确显示
"""

import threading
import time
import pandas as pd
import random
from datetime import datetime, timedelta
from cache.data_cache import StockDataCache

# 创建一个测试用的StockDataCache实例
data_cache = StockDataCache(db_path="test_cache.db")

# 生成测试数据
def generate_test_data(symbol, days=100):
    """生成测试用的股票数据"""
    dates = [datetime.now() - timedelta(days=i) for i in range(days)]
    data = {
        'trade_date': [date.strftime('%Y-%m-%d') for date in dates],
        'open': [random.uniform(10, 100) for _ in range(days)],
        'high': [random.uniform(10, 110) for _ in range(days)],
        'low': [random.uniform(5, 90) for _ in range(days)],
        'close': [random.uniform(10, 100) for _ in range(days)],
        'volume': [random.randint(1000000, 10000000) for _ in range(days)]
    }
    return pd.DataFrame(data)

# 测试函数
def test_cache(symbol):
    """测试缓存功能"""
    trade_date = datetime.now().strftime('%Y-%m-%d')
    data = generate_test_data(symbol, 124)
    # 故意添加一些延迟，模拟网络请求
    time.sleep(random.uniform(0.1, 0.3))
    data_cache.cache_incremental_data(symbol, trade_date, 180, data)

# 运行测试
if __name__ == "__main__":
    # 创建多个线程测试
    symbols = [f"SHSE.{code}" for code in range(600000, 600020)]
    threads = []
    
    print("开始测试多线程缓存...")
    start_time = time.time()
    
    for symbol in symbols:
        thread = threading.Thread(target=test_cache, args=(symbol,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    print(f"测试完成，耗时 {end_time - start_time:.2f} 秒")
    print("检查打印输出是否按预期格式显示，没有交错")
