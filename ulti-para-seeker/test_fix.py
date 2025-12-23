#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的参数传递和初始资金设置功能
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.strategy_params import StrategyParams, save_params_to_file, load_params_from_file
from strategy import BacktestStrategy
from report_generator import ReportGenerator


# 模拟context对象用于测试
class MockContext:
    def __init__(self):
        self._now = datetime.now()
        self._cash = 60000
        self._positions = []
    
    def now(self):
        return self._now
    
    def account(self):
        return MockAccount(self._cash, self._positions)


class MockAccount:
    def __init__(self, cash, positions):
        self._cash = cash
        self._positions = positions
    
    @property
    def cash(self):
        return {'available': self._cash}
    
    def positions(self):
        return self._positions


class MockPosition:
    def __init__(self, symbol, volume, vwap):
        self._symbol = symbol
        self._volume = volume
        self._vwap = vwap
    
    @property
    def symbol(self):
        return self._symbol
    
    @property
    def volume(self):
        return self._volume
    
    @property
    def vwap(self):
        return self._vwap



def test_parameter_transmission():
    """测试参数传递功能"""
    print("=== 测试参数传递 ===")
    
    # 测试1: 直接初始化参数
    params = StrategyParams(initial_capital=60000, stop_profit_ratio=0.02, stop_loss_ratio=-0.01)
    print(f"1. 参数直接初始化:")
    print(f"   - 初始资金: {params.initial_capital}")
    print(f"   - 止盈比例: {params.stop_profit_ratio}")
    print(f"   - 止损比例: {params.stop_loss_ratio}")
    
    # 测试2: 保存参数到文件
    try:
        save_params_to_file(params)
        print("2. 参数保存到文件: 成功")
    except Exception as e:
        print(f"2. 参数保存到文件: 失败 - {e}")
        return False
    
    # 测试3: 从文件加载参数
    try:
        loaded_params = load_params_from_file()
        print(f"3. 从文件加载参数:")
        print(f"   - 初始资金: {loaded_params.initial_capital}")
        print(f"   - 止盈比例: {loaded_params.stop_profit_ratio}")
        print(f"   - 止损比例: {loaded_params.stop_loss_ratio}")
    except Exception as e:
        print(f"3. 从文件加载参数: 失败 - {e}")
        return False
    
    # 验证初始资金是否正确传递
    if params.initial_capital != 60000 or loaded_params.initial_capital != 60000:
        print("错误: 初始资金传递失败")
        return False
    
    print("参数传递测试通过")
    return True


def test_initial_capital_in_report():
    """测试报告中的初始资金设置"""
    print("\n=== 测试报告中的初始资金 ===")
    
    # 初始化策略参数
    params = StrategyParams(initial_capital=60000)
    
    # 初始化策略
    strategy = BacktestStrategy(params)
    
    # 验证策略中的初始资金
    print(f"1. 策略中的初始资金: {strategy.initial_capital}")
    
    if strategy.initial_capital != 60000:
        print("错误: 策略初始资金设置不正确")
        return False
    
    # 模拟context对象
    mock_context = MockContext()
    
    # 计算投资组合价值
    portfolio_value = strategy.calculate_portfolio_value(mock_context)
    print(f"2. 投资组合价值: {portfolio_value:.2f}")
    
    # 设置投资组合价值记录
    strategy.portfolio_values.append({
        'date': datetime.now(),
        'value': portfolio_value
    })
    
    # 初始化报告生成器
    report_generator = ReportGenerator()
    
    # 生成基础报告
    try:
        report_data = report_generator.generate_basic_report(strategy)
        print(f"3. 报告数据:")
        print(f"   - 初始资金: {report_data.get('initial_capital', '未找到')}")
        print(f"   - 最终资金: {report_data.get('final_capital', '未找到')}")
        print(f"   - 总收益率: {report_data.get('total_return', '未找到')}")
    except Exception as e:
        print(f"3. 生成报告失败: {e}")
        return False
    
    # 验证报告中的初始资金
    if report_data.get('initial_capital') != 60000:
        print("错误: 报告中的初始资金不正确")
        return False
    
    print("报告初始资金测试通过")
    return True


def test_save_report_to_file():
    """测试保存报告到文件功能"""
    print("\n=== 测试保存报告到文件 ===")
    
    # 初始化策略参数
    params = StrategyParams(initial_capital=60000)
    strategy = BacktestStrategy(params)
    
    # 模拟context对象
    mock_context = MockContext()
    
    # 设置策略的投资组合价值
    strategy.cash = 60000
    strategy.positions = {}
    
    # 计算投资组合价值
    portfolio_value = strategy.calculate_portfolio_value(mock_context)
    
    # 设置投资组合价值记录
    strategy.portfolio_values.append({
        'date': datetime.now(),
        'value': portfolio_value
    })
    
    # 生成报告
    report_generator = ReportGenerator()
    report_data = report_generator.generate_basic_report(strategy)
    
    # 保存报告到文件
    try:
        report_generator._save_report_to_file(report_data)
        print("保存报告到文件: 成功")
        return True
    except Exception as e:
        print(f"保存报告到文件: 失败 - {e}")
        return False


if __name__ == "__main__":
    print("开始测试修复后的功能...")
    
    # 运行所有测试
    test1_passed = test_parameter_transmission()
    test2_passed = test_initial_capital_in_report()
    test3_passed = test_save_report_to_file()
    
    print("\n=== 测试结果汇总 ===")
    print(f"1. 参数传递测试: {'通过' if test1_passed else '失败'}")
    print(f"2. 报告初始资金测试: {'通过' if test2_passed else '失败'}")
    print(f"3. 保存报告到文件测试: {'通过' if test3_passed else '失败'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n所有测试通过! 修复有效。")
        sys.exit(0)
    else:
        print("\n存在测试失败，需要进一步修复。")
        sys.exit(1)
