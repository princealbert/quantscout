#!/usr/bin/env python3
# coding=utf-8
"""
智能预加载管理器 - 提高缓存命中率
"""

import threading
import time
import pandas as pd
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from cache import stock_cache
from data.stock_data_provider import StockDataProvider


class PreloadManager:
    """智能预加载管理器"""
    
    def __init__(self, max_workers: int = 8, batch_size: int = 50):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self._provider = None  # 延迟创建,避免启动时Token未配置导致错误
        self._lock = threading.Lock()
        self._preload_history = {}  # 预加载历史记录

    @property
    def provider(self) -> StockDataProvider:
        """延迟创建StockDataProvider实例"""
        if self._provider is None:
            self._provider = StockDataProvider()
        return self._provider
    
    def smart_preload_basic_info(self, symbols: List[str], trade_date: str) -> Dict[str, Any]:
        """智能预加载基础信息 - 优化性能"""
        
        # 检查缓存状态
        stats = self._analyze_cache_status(symbols, trade_date)
        
        # 只预加载未缓存的数据
        uncached_symbols = stats['uncached_symbols']
        
        if not uncached_symbols:
            return stats
        
        # 分批预加载
        batches = [uncached_symbols[i:i + self.batch_size] 
                  for i in range(0, len(uncached_symbols), self.batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_symbol = {
                    executor.submit(self._preload_single_basic_info, symbol, trade_date): symbol
                    for symbol in batch
                }
                
                completed = 0
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        success = future.result()
                        if success:
                            stats['preloaded_count'] += 1
                    except Exception:
                        stats['failed_count'] += 1
                    
                    completed += 1
        
        # 更新预加载历史
        self._update_preload_history(symbols, trade_date, stats)
        
        return stats
    
    def smart_preload_kline_data(self, symbols: List[str], trade_date: str, days: int = 180) -> Dict[str, Any]:
        """智能预加载K线数据"""
        print(f"🧠 智能预加载K线数据: {len(symbols)} 只股票，{days} 天")
        
        # 检查缓存状态
        stats = self._analyze_kline_cache_status(symbols, trade_date, days)
        
        # 只预加载未缓存的数据
        uncached_symbols = stats['uncached_symbols']
        
        if not uncached_symbols:
            print("✅ 所有股票K线数据已缓存，无需预加载")
            return stats
        
        print(f"📥 预加载 {len(uncached_symbols)} 只股票的K线数据")
        
        # 分批预加载
        batches = [uncached_symbols[i:i + min(self.batch_size, 10)] 
                  for i in range(0, len(uncached_symbols), min(self.batch_size, 10))]  # K线数据预加载批次更小
        
        for batch_idx, batch in enumerate(batches):
            print(f"🔧 预加载批次 {batch_idx + 1}/{len(batches)}: {len(batch)} 只股票")
            
            with ThreadPoolExecutor(max_workers=min(self.max_workers, 4)) as executor:  # K线数据并发数更小
                future_to_symbol = {
                    executor.submit(self._preload_single_kline_data, symbol, trade_date, days): symbol
                    for symbol in batch
                }
                
                completed = 0
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        success = future.result()
                        if success:
                            stats['preloaded_count'] += 1
                    except Exception:
                        stats['failed_count'] += 1
                    
                    completed += 1
                    if completed % 5 == 0:
                        print(f"  进度: {completed}/{len(batch)} ({completed/len(batch)*100:.1f}%)")
        
        print(f"✅ K线数据预加载完成: 成功 {stats['preloaded_count']}, 失败 {stats['failed_count']}")
        
        return stats
    
    def _analyze_cache_status(self, symbols: List[str], trade_date: str) -> Dict[str, Any]:
        """分析缓存状态"""
        stats = {
            'total_symbols': len(symbols),
            'cached_count': 0,
            'uncached_symbols': [],
            'preloaded_count': 0,
            'failed_count': 0
        }
        
        for symbol in symbols:
            cached_info = stock_cache.get_cached_basic_info(symbol, trade_date)
            if cached_info is not None:
                stats['cached_count'] += 1
            else:
                stats['uncached_symbols'].append(symbol)
        
        print(f"📊 缓存分析: 已缓存 {stats['cached_count']}/{stats['total_symbols']} "
              f"({stats['cached_count']/stats['total_symbols']*100:.1f}%)")
        
        return stats
    
    def _analyze_kline_cache_status(self, symbols: List[str], trade_date: str, days: int) -> Dict[str, Any]:
        """分析K线数据缓存状态"""
        stats = {
            'total_symbols': len(symbols),
            'cached_count': 0,
            'uncached_symbols': [],
            'preloaded_count': 0,
            'failed_count': 0
        }
        
        for symbol in symbols:
            cached_data = stock_cache.get_cached_kline_data(symbol, trade_date, days)
            if cached_data is not None:
                stats['cached_count'] += 1
            else:
                stats['uncached_symbols'].append(symbol)
        
        print(f"📊 K线缓存分析: 已缓存 {stats['cached_count']}/{stats['total_symbols']} "
              f"({stats['cached_count']/stats['total_symbols']*100:.1f}%)")
        
        return stats
    
    def _preload_single_basic_info(self, symbol: str, trade_date: str) -> bool:
        """预加载单只股票的基础信息"""
        try:
            # 使用静默模式获取，不输出详细日志
            info = self.provider.get_stock_basic_info(symbol, trade_date)
            return info is not None and 'symbol' in info
        except Exception as e:
            print(f"⚠️  预加载 {symbol} 基础信息失败: {e}")
            return False
    
    def _preload_single_kline_data(self, symbol: str, trade_date: str, days: int) -> bool:
        """预加载单只股票的K线数据"""
        try:
            # 使用静默模式获取，不输出详细日志
            data = self.provider.get_stock_kline_data(symbol, trade_date, days, incremental=True)
            return data is not None and not data.empty
        except Exception as e:
            print(f"⚠️  预加载 {symbol} K线数据失败: {e}")
            return False
    
    def _update_preload_history(self, symbols: List[str], trade_date: str, stats: Dict[str, Any]):
        """更新预加载历史记录"""
        with self._lock:
            key = f"{trade_date}_{len(symbols)}"
            self._preload_history[key] = {
                'timestamp': time.time(),
                'symbols_count': len(symbols),
                'trade_date': trade_date,
                'stats': stats
            }
    
    def get_preload_recommendation(self, symbols: List[str], trade_date: str) -> Dict[str, Any]:
        """获取预加载建议"""
        cache_stats = stock_cache.get_cache_stats()
        
        # 分析当前缓存状态
        basic_stats = self._analyze_cache_status(symbols, trade_date)
        kline_stats = self._analyze_kline_cache_status(symbols, trade_date, 180)
        
        recommendation = {
            'basic_info': {
                'cached_ratio': basic_stats['cached_count'] / basic_stats['total_symbols'],
                'recommend_preload': basic_stats['cached_count'] / basic_stats['total_symbols'] < 0.8,
                'uncached_count': len(basic_stats['uncached_symbols'])
            },
            'kline_data': {
                'cached_ratio': kline_stats['cached_count'] / kline_stats['total_symbols'],
                'recommend_preload': kline_stats['cached_count'] / kline_stats['total_symbols'] < 0.5,
                'uncached_count': len(kline_stats['uncached_symbols'])
            },
            'database_size': cache_stats.get('total_size_kb', 0) / 1024,  # MB
            'recommend_cleanup': cache_stats.get('total_size_kb', 0) / 1024 > 100  # 超过100MB建议清理
        }
        
        return recommendation
    
    def optimize_preload_strategy(self, strategy_type: str, symbols_count: int) -> Dict[str, Any]:
        """根据策略类型优化预加载策略"""
        
        if strategy_type == "回测":
            # 回测模式：预加载更多数据，使用更大的批次
            return {
                'batch_size': min(100, symbols_count // 10),
                'max_workers': 8,
                'preload_days': 180,  # 回测需要更多历史数据
                'priority': 'kline_data'  # 优先预加载K线数据
            }
        elif strategy_type == "实时":
            # 实时模式：预加载较少数据，快速响应
            return {
                'batch_size': min(20, symbols_count // 5),
                'max_workers': 4,
                'preload_days': 30,  # 实时只需要最近数据
                'priority': 'basic_info'  # 优先预加载基础信息
            }
        else:
            # 默认模式
            return {
                'batch_size': min(50, symbols_count // 8),
                'max_workers': 6,
                'preload_days': 90,
                'priority': 'balanced'  # 平衡预加载
            }


# 全局预加载管理器实例
preload_manager = PreloadManager()