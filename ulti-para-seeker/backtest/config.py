#!/usr/bin/env python
# coding=utf-8
"""
配置管理模块 - 负责参数优化器专属的配置管理
依赖统一的strategy_engine.config_manager，只保留优化器专属功能
"""

from typing import Dict, Any, Optional, List
import os

# 导入统一的配置管理器
from strategy_engine.config_manager import ConfigManager as BaseConfigManager
from strategy_engine.config_manager import FrontendConfigLoader as BaseFrontendConfigLoader


class OptimizerConfigManager(BaseConfigManager):
    """
    优化器配置管理器 - 继承自基础配置管理器，添加优化器专属功能
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化优化器配置管理器
        
        Args:
            config_path: 配置文件路径，默认为None（使用默认路径）
        """
        # 调用父类初始化
        super().__init__(config_path)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置 - 针对优化器的特殊配置
        """
        # 获取基础配置
        base_config = super()._get_default_config()
        
        # 针对优化器的特殊配置
        base_config['backtest']['stock_pool_limit'] = None  # 优化器模式下不限制股票池大小
        
        return base_config


class OptimizerFrontendConfigLoader(BaseFrontendConfigLoader):
    """
    优化器前端配置加载器 - 继承自基础加载器，添加优化器专属功能
    """
    
    @staticmethod
    def convert_to_strategy_params(frontend_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        将前端配置转换为StrategyParams兼容的格式 - 针对优化器优化
        
        Args:
            frontend_config: 前端生成的配置数据
            
        Returns:
            Dict[str, Any]: 转换后的配置数据
        """
        # 使用基础转换方法
        params = BaseFrontendConfigLoader.convert_to_strategy_params(frontend_config)
        
        # 针对优化器的特殊调整
        params['stock_pool_limit'] = None  # 优化器模式下不限制股票池大小
        
        return params


# 导出优化器专用的快速函数
def get_optimizer_config() -> Dict[str, Any]:
    """
    获取优化器配置（快速函数）
    
    Returns:
        Dict[str, Any]: 当前配置
    """
    manager = OptimizerConfigManager()
    return manager.load_config()


def get_current_config() -> Dict[str, Any]:
    """
    获取当前配置（快速函数）- 兼容现有代码
    
    Returns:
        Dict[str, Any]: 当前配置
    """
    manager = OptimizerConfigManager()
    return manager.load_config()


def update_backtest_config(new_params: Dict[str, Any]) -> bool:
    """
    更新回测配置（快速函数）- 兼容现有代码
    
    Args:
        new_params: 新参数
        
    Returns:
        bool: 是否成功
    """
    manager = OptimizerConfigManager()
    manager.update_backtest_params(new_params)
    return True


def validate_current_config() -> Dict[str, Any]:
    """
    验证当前配置（快速函数）- 兼容现有代码
    
    Returns:
        Dict[str, Any]: 验证结果
    """
    manager = OptimizerConfigManager()
    return manager.validate_config()


def get_strategy_params_optimizer() -> Dict[str, Any]:
    """
    获取策略参数（兼容现有代码，针对优化器）
    
    Returns:
        Dict[str, Any]: 策略参数
    """
    manager = OptimizerConfigManager()
    config = manager.load_config()
    
    # 转换为与StrategyParams类兼容的格式
    strategy_params = config.get('strategy', {})
    backtest_params = config.get('backtest', {})
    trading_params = config.get('trading', {})
    fallback_params = config.get('fallback', {})
    
    return {
        'initial_capital': backtest_params.get('initial_capital', 100000),
        'commission_ratio': backtest_params.get('commission_ratio', 0.0003),
        'backtest_days': backtest_params.get('backtest_days', 90),
        'stop_profit_ratio': trading_params.get('stop_profit_ratio', 0.03),
        'stop_loss_ratio': trading_params.get('stop_loss_ratio', -0.02),
        'strategy_id': strategy_params.get('strategy_id', 'zge_strategy_v1'),
        'strategy_type': strategy_params.get('strategy_type', '碗选股'),
        'max_stocks_to_backtest': backtest_params.get('max_stocks_to_backtest', 1),
        'stock_pool_limit': None,  # 优化器模式下不限制股票池大小
        'weights_config': strategy_params.get('weights_config', {}),
        'sub_weights_config': strategy_params.get('sub_weights_config', {}),
        'fallback_stocks': fallback_params.get('fallback_stocks', [])
    }
