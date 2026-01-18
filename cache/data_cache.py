# coding=utf-8
"""
数据缓存模块 - 大幅提升回测效率
使用SQLite本地数据库缓存股票数据
"""

import sqlite3
import json
import hashlib
import datetime
import threading
import concurrent.futures
from typing import Dict, Any, List
from io import StringIO
import pandas as pd


class StockDataCache:
    """股票数据缓存管理器 - 支持多线程安全访问"""
    
    def __init__(self, db_path="stock_data_cache.db", cache_expiry_days=7, permanent_storage_for_backtest=True):
        self.db_path = db_path
        self._lock = threading.RLock()  # 使用可重入锁
        self.cache_expiry_days = cache_expiry_days  # 缓存过期天数
        self.permanent_storage_for_backtest = permanent_storage_for_backtest  # 回测数据是否永久化存储

        self._init_database()
        self._create_config_table()  # 创建配置表

        # 创建连接池
        self._conn_pool = []
        self._max_connections = 20  # 增加连接池大小以处理更多并发请求
        self._pool_lock = threading.Lock()  # 连接池锁
        # 初始化连接池
        for _ in range(self._max_connections):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute('PRAGMA journal_mode=WAL')  # 启用WAL模式
            conn.execute('PRAGMA busy_timeout = 10000')  # 设置10秒超时，避免立即锁定
            conn.execute('PRAGMA synchronous = NORMAL')  # 平衡性能和安全
            self._conn_pool.append(conn)
        print(f"[OK] 数据库连接池初始化完成，连接数: {self._max_connections}", flush=True)

        # 创建异步写入线程池 - 减少并发写线程数以降低锁争用
        self._write_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="CacheWriter")
        print("[OK] 异步缓存写入线程池初始化完成", flush=True)

        # 检查并清理过大的WAL文件（在连接池初始化之后）
        self._cleanup_large_wal()

    def _cleanup_large_wal(self):
        """检查并清理过大的WAL文件"""
        import os
        import time

        wal_path = f"{self.db_path}-wal"
        if not os.path.exists(wal_path):
            return

        wal_size_mb = os.path.getsize(wal_path) / (1024 * 1024)

        # WAL文件超过100MB则清理
        if wal_size_mb > 100:
            print(f"[警告] 检测到过大的WAL文件 ({wal_size_mb:.1f}MB)，正在清理...", flush=True)
            try:
                # 先关闭所有连接池中的连接，避免锁争用
                with self._pool_lock:
                    for conn in self._conn_pool:
                        try:
                            conn.close()
                        except:
                            pass
                    self._conn_pool.clear()

                # 等待一下让所有连接完全关闭
                time.sleep(0.5)

                # 创建新连接进行清理
                conn = sqlite3.connect(self.db_path, timeout=30)
                conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                conn.execute('PRAGMA optimize')
                conn.commit()
                conn.close()

                new_size_mb = os.path.getsize(wal_path) / (1024 * 1024) if os.path.exists(wal_path) else 0
                reduced_mb = wal_size_mb - new_size_mb
                print(f"[OK] WAL文件清理完成，减少 {reduced_mb:.1f}MB", flush=True)

                # 重新初始化连接池
                for _ in range(self._max_connections):
                    conn = sqlite3.connect(self.db_path, check_same_thread=False)
                    conn.execute('PRAGMA journal_mode=WAL')  # 启用WAL模式
                    conn.execute('PRAGMA busy_timeout = 10000')  # 设置10秒超时，避免立即锁定
                    conn.execute('PRAGMA synchronous = NORMAL')  # 平衡性能和安全
                    self._conn_pool.append(conn)

            except Exception as e:
                print(f"[警告] WAL文件清理失败: {e}", flush=True)
                # 即使失败也要重新初始化连接池
                if not self._conn_pool:
                    for _ in range(self._max_connections):
                        try:
                            conn = sqlite3.connect(self.db_path, check_same_thread=False)
                            conn.execute('PRAGMA journal_mode=WAL')
                            conn.execute('PRAGMA busy_timeout = 10000')
                            conn.execute('PRAGMA synchronous = NORMAL')
                            self._conn_pool.append(conn)
                        except:
                            pass
    
    def _get_connection(self):
        """从连接池获取一个连接"""
        with self._pool_lock:
            if not self._conn_pool:
                # 如果连接池为空，创建一个新连接
                # print("[!]️  连接池为空，创建新连接", flush=True)
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.execute('PRAGMA journal_mode=WAL')  # 启用WAL模式
                return conn
            return self._conn_pool.pop()
    
    def _return_connection(self, conn):
        """将连接返回连接池"""
        with self._pool_lock:
            self._conn_pool.append(conn)
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # 创建表（如果不存在）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS kline_data (
                    cache_key TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    days INTEGER NOT NULL,
                    data_json TEXT NOT NULL,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_permanent INTEGER DEFAULT 0  -- 0: 非永久, 1: 永久
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS basic_info (
                    cache_key TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_permanent INTEGER DEFAULT 0  -- 0: 非永久, 1: 永久
                )
            ''')
            
            # 检查并添加缺失的字段（数据库迁移）
            try:
                # 检查kline_data表是否有is_permanent字段
                cursor = conn.execute("PRAGMA table_info(kline_data)")
                kline_columns = [column[1] for column in cursor.fetchall()]
                if 'is_permanent' not in kline_columns:
                    conn.execute("ALTER TABLE kline_data ADD COLUMN is_permanent INTEGER DEFAULT 0")
                    print("[OK] 已为kline_data表添加is_permanent字段", flush=True)
                
                # 检查basic_info表是否有is_permanent字段
                cursor = conn.execute("PRAGMA table_info(basic_info)")
                basic_columns = [column[1] for column in cursor.fetchall()]
                if 'is_permanent' not in basic_columns:
                    conn.execute("ALTER TABLE basic_info ADD COLUMN is_permanent INTEGER DEFAULT 0")
                    print("[OK] 已为basic_info表添加is_permanent字段", flush=True)
            except Exception as e:
                print(f"[!]️  数据库迁移失败: {e}")
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_kline_symbol_date ON kline_data(symbol, trade_date, days)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_basic_symbol_date ON basic_info(symbol, trade_date)
            ''')
            
            # 启用WAL模式，提高并发性能
            conn.execute('PRAGMA journal_mode=WAL')
            
            conn.commit()
            conn.close()
            
    def _create_config_table(self):
        """创建配置表"""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # 创建配置表（如果不存在）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_config (
                    config_key TEXT PRIMARY KEY,
                    config_value TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 插入默认配置
            conn.execute('''
                INSERT OR REPLACE INTO cache_config (config_key, config_value)
                VALUES (?, ?)
            ''', ('permanent_storage_for_backtest', str(int(self.permanent_storage_for_backtest))))
            
            conn.commit()
            conn.close()
    
    def _generate_cache_key(self, symbol: str, trade_date: str, data_type: str, days: int = None) -> str:
        """生成缓存键 - 优化设计，更高效的键生成"""
        # 直接使用连接字符串，避免md5计算开销，同时保持键的可读性
        key_parts = [symbol, trade_date, data_type]
        if days is not None:
            key_parts.append(str(days))
        
        # 使用更高效的分隔符和格式，提高查询效率
        return ":".join(key_parts)
    
    def cache_kline_data(self, symbol: str, trade_date: str, days: int, data: pd.DataFrame, is_permanent=None, asynchronous=True) -> bool:
        """缓存K线数据"""
        try:
            cache_key = self._generate_cache_key(symbol, trade_date, "kline", days)
            
            # 转换DataFrame为JSON
            data_json = data.to_json(orient='records', date_format='iso')
            
            # 如果未指定is_permanent，使用默认配置
            if is_permanent is None:
                is_permanent = self.permanent_storage_for_backtest
            
            # 异步写入
            if asynchronous:
                self._write_pool.submit(self._cache_kline_data_sync, symbol, trade_date, days, data_json, cache_key, int(is_permanent))
                return True
            # 同步写入
            else:
                return self._cache_kline_data_sync(symbol, trade_date, days, data_json, cache_key, int(is_permanent))
        except Exception as e:
            print(f"缓存K线数据失败: {e}", flush=True)
            return False
    
    def _cache_kline_data_sync(self, symbol: str, trade_date: str, days: int, data_json: str, cache_key: str, is_permanent: int) -> bool:
        """同步缓存K线数据 - 内部使用"""
        import time
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                conn = self._get_connection()
                try:
                    conn.execute('''INSERT OR REPLACE INTO kline_data
                        (cache_key, symbol, trade_date, days, data_json, created_time, last_accessed, is_permanent)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
                    ''', (cache_key, symbol, trade_date, days, data_json, is_permanent))

                    conn.commit()
                finally:
                    self._return_connection(conn)
                return True
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
                    continue
                # 数据库锁定错误静默处理，不打印日志
                return False
            except Exception as e:
                print(f"同步缓存K线数据失败: {e}", flush=True)
                return False
        return False
    
    def get_cached_kline_data(self, symbol: str, trade_date: str, days: int) -> pd.DataFrame:
        """获取缓存的K线数据 - 简化命中逻辑"""
        try:
            cache_key = self._generate_cache_key(symbol, trade_date, "kline", days)
            
            conn = self._get_connection()
            try:
                cursor = conn.execute('''
                    SELECT data_json, created_time, is_permanent FROM kline_data 
                    WHERE symbol = ? AND trade_date = ? AND days = ?
                ''', (symbol, trade_date, days))
                
                result = cursor.fetchone()
            finally:
                self._return_connection(conn)
            
            if not result:
                return None
            
            data_json, created_time, is_permanent = result
            
            # 简化过期检查：直接在SQL查询中已处理，这里只做基本验证
            import datetime
            is_permanent_bool = bool(is_permanent)
            if not is_permanent_bool:
                cache_time = datetime.datetime.strptime(created_time, '%Y-%m-%d %H:%M:%S')
                if (datetime.datetime.now() - cache_time).total_seconds() > self.cache_expiry_days * 24 * 3600:
                    return None
            
            # 简化数据解析和验证
            try:
                data = pd.read_json(StringIO(data_json), orient='records')
                if data.empty:
                    return None
                
                # 异步更新最后访问时间
                threading.Thread(target=self._update_last_accessed_async, 
                               args=("kline_data", cache_key), daemon=True).start()
                
                return data
            except Exception:
                return None
        except Exception:
            return None
    
    def batch_check_cached_kline_data(self, symbols: List[str], trade_date: str, days: int) -> Dict[str, bool]:
        """批量检查K线数据缓存 - 提高大量股票检查效率"""
        try:
            if not symbols:
                return {}
            
            conn = self._get_connection()
            try:
                # 构建批量查询参数
                placeholders = ', '.join(['(?, ?, ?)'] * len(symbols))
                params = []
                for symbol in symbols:
                    params.extend([symbol, trade_date, days])
                
                # 执行批量查询
                cursor = conn.execute(f'''
                    SELECT symbol FROM kline_data 
                    WHERE (symbol, trade_date, days) IN ({placeholders})
                    AND (is_permanent = 1 OR julianday('now') - julianday(created_time) < ?)
                ''', params + [self.cache_expiry_days])
                
                # 收集结果
                cached_symbols = set()
                for row in cursor.fetchall():
                    cached_symbols.add(row[0])
            finally:
                self._return_connection(conn)
            
            # 构建返回结果
            result = {}
            for symbol in symbols:
                result[symbol] = symbol in cached_symbols
            
            return result
        except Exception as e:
            print(f"批量检查K线数据缓存失败: {e}", flush=True)
            # 失败时回退到逐个检查
            result = {}
            for symbol in symbols:
                result[symbol] = self.get_cached_kline_data(symbol, trade_date, days) is not None
            return result
    
    def cache_basic_info(self, symbol: str, trade_date: str, data: Dict[str, Any], is_permanent=None, asynchronous=True) -> bool:
        """缓存基础信息"""
        try:
            cache_key = self._generate_cache_key(symbol, trade_date, "basic")
            
            data_json = json.dumps(data, ensure_ascii=False)
            
            # 如果未指定is_permanent，使用默认配置
            if is_permanent is None:
                is_permanent = self.permanent_storage_for_backtest
            
            # 异步写入
            if asynchronous:
                self._write_pool.submit(self._cache_basic_info_sync, symbol, trade_date, data_json, cache_key, int(is_permanent))
                return True
            # 同步写入
            else:
                return self._cache_basic_info_sync(symbol, trade_date, data_json, cache_key, int(is_permanent))
        except Exception as e:
            print(f"缓存基础信息失败: {e}", flush=True)
            return False
    
    def _cache_basic_info_sync(self, symbol: str, trade_date: str, data_json: str, cache_key: str, is_permanent: int) -> bool:
        """同步缓存基础信息 - 内部使用"""
        import time
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                conn = self._get_connection()
                try:
                    conn.execute('''INSERT OR REPLACE INTO basic_info
                        (cache_key, symbol, trade_date, data_json, created_time, last_accessed, is_permanent)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
                    ''', (cache_key, symbol, trade_date, data_json, is_permanent))

                    conn.commit()
                finally:
                    self._return_connection(conn)
                return True
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
                    continue
                # 最后一次失败或不是锁定错误，打印日志
                if "database is locked" in str(e):
                    # 数据库锁定错误已静默处理，不打印日志
                    pass
                else:
                    print(f"同步缓存基础信息失败: {e}", flush=True)
                return False
            except Exception as e:
                print(f"同步缓存基础信息失败: {e}", flush=True)
                return False
        return False
    
    def get_cached_basic_info(self, symbol: str, trade_date: str) -> Dict[str, Any]:
        """获取缓存的基础信息 - 简化命中逻辑"""
        try:
            cache_key = self._generate_cache_key(symbol, trade_date, "basic")
            
            conn = self._get_connection()
            try:
                cursor = conn.execute('''
                    SELECT data_json, created_time, is_permanent FROM basic_info 
                    WHERE symbol = ? AND trade_date = ?
                ''', (symbol, trade_date))
                
                result = cursor.fetchone()
            finally:
                self._return_connection(conn)
            
            if not result:
                return None
            
            data_json, created_time, is_permanent = result
            
            # 简化过期检查：直接在SQL查询中已处理，这里只做基本验证
            import datetime
            is_permanent_bool = bool(is_permanent)
            if not is_permanent_bool:
                cache_time = datetime.datetime.strptime(created_time, '%Y-%m-%d %H:%M:%S')
                if (datetime.datetime.now() - cache_time).total_seconds() > self.cache_expiry_days * 24 * 3600:
                    return None
            
            # 简化数据解析
            try:
                data = json.loads(data_json)
                
                # 异步更新最后访问时间
                threading.Thread(target=self._update_last_accessed_async, 
                               args=("basic_info", cache_key), daemon=True).start()
                
                return data
            except Exception:
                return None
        except Exception:
            return None
    
    def batch_check_cached_basic_info(self, symbols: List[str], trade_date: str) -> Dict[str, bool]:
        """批量检查基础信息缓存 - 提高大量股票检查效率"""
        try:
            if not symbols:
                return {}
            
            conn = self._get_connection()
            try:
                # 构建批量查询参数
                placeholders = ', '.join(['(?, ?)'] * len(symbols))
                params = []
                for symbol in symbols:
                    params.extend([symbol, trade_date])
                
                # 执行批量查询
                cursor = conn.execute(f'''
                    SELECT symbol FROM basic_info 
                    WHERE (symbol, trade_date) IN ({placeholders})
                    AND (is_permanent = 1 OR julianday('now') - julianday(created_time) < ?)
                ''', params + [self.cache_expiry_days])
                
                # 收集结果
                cached_symbols = set()
                for row in cursor.fetchall():
                    cached_symbols.add(row[0])
            finally:
                self._return_connection(conn)
            
            # 构建返回结果
            result = {}
            for symbol in symbols:
                result[symbol] = symbol in cached_symbols
            
            return result
        except Exception as e:
            print(f"批量检查基础信息缓存失败: {e}", flush=True)
            # 失败时回退到逐个检查
            result = {}
            for symbol in symbols:
                result[symbol] = self.get_cached_basic_info(symbol, trade_date) is not None
            return result
    
    def _update_last_accessed_async(self, table_name: str, cache_key: str):
        """异步更新最后访问时间"""
        try:
            conn = self._get_connection()
            try:
                conn.execute(f'''
                    UPDATE {table_name} SET last_accessed = CURRENT_TIMESTAMP 
                    WHERE cache_key = ?
                ''', (cache_key,))
                conn.commit()
            finally:
                self._return_connection(conn)
        except Exception as e:
            # 异步操作失败不影响主流程，静默处理
            pass
            
    def _update_last_accessed(self, table_name: str, cache_key: str):
        """同步更新最后访问时间（已废弃，建议使用异步版本）"""
        self._update_last_accessed_async(table_name, cache_key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            conn = self._get_connection()
            try:
                # K线数据统计
                kline_stats = conn.execute('''
                    SELECT 
                        COUNT(*) as total_count,
                        COUNT(DISTINCT symbol) as unique_symbols,
                        MAX(last_accessed) as latest_access,
                        MIN(last_accessed) as earliest_access
                    FROM kline_data
                ''').fetchone()
                
                # 基础信息统计
                basic_stats = conn.execute('''
                    SELECT 
                        COUNT(*) as total_count,
                        COUNT(DISTINCT symbol) as unique_symbols,
                        MAX(last_accessed) as latest_access,
                        MIN(last_accessed) as earliest_access
                    FROM basic_info
                ''').fetchone()
            finally:
                self._return_connection(conn)
            
            return {
                'kline_data': {
                    'total_count': kline_stats[0],
                    'unique_symbols': kline_stats[1],
                    'latest_access': kline_stats[2],
                    'earliest_access': kline_stats[3]
                },
                'basic_info': {
                    'total_count': basic_stats[0],
                    'unique_symbols': basic_stats[1],
                    'latest_access': basic_stats[2],
                    'earliest_access': basic_stats[3]
                },
                'total_size_kb': self._get_database_size()
            }
        except Exception as e:
            print(f"获取缓存统计失败: {e}", flush=True)
            return {}
    
    def _get_database_size(self) -> float:
        """获取数据库文件大小（KB）"""
        import os
        try:
            size_bytes = os.path.getsize(self.db_path)
            return size_bytes / 1024
        except:
            return 0
    
    def clear_old_cache(self, days: int = 7):
        """清理过期缓存（默认7天前）"""
        try:
            conn = self._get_connection()
            try:
                # 清理前统计
                before_kline = conn.execute('SELECT COUNT(*) FROM kline_data').fetchone()[0]
                before_basic = conn.execute('SELECT COUNT(*) FROM basic_info').fetchone()[0]
                
                # 清理K线数据缓存 - 只清理非永久化数据
                conn.execute('''
                    DELETE FROM kline_data 
                    WHERE julianday('now') - julianday(last_accessed) > ? AND is_permanent = 0
                ''', (days,))
                
                # 清理基础信息缓存 - 只清理非永久化数据
                conn.execute('''
                    DELETE FROM basic_info 
                    WHERE julianday('now') - julianday(last_accessed) > ? AND is_permanent = 0
                ''', (days,))
                
                # 清理后统计
                after_kline = conn.execute('SELECT COUNT(*) FROM kline_data').fetchone()[0]
                after_basic = conn.execute('SELECT COUNT(*) FROM basic_info').fetchone()[0]
                
                conn.commit()
            finally:
                self._return_connection(conn)
            
            kline_cleaned = before_kline - after_kline
            basic_cleaned = before_basic - after_basic
            
            print(f"[OK] 已清理{days}天前的缓存数据:", flush=True)
            print(f"   • K线数据: {kline_cleaned} 条", flush=True)
            print(f"   • 基础信息: {basic_cleaned} 条", flush=True)
            print(f"   • 剩余K线数据: {after_kline} 条", flush=True)
            print(f"   • 剩余基础信息: {after_basic} 条", flush=True)
            
        except Exception as e:
            print(f"清理缓存失败: {e}", flush=True)
    
    def optimize_database(self):
        """优化数据库性能"""
        try:
            conn = self._get_connection()
            try:
                # 执行VACUUM命令，整理数据库文件
                conn.execute('VACUUM')
                
                # 重新分析索引
                conn.execute('ANALYZE')
                
                conn.commit()
            finally:
                self._return_connection(conn)
            
            print("[OK] 数据库优化完成", flush=True)
            
        except Exception as e:
            print(f"数据库优化失败: {e}", flush=True)
    
    def cache_incremental_data(self, symbol: str, trade_date: str, days: int, new_data: pd.DataFrame) -> bool:
        """增量缓存策略 - 只缓存新增数据"""
        try:
            # 首先检查是否有现有缓存
            existing_data = self.get_cached_kline_data(symbol, trade_date, days)
            
            if existing_data is not None:
                # 合并新旧数据，去重
                combined_data = pd.concat([existing_data, new_data], ignore_index=True)
                combined_data = combined_data.drop_duplicates(subset=['trade_date'], keep='last')
                combined_data = combined_data.sort_values('trade_date').reset_index(drop=True)
                
                # 检查是否真的有新增数据
                if len(combined_data) == len(existing_data):
                    with self._lock:
                        print(f"📊 {symbol} 无新增数据，跳过缓存", flush=True)
                    return False
                
                # 缓存合并后的数据
                result = self.cache_kline_data(symbol, trade_date, days, combined_data)
                
                with self._lock:
                    # print(f"📈 {symbol} 更新缓存完成", flush=True)
                    pass
                return result
            else:
                # 没有现有缓存，直接缓存新数据
                result = self.cache_kline_data(symbol, trade_date, days, new_data)
                
                with self._lock:
                    # print(f"🆕 {symbol} 首次缓存完成", flush=True)
                    pass
                return result
                
        except Exception as e:
            with self._lock:
                print(f"增量缓存失败: {e}", flush=True)
            return False
    
    def pre_warm_cache(self, symbols: List[str], trade_date: str, days: int = 180, 
                       batch_size: int = 100, max_workers: int = 8) -> Dict[str, Any]:
        """批量缓存预热功能 - 提高首次运行效率"""
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from gm.api import history
        import datetime
        
        try:
            print(f"🔥 开始缓存预热: {len(symbols)} 只股票，日期: {trade_date}", flush=True)
            start_time = time.time()
            
            # 统计信息
            stats = {
                'total_symbols': len(symbols),
                'cached_count': 0,
                'failed_count': 0,
                'skipped_count': 0,
                'total_time': 0
            }
            
            # 分批处理
            batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
            
            for batch_idx, batch in enumerate(batches):
                print(f"🔧 处理批次 {batch_idx + 1}/{len(batches)}: {len(batch)} 只股票", flush=True)
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_symbol = {}
                    
                    for symbol in batch:
                        # 检查是否已有缓存
                        if self.get_cached_kline_data(symbol, trade_date, days) is not None:
                            stats['skipped_count'] += 1
                            continue
                        
                        # 提交缓存任务
                        future = executor.submit(self._pre_warm_single_stock, symbol, trade_date, days)
                        future_to_symbol[future] = symbol
                    
                    # 处理结果
                    for future in as_completed(future_to_symbol):
                        symbol = future_to_symbol[future]
                        try:
                            result = future.result()
                            if result:
                                stats['cached_count'] += 1
                                if stats['cached_count'] % 50 == 0:
                                    print(f"  已预热 {stats['cached_count']} 只股票", flush=True)
                            else:
                                stats['failed_count'] += 1
                        except Exception as e:
                            stats['failed_count'] += 1
                            print(f"[!]️  {symbol} 预热失败: {e}", flush=True)
            
            stats['total_time'] = time.time() - start_time
            
            print(f"[OK] 缓存预热完成:", flush=True)
            print(f"   • 总股票数: {stats['total_symbols']}", flush=True)
            print(f"   • 新增缓存: {stats['cached_count']}", flush=True)
            print(f"   • 跳过已缓存: {stats['skipped_count']}", flush=True)
            print(f"   • 失败: {stats['failed_count']}", flush=True)
            print(f"   • 总耗时: {stats['total_time']:.1f}秒 ({stats['total_time']/60:.1f}分钟)", flush=True)
            
            return stats
            
        except Exception as e:
            print(f"[X] 缓存预热失败: {e}", flush=True)
            return {}
    
    def _pre_warm_single_stock(self, symbol: str, trade_date: str, days: int) -> bool:
        """预热单只股票的缓存"""
        from gm.api import history
        import datetime
        
        try:
            # 计算开始日期
            start_date = (datetime.datetime.strptime(trade_date, "%Y-%m-%d") - 
                         datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            
            # 获取K线数据
            bars = history(symbol=symbol, frequency='1d', 
                          start_time=start_date, end_time=trade_date, 
                          fields='symbol,trade_date,open,high,low,close,volume', 
                          df=True)
            
            if bars is not None and not bars.empty:
                # 缓存数据
                return self.cache_kline_data(symbol, trade_date, days, bars)
            
            return False
            
        except Exception as e:
            return False
    
    def smart_cache_cleanup(self, strategy_type: str = "回测", 
                           keep_days: int = None, 
                           max_size_mb: int = 100) -> Dict[str, Any]:
        """智能缓存清理 - 根据使用场景调整缓存策略"""
        try:
            stats = self.get_cache_stats()
            current_size_mb = stats.get('total_size_kb', 0) / 1024
            
            print(f"🧠 智能缓存清理 - 策略: {strategy_type}", flush=True)
            print(f"   • 当前缓存大小: {current_size_mb:.1f}MB", flush=True)
            print(f"   • K线数据: {stats.get('kline_data', {}).get('total_count', 0)} 条", flush=True)
            print(f"   • 基础信息: {stats.get('basic_info', {}).get('total_count', 0)} 条", flush=True)
            
            # 根据策略类型设置参数
            if strategy_type == "回测":
                # 回测模式：保留更长时间的数据
                default_days = 30
                size_threshold = 500  # 500MB
            elif strategy_type == "实时":
                # 实时模式：只保留最近数据
                default_days = 7
                size_threshold = 100  # 100MB
            else:
                # 默认模式
                default_days = 14
                size_threshold = 200
            
            # 使用用户指定的天数或默认值
            cleanup_days = keep_days if keep_days is not None else default_days
            
            # 检查是否需要清理
            if current_size_mb > max_size_mb:
                print(f"[!]️  缓存超过 {max_size_mb}MB，执行清理...", flush=True)
                self.clear_old_cache(cleanup_days)
                
                # 清理后重新统计
                new_stats = self.get_cache_stats()
                new_size_mb = new_stats.get('total_size_kb', 0) / 1024
                
                print(f"[OK] 清理完成:", flush=True)
                print(f"   • 新缓存大小: {new_size_mb:.1f}MB", flush=True)
                print(f"   • 减少: {current_size_mb - new_size_mb:.1f}MB", flush=True)
                
                return new_stats
            else:
                print(f"[OK] 缓存大小正常，无需清理", flush=True)
                return stats
                
        except Exception as e:
            print(f"智能缓存清理失败: {e}", flush=True)
            return {}
    
    def get_cache_health_report(self) -> Dict[str, Any]:
        """获取缓存健康度报告"""
        try:
            stats = self.get_cache_stats()
            
            # 计算缓存命中率（需要访问日志，这里简化处理）
            # 在实际应用中，可以添加访问日志来统计真实的命中率
            
            # 计算数据新鲜度
            conn = self._get_connection()
            try:
                # 获取最近访问时间分布
                kline_age_stats = conn.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN julianday('now') - julianday(last_accessed) < 1 THEN 1 ELSE 0 END) as today,
                        SUM(CASE WHEN julianday('now') - julianday(last_accessed) BETWEEN 1 AND 7 THEN 1 ELSE 0 END) as week,
                        SUM(CASE WHEN julianday('now') - julianday(last_accessed) > 7 THEN 1 ELSE 0 END) as old
                    FROM kline_data
                ''').fetchone()
                
                basic_age_stats = conn.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN julianday('now') - julianday(last_accessed) < 1 THEN 1 ELSE 0 END) as today,
                        SUM(CASE WHEN julianday('now') - julianday(last_accessed) BETWEEN 1 AND 7 THEN 1 ELSE 0 END) as week,
                        SUM(CASE WHEN julianday('now') - julianday(last_accessed) > 7 THEN 1 ELSE 0 END) as old
                    FROM basic_info
                ''').fetchone()
            finally:
                self._return_connection(conn)
            
            health_report = {
                'cache_size': stats.get('total_size_kb', 0) / 1024,
                'kline_data': {
                    'total_count': stats.get('kline_data', {}).get('total_count', 0),
                    'unique_symbols': stats.get('kline_data', {}).get('unique_symbols', 0),
                    'freshness': {
                        'today': kline_age_stats[1] if kline_age_stats else 0,
                        'week': kline_age_stats[2] if kline_age_stats else 0,
                        'old': kline_age_stats[3] if kline_age_stats else 0
                    }
                },
                'basic_info': {
                    'total_count': stats.get('basic_info', {}).get('total_count', 0),
                    'unique_symbols': stats.get('basic_info', {}).get('unique_symbols', 0),
                    'freshness': {
                        'today': basic_age_stats[1] if basic_age_stats else 0,
                        'week': basic_age_stats[2] if basic_age_stats else 0,
                        'old': basic_age_stats[3] if basic_age_stats else 0
                    }
                },
                'health_score': self._calculate_health_score(stats, kline_age_stats, basic_age_stats)
            }
            
            return health_report
            
        except Exception as e:
            print(f"获取缓存健康度报告失败: {e}", flush=True)
            return {}
    
    def _calculate_health_score(self, stats: Dict, kline_age_stats: tuple, basic_age_stats: tuple) -> float:
        """计算缓存健康度分数（0-100）"""
        try:
            score = 100.0
            
            # 1. 缓存大小评分（越小越好）
            size_mb = stats.get('total_size_kb', 0) / 1024
            if size_mb > 500:
                score -= 20
            elif size_mb > 200:
                score -= 10
            elif size_mb > 100:
                score -= 5
            
            # 2. 数据新鲜度评分
            if kline_age_stats and kline_age_stats[0] > 0:
                old_ratio = kline_age_stats[3] / kline_age_stats[0]
                if old_ratio > 0.5:
                    score -= 20
                elif old_ratio > 0.3:
                    score -= 10
                elif old_ratio > 0.1:
                    score -= 5
            
            if basic_age_stats and basic_age_stats[0] > 0:
                old_ratio = basic_age_stats[3] / basic_age_stats[0]
                if old_ratio > 0.5:
                    score -= 20
                elif old_ratio > 0.3:
                    score -= 10
                elif old_ratio > 0.1:
                    score -= 5
            
            return max(0, min(100, score))
            
        except Exception:
            return 50.0


# 全局缓存实例由 cache/__init__.py 创建和管理