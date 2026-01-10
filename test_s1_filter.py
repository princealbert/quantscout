# coding=utf-8
"""
S1筛选器测试脚本
功能：测试100只股票，找出存在S1信号的股票
"""

import os
import sys
from typing import List, Dict, Any
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.stock_data_provider import StockDataProvider
from indicators.s1_filter import S1Filter


class S1Tester:
    """S1筛选器测试器"""
    
    def __init__(self, test_count: int = 100, trade_date: str = None):
        """
        初始化测试器
        
        Args:
            test_count: 测试股票数量
            trade_date: 测试日期（格式：YYYY-MM-DD），默认为最新交易日
        """
        self.test_count = test_count
        self.trade_date = trade_date
        self.data_provider = StockDataProvider()
        self.s1_filter = S1Filter(lookback_days=30, context_days=2)
        
        # 统计数据
        self.stats = {
            'total_tested': 0,
            's1_found': 0,
            's1_passed': 0,
            'data_insufficient': 0,
            'errors': 0
        }
        
        # 存储有S1信号的股票
        self.s1_stocks = []
        
        # 存储通过筛选的股票
        self.passed_stocks = []
    
    def get_trade_date(self) -> str:
        """获取测试日期"""
        if self.trade_date:
            return self.trade_date
        
        # 默认使用最新交易日（昨天）
        yesterday = datetime.datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    def get_test_symbols(self) -> List[str]:
        """获取测试股票列表"""
        print(f"📊 获取股票池...")
        
        # 获取所有股票列表
        all_symbols = self.data_provider.get_stock_pool(stock_pool_type='全量A股')
        
        if not all_symbols:
            print("❌ 无法获取股票列表")
            return []
        
        print(f"✅ 股票池共有 {len(all_symbols)} 只股票")
        
        # 随机选择 test_count 只股票
        import random
        test_symbols = random.sample(all_symbols, min(self.test_count, len(all_symbols)))
        
        return test_symbols
    
    def test_single_stock(self, symbol: str) -> Dict[str, Any]:
        """
        测试单只股票
        
        Returns:
            测试结果字典
        """
        try:
            trade_date = self.get_trade_date()
            
            # 获取股票K线数据（至少60天，确保有足够数据做S1筛选）
            df = self.data_provider.get_stock_kline_data(symbol, trade_date, days=60)
            
            if df.empty or len(df) < 35:
                return {
                    'symbol': symbol,
                    'status': 'insufficient_data',
                    'message': '数据不足'
                }
            
            # 获取股票基础信息
            basic_info = self.data_provider.get_stock_basic_info(symbol, trade_date)
            if not basic_info:
                return {
                    'symbol': symbol,
                    'status': 'error',
                    'message': '无法获取基础信息'
                }
            
            # 执行S1筛选
            s1_passed, s1_result = self.s1_filter.filter_stock(df)
            
            if s1_result.get('has_s1_signal'):
                # 发现S1信号
                return {
                    'symbol': symbol,
                    'sec_name': basic_info.get('sec_name', '未知'),
                    'status': 's1_found',
                    'close_price': float(df['close'].iloc[-1]),
                    'pe': basic_info.get('pe', 0),
                    'a_mv': basic_info.get('a_mv', 0),
                    's1_result': s1_result
                }
            else:
                # 通过筛选
                return {
                    'symbol': symbol,
                    'sec_name': basic_info.get('sec_name', '未知'),
                    'status': 'passed',
                    's1_reason': s1_result.get('s1_reason', '')
                }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'status': 'error',
                'message': str(e)
            }
    
    def run_test(self):
        """运行测试"""
        print("=" * 80)
        print("S1筛选器测试开始")
        print("=" * 80)
        
        trade_date = self.get_trade_date()
        print(f"📅 测试日期: {trade_date}")
        print(f"🎯 测试数量: {self.test_count} 只股票")
        print(f"📋 S1筛选配置: 回溯30天，前后2天范围")
        print("-" * 80)
        
        # 获取测试股票列表
        test_symbols = self.get_test_symbols()
        
        if not test_symbols:
            print("❌ 无法获取测试股票列表")
            return
        
        # 测试每只股票
        for idx, symbol in enumerate(test_symbols, 1):
            print(f"\r[进度] {idx}/{len(test_symbols)} 测试 {symbol}...", end='', flush=True)
            
            result = self.test_single_stock(symbol)
            
            # 更新统计
            self.stats['total_tested'] += 1
            
            if result['status'] == 's1_found':
                self.stats['s1_found'] += 1
                self.s1_stocks.append(result)
            elif result['status'] == 'passed':
                self.stats['s1_passed'] += 1
                self.passed_stocks.append(result)
            elif result['status'] == 'insufficient_data':
                self.stats['data_insufficient'] += 1
            elif result['status'] == 'error':
                self.stats['errors'] += 1
        
        print("\r" + " " * 80 + "\r", end='')  # 清空进度行
        
        # 输出测试结果
        self.print_summary()
        self.print_s1_details()
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("📊 测试摘要")
        print("=" * 80)
        print(f"总测试股票数: {self.stats['total_tested']}")
        print(f"发现S1信号:   {self.stats['s1_found']} 只 ({self.stats['s1_found']/self.stats['total_tested']*100:.1f}%)")
        print(f"通过筛选:     {self.stats['s1_passed']} 只 ({self.stats['s1_passed']/self.stats['total_tested']*100:.1f}%)")
        print(f"数据不足:     {self.stats['data_insufficient']} 只")
        print(f"错误数量:     {self.stats['errors']} 只")
        print("-" * 80)
    
    def print_s1_details(self):
        """打印S1信号详细信息"""
        if not self.s1_stocks:
            print("✅ 未发现S1信号股票")
            return
        
        print("\n" + "=" * 80)
        print(f"🚨 发现 {len(self.s1_stocks)} 只S1信号股票")
        print("=" * 80)
        
        for idx, stock in enumerate(self.s1_stocks, 1):
            s1 = stock['s1_result']
            print(f"\n【{idx}】{stock['symbol']} - {stock['sec_name']}")
            print(f"    当前价格: {stock['close_price']:.2f}  PE: {stock['pe']:.1f}  市值: {stock['a_mv']/1e8:.1f}亿")
            print(f"    S1原因:   {s1['s1_reason']}")
            print(f"    高点价格: {s1['s1_high_price']:.2f}")
            print(f"    绿柱量:   {s1['s1_green_volume']:,.0f}")
            print(f"    前日红柱: {s1['s1_prev_red_volume']:,.0f}")
            print(f"    量比:     {s1['s1_volume_ratio']:.2f}")
            print(f"    30日最大: {s1['s1_max_volume_30days']:,.0f}")
        
        print("\n" + "=" * 80)
        print("💡 分析建议")
        print("=" * 80)
        print(f"1. S1信号占比: {len(self.s1_stocks)}/{self.stats['total_tested']} = {len(self.s1_stocks)/self.stats['total_tested']*100:.1f}%")
        print(f"2. 如果占比过高(>30%)，可能需要调整筛选条件")
        print(f"3. 建议人工检查前5只股票的K线图，验证逻辑准确性")
        print("=" * 80)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='S1筛选器测试脚本')
    parser.add_argument('-n', '--count', type=int, default=100, help='测试股票数量（默认100）')
    parser.add_argument('-d', '--date', type=str, default=None, help='测试日期（格式：YYYY-MM-DD）')
    
    args = parser.parse_args()
    
    # 创建测试器并运行测试
    tester = S1Tester(test_count=args.count, trade_date=args.date)
    tester.run_test()


if __name__ == '__main__':
    main()
