#!/usr/bin/env python
# coding=utf-8
"""
参数优化器模块 - 提供参数优化相关的功能
"""

# 从backtest模块导入
from .backtest import (
    OptimizerBacktestStrategy as BacktestStrategy,
    OptimizerBacktestRunner as BacktestRunner,
    run_optimizer_backtest as run_backtest,
    OptimizerReportGenerator as ReportGenerator,
    OptimizerConfigManager as ConfigManager,
    OptimizerFrontendConfigLoader
)

# 从backtest.config导入配置管理功能
from .backtest.config import get_current_config, update_backtest_config, validate_current_config
from .token_manager import TokenManager, get_token_manager, get_token, validate_token, update_token, get_token_info

__all__ = [
    # 回测策略和执行器
    'BacktestStrategy',
    'BacktestRunner', 
    'run_backtest',
    
    # 报告生成
    'ReportGenerator',
    
    # 配置管理
    'ConfigManager',
    'OptimizerFrontendConfigLoader',
    'get_current_config',
    'update_backtest_config',
    'validate_current_config',
    
    # Token管理
    'TokenManager',
    'get_token_manager',
    'get_token',
    'validate_token',
    'update_token',
    'get_token_info'
]

__version__ = '1.0.0'