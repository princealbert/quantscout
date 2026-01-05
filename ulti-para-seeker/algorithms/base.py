#!/usr/bin/env python
# coding=utf-8
"""
基础优化器接口 - 所有优化算法的基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseOptimizer(ABC):
    """
    基础优化器抽象类 - 仅定义算法接口
    """
    
    def __init__(self):
        """初始化优化器"""
        self.initial_capital = 60000  # 固定初始资金
    
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
