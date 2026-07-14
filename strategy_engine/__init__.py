#!/usr/bin/env python
# coding=utf-8
"""
策略引擎模块 - 回测系统的核心组件
提供策略执行、回测运行、报告生成等功能的解耦实现
"""

import sys
import os

# 优先添加项目根目录到Python路径，避免ulti-para-seeker/config.py与根目录config包冲突
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from .strategy import BacktestStrategy
from .backtest_runner import BacktestRunner, run_backtest
from .report_generator import ReportGenerator, generate_backtest_summary
from .config_manager import ConfigManager, get_current_config, update_backtest_config, validate_current_config

# 从新的Token管理模块导入(位于根目录config包)
from config.token_manager import TokenManager, get_token_manager, get_token, validate_token, update_token, get_token_info

__all__ = [
    'BacktestStrategy',
    'BacktestRunner', 
    'ReportGenerator',
    'ConfigManager',
    'TokenManager',
    'run_backtest',
    'generate_backtest_summary',
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