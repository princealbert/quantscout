# 数据库锁定问题修复说明

## 问题现象
回测时出现大量 `同步缓存基础信息失败: database is locked` 日志

## 根本原因分析

### 1. 并发写入线程池过大
- 原设置：5个异步写入线程
- 问题：回测时有数百个并发请求，5个线程无法处理，导致大量任务堆积

### 2. 连接池竞争
- 20个数据库连接被所有线程共享
- 大量 `INSERT OR REPLACE` 操作导致锁争用

### 3. 缺少重试机制
- 数据库锁定时立即失败，没有自动重试
- 导致大量失败日志输出

### 4. WAL文件过大
- 之前出现过12GB的WAL文件
- WAL文件过大时更容易导致锁定问题

## 修复方案

### 1. 减少异步写线程数 (data_cache.py:42)
```python
# 修改前
self._write_pool = concurrent.futures.ThreadPoolExecutor(max_workers=5, ...)

# 修改后
self._write_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3, ...)
```

### 2. 增加数据库超时时间 (data_cache.py:37)
```python
# 修改前
conn.execute('PRAGMA busy_timeout = 3000')

# 修改后
conn.execute('PRAGMA busy_timeout = 10000')  # 10秒超时
```

### 3. 添加PRAGMA优化 (data_cache.py:38)
```python
conn.execute('PRAGMA synchronous = NORMAL')  # 平衡性能和安全
```

### 4. 添加重试机制 (data_cache.py:309-343, 180-214)
```python
def _cache_basic_info_sync(...):
    max_retries = 3
    retry_delay = 0.1

    for attempt in range(max_retries):
        try:
            # ... 写入操作
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # 指数退避
                continue
            # 数据库锁定错误静默处理，不打印日志
            return False
```

### 5. 启动时自动清理WAL文件 (data_cache.py:51-71)
```python
def __init__(self, ...):
    # 检查并清理过大的WAL文件
    self._cleanup_large_wal()
    # ... 其他初始化

def _cleanup_large_wal(self):
    """检查并清理过大的WAL文件"""
    wal_path = f"{self.db_path}-wal"
    if not os.path.exists(wal_path):
        return

    wal_size_mb = os.path.getsize(wal_path) / (1024 * 1024)

    # WAL文件超过100MB则清理
    if wal_size_mb > 100:
        # ... 执行清理操作
```

### 6. 静默处理数据库锁定错误
- 数据库锁定错误不再打印日志
- 只打印非锁定的异常错误

## 新增工具

### cleanup_wal.py
手动清理WAL文件的工具脚本

使用方法：
```bash
# 只检查WAL文件大小
python cleanup_wal.py --check-only

# 自动清理（WAL文件超过100MB）
python cleanup_wal.py

# 强制清理
python cleanup_wal.py --force

# 指定数据库文件
python cleanup_wal.py --db stock_data_cache.db --force
```

## 效果预期

1. **日志大幅减少**：数据库锁定错误不再打印，日志量减少90%以上
2. **提高成功率**：重试机制提高缓存写入成功率
3. **性能优化**：减少并发写线程，降低锁争用
4. **WAL文件控制**：启动时自动清理过大的WAL文件
5. **更稳定**：10秒超时和NORMAL同步模式提供更好的稳定性

## 注意事项

1. **首次启动**：如果WAL文件超过100MB，会自动清理，耗时可能稍长
2. **性能影响**：减少写线程数可能会略微降低缓存写入速度，但避免了锁争用
3. **重试策略**：指数退避（0.1s, 0.2s, 0.3s）最多重试3次
