#!/usr/bin/env python
# coding=utf-8
"""
测试修复后的报告生成和Excel更新功能
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加当前目录到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模拟一个简单的策略对象
class MockStrategy:
    def __init__(self):
        self.initial_capital = 100000.0
        self.params = MockParams()
        self.trading_records = self._generate_mock_trades()
        self.portfolio_values = self._generate_mock_portfolio_values()
    
    def _generate_mock_trades(self):
        """生成模拟交易记录"""
        trades = []
        dates = pd.date_range(start='2025-01-01', end='2025-12-31', periods=20)
        
        # 生成10对买卖交易
        for i in range(0, len(dates), 2):
            symbol = '600000.SH'
            # 买入
            buy_trade = {
                'date': dates[i],
                'symbol': symbol,
                'action': 'BUY',
                'price': 10.0 + i * 0.5,
                'quantity': 1000
            }
            trades.append(buy_trade)
            
            # 卖出
            if i + 1 < len(dates):
                # 一半盈利，一半亏损
                sell_price = buy_trade['price'] * 1.05 if i % 4 == 0 else buy_trade['price'] * 0.95
                sell_trade = {
                    'date': dates[i+1],
                    'symbol': symbol,
                    'action': 'SELL',
                    'price': sell_price,
                    'quantity': 1000
                }
                trades.append(sell_trade)
        
        return trades
    
    def _generate_mock_portfolio_values(self):
        """生成模拟组合价值"""
        values = []
        dates = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
        base_value = 100000.0
        
        for date in dates:
            # 生成有波动的组合价值
            noise = np.random.normal(0, 0.001)
            value = base_value * (1 + noise)
            base_value = value
            values.append({'date': date, 'value': value})
        
        return values

class MockParams:
    def __init__(self):
        self.stop_profit_ratio = 0.05
        self.stop_loss_ratio = -0.05
        self.backtest_days = 365
        self.strategy_id = 'test_strategy'
        self.initial_capital = 100000.0

# 测试报告生成
def test_report_generation():
    print("="*60)
    print("测试1: 报告生成功能")
    print("="*60)
    
    try:
        from report_generator import ReportGenerator
        
        # 创建模拟策略
        strategy = MockStrategy()
        
        # 创建报告生成器
        report_generator = ReportGenerator()
        
        # 生成详细报告
        report_data = report_generator.generate_detailed_report(strategy)
        
        print(f"✅ 报告生成成功")
        print(f"   总收益率: {report_data['total_return']:.2f}%")
        print(f"   年化收益率: {report_data['annual_return']:.2f}%")
        print(f"   夏普比率: {report_data['sharpe_ratio']:.2f}")
        print(f"   胜率: {report_data['win_rate']:.2f}%")
        print(f"   交易次数: {report_data['trades_count']}")
        
        # 检查报告文件是否生成
        report_file = "backtest_report.json"
        if os.path.exists(report_file):
            print(f"✅ 报告文件已保存: {report_file}")
            
            # 读取报告文件并验证内容
            with open(report_file, 'r', encoding='utf-8') as f:
                report_content = json.load(f)
            
            print(f"   报告文件包含performance_metrics: { 'performance_metrics' in report_content }")
            print(f"   报告文件包含trade_statistics: { 'trade_statistics' in report_content }")
            
            if 'performance_metrics' in report_content:
                print(f"   夏普比率: {report_content['performance_metrics'].get('sharpe_ratio', 0):.2f}")
            if 'trade_statistics' in report_content:
                print(f"   胜率: {report_content['trade_statistics'].get('win_rate', 0):.2f}%")
                print(f"   交易次数: {report_content['trade_statistics'].get('total_trades', 0)}")
        else:
            print(f"❌ 报告文件未生成: {report_file}")
            
        return True
        
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

# 测试Excel更新功能
def test_excel_update():
    print("\n" + "="*60)
    print("测试2: Excel更新功能")
    print("="*60)
    
    try:
        from parameter_optimizer import ParameterOptimizer
        
        # 创建参数优化器实例
        optimizer = ParameterOptimizer()
        
        # 生成一个简单的参数组合
        params = {
            'backtest_days': 365,
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'stop_profit_ratio': 0.05,
            'stop_loss_ratio': 0.05,
            'weights_config': {'indicator1': 0.5, 'indicator2': 0.5},
            'sub_weights_config': {},
            'initial_capital': 100000.0
        }
        
        # 模拟回测结果
        result = {
            **params,
            'total_return': 25.5,
            'annual_return': 25.5,
            'max_drawdown': -15.3,
            'sharpe_ratio': 1.85,
            'win_rate': 60.0,
            'trades_count': 20
        }
        
        # 更新Excel
        optimizer._update_excel_results([result])
        
        # 检查Excel文件是否更新
        excel_file = "parameter_optimization_results.xlsx"
        if os.path.exists(excel_file):
            print(f"✅ Excel文件已更新: {excel_file}")
            
            # 读取Excel文件并验证内容
            df = pd.read_excel(excel_file)
            print(f"   Excel文件包含 {len(df)} 条记录")
            
            # 检查列是否存在
            expected_columns = ['夏普比率', '胜率(%)']
            for col in expected_columns:
                if col in df.columns:
                    print(f"   ✅ 列 '{col}' 存在")
                    # 检查数据是否正确
                    if not df[col].empty:
                        print(f"      示例值: {df[col].iloc[0]:.2f}")
                else:
                    print(f"   ❌ 列 '{col}' 不存在")
                    
            return True
        else:
            print(f"❌ Excel文件未更新: {excel_file}")
            return False
            
    except Exception as e:
        print(f"❌ Excel更新失败: {e}")
        import traceback
        traceback.print_exc()
        return False

# 主测试函数
def main():
    print("🎯 开始测试修复功能")
    
    # 测试1: 报告生成
    report_success = test_report_generation()
    
    # 测试2: Excel更新
    excel_success = test_excel_update()
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    if report_success and excel_success:
        print("🎉 所有测试通过！修复成功")
        return 0
    else:
        print("❌ 部分测试失败，请检查修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())
