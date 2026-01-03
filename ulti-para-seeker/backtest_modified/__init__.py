#!/usr/bin/env python
# coding=utf-8
"""
参数优化器专属回测模块
包含优化器定制的回测执行、配置管理、报告生成和策略实现
"""

# 导出模块功能
from .runner import OptimizerBacktestRunner, run_optimizer_backtest
from .config import OptimizerConfigManager, OptimizerFrontendConfigLoader
from .reporter import OptimizerReportGenerator
from .strategy import OptimizerBacktestStrategy

__all__ = [
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
