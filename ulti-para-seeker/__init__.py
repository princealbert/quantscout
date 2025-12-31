#!/usr/bin/env python
# coding=utf-8
"""
策略引擎模块 - 回测系统的核心组件
提供策略执行、回测运行、报告生成等功能的解耦实现
"""

from .strategy import BacktestStrategy
from .backtest_runner import BacktestRunner, run_backtest
from .report_generator import ReportGenerator
from .config_manager import ConfigManager, get_current_config, update_backtest_config, validate_current_config
from .token_manager import TokenManager, get_token_manager, get_token, validate_token, update_token, get_token_info

__all__ = [
    'BacktestStrategy',
    'BacktestRunner', 
    'ReportGenerator',
    'ConfigManager',
    'TokenManager',
    'run_backtest',
    'get_current_config',
    'update_backtest_config',
    'validate_current_config',
    'get_token_manager',
    'get_token',
    'validate_token',
    'update_token',
    'get_token_info'
]

__version__ = '1.0.0'