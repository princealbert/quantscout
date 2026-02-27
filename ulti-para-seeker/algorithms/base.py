#!/usr/bin/env python
# coding=utf-8
"""
基础优化器接口 - 所有优化算法的基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseOptimizer(ABC):
    """
    基础优化器抽象类 - 定义算法接口和通用参数生成逻辑
    """
    
    def __init__(self):
        """初始化优化器"""
        self.initial_capital = 60000  # 固定初始资金
        self.population_size = 50  # 默认种群大小
    
    @abstractmethod
    def define_parameter_space(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                              end_date: str = '2025-12-25', backtest_days: int = 90) -> Dict[str, Any]:
        """
        定义参数空间
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            backtest_days: 回测天数
            
        Returns:
            参数空间字典
        """
        pass
    
    @abstractmethod
    def generate_initial_population(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                  end_date: str = '2025-12-25', backtest_days: int = 90) -> List[Dict[str, Any]]:
        """
        生成初始种群/参数组合
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            backtest_days: 回测天数
            
        Returns:
            参数组合列表
        """
        pass
    
    @abstractmethod
    def optimize(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                end_date: str = '2025-12-25', initial_capital: int = 60000) -> List[Dict[str, Any]]:
        """
        执行优化
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            initial_capital: 初始资金
            
        Returns:
            优化结果列表
        """
        pass
    
    def run_backtest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个参数组合的回测（默认实现，子类可重写）
        
        Args:
            params: 参数组合
            
        Returns:
            Dict[str, Any]: 回测结果
        """
        from backtest.backtest_adapter import BacktestAdapter
        return BacktestAdapter.run_backtest(params)
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        验证参数组合的有效性
        
        Args:
            params: 参数组合
            
        Returns:
            参数组合是否有效
        """
        try:
            # 验证止盈止损逻辑
            stop_profit = params.get('stop_profit_ratio', 0)
            stop_loss = params.get('stop_loss_ratio', 0)
            
            if stop_profit <= stop_loss:
                return False
            
            # 支持百分位格式（如3表示3%）和千分位格式（如0.03）
            # 百分位格式：stop_profit 在 1-100 之间，stop_loss 在 -100 到 -1 之间
            # 千分位格式：stop_profit 在 0.01-1 之间，stop_loss 在 -1 到 -0.01 之间
            if stop_profit >= 1:
                # 百分位格式
                if not (1 <= stop_profit <= 100):
                    return False
                if not (-100 <= stop_loss <= -1):
                    return False
            else:
                # 千分位格式
                if not (0 < stop_profit <= 1):
                    return False
                if not (-1 <= stop_loss < 0):
                    return False
            
            # 验证权重配置
            weights = params.get('weights_config', {})
            total_weight = sum(weights.values())
            
            if total_weight != 100:
                return False
            
            # 核心指标权重必须为正数，deepv权重可以为零
            core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
            for ind in core_indicators:
                if weights.get(ind, 0) <= 0:
                    return False
            
            # 验证子权重配置
            sub_weights = params.get('sub_weights_config', {})
            for main_indicator, sub_config in sub_weights.items():
                if 'sub_weights' not in sub_config:
                    return False
                
                sub_weights_dict = sub_config['sub_weights']
                if sum(sub_weights_dict.values()) != 100 or any(w <= 0 for w in sub_weights_dict.values()):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _generate_random_weights_config(self, step: int) -> Dict[str, int]:
        """
        生成随机权重配置
        
        Args:
            step: 权重步长
        
        Returns:
            Dict[str, int]: 权重配置字典
        """
        import random
        core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
        num_indicators = len(core_indicators)
        
        # 生成随机权重（确保在5%-95%之间，使用随机步长）
        weights = []
        remaining = 100
        
        # 为前n-1个指标分配随机权重
        for i in range(num_indicators - 1):
            # 计算当前指标可分配的最大权重
            max_possible = min(95, remaining - (num_indicators - 1 - i) * 5)
            if max_possible < 5:
                weight = 5
            else:
                # 生成随机权重，确保是step的倍数
                # 确保max_possible + 1 >= 5 + step，否则调整步长为1
                if max_possible + 1 < 5 + step:
                    adjusted_step = 1
                else:
                    adjusted_step = step
                weight = random.randrange(5, max_possible + 1, adjusted_step)
            weights.append(weight)
            remaining -= weight
        
        # 最后一个指标分配剩余权重
        weights.append(remaining)
        
        # 随机打乱权重顺序，增加多样性
        random.shuffle(weights)
        
        # 创建权重配置字典
        weights_config = dict(zip(core_indicators, weights))
        weights_config['deepv'] = 0  # deepv权重设为0
        
        # 确保权重总和为100
        assert sum(weights_config.values()) == 100, f"权重总和必须为100，当前为{sum(weights_config.values())}"
        
        return weights_config
    
    def _generate_default_sub_weights(self) -> Dict[str, Dict[str, int]]:
        """
        生成默认子权重配置
        
        Returns:
            Dict[str, Dict[str, int]]: 默认子权重配置
        """
        default_sub_weights = {
            'kdj_j': {'sub_weights': {'j_0_20': 20, 'j_-10_0': 20, 'j_-20_-10': 20, 'j_-30_-20': 20, 'j_below_-30': 20}},
            'position': {'sub_weights': {'above_white': 33, 'between_lines': 34, 'below_yellow': 33}},
            'volume': {'sub_weights': {'big_volume': 33, 'volume_anomaly': 34, 'volume_breathing': 33}},
            'fundamental': {'sub_weights': {'pe_positive': 25, 'pe_low': 25, 'market_cap': 25, 'volume_threshold': 25}},
            'trend': {'sub_weights': {'up_trend': 34, 'volume_price_rise': 33, 'volume_contraction': 33}}
        }
        return default_sub_weights
    
    def _generate_random_sub_weights(self, test_mode: bool, max_combinations: int = 5) -> Dict[str, Dict[str, int]]:
        """
        生成随机子权重配置
        
        Args:
            test_mode: 是否为测试模式
            max_combinations: 最大生成组合数
        
        Returns:
            Dict[str, Dict[str, int]]: 随机子权重配置
        """
        from utils.weight_utils import generate_sub_weights_combinations
        sub_weights_combos = generate_sub_weights_combinations(
            test_mode, max_combinations=max_combinations, use_advanced_mode=True
        )
        if sub_weights_combos:
            import random
            return random.choice(sub_weights_combos)
        else:
            return self._generate_default_sub_weights()
    
    def _generate_parameter_combination(self, param_space: Dict[str, Any], sub_weights_configs: List[Dict[str, Dict[str, int]]], 
                                      backtest_days: int, end_date: str, initial_capital: int = 60000) -> Dict[str, Any]:
        """
        生成单个参数组合
        
        Args:
            param_space: 参数空间
            sub_weights_configs: 子权重配置列表
            backtest_days: 回测天数
            end_date: 回测终点日期
            initial_capital: 初始资金
        
        Returns:
            Dict[str, Any]: 参数组合
        """
        import random
        
        # 随机生成止盈止损比例（整数格式，百分位）
        # 生成止盈选项列表，按照指定步长
        stop_profit_options = list(range(
            param_space['stop_profit_ratio']['min'],
            param_space['stop_profit_ratio']['max'] + 1,
            param_space['stop_profit_ratio']['step']
        ))
        stop_profit = random.choice(stop_profit_options)
        
        # 生成止损选项列表，按照指定步长
        stop_loss_options = list(range(
            param_space['stop_loss_ratio']['min'],
            param_space['stop_loss_ratio']['max'] + 1,
            param_space['stop_loss_ratio']['step']
        ))
        stop_loss = random.choice(stop_loss_options)
        
        # 确保止盈大于止损
        if stop_profit <= stop_loss:
            # 重新选择止盈值，确保大于止损
            valid_stop_profit = [p for p in stop_profit_options if p > stop_loss]
            if valid_stop_profit:
                stop_profit = random.choice(valid_stop_profit)
            else:
                # 如果没有有效止盈值，重新选择止损值
                valid_stop_loss = [l for l in stop_loss_options if stop_profit > l]
                if valid_stop_loss:
                    stop_loss = random.choice(valid_stop_loss)
                else:
                    # 极端情况下，调整止损值
                    stop_loss = stop_profit - param_space['stop_loss_ratio']['step']
        
        # 生成最大持仓天数选项列表，按照指定步长
        max_holding_days_options = list(range(
            param_space.get('max_holding_days', {'min': 1})['min'],
            param_space.get('max_holding_days', {'max': 30})['max'] + 1,
            param_space.get('max_holding_days', {'step': 1})['step']
        ))
        max_holding_days = random.choice(max_holding_days_options)
        
        # 生成权重配置
        weights_config = self._generate_random_weights_config(param_space['weights_step'])
        
        # 随机选择一个子权重配置
        if sub_weights_configs:
            sub_weights = random.choice(sub_weights_configs)
        else:
            sub_weights = self._generate_random_sub_weights(param_space.get('test_mode', False))
        
        # 创建参数组合
        param_comb = {
            'backtest_days': backtest_days,
            'end_date': end_date,
            'stop_profit_ratio': stop_profit,
            'stop_loss_ratio': stop_loss,
            'max_holding_days': max_holding_days,
            'weights_config': weights_config,
            'sub_weights_config': sub_weights,
            'initial_capital': initial_capital
        }
        
        return param_comb
    
    def _generate_random_params(self, param_space: Dict[str, Any], backtest_days: int, end_date: str, 
                              initial_capital: int = 60000) -> Dict[str, Any]:
        """
        生成随机参数组合
        
        Args:
            param_space: 参数空间
            backtest_days: 回测天数
            end_date: 回测终点日期
            initial_capital: 初始资金
        
        Returns:
            Dict[str, Any]: 随机参数组合
        """
        # 生成子权重配置
        from utils.weight_utils import generate_sub_weights_combinations
        sub_weights_configs = generate_sub_weights_combinations(
            param_space.get('test_mode', False), 
            max_combinations=5, 
            use_advanced_mode=True
        )
        
        # 生成参数组合
        return self._generate_parameter_combination(param_space, sub_weights_configs, backtest_days, end_date, initial_capital)
