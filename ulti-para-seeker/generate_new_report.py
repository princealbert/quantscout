#!/usr/bin/env python
# coding=utf-8
"""
生成新的JSON报告来测试修复是否有效
"""

import os
import sys
import json
from datetime import datetime

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入报告生成器
from report_generator import ReportGenerator, OptimizedReportGenerator

class MockStrategy:
    """模拟策略类用于测试"""
    def __init__(self):
        self.initial_capital = 100000.0
        self.params = type('Params', (), {
            'stop_profit_ratio': 0.02,
            'stop_loss_ratio': 0.01
        })()
        self.trading_records = []
        self.portfolio_values = [
            {'date': datetime.now(), 'value': 100000.0},
            {'date': datetime.now(), 'value': 102000.0},
            {'date': datetime.now(), 'value': 105000.0}
        ]

class MockContext:
    """模拟回测上下文用于测试"""
    def __init__(self):
        self._cash = 100000.0
        self._transactions = []
        self._portfolio_values = [
            {'date': datetime.now(), 'value': 100000.0},
            {'date': datetime.now(), 'value': 102000.0},
            {'date': datetime.now(), 'value': 105000.0}
        ]
    
    def account(self):
        return MockAccount()
    
    def history(self):
        return MockHistory()

class MockAccount:
    """模拟账户类"""
    def __init__(self):
        self.cash = 100000.0
    
    def positions(self):
        return []

class MockHistory:
    """模拟历史数据类"""
    def __init__(self):
        self.transactions = []

if __name__ == "__main__":
    print("生成新的JSON报告...")
    
    # 使用ReportGenerator生成报告
    print("\n1. 使用ReportGenerator生成报告:")
    strategy = MockStrategy()
    report_generator = ReportGenerator()
    basic_report = report_generator.generate_basic_report(strategy)
    detailed_report = report_generator.generate_detailed_report(strategy)
    
    print(f"基础报告包含的键: {list(basic_report.keys())}")
    print(f"详细报告包含的键: {list(detailed_report.keys())}")
    
    # 使用OptimizedReportGenerator生成报告
    print("\n2. 使用OptimizedReportGenerator生成报告:")
    params = {'stop_profit_ratio': 0.02, 'stop_loss_ratio': 0.01}
    initial_capital = 100000.0
    optimized_report_generator = OptimizedReportGenerator(params, initial_capital)
    context = MockContext()
    indicator_data = {'portfolio_values': context._portfolio_values}
    report = optimized_report_generator.generate_basic_report(context, indicator_data)
    
    print(f"优化版报告包含的键: {list(report.keys())}")
    
    print("\n报告生成完成！")
