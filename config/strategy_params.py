#!/usr/bin/env python
# coding=utf-8
"""
策略参数配置系统
提供参数化配置，避免硬编码问题
"""

import os
import json
from typing import Dict, Any, Optional


class StrategyParams:
    """策略参数配置类"""
    
    def __init__(self, **kwargs):
        """
        初始化策略参数
        
        Args:
            **kwargs: 用户配置参数
        """
        # 基础回测参数
        self.initial_capital = kwargs.get('initial_capital', 100000)
        self.commission_ratio = kwargs.get('commission_ratio', 0.0003)
        self.backtest_days = kwargs.get('backtest_days', 90)
        self.strategy_id = kwargs.get('strategy_id', 'zge_strategy_backtest_v1')
        
        # 交易参数
        self.stop_profit_ratio = kwargs.get('stop_profit_ratio', 0.03)  # 止盈比例3%
        self.stop_loss_ratio = kwargs.get('stop_loss_ratio', -0.02)     # 止损比例2%
        
        # 选股参数
        self.weights_config = kwargs.get('weights_config', None)
        self.sub_weights_config = kwargs.get('sub_weights_config', None)
        self.strategy_type = kwargs.get('strategy_type', 'zge_strategy')
        
        # 股票池配置
        self.stock_pool_limit = kwargs.get('stock_pool_limit', None)  # 股票池大小限制，None表示不限制
        self.max_stocks_to_backtest = kwargs.get('max_stocks_to_backtest', 1)
        
        # 备用股票列表
        self.fallback_stocks = kwargs.get('fallback_stocks', [
            'SHSE.600036',  # 招商银行
            'SHSE.601318',  # 中国平安
            'SZSE.000858',  # 五粮液
            'SZSE.000001',  # 平安银行
            'SHSE.600519',  # 贵州茅台
        ])
        
        # 权重配置文件路径（可配置）
        self.weight_config_path = kwargs.get(
            'weight_config_path', 
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        'web', 'configs', 'weight_configs.json')
        )
        
        # 特定策略ID（可配置）
        self.bowl_strategy_id = kwargs.get(
            'bowl_strategy_id', 
            '3b229f1c-7c1a-423b-a572-e82e3d89eb08'
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'initial_capital': self.initial_capital,
            'commission_ratio': self.commission_ratio,
            'backtest_days': self.backtest_days,
            'strategy_id': self.strategy_id,
            'stop_profit_ratio': self.stop_profit_ratio,
            'stop_loss_ratio': self.stop_loss_ratio,
            'weights_config': self.weights_config,
            'sub_weights_config': self.sub_weights_config,
            'strategy_type': self.strategy_type,
            'stock_pool_limit': self.stock_pool_limit,
            'max_stocks_to_backtest': self.max_stocks_to_backtest,
            'fallback_stocks': self.fallback_stocks,
            'weight_config_path': self.weight_config_path,
            'bowl_strategy_id': self.bowl_strategy_id
        }
    
    def load_weights_from_file(self) -> Optional[Dict[str, Any]]:
        """从文件加载权重配置"""
        try:
            if os.path.exists(self.weight_config_path):
                with open(self.weight_config_path, 'r', encoding='utf-8') as f:
                    all_configs = json.load(f)
                    
                if self.bowl_strategy_id in all_configs:
                    bowl_strategy = all_configs[self.bowl_strategy_id]
                    return {
                        'weights_config': bowl_strategy.get('weights'),
                        'sub_weights_config': bowl_strategy.get('sub_weights')
                    }
        except Exception as e:
            print(f"权重配置文件加载失败: {e}")
        
        return None


# 默认参数配置
default_params = StrategyParams()

# 当前参数实例（支持动态更新）
_current_params = default_params


def create_strategy_params(**kwargs) -> StrategyParams:
    """
    创建策略参数实例
    
    Args:
        **kwargs: 用户配置参数
        
    Returns:
        StrategyParams: 策略参数实例
    """
    return StrategyParams(**kwargs)


def get_current_params() -> StrategyParams:
    """
    获取当前策略参数（从文件或默认值）
    
    Returns:
        StrategyParams: 当前策略参数
    """
    global _current_params
    return _current_params


def set_current_params(params: Dict[str, Any]):
    """
    设置当前策略参数
    
    Args:
        params: 策略参数字典
    """
    global _current_params
    _current_params = StrategyParams(**params)
    print(f"✅ 策略参数已更新: 策略ID={_current_params.strategy_id}")