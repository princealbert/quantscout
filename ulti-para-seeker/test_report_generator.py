#!/usr/bin/env python
# coding=utf-8
"""
测试report_generator.py是否能正确生成回测结果
"""

import sys
import os
import json

# 添加当前目录到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入ReportGenerator
from datetime import datetime
try:
    from report_generator import ReportGenerator
except ImportError as e:
    print(f"导入ReportGenerator失败: {e}")
    sys.exit(1)

# 创建模拟的策略对象
class MockParams:
    def __init__(self):
        self.stop_profit_ratio = 0.02
        self.stop_loss_ratio = -0.01

class MockStrategy:
    def __init__(self, initial_capital, portfolio_values):
        self.initial_capital = initial_capital
        self.portfolio_values = portfolio_values
        self.trading_records = []
        self.params = MockParams()

# 测试用例1: 有portfolio_values但没有trading_records的情况
print("测试用例1: 有portfolio_values但没有trading_records的情况")
initial_capital = 60000
portfolio_values = [
    {'value': 60000, 'date': '2025-12-01'},
    {'value': 61000, 'date': '2025-12-02'},
    {'value': 62500, 'date': '2025-12-03'}
]

strategy = MockStrategy(initial_capital, portfolio_values)
report_generator = ReportGenerator()
report = report_generator.generate_basic_report(strategy)

print(f"初始资金: {initial_capital}")
print(f"最终资金: {portfolio_values[-1]['value']}")
print(f"计算的总收益率: {report.get('total_return', 0.0)}%")
print(f"计算的最大回撤: {report.get('max_drawdown', 0.0)}%")
print()

# 测试用例2: portfolio_values变化为负的情况
print("测试用例2: portfolio_values变化为负的情况")
portfolio_values_neg = [
    {'value': 60000, 'date': '2025-12-01'},
    {'value': 59000, 'date': '2025-12-02'},
    {'value': 58500, 'date': '2025-12-03'}
]

strategy_neg = MockStrategy(initial_capital, portfolio_values_neg)
report_neg = report_generator.generate_basic_report(strategy_neg)

print(f"初始资金: {initial_capital}")
print(f"最终资金: {portfolio_values_neg[-1]['value']}")
print(f"计算的总收益率: {report_neg.get('total_return', 0.0)}%")
print(f"计算的最大回撤: {report_neg.get('max_drawdown', 0.0)}%")
print()

# 测试用例3: portfolio_values不变的情况
print("测试用例3: portfolio_values不变的情况")
portfolio_values_same = [
    {'value': 60000, 'date': '2025-12-01'},
    {'value': 60000, 'date': '2025-12-02'},
    {'value': 60000, 'date': '2025-12-03'}
]

strategy_same = MockStrategy(initial_capital, portfolio_values_same)
report_same = report_generator.generate_basic_report(strategy_same)

print(f"初始资金: {initial_capital}")
print(f"最终资金: {portfolio_values_same[-1]['value']}")
print(f"计算的总收益率: {report_same.get('total_return', 0.0)}%")
print(f"计算的最大回撤: {report_same.get('max_drawdown', 0.0)}%")
print()

# 测试保存报告到文件
print("测试保存报告到文件")
try:
    # 测试_save_report_to_file方法
    if hasattr(report_generator, '_save_report_to_file'):
        report_generator._save_report_to_file(report)
        print("✅ 报告保存成功")
        
        # 检查文件是否存在
        report_file = 'backtest_report.json'
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                saved_report = json.load(f)
            print(f"✅ 成功读取保存的报告，总收益率: {saved_report.get('performance_metrics', {}).get('total_return', 0.0)}%")
            # 删除测试文件
            os.unlink(report_file)
        else:
            print("❌ 保存的报告文件不存在")
    else:
        print("❌ _save_report_to_file方法不存在")
except Exception as e:
    print(f"❌ 保存报告失败: {e}")

# 测试用例4: 测试详细报告生成（包含夏普比率和胜率）
print("\n测试用例4: 测试详细报告生成（包含夏普比率和胜率）")

# 创建模拟的策略对象，包含交易记录
class MockStrategyWithTrades:
    def __init__(self):
        self.initial_capital = 60000
        self.params = MockParams()
        # 模拟组合价值变化
        self.portfolio_values = [
            {'date': datetime(2025, 12, 1), 'value': 60000},
            {'date': datetime(2025, 12, 2), 'value': 61500},
            {'date': datetime(2025, 12, 3), 'value': 63000},
            {'date': datetime(2025, 12, 4), 'value': 62000},
            {'date': datetime(2025, 12, 5), 'value': 64500}
        ]
        # 模拟交易记录（3笔交易，2赢1输）
        self.trading_records = [
            {'date': datetime(2025, 12, 1), 'symbol': 'AAPL', 'action': 'BUY', 'price': 100, 'quantity': 100},
            {'date': datetime(2025, 12, 2), 'symbol': 'AAPL', 'action': 'SELL', 'price': 102, 'quantity': 100},
            {'date': datetime(2025, 12, 3), 'symbol': 'MSFT', 'action': 'BUY', 'price': 200, 'quantity': 50},
            {'date': datetime(2025, 12, 4), 'symbol': 'MSFT', 'action': 'SELL', 'price': 198, 'quantity': 50},
            {'date': datetime(2025, 12, 4), 'symbol': 'GOOGL', 'action': 'BUY', 'price': 150, 'quantity': 100},
            {'date': datetime(2025, 12, 5), 'symbol': 'GOOGL', 'action': 'SELL', 'price': 155, 'quantity': 100}
        ]

try:
    strategy_with_trades = MockStrategyWithTrades()
    detailed_report = report_generator.generate_detailed_report(strategy_with_trades)
    
    print(f"✅ 详细报告生成成功")
    print(f"总收益率: {detailed_report.get('total_return', 0.0):.2f}%")
    print(f"夏普比率: {detailed_report.get('sharpe_ratio', 0.0):.4f}")
    print(f"胜率: {detailed_report.get('win_rate', 0.0):.2f}%")
    print(f"交易次数: {detailed_report.get('trades_count', 0)}")
    
    # 验证夏普比率和胜率是否已计算
    if 'sharpe_ratio' in detailed_report and 'win_rate' in detailed_report:
        print("✅ 夏普比率和胜率已正确添加到报告中")
    else:
        print("❌ 夏普比率和胜率未添加到报告中")
        
    # 检查夏普比率和胜率的合理性
    if detailed_report.get('sharpe_ratio', 0.0) > 0:
        print("✅ 夏普比率为正数，符合预期")
    if 0 <= detailed_report.get('win_rate', 0.0) <= 100:
        print("✅ 胜率在合理范围内（0-100%）")
        
except Exception as e:
    print(f"❌ 详细报告生成失败: {e}")
    import traceback
    traceback.print_exc()
