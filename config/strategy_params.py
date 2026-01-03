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
    
    def update_params(self, config: Dict[str, Any]) -> None:
        """
        根据配置字典更新参数
        
        Args:
            config: 参数配置字典
        """
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)


# 参数文件路径（用于进程间参数传递）
_PARAMS_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'current_backtest_config.json')


def save_params_to_file(params=None) -> str:
    """
    保存策略参数到文件（用于进程间参数传递）
    
    Args:
        params: 策略参数字典或StrategyParams对象，默认为当前参数
    
    Returns:
        str: 参数文件路径
    """
    global _current_params
    if params is None:
        params = _current_params
    
    if not isinstance(params, StrategyParams):
        params = StrategyParams(**params)
    
    try:
        # 将参数转换为前端配置文件的嵌套结构
        flat_params = params.to_dict()
        
        # 构建嵌套结构的配置文件
        frontend_config = {
            'backtest': {
                'initial_capital': flat_params.get('initial_capital'),
                'backtest_days': flat_params.get('backtest_days'),
                'max_stocks_to_backtest': flat_params.get('max_stocks_to_backtest'),
                'strategy_id': flat_params.get('strategy_id'),
                'commission_ratio': flat_params.get('commission_ratio')
            },
            'strategy': {
                'stop_profit_ratio': flat_params.get('stop_profit_ratio'),
                'stop_loss_ratio': flat_params.get('stop_loss_ratio'),
                'weights_config': flat_params.get('weights_config'),
                'sub_weights_config': flat_params.get('sub_weights_config'),
                'strategy_type': flat_params.get('strategy_type')
            }
        }
        
        with open(_PARAMS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(frontend_config, f, ensure_ascii=False, indent=2)
        print(f"✅ 策略参数已保存到文件: {_PARAMS_FILE_PATH}")
        return _PARAMS_FILE_PATH
    except Exception as e:
        print(f"❌ 保存策略参数到文件失败: {e}")
        return None


def load_params_from_file(file_path=None) -> Optional[StrategyParams]:
    """
    从文件加载策略参数（用于进程间参数传递）
    
    Args:
        file_path: 参数文件路径，默认为默认路径
    
    Returns:
        Optional[StrategyParams]: 策略参数对象，如果加载失败则返回None
    """
    if file_path is None:
        file_path = _PARAMS_FILE_PATH
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        else:
            print(f"⚠️ 参数文件不存在: {file_path}")
            return None
    except Exception as e:
        print(f"❌ 从文件加载策略参数失败: {e}")
        return None
    
    # 解析前端配置文件结构（嵌套结构）
    try:
        params_dict = {}
        
        # 提取backtest部分参数
        if 'backtest' in config_data:
            backtest_config = config_data['backtest']
            params_dict['initial_capital'] = backtest_config.get('initial_capital')
            params_dict['commission_ratio'] = backtest_config.get('commission_ratio')
            params_dict['backtest_days'] = backtest_config.get('backtest_days')
            params_dict['strategy_id'] = backtest_config.get('strategy_id')
            params_dict['max_stocks_to_backtest'] = backtest_config.get('max_stocks_to_backtest')
        
        # 确保必填参数有默认值
        if params_dict.get('commission_ratio') is None:
            params_dict['commission_ratio'] = 0.0003
        
        # 提取strategy部分参数
        if 'strategy' in config_data:
            strategy_config = config_data['strategy']
            params_dict['stop_profit_ratio'] = strategy_config.get('stop_profit_ratio')
            params_dict['stop_loss_ratio'] = strategy_config.get('stop_loss_ratio')
            params_dict['weights_config'] = strategy_config.get('weights_config')
            params_dict['sub_weights_config'] = strategy_config.get('sub_weights_config')
            params_dict['strategy_type'] = strategy_config.get('strategy_type')
        
        # 创建并返回策略参数对象
        params = StrategyParams(**params_dict)
        print(f"✅ 从文件加载策略参数成功: {file_path}")
        print(f"💰 初始资金: {params.initial_capital:,}元")
        return params
    except Exception as e:
        print(f"❌ 解析策略参数失败: {e}")
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
    获取当前策略参数（优先从文件加载，然后是全局变量，最后是默认值）
    
    Returns:
        StrategyParams: 当前策略参数
    """
    global _current_params
    
    # 1. 优先从文件加载参数（用于解决进程间参数传递问题）
    file_params = load_params_from_file()
    if file_params is not None:
        return file_params
    
    # 2. 如果文件不存在或加载失败，使用全局变量
    return _current_params


def set_current_params(params: Dict[str, Any]):
    """
    设置当前策略参数
    
    Args:
        params: 策略参数字典
    """
    global _current_params
    _current_params = StrategyParams(**params)
    # 将参数保存到文件，确保进程间参数传递正确
    save_params_to_file(_current_params)
    print(f"✅ 策略参数已更新: 策略ID={_current_params.strategy_id}")