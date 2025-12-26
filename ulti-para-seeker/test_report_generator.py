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
