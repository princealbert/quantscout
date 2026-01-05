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
                             end_date: str = '2025-12-25', backtest_days: int = 90) -> Dict[str, Any]:
        """
        定义参数空间

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            backtest_days: 回测天数

        Returns:
            Dict[str, Any]: 参数空间字典
        """
        logger.info("定义参数范围...")
        logger.info(f"- 回测天数: {'10天' if test_mode else f'{backtest_days}天'}，终点日期为{end_date}")
        
        # 根据模式调整参数范围
        if test_mode:
            logger.info("[测试模式] 使用最小参数范围")
            param_space = {
                'stop_profit_ratio': {'min': 0.02, 'max': 0.05, 'step': 0.01},
                'stop_loss_ratio': {'min': -0.03, 'max': -0.01, 'step': 0.01},
                'weight_step': 50,
                'test_mode': True,
                'end_date': end_date,
                'backtest_days': backtest_days
            }
        else:
            logger.info("- 止盈比例: 3%-15%，步长2%")
            logger.info("- 止损比例: -5%--1%，步长1%")
            logger.info("- 权重配置: 总和100，步长10%")
            
            param_space = {
                'stop_profit_ratio': {'min': 0.03, 'max': 0.15, 'step': 0.02},
                'stop_loss_ratio': {'min': -0.05, 'max': -0.01, 'step': 0.01},
                'weight_step': 10,
                'test_mode': False,
                'end_date': end_date,
                'backtest_days': backtest_days
            }
        
        return param_space
    
    def generate_initial_population(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                  end_date: str = '2025-12-25', backtest_days: int = 90) -> List[Dict[str, Any]]:
        """
        生成参数组合

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            backtest_days: 回测天数
            
        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        # 生成参数范围
        param_space = self.define_parameter_space(test_mode, max_sub_combinations, end_date, backtest_days)
        
        # 生成止盈止损比例列表
        stop_profit_values = [round(param_space['stop_profit_ratio']['min'] + i * param_space['stop_profit_ratio']['step'], 3)
                            for i in range(int((param_space['stop_profit_ratio']['max'] - param_space['stop_profit_ratio']['min']) / param_space['stop_profit_ratio']['step']) + 1)]
        
        stop_loss_values = [round(param_space['stop_loss_ratio']['min'] + i * param_space['stop_loss_ratio']['step'], 3)
                          for i in range(int((param_space['stop_loss_ratio']['max'] - param_space['stop_loss_ratio']['min']) / param_space['stop_loss_ratio']['step']) + 1)]
        
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
                                      end_date: str = '2025-12-25', focus_indicators: List[str] = None, 
                                      focus_weight_factor: float = 1.5, backtest_days: int = 90) -> List[Dict[str, Any]]:
        """
        兼容旧接口的参数组合生成方法
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            backtest_days: 回测天数
            
        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        return self.generate_initial_population(test_mode, max_sub_combinations, end_date, backtest_days)
