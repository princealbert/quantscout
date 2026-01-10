# coding=utf-8
"""
投机炒作筛选器测试脚本
功能：测试100只股票，找出被爆炒过的股票
"""

import os
import sys
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.stock_data_provider import StockDataProvider
from indicators.speculation_filter import SpeculationFilter


class SpeculationTester:
    """投机炒作筛选器测试器"""

    def __init__(self, test_count: int = 100, use_volatility: bool = False):
        """
        初始化测试器

        Args:
            test_count: 测试股票数量
            use_volatility: 是否使用波动率条件（默认False，只检测一字板）
        """
        self.test_count = test_count
        self.use_volatility = use_volatility
        self.data_provider = StockDataProvider()
        self.speculation_filter = SpeculationFilter(lookback_days=30)
        
        # 统计数据
        self.stats = {
            'total_tested': 0,
            'speculation_found': 0,
            'high_volatility': 0,
            'limit_up_board': 0,
            'passed': 0,
            'data_insufficient': 0,
            'errors': 0
        }
        
        # 存储被投机炒作的股票
        self.speculation_stocks = []
        
        # 存储通过筛选的股票
        self.passed_stocks = []
    
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
    
    def get_trade_date(self) -> str:
        """获取测试日期"""
        import datetime
        from datetime import timedelta
        # 默认使用最新交易日（昨天）
        yesterday = datetime.datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    def test_single_stock(self, symbol: str) -> Dict[str, Any]:
        """
        测试单只股票
        
        Returns:
            测试结果字典
        """
        try:
            trade_date = self.get_trade_date()
            
            # 获取股票K线数据（至少40天，确保有足够数据）
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
            
            # 执行投机炒作筛选
            speculation_passed, speculation_result = self.speculation_filter.filter_stock(df)
            # 更新使用波动率状态
            speculation_result['use_volatility'] = self.use_volatility
            
            if speculation_result.get('has_speculation_signal'):
                # 发现投机炒作信号
                return {
                    'symbol': symbol,
                    'sec_name': basic_info.get('sec_name', '未知'),
                    'status': 'speculation',
                    'close_price': float(df['close'].iloc[-1]),
                    'pe': basic_info.get('pe', 0),
                    'a_mv': basic_info.get('a_mv', 0),
                    'speculation_result': speculation_result
                }
            else:
                # 通过筛选
                return {
                    'symbol': symbol,
                    'sec_name': basic_info.get('sec_name', '未知'),
                    'status': 'passed',
                    'speculation_reason': speculation_result.get('reason', '')
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
        print("投机炒作筛选器测试开始")
        print("=" * 80)

        trade_date = self.get_trade_date()
        print(f"📅 测试日期: {trade_date}")
        print(f"🎯 测试数量: {self.test_count} 只股票")
        print(f"📋 投机筛选配置: 回溯30天，主要检测一字涨停板")
        if self.use_volatility:
            print(f"    ⚠️  启用了波动率条件（可能误杀主升浪）")
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
            
            if result['status'] == 'speculation':
                self.stats['speculation_found'] += 1
                
                # 统计具体原因
                spec_result = result['speculation_result']
                if spec_result['volatility_result'].get('is_high_volatility'):
                    self.stats['high_volatility'] += 1
                if spec_result['limit_up_result'].get('has_limit_up_board'):
                    self.stats['limit_up_board'] += 1
                
                self.speculation_stocks.append(result)
            elif result['status'] == 'passed':
                self.stats['passed'] += 1
                self.passed_stocks.append(result)
            elif result['status'] == 'insufficient_data':
                self.stats['data_insufficient'] += 1
            elif result['status'] == 'error':
                self.stats['errors'] += 1
        
        print("\r" + " " * 80 + "\r", end='')  # 清空进度行
        
        # 输出测试结果
        self.print_summary()
        self.print_speculation_details()
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("📊 测试摘要")
        print("=" * 80)
        print(f"总测试股票数:    {self.stats['total_tested']}")
        print(f"发现投机炒作:     {self.stats['speculation_found']} 只 ({self.stats['speculation_found']/self.stats['total_tested']*100:.1f}%)")
        print(f"  - 高波动率:     {self.stats['high_volatility']} 只")
        print(f"  - 一字板:       {self.stats['limit_up_board']} 只")
        print(f"通过筛选:        {self.stats['passed']} 只 ({self.stats['passed']/self.stats['total_tested']*100:.1f}%)")
        print(f"数据不足:        {self.stats['data_insufficient']} 只")
        print(f"错误数量:        {self.stats['errors']} 只")
        print("-" * 80)
    
    def print_speculation_details(self):
        """打印投机炒作股票详细信息"""
        if not self.speculation_stocks:
            print("✅ 未发现投机炒作股票")
            return
        
        print("\n" + "=" * 80)
        print(f"🚨 发现 {len(self.speculation_stocks)} 只投机炒作股票")
        print("=" * 80)
        
        for idx, stock in enumerate(self.speculation_stocks, 1):
            spec = stock['speculation_result']
            vol = spec['volatility_result']
            limit = spec['limit_up_result']
            
            print(f"\n【{idx}】{stock['symbol']} - {stock['sec_name']}")
            print(f"    当前价格: {stock['close_price']:.2f}  PE: {stock['pe']:.1f}  市值: {stock['a_mv']/1e8:.1f}亿")
            print(f"    投机原因: {spec['reason']}")
            
            if vol.get('is_high_volatility'):
                print(f"    波动率详情:")
                print(f"      - 波动率: {vol['volatility_ratio']*100:.1f}%")
                print(f"      - 最高价: {vol['high_price']:.2f}（{vol['high_date']}）")
                print(f"      - 最低价: {vol['low_price']:.2f}（{vol['low_date']}）")
            
            if limit.get('has_limit_up_board'):
                print(f"    一字板详情:")
                print(f"      - 出现次数: {limit['board_count']} 次")
                print(f"      - 最近一次: {limit['limit_up_date']}")
                print(f"      - 价格: {limit['limit_up_price']:.2f}")
                print(f"      - 涨幅: {limit['limit_up_rate']*100:.2f}%")
                print(f"      - 成交量: {limit['limit_up_volume']:,.0f}")
        
        print("\n" + "=" * 80)
        print("💡 分析建议")
        print("=" * 80)
        print(f"1. 投机股票占比: {len(self.speculation_stocks)}/{self.stats['total_tested']} = {len(self.speculation_stocks)/self.stats['total_tested']*100:.1f}%")
        print(f"2. 如果占比过高(>30%)，可能需要调整筛选条件")
        print(f"3. 建议人工检查前5只股票的K线图，验证逻辑准确性")
        print("=" * 80)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='投机炒作筛选器测试脚本')
    parser.add_argument('-n', '--count', type=int, default=100, help='测试股票数量（默认100）')
    parser.add_argument('--use-volatility', action='store_true', help='启用波动率条件（可能误杀主升浪）')

    args = parser.parse_args()

    # 创建测试器并运行测试
    tester = SpeculationTester(test_count=args.count, use_volatility=args.use_volatility)
    tester.run_test()


if __name__ == '__main__':
    main()
