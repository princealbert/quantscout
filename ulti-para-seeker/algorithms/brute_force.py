#!/usr/bin/env python
# coding=utf-8
"""
暴力优化器 - 使用暴力枚举方法进行参数优化
"""

import itertools
import os
import sys
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from .base import BaseOptimizer

# 项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入日志系统
from utils.logger import logger


class BruteForceOptimizer(BaseOptimizer):
    """
    暴力优化器类 - 使用暴力枚举方法进行参数优化
    """
    
    def __init__(self):
        """初始化暴力优化器"""
        super().__init__()
        self.current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def define_parameter_space(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                             end_date: str = '2025-12-25', backtest_days: int = 90, 
                             stop_profit_min: int = None, stop_profit_max: int = None, 
                             stop_profit_step: int = None, stop_loss_min: int = None, 
                             stop_loss_max: int = None, stop_loss_step: int = None, 
                             weight_step: int = None, initial_capital: int = 60000) -> Dict[str, Any]:
        """
        定义参数空间

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            backtest_days: 回测天数
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            initial_capital: 初始资金

        Returns:
            Dict[str, Any]: 参数空间字典
        """
        logger.info("定义参数范围...")
        logger.info(f"- 回测天数: {'10天' if test_mode else f'{backtest_days}天'}，终点日期为{end_date}")
        logger.info(f"- 初始资金: {initial_capital}元")
        
        # 如果用户提供了参数边界，使用用户提供的值，否则使用默认值
        if test_mode:
            logger.info("[测试模式] 使用最小参数范围")
            param_space = {
                'stop_profit_ratio': {'min': stop_profit_min if stop_profit_min is not None else 2, 
                                    'max': stop_profit_max if stop_profit_max is not None else 5, 
                                    'step': stop_profit_step if stop_profit_step is not None else 1},
                'stop_loss_ratio': {'min': stop_loss_min if stop_loss_min is not None else -3, 
                                  'max': stop_loss_max if stop_loss_max is not None else -1, 
                                  'step': stop_loss_step if stop_loss_step is not None else 1},
                'weight_step': weight_step if weight_step is not None else 50,
                'test_mode': True,
                'end_date': end_date,
                'backtest_days': backtest_days
            }
        else:
            # 使用用户提供的参数边界或默认值
            actual_stop_profit_min = stop_profit_min if stop_profit_min is not None else 3
            actual_stop_profit_max = stop_profit_max if stop_profit_max is not None else 15
            actual_stop_profit_step = stop_profit_step if stop_profit_step is not None else 2
            
            actual_stop_loss_min = stop_loss_min if stop_loss_min is not None else -5
            actual_stop_loss_max = stop_loss_max if stop_loss_max is not None else -1
            actual_stop_loss_step = stop_loss_step if stop_loss_step is not None else 1
            
            actual_weight_step = weight_step if weight_step is not None else 10
            
            logger.info(f"- 止盈比例: {actual_stop_profit_min}%-{actual_stop_profit_max}%，步长{actual_stop_profit_step}%")
            logger.info(f"- 止损比例: {actual_stop_loss_min}%--{abs(actual_stop_loss_max)}%，步长{actual_stop_loss_step}%")
            logger.info(f"- 权重配置: 总和100，步长{actual_weight_step}%")
            
            param_space = {
                'stop_profit_ratio': {'min': actual_stop_profit_min, 
                                    'max': actual_stop_profit_max, 
                                    'step': actual_stop_profit_step},
                'stop_loss_ratio': {'min': actual_stop_loss_min, 
                                  'max': actual_stop_loss_max, 
                                  'step': actual_stop_loss_step},
                'weight_step': actual_weight_step,
                'test_mode': False,
                'end_date': end_date,
                'backtest_days': backtest_days
            }
        
        return param_space
    
    def generate_initial_population(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                  end_date: str = '2025-12-25', backtest_days: int = 90, 
                                  stop_profit_min: int = None, stop_profit_max: int = None, 
                                  stop_profit_step: int = None, stop_loss_min: int = None, 
                                  stop_loss_max: int = None, stop_loss_step: int = None, 
                                  weight_step: int = None, initial_capital: int = 60000) -> List[Dict[str, Any]]:
        """
        生成参数组合

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            backtest_days: 回测天数
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            initial_capital: 初始资金
            
        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        # 生成参数范围，传递所有参数边界
        param_space = self.define_parameter_space(test_mode, max_sub_combinations, end_date, backtest_days, 
                                               stop_profit_min, stop_profit_max, stop_profit_step, 
                                               stop_loss_min, stop_loss_max, stop_loss_step, 
                                               weight_step, initial_capital)
        
        # 生成止盈止损比例列表（百分位格式，如 3 表示 3%）
        stop_profit_values = [param_space['stop_profit_ratio']['min'] + i * param_space['stop_profit_ratio']['step']
                            for i in range(int((param_space['stop_profit_ratio']['max'] - param_space['stop_profit_ratio']['min']) / param_space['stop_profit_ratio']['step']) + 1)]
        
        # 确保止损比例的范围是正确的
        stop_loss_min = param_space['stop_loss_ratio']['min']
        stop_loss_max = param_space['stop_loss_ratio']['max']
        stop_loss_step = param_space['stop_loss_ratio']['step']
        
        # 生成止损比例列表
        stop_loss_values = [stop_loss_min + i * stop_loss_step
                          for i in range(int((stop_loss_max - stop_loss_min) / stop_loss_step) + 1)]
        
        # 生成权重配置
        from utils.weight_utils import generate_weights_combinations, generate_sub_weights_combinations
        core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
        
        # 生成主权重组合
        weights_configs = generate_weights_combinations(
            core_indicators, 100, param_space['weight_step'], min_weight=5, max_weight=95
        )
        
        # 生成子权重组合
        sub_weights_configs = generate_sub_weights_combinations(
            test_mode, max_combinations=max_sub_combinations, use_advanced_mode=True
        )
        
        # 生成所有有效参数组合
        combinations = []
        for stop_profit in stop_profit_values:
            for stop_loss in stop_loss_values:
                if stop_profit <= stop_loss:
                    continue  # 跳过无效的止盈止损组合
                
                for weights_config in weights_configs:
                    for sub_weights_config in sub_weights_configs:
                        # 将deepv权重设置为零
                        weights_config_with_zero_deepv = weights_config.copy()
                        weights_config_with_zero_deepv['deepv'] = 0
                        
                        param_comb = {
                            'backtest_days': backtest_days,
                            'end_date': end_date,
                            'stop_profit_ratio': stop_profit,
                            'stop_loss_ratio': stop_loss,
                            'weights_config': weights_config_with_zero_deepv,
                            'sub_weights_config': sub_weights_config
                        }
                        
                        combinations.append(param_comb)
        
        # 测试模式下只返回第一个组合
        if test_mode and combinations:
            combinations = combinations[:1]
        
        logger.info(f"总共生成 {len(combinations)} 个参数组合")
        return combinations
    
    def optimize(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                end_date: str = '2025-12-25', initial_capital: int = 60000) -> List[Dict[str, Any]]:
        """
        执行暴力优化
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            initial_capital: 初始资金
            
        Returns:
            List[Dict[str, Any]]: 优化结果列表
        """
        logger.info("\n=== 执行暴力优化 ===")
        
        # 生成参数组合
        param_combinations = self.generate_initial_population(
            test_mode=test_mode,
            max_sub_combinations=max_sub_combinations,
            end_date=end_date,
            backtest_days=90  # 默认使用90天回测
        )
        
        # 为每个参数组合添加初始资金
        for param in param_combinations:
            param['initial_capital'] = initial_capital
        
        # 执行串行回测
        results = []
        total_combinations = len(param_combinations)
        
        for i, params in enumerate(param_combinations):
            logger.info(f"\n处理组合 {i+1}/{total_combinations}")
            logger.info(f"- 止盈: {params['stop_profit_ratio']*100:.1f}%，止损: {params['stop_loss_ratio']*100:.1f}%")
            
            # 运行回测
            result = self.run_backtest(params)
            results.append(result)
        
        # 按总收益率降序排序
        results.sort(key=lambda x: x.get('total_return', 0), reverse=True)
        
        return results
    
    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                      end_date: str = '2025-12-25', stop_profit_min: int = None, 
                                      stop_profit_max: int = None, stop_profit_step: int = None, 
                                      stop_loss_min: int = None, stop_loss_max: int = None, 
                                      stop_loss_step: int = None, weight_step: int = None, 
                                      focus_indicators: List[str] = None, focus_weight_factor: float = 1.5, 
                                      initial_capital: int = 60000, backtest_days: int = 90) -> List[Dict[str, Any]]:
        """
        生成参数组合

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            initial_capital: 初始资金
            backtest_days: 回测天数
            
        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        return self.generate_initial_population(test_mode, max_sub_combinations, end_date, backtest_days, 
                                              stop_profit_min, stop_profit_max, stop_profit_step, 
                                              stop_loss_min, stop_loss_max, stop_loss_step, 
                                              weight_step, initial_capital)
