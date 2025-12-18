# coding=utf-8
"""
z哥选股策略 - 重构后的精简版本
集成KDJ、知行趋势线、深V信号的综合选股器
"""

import time
import datetime
import json
import os
import sys
import pandas as pd
import numpy as np
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.batch_processor import BatchProcessor


class ZGeStrategyScreener:
    """z哥选股策略集成器（重构精简版）"""
    
    def __init__(self, batch_size=500, max_workers=6, weights_config=None, sub_weights_config=None):
        self.batch_size = batch_size
        self.max_workers = max_workers
        
        # 记录实际接收到的权重配置
        print(f"[ZGE_STRATEGY] 接收到的权重配置: {weights_config}")
        print(f"[ZGE_STRATEGY] 接收到的子权重配置: {sub_weights_config}")
        
        # 使用BatchProcessor处理核心逻辑
        self.batch_processor = BatchProcessor(batch_size, max_workers, weights_config, sub_weights_config)
    
    def get_latest_trading_date(self) -> str:
        """获取最新的交易日"""
        return self.batch_processor.data_provider.get_latest_trading_date()
    
    def get_stock_pool(self, skip_st=True, stock_pool_type='全量A股', custom_symbols=None) -> List[str]:
        """获取股票池"""
        return self.batch_processor.data_provider.get_stock_pool(skip_st, stock_pool_type, custom_symbols)
    
    def process_stock_batch(self, symbols: List[str], trade_date: str) -> List[Dict[str, Any]]:
        """批量处理股票数据"""
        return self.batch_processor.process_stock_batch(symbols, trade_date)
    
    def filter_stocks(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """筛选符合条件的股票"""
        return self.batch_processor.filter_stocks(stocks)
    
    def screen_stocks_batch(self, max_results=50, test_mode=False, skip_st=True) -> List[Dict[str, Any]]:
        """串行分批筛选股票（保持兼容性）"""
        return self.screen_stocks_parallel(max_results, test_mode, skip_st)
    
    def screen_stocks_parallel(self, max_results=50, test_mode=False, skip_st=True) -> List[Dict[str, Any]]:
        """真正并行的股票筛选 - 同时处理所有股票"""
        trade_date = self.get_latest_trading_date()
        stock_pool = self.get_stock_pool(skip_st=skip_st)
        
        if test_mode:
            stock_pool = stock_pool[:100]
            print(f"🧪 测试模式：仅处理前 {len(stock_pool)} 只股票")
        
        print(f"📊 开始真正并行筛选 {len(stock_pool)} 只股票...")
        
        # 使用真正的并行处理所有股票
        try:
            all_stocks = self.batch_processor.process_all_stocks_parallel(stock_pool, trade_date, self.batch_size)
            
            # 按综合评分排序
            all_stocks.sort(key=lambda x: x.get('total_score', 0), reverse=True)
            
            # 限制结果数量
            final_results = all_stocks[:max_results]
            
            print(f"✅ 并行筛选完成：从 {len(stock_pool)} 只股票中筛选出 {len(final_results)} 只符合条件的股票")
            
            return final_results
            
        except Exception as e:
            print(f"❌ 并行处理失败，回退到串行处理: {e}")
            
            # 回退到串行处理
            all_stocks = self.process_stock_batch(stock_pool, trade_date)
            
            # 按综合评分排序
            all_stocks.sort(key=lambda x: x.get('total_score', 0), reverse=True)
            
            # 限制结果数量
            final_results = all_stocks[:max_results]
            
            print(f"✅ 串行筛选完成：从 {len(stock_pool)} 只股票中筛选出 {len(final_results)} 只符合条件的股票")
            
            return final_results
    
    def display_results(self, results: List[Dict[str, Any]], show_all=False):
        """显示选股结果"""
        if not results:
            print("无符合条件的股票")
            return
        
        print("\n" + "="*180)
        print("z哥选股策略结果 (KDJ J值<20 + 趋势信号 + 深V信号)")
        print("="*180)
        print(f"{'排名':<4} {'股票代码':<12} {'股票名称':<10} {'收盘价':<8} {'J值':<8} {'综合评分':<8} {'目标价':<8} {'止损价':<8} {'盈亏比':<8} {'位置':<10} {'白线斜率':<8} {'深V信号':<8} {'PE':<8} {'流通市值(亿)':<12}")
        print("-"*180)
        
        display_count = len(results) if show_all else min(20, len(results))
        
        for i, stock in enumerate(results[:display_count]):
            zhi_xing = stock.get('zhi_xing', {})
            deepv = stock.get('deepv', {})
            
            risk_reward_data = stock.get('risk_reward_data', {})
            target_price = risk_reward_data.get('target_price', 0)
            stop_loss_price = risk_reward_data.get('stop_loss_price', 0)
            risk_reward_ratio = risk_reward_data.get('risk_reward_ratio', 0)
            
            print(f"{i+1:<4} {stock['symbol']:<12} {stock['sec_name']:<10} {stock['close']:<8.2f} {stock['kdj_j']:<8.2f} "
                  f"{stock['total_score']:<8.2f} {target_price:<8.2f} {stop_loss_price:<8.2f} {risk_reward_ratio:<8.2f} {stock.get('position_desc', '未知'):<10} {zhi_xing.get('white_slope', 0):<8.2f} "
                  f"{'是' if deepv.get('deepv_signal') else '否':<8} {stock['pe']:<8.1f} {stock['a_mv']/1e8:<12.2f}")
    
    def save_results(self, results: list, filename=None):
        """保存结果到文件"""
        if not results:
            print("无结果可保存")
            return
        
        os.makedirs('reports', exist_ok=True)
        
        if filename is None:
            filename = f'reports/zge_strategy_results_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # 转换数据类型，确保JSON序列化
        serializable_results = []
        for stock in results:
            serializable_stock = {}
            for key, value in stock.items():
                if isinstance(value, (bool, np.bool_)):
                    serializable_stock[key] = bool(value)
                elif isinstance(value, (np.integer)):
                    serializable_stock[key] = int(value)
                elif isinstance(value, (np.floating)):
                    serializable_stock[key] = float(value)
                elif isinstance(value, (np.ndarray)):
                    serializable_stock[key] = value.tolist()
                else:
                    serializable_stock[key] = value
            serializable_results.append(serializable_stock)
        
        save_data = {
            'screener_info': {
                'strategy': 'z哥选股策略 (KDJ+知行趋势+深V信号)',
                'trade_date': results[0]['trade_date'] if results else '',
                'total_stocks': len(results),
                'created_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            'results': serializable_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"详细结果已保存至: {filename}")
        return filename


def run_zge_strategy_screener(test_mode=True, max_results=50, skip_st=True):
    """运行z哥选股策略"""
    print("正在启动z哥选股策略...")
    
    screener = ZGeStrategyScreener(batch_size=1000, max_workers=6)
    
    try:
        results = screener.screen_stocks_batch(
            max_results=max_results, 
            test_mode=test_mode,
            skip_st=skip_st
        )
        
        screener.display_results(results)
        
        # 保存结果
        if results:
            screener.save_results(results)
        
        return results
        
    except Exception as e:
        print(f"选股器运行失败: {e}")
        return []


if __name__ == "__main__":
    # 运行测试模式
    run_zge_strategy_screener(test_mode=False, max_results=50, skip_st=True)