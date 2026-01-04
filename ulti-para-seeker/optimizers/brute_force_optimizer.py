#!/usr/bin/env python
# coding=utf-8
"""
暴力优化器 - 使用暴力枚举方法进行参数优化
"""

import itertools
import os
import sys
import json
import time
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from .base_optimizer import BaseOptimizer

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
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
    
    def define_parameter_ranges(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                               use_advanced_weights: bool = True, end_date: str = '2025-12-25',
                               focus_indicators: List[str] = None, focus_weight_factor: float = 1.5, initial_capital: int = 60000,
                               backtest_days: int = 90) -> Dict[str, List[Any]]:
        """
        定义参数范围

        Args:
            test_mode: 是否为测试模式（只生成一个简单子权重组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            use_advanced_weights: 是否使用高级权重配置模式
            end_date: 回测终点日期（格式：YYYY-MM-DD）
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            initial_capital: 初始资金
            backtest_days: 回测天数

        Returns:
            Dict[str, List[Any]]: 参数范围字典
        """
        logger.info("定义参数范围...")
        logger.info(f"- 回测天数: {'10天' if test_mode else f'{backtest_days}天'}，终点日期为{end_date}")
        
        # 根据模式调整参数范围
        if test_mode:
            logger.info("[测试模式] 使用最小参数范围")
            stop_profit_ratio = [0.02]  # 仅测试2%止盈
            stop_loss_ratio = [-0.01]  # 仅测试1%止损
            weight_step = 10  # 使用合理步长以生成有效组合
        else:
            logger.info("- 止盈比例: 3%-15%，步长2%")
            logger.info("- 止损比例: -5%--1%，步长1%")
            if use_advanced_weights:
                logger.info("- 权重配置: 总和100，步长10%")
                weight_step = 10
            else:
                logger.info("- 权重配置: 总和100，步长20%")
                weight_step = 20
            
            # 缩小止盈止损范围以减少组合数量（量化专家建议范围）
            stop_profit_ratio = [x/100 for x in range(3, 16, 2)]  # 3%-15%，步长2%
            stop_loss_ratio = [-x/100 for x in range(1, 6, 1)]  # -5%--1%，步长1%
        
        logger.info("- 子权重配置: 每个主指标子权重总和100")
        
        # 选股策略核心指标（权重配置）
        # 移除deepv指标，将其权重设为零以减少组合数量
        core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
        
        # 生成权重配置
        if test_mode:
            logger.info("[测试模式] 直接生成简单权重组合")
            weights_config = [{
                'kdj_j': 30,
                'trend': 20,
                'volume': 15,
                'fundamental': 15,
                'position': 10,
                'risk_reward': 10
            }]
        elif use_advanced_weights:
            # 高级模式：生成基础组合 + 重点指标加权组合
            logger.info("[高级模式] 使用重点指标加权的权重配置")
            
            # 基础权重组合 - 限制主权重范围为5%-95%，避免极端值
            base_weights = self._generate_weights_combinations(core_indicators, 100, weight_step, min_weight=5, max_weight=95)
            
            # 使用传入的重点指标和权重因子
            if focus_indicators is None:
                focus_indicators = ['kdj_j', 'trend']
            
            kdj_trend_weights = self._generate_custom_weights_combinations(
                core_indicators, 100, weight_step, 
                focus_indicators=focus_indicators, 
                focus_weight_factor=focus_weight_factor
            )
            
            # 合并权重组合并去重
            all_weights = base_weights + kdj_trend_weights
            
            # 去重
            seen = set()
            unique_weights = []
            for combo in all_weights:
                key = tuple(sorted(combo.items()))
                if key not in seen:
                    seen.add(key)
                    unique_weights.append(combo)
            
            weights_config = unique_weights
        else:
            # 普通模式：仅生成基础权重组合 - 限制主权重范围为5%-95%，避免极端值
            weights_config = self._generate_weights_combinations(core_indicators, 100, weight_step, min_weight=5, max_weight=95)
        
        return {
            # 回测天数 - 使用传入的参数值
            'backtest_days': [10] if test_mode else [backtest_days],
            
            # 回测终点日期 - 确保所有组合在相同时间段回测
            'end_date': [end_date],
            
            # 止盈比例 - 核心回测参数
            'stop_profit_ratio': stop_profit_ratio,
            
            # 止损比例 - 核心回测参数
            'stop_loss_ratio': stop_loss_ratio,
            
            # 权重配置 (总和必须为100) - 选股策略核心
            'weights_config': weights_config,
            
            # 子权重配置 (每个主指标的子权重总和必须为100) - 选股策略细节
            'sub_weights_config': self._generate_sub_weights_combinations(test_mode, max_combinations=max_sub_combinations, use_advanced_mode=use_advanced_weights)
        }
    
    def _generate_custom_weights_combinations(self, indicators: List[str], total: int, step: int, focus_indicators: List[str] = None, focus_weight_factor: float = 1.5) -> List[Dict[str, int]]:
        """
        生成自定义权重组合，支持重点指标加权
        
        Args:
            indicators: 指标列表
            total: 总权重
            step: 步长
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            
        Returns:
            List[Dict[str, int]]: 自定义权重组合列表
        """
        # 先生成基础组合
        base_combinations = self._generate_weights_combinations(indicators, total, step)
        
        if not focus_indicators or not base_combinations:
            return base_combinations
        
        custom_combinations = []
        focus_indicators = [ind for ind in focus_indicators if ind in indicators]
        
        if not focus_indicators:
            return base_combinations
        
        # 策略1: 基础重点指标加权
        for base_weights in base_combinations:
            # 生成重点指标加权的组合
            focus_weighted = base_weights.copy()
            non_focus_total = sum(weight for ind, weight in focus_weighted.items() if ind not in focus_indicators)
            focus_total = sum(weight for ind, weight in focus_weighted.items() if ind in focus_indicators)
            
            # 如果有重点指标和非重点指标
            if focus_total > 0 and non_focus_total > 0:
                # 调整权重，放大重点指标
                new_non_focus_total = max(1, int(non_focus_total / focus_weight_factor))
                new_focus_total = total - new_non_focus_total
                
                if new_non_focus_total > 0:
                    # 缩放非重点指标
                    for ind in focus_weighted:
                        if ind not in focus_indicators and focus_weighted[ind] > 0:
                            ratio = new_non_focus_total / non_focus_total
                            focus_weighted[ind] = max(1, int(focus_weighted[ind] * ratio))
                    
                    # 重新计算非重点指标总权重
                    non_focus_total = sum(focus_weighted[ind] for ind in focus_weighted if ind not in focus_indicators)
                    
                    # 分配剩余权重给重点指标
                    remaining = total - non_focus_total
                    if remaining > 0:
                        # 按比例分配给重点指标
                        if focus_total > 0:
                            for ind in focus_weighted:
                                if ind in focus_indicators:
                                    ratio = focus_weighted[ind] / focus_total
                                    focus_weighted[ind] = int(remaining * ratio)
                        else:
                            # 如果原重点指标总权重为0，平均分配
                            num_focus = len(focus_indicators)
                            avg = remaining // num_focus
                            remainder = remaining % num_focus
                            for i, ind in enumerate(focus_indicators):
                                focus_weighted[ind] = avg + (1 if i < remainder else 0)
                    
                    # 确保总权重为100
                    current_total = sum(focus_weighted.values())
                    if current_total < total:
                        # 分配剩余权重
                        for ind in focus_indicators:
                            focus_weighted[ind] += 1
                            current_total += 1
                            if current_total == total:
                                break
                    elif current_total > total:
                        # 减少权重
                        for ind in focus_weighted:
                            if ind not in focus_indicators and focus_weighted[ind] > 1:
                                focus_weighted[ind] -= 1
                                current_total -= 1
                                if current_total == total:
                                    break
                    
                    custom_combinations.append(focus_weighted)
        
        # 策略2: 直接为重点指标分配固定比例权重
        fixed_focus_combinations = []
        for base_weights in base_combinations[:10]:  # 仅使用前10个基础组合
            for focus_ratio in [0.6, 0.7, 0.8]:  # 重点指标总权重占比
                if focus_ratio * total < len(focus_indicators) * 5:  # 确保每个重点指标至少5分
                    continue
                
                fixed_weights = {ind: 5 for ind in indicators}  # 基础分5分
                remaining = total - len(indicators) * 5
                
                # 重点指标分配剩余权重的大部分
                focus_remaining = int(remaining * focus_ratio)
                non_focus_remaining = remaining - focus_remaining
                
                # 分配给重点指标
                for i, ind in enumerate(focus_indicators):
                    if i < len(focus_indicators) - 1:
                        fixed_weights[ind] += focus_remaining // len(focus_indicators)
                    else:
                        fixed_weights[ind] += focus_remaining // len(focus_indicators) + focus_remaining % len(focus_indicators)
                
                # 分配给非重点指标
                non_focus_indicators = [ind for ind in indicators if ind not in focus_indicators]
                if non_focus_indicators:
                    for i, ind in enumerate(non_focus_indicators):
                        if i < len(non_focus_indicators) - 1:
                            fixed_weights[ind] += non_focus_remaining // len(non_focus_indicators)
                        else:
                            fixed_weights[ind] += non_focus_remaining // len(non_focus_indicators) + non_focus_remaining % len(non_focus_indicators)
                
                # 确保总权重正确
                current_total = sum(fixed_weights.values())
                if current_total != total:
                    diff = total - current_total
                    for ind in focus_indicators:
                        fixed_weights[ind] += diff
                        break
                
                fixed_focus_combinations.append(fixed_weights)
        
        # 策略3: 组合不同的重点指标
        multi_focus_combinations = []
        if len(focus_indicators) >= 2:
            # 为每个重点指标单独生成极端组合
            for focus_ind in focus_indicators:
                single_focus = {ind: 5 for ind in indicators}
                single_focus[focus_ind] = total - (len(indicators) - 1) * 5
                if single_focus[focus_ind] <= 90:  # 限制最大权重
                    multi_focus_combinations.append(single_focus)
            
            # 为两两重点指标组合生成极端组合
            for i in range(len(focus_indicators) - 1):
                for j in range(i + 1, len(focus_indicators)):
                    pair_focus = {ind: 5 for ind in indicators}
                    pair_total = total - (len(indicators) - 2) * 5
                    pair_focus[focus_indicators[i]] = pair_total // 2
                    pair_focus[focus_indicators[j]] = pair_total - pair_focus[focus_indicators[i]]
                    if pair_focus[focus_indicators[i]] <= 80 and pair_focus[focus_indicators[j]] <= 80:
                        multi_focus_combinations.append(pair_focus)
        
        # 合并所有自定义组合
        all_custom = custom_combinations + fixed_focus_combinations + multi_focus_combinations
        
        # 去重
        seen = set()
        unique_custom = []
        for combo in all_custom:
            key = tuple(sorted(combo.items()))
            if key not in seen:
                seen.add(key)
                unique_custom.append(combo)
        
        # 合并基础组合和自定义组合，并再次去重
        all_combos = unique_custom + base_combinations
        final_seen = set()
        final_combinations = []
        
        for combo in all_combos:
            key = tuple(sorted(combo.items()))
            if key not in final_seen:
                final_seen.add(key)
                final_combinations.append(combo)
        
        return final_combinations
    
    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                       end_date: str = '2025-12-25', focus_indicators: List[str] = None, 
                                       focus_weight_factor: float = 1.5, initial_capital: int = 60000,
                                       backtest_days: int = 90) -> List[Dict[str, Any]]:
        """
        生成所有参数组合

        Args:
            test_mode: 是否为测试模式（使用最小参数范围，仅生成第一个组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            end_date: 回测终点日期（格式：YYYY-MM-DD）
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            initial_capital: 初始资金
            backtest_days: 回测天数
            
        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        param_ranges = self.define_parameter_ranges(test_mode, max_sub_combinations, True, end_date, focus_indicators, focus_weight_factor, initial_capital, backtest_days)
        
        # 优化：参数空间剪枝 - 减少不必要的参数组合
        print(f"开始生成参数组合...")
        
        combinations = []
        current_count = 0
        
        # 生成所有可能的组合
        for backtest_days in param_ranges['backtest_days']:
            for end_date in param_ranges['end_date']:
                # 优化1：提前计算有效止盈止损组合
                valid_pairs = []
                for stop_profit_ratio in param_ranges['stop_profit_ratio']:
                    for stop_loss_ratio in param_ranges['stop_loss_ratio']:
                        if stop_profit_ratio > stop_loss_ratio:
                            valid_pairs.append((stop_profit_ratio, stop_loss_ratio))
                
                # 计算总组合数（用于进度显示）
                total_combinations = len(valid_pairs) * len(param_ranges['weights_config']) * len(param_ranges['sub_weights_config'])
                logger.info(f"预计总组合数: {total_combinations}")
                
                for stop_profit_ratio, stop_loss_ratio in valid_pairs:
                    for weights_config in param_ranges['weights_config']:
                        # 优化2：跳过不合理的权重配置
                        # 避免deepv权重过大
                        if weights_config.get('deepv', 0) > 50:
                            continue
                        
                        for sub_weights_config in param_ranges['sub_weights_config']:
                            # 将deepv权重设置为零
                            weights_config_with_zero_deepv = weights_config.copy()
                            weights_config_with_zero_deepv['deepv'] = 0
                            
                            param_comb = {
                            'backtest_days': backtest_days,
                            'end_date': end_date,
                            'stop_profit_ratio': stop_profit_ratio,
                            'stop_loss_ratio': stop_loss_ratio,
                            'weights_config': weights_config_with_zero_deepv,
                            'sub_weights_config': sub_weights_config,
                            'initial_capital': initial_capital
                        }
                            combinations.append(param_comb)
                            current_count += 1
                            
                            # 每生成1000个组合显示一次进度
                            if current_count % 1000 == 0:
                                logger.info(f"已生成 {current_count}/{total_combinations} 个参数组合")
                            
                            # 测试模式下仅生成第一个组合
                            if test_mode and current_count >= 1:
                                logger.info(f"[测试模式] 仅生成并返回第一个参数组合")
                                return combinations
        
        logger.info(f"总共生成 {len(combinations)} 个参数组合")
        return combinations
    
    # run_backtest method inherited from BaseOptimizer
    
    def optimize(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                end_date: str = '2025-12-25', focus_indicators: List[str] = None, 
                focus_weight_factor: float = 1.5, blueprint_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        生成暴力优化的参数组合

        Args:
            test_mode: 是否为测试模式（使用最小参数范围，仅生成第一个组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            end_date: 回测终点日期（格式：YYYY-MM-DD）
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            blueprint_file: 蓝图文件路径（用于保存参数组合）

        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        # 生成参数组合
        param_combinations = self.generate_parameter_combinations(test_mode, max_sub_combinations, end_date, focus_indicators, focus_weight_factor)
        
        # 如果提供了蓝图文件路径，生成蓝图
        if blueprint_file:
            blueprint_path = self.generate_blueprint(test_mode, max_sub_combinations, end_date, blueprint_file)
            
        return param_combinations
    


# 测试代码
if __name__ == "__main__":
    optimizer = BruteForceOptimizer()
    
    # 测试模式
    print("=== 测试模式 ===")
    results = optimizer.optimize(test_mode=True, max_sub_combinations=1, end_date='2025-12-25')
    print(f"测试结果: {results}")
