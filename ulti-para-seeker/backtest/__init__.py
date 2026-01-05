#!/usr/bin/env python
# coding=utf-8
"""
回测模块 - 提供统一的回测接口
包含优化器定制的回测执行、配置管理、报告生成和策略实现
"""

from .backtest_adapter import BacktestAdapter
from .runner import OptimizerBacktestRunner, run_optimizer_backtest
from .config import OptimizerConfigManager, OptimizerFrontendConfigLoader
from .reporter import OptimizerReportGenerator
from .strategy import OptimizerBacktestStrategy

__all__ = [
    # 回测适配器
    'BacktestAdapter',
    
    # 回测执行器
    'OptimizerBacktestRunner',
    'run_optimizer_backtest',
    
    # 配置管理
    'OptimizerConfigManager',
    'OptimizerFrontendConfigLoader',
    
    # 报告生成
    'OptimizerReportGenerator',
    
    # 策略实现
    'OptimizerBacktestStrategy'
]

__version__ = '1.0.0'
