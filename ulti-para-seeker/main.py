#!/usr/bin/env python
# coding=utf-8
"""
参数优化专用主程序 - 避免调用原项目代码
"""

import sys
import os
from datetime import datetime, timedelta

# 添加当前目录到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gm.api import *

# 导入本地模块
try:
    from .backtest_runner import BacktestRunner
except ImportError:
    from backtest_runner import BacktestRunner

def init(context):
    """策略初始化 - 参数优化专用"""
    # 导入参数配置系统
    try:
        from .config.strategy_params import get_current_params, load_params_from_file
    except ImportError:
        from config.strategy_params import get_current_params, load_params_from_file
    
    # 获取当前策略参数（优先从文件加载）
    strategy_params = get_current_params()
    
    # 调试：验证参数加载
    print(f"调试: main.py中获取的初始资金={strategy_params.initial_capital}")
    print(f"调试: main.py中获取的止盈比例={strategy_params.stop_profit_ratio}")
    print(f"调试: main.py中获取的止损比例={strategy_params.stop_loss_ratio}")
    
    # 创建回测执行器
    context.runner = BacktestRunner(strategy_params=strategy_params)
    
    # 调用执行器的初始化方法
    context.runner.init(context)


def daily_strategy(context):
    """每日策略执行"""
    context.runner.daily_strategy(context)


def on_backtest_finished(context, indicator):
    """回测结束回调"""
    context.runner.on_backtest_finished(context, indicator)


if __name__ == '__main__':
    """参数优化专用回测主函数"""
    print("🎯 参数优化专用回测系统")
    print("="*60)
    print("📁 使用本地模块:")
    print("  - 本地backtest_runner.py: 回测执行管理")  
    print("  - 本地report_generator.py: 报告生成功能")
    print("  - 本地config_manager.py: 配置管理")
    print("="*60)
    
    # 直接运行回测（参数优化时不会直接调用这里）
    print("此主程序仅用于参数优化过程中的回测调用，不支持直接运行")
