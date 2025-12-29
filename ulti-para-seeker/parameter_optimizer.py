#!/usr/bin/env python
# coding=utf-8
"""
参数暴力求解器 - 寻找回测收益率最高的参数组合
"""

import itertools
import multiprocessing
import pandas as pd
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# 项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入现有组件
import os
import sys

# 支持直接运行和作为模块导入两种方式
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 根据运行方式选择导入方式
try:
    from .config_manager import FrontendConfigLoader
    from .strategy import BacktestStrategy
    from .report_generator import ReportGenerator
except ImportError:
    from config_manager import FrontendConfigLoader
    from strategy import BacktestStrategy
    from report_generator import ReportGenerator

class ParameterOptimizer:
    """
    参数优化器 - 用于暴力求解最佳参数组合
    """
    
    def __init__(self):
        """初始化参数优化器"""
        self.initial_capital = 60000  # 固定初始资金
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def define_parameter_ranges(self, test_mode: bool = False, max_sub_combinations: int = 10, use_advanced_weights: bool = True, end_date: str = '2025-12-25') -> Dict[str, List[Any]]:
        """
        定义参数范围

        Args:
            test_mode: 是否为测试模式（只生成一个简单子权重组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            use_advanced_weights: 是否使用高级权重配置模式
            end_date: 回测终点日期（格式：YYYY-MM-DD）

        Returns:
            Dict[str, List[Any]]: 参数范围字典
        """
        print("定义参数范围...")
        print(f"- 回测天数固定为90天，终点日期为{end_date}")
        
        # 根据模式调整参数范围
        if test_mode:
            print("[测试模式] 使用最小参数范围")
            stop_profit_ratio = [0.02]  # 仅测试2%止盈
            stop_loss_ratio = [-0.01]  # 仅测试1%止损
            weight_step = 10  # 使用合理步长以生成有效组合
        else:
            print("- 止盈比例: 3%-15%，步长2%")
            print("- 止损比例: -5%--1%，步长1%")
            if use_advanced_weights:
                print("- 权重配置: 总和100，步长10%")
                weight_step = 10
            else:
                print("- 权重配置: 总和100，步长20%")
                weight_step = 20
            
            # 缩小止盈止损范围以减少组合数量（量化专家建议范围）
            stop_profit_ratio = [x/100 for x in range(3, 16, 2)]  # 3%-15%，步长2%
            stop_loss_ratio = [-x/100 for x in range(1, 6, 1)]  # -5%--1%，步长1%
        
        print("- 子权重配置: 每个主指标子权重总和100")
        
        # 选股策略核心指标（权重配置）
        # 移除deepv指标，将其权重设为零以减少组合数量
        core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
        
        # 生成权重配置
        if test_mode:
            # 测试模式：直接生成一个简单的权重组合
            print("[测试模式] 直接生成简单权重组合")
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
            print("[高级模式] 使用重点指标加权的权重配置")
            
            # 基础权重组合 - 限制主权重范围为5%-95%，避免极端值
            base_weights = self._generate_weights_combinations(core_indicators, 100, weight_step, min_weight=5, max_weight=95)
            
            # 仅保留KDJ J值和趋势作为重点指标的组合（减少组合数）
            kdj_trend_weights = self._generate_custom_weights_combinations(
                core_indicators, 100, weight_step, 
                focus_indicators=['kdj_j', 'trend'], 
                focus_weight_factor=1.5
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
            # 回测天数 - 固定为90天（适合超跌反弹策略）
            'backtest_days': [90],
            
            # 回测终点日期 - 确保所有组合在相同时间段回测
            'end_date': [end_date],
            
            # 止盈比例 - 核心回测参数
            'stop_profit_ratio': stop_profit_ratio,
            
            # 止损比例 - 核心回测参数
            'stop_loss_ratio': stop_loss_ratio,
            
            # 权重配置 (总和必须为100) - 选股策略核心
            'weights_config': weights_config,
            
            # 子权重配置 (每个主指标的子权重总和必须为100) - 选股策略细节
            'sub_weights_config': self._generate_sub_weights_combinations(test_mode, max_sub_combinations, use_advanced_mode=use_advanced_weights)
        }
    
    def _generate_weights_combinations(self, indicators: List[str], total: int, step: int, min_weight: int = 0, max_weight: int = 100) -> List[Dict[str, int]]:
        """
        生成权重组合
        
        Args:
            indicators: 指标列表
            total: 总权重
            step: 步长
            min_weight: 单个指标最小权重
            max_weight: 单个指标最大权重
            
        Returns:
            List[Dict[str, int]]: 权重组合列表，确保总和为100且所有权重为正数
        """
        combinations = []
        n = len(indicators)
        
        if n == 0:
            return []
        
        # 方法1: 笛卡尔积生成 - 基础方法
        ranges = [range(min_weight, max_weight + 1, step) for _ in range(n)]
        
        for weights in itertools.product(*ranges):
            if sum(weights) == total and all(w >= min_weight and w <= max_weight for w in weights):
                combinations.append(dict(zip(indicators, weights)))
        
        # 方法2: 如果笛卡尔积没有生成足够的组合，使用递归生成更灵活的组合
        if len(combinations) < 5 and n > 1:
            print(f"笛卡尔积仅生成 {len(combinations)} 个组合，使用递归生成更多组合")
            
            def recursive_generate(start_idx, remaining, current):
                if start_idx == n - 1:
                    if remaining >= min_weight and remaining <= max_weight:
                        current[indicators[start_idx]] = remaining
                        combinations.append(dict(current))
                    return
                
                min_val = min_weight
                max_val = min(max_weight, remaining - (n - 1 - start_idx) * min_weight)
                
                for weight in range(min_val, max_val + 1, step):
                    current[indicators[start_idx]] = weight
                    recursive_generate(start_idx + 1, remaining - weight, current.copy())
            
            recursive_generate(0, total, {})
        
        # 方法3: 添加一些特殊组合
        if n > 0 and len(combinations) < 10:
            print(f"当前仅生成 {len(combinations)} 个组合，添加特殊组合")
            
            # 添加平均分配组合
            avg_weight = total // n
            remainder = total % n
            avg_weights = [avg_weight] * n
            for i in range(remainder):
                avg_weights[i] += 1
            
            # 验证平均分配组合
            if sum(avg_weights) == total and all(w >= min_weight for w in avg_weights):
                combinations.append(dict(zip(indicators, avg_weights)))
            
            # 添加极端权重组合（一个指标占大部分权重）
            for i in range(min(3, n)):  # 最多为前3个指标生成极端组合
                extreme_weights = [min_weight] * n
                extreme_weights[i] = total - (n - 1) * min_weight
                
                # 验证极端权重组合
                if sum(extreme_weights) == total and extreme_weights[i] <= max_weight and all(w >= min_weight for w in extreme_weights):
                    combinations.append(dict(zip(indicators, extreme_weights)))
            
            # 添加两两指标占主导的组合
            if n >= 2:
                for i in range(n - 1):
                    for j in range(i + 1, n):
                        if len(combinations) >= 15:  # 控制总数
                            break
                        pair_weights = [min_weight] * n
                        pair_weights[i] = (total - (n - 2) * min_weight) // 2
                        pair_weights[j] = total - (n - 2) * min_weight - pair_weights[i]
                        
                        # 验证两两主导组合
                        if sum(pair_weights) == total and pair_weights[i] <= max_weight and pair_weights[j] <= max_weight and all(w >= min_weight for w in pair_weights):
                            combinations.append(dict(zip(indicators, pair_weights)))
        
        # 去重
        seen = set()
        unique_combinations = []
        for combo in combinations:
            # 再次验证组合的有效性
            if sum(combo.values()) == total and all(w >= min_weight and w <= max_weight for w in combo.values()):
                key = tuple(sorted(combo.items()))
                if key not in seen:
                    seen.add(key)
                    unique_combinations.append(combo)
        
        return unique_combinations
    
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
    
    def _generate_sub_weights_combinations(self, test_mode: bool = False, max_combinations: int = 10, use_advanced_mode: bool = True) -> List[Dict[str, Dict[str, int]]]:
        """
        生成子权重组合

        Args:
            test_mode: 是否为测试模式（只生成一个简单组合）
            max_combinations: 最大子权重组合数（仅在非测试模式下生效）
            use_advanced_mode: 是否使用高级模式生成更多组合

        Returns:
            List[Dict[str, Dict[str, int]]]: 子权重组合列表
        """
        print("\n开始生成子权重组合...")
        
        # 定义每个主指标的子指标（与weights_config.py一致）
        sub_indicators = {
            'kdj_j': ['j_0_20', 'j_-10_0', 'j_-20_-10', 'j_-30_-20', 'j_below_-30'],
            'position': ['above_white', 'between_lines', 'below_yellow'],
            'volume': ['big_volume', 'volume_anomaly', 'volume_breathing'],
            'fundamental': ['pe_positive', 'pe_low', 'market_cap', 'volume_threshold'],
            'trend': ['up_trend', 'volume_price_rise', 'volume_contraction']
        }
        
        print(f"主指标及其子指标：")
        for main_ind, subs in sub_indicators.items():
            print(f"- {main_ind}: {', '.join(subs)}")
        
        # 测试模式：只生成一个简单的子权重组合
        if test_mode:
            print("[测试模式] 仅生成一个简单的子权重组合")
            simple_sub_weights = {}
            for main_indicator, subs in sub_indicators.items():
                num_subs = len(subs)
                # 计算每个子指标的权重（相等分配）
                weight_per_sub = 100 // num_subs
                remainder = 100 % num_subs
                
                weights = [weight_per_sub] * num_subs
                for i in range(remainder):
                    weights[i] += 1
                
                simple_sub_weights[main_indicator] = {'sub_weights': dict(zip(subs, weights))}
            
            combinations = [simple_sub_weights]
        else:
            # 正式模式：生成可控数量的子权重组合
            print(f"[正式模式] 生成最多 {max_combinations} 个子权重组合")
            
            # 为每个主指标生成子权重组合（使用合理步长确保能生成有效组合）
            sub_weights_combinations = {}
            for main_indicator, subs in sub_indicators.items():
                # 根据子指标数量选择合适的步长，确保能生成总和为100的组合
                num_subs = len(subs)
                if use_advanced_mode:
                    # 高级模式：使用更小的步长生成更多组合
                    if num_subs == 3:
                        step = 5   # 3个子指标，使用5步长，更细粒度
                    elif num_subs == 4:
                        step = 5   # 4个子指标，使用5步长
                    else:  # num_subs == 5
                        step = 5   # 5个子指标，使用5步长
                else:
                    # 普通模式：使用较大步长
                    if num_subs == 3:
                        step = 10  # 3个子指标，使用10步长
                    elif num_subs == 4:
                        step = 10  # 4个子指标，使用10步长
                    else:  # num_subs == 5
                        step = 10  # 5个子指标，使用10步长
                
                # 生成子权重组合，限制子权重范围为5%-90%，避免极端值
                sub_weights = self._generate_weights_combinations(subs, 100, step, min_weight=5, max_weight=90)
                
                # 提前筛选有效的子权重组合 - 确保子权重范围为5%-90%
                valid_sub_weights = []
                for sw in sub_weights:
                    if sum(sw.values()) == 100 and all(5 <= w <= 90 for w in sw.values()):
                        valid_sub_weights.append(sw)
                
                sub_weights_combinations[main_indicator] = valid_sub_weights
                print(f"为{main_indicator}生成了 {len(valid_sub_weights)} 个有效子权重组合")
            
            # 生成所有主指标的子权重组合的笛卡尔积
            main_indicators = list(sub_weights_combinations.keys())
            sub_weights_lists = [sub_weights_combinations[ind] for ind in main_indicators]
            
            # 计算总笛卡尔积数量
            total_cartesian = 1
            for sub_list in sub_weights_lists:
                total_cartesian *= len(sub_list)
            
            print(f"预计总笛卡尔积数量: {total_cartesian}")
            
            # 生成笛卡尔积，但限制数量
            combinations = []
            
            # 高级模式：使用多种策略生成组合
            if use_advanced_mode and total_cartesian > max_combinations:
                import random
                print("[高级模式] 使用多种策略生成子权重组合")
                
                # 策略1: 分层随机采样（确保每个主指标都有代表性）
                print("- 使用分层随机采样策略")
                stratified_samples = []
                
                # 为每个主指标选择固定数量的子权重组合
                samples_per_indicator = 3  # 每个主指标至少采样3个组合
                
                # 为每个主指标创建子权重组合池
                indicator_pools = {}
                for main_ind, sub_weights_list in sub_weights_combinations.items():
                    # 为每个主指标随机选择samples_per_indicator个组合
                    if len(sub_weights_list) > samples_per_indicator:
                        indicator_pools[main_ind] = random.sample(sub_weights_list, samples_per_indicator)
                    else:
                        indicator_pools[main_ind] = sub_weights_list.copy()
                
                # 生成这些组合的笛卡尔积
                stratified_cartesian = list(itertools.product(*[indicator_pools[ind] for ind in main_indicators]))
                
                # 如果生成的组合过多，再次随机采样
                if len(stratified_cartesian) > max_combinations:
                    stratified_samples = random.sample(stratified_cartesian, max_combinations)
                else:
                    stratified_samples = stratified_cartesian
                
                # 将采样结果转换为标准格式
                stratified_combinations = []
                for combo in stratified_samples:
                    sub_weights_config = {}
                    for i, main_indicator in enumerate(main_indicators):
                        sub_weights_config[main_indicator] = {'sub_weights': combo[i]}
                    stratified_combinations.append(sub_weights_config)
                
                combinations.extend(stratified_combinations)
                
                # 策略2: 变异策略（基于已生成的组合进行变异）
                if len(combinations) < max_combinations and len(combinations) > 0:
                    print("- 使用变异策略生成新组合")
                    mutation_count = min(5, max_combinations - len(combinations))
                    
                    for _ in range(mutation_count):
                        # 随机选择一个基础组合
                        base_combo = random.choice(combinations)
                        mutated_combo = base_combo.copy()
                        
                        # 随机选择一个主指标进行变异
                        mutate_indicator = random.choice(main_indicators)
                        mutate_subs = sub_indicators[mutate_indicator]
                        num_subs = len(mutate_subs)
                        
                        # 获取当前子权重
                        current_weights = base_combo[mutate_indicator]['sub_weights']
                        
                        # 随机选择两个子指标进行权重交换或调整
                        if num_subs >= 2:
                            i, j = random.sample(range(num_subs), 2)
                            sub_i = mutate_subs[i]
                            sub_j = mutate_subs[j]
                            
                            # 随机调整权重（±5%范围内）
                            adjust_amount = random.randint(1, 10)
                            if random.random() > 0.5:
                                # 增加i，减少j
                                if current_weights[sub_i] + adjust_amount <= 90 and current_weights[sub_j] - adjust_amount >= 5:
                                    current_weights[sub_i] += adjust_amount
                                    current_weights[sub_j] -= adjust_amount
                            else:
                                # 增加j，减少i
                                if current_weights[sub_j] + adjust_amount <= 90 and current_weights[sub_i] - adjust_amount >= 5:
                                    current_weights[sub_j] += adjust_amount
                                    current_weights[sub_i] -= adjust_amount
                        
                        # 验证变异后的组合是否有效
                        if sum(current_weights.values()) == 100 and all(w > 0 for w in current_weights.values()):
                            # 更新变异后的组合
                            mutated_combo[mutate_indicator]['sub_weights'] = current_weights.copy()
                            combinations.append(mutated_combo)
                
                # 策略3: 增强的极端组合生成
                if len(combinations) < max_combinations:
                    print("- 使用增强的极端组合策略")
                    
                    # 为每个主指标生成多种极端组合
                    for main_indicator in main_indicators:
                        if len(combinations) >= max_combinations:
                            break
                        
                        subs = sub_indicators[main_indicator]
                        num_subs = len(subs)
                        
                        # 为每个子指标生成多种极端权重
                        for i in range(num_subs):
                            if len(combinations) >= max_combinations:
                                break
                            
                            # 生成不同程度的极端组合
                            for extreme_ratio in [0.7, 0.75, 0.8]:  # 主要子指标权重比例
                                if len(combinations) >= max_combinations:
                                    break
                                    
                                extreme_weights = {}
                                for main_ind, subs_list in sub_indicators.items():
                                    if main_ind == main_indicator:
                                        # 当前主指标设置极端权重
                                        sub_weights = [int(100 * (1 - extreme_ratio) / (num_subs - 1))] * len(subs_list)
                                        remaining = 100 - sum(sub_weights)
                                        sub_weights[i] = remaining  # 主要子指标占大部分权重
                                        
                                        # 确保所有子指标至少1分
                                        for j in range(len(sub_weights)):
                                            if sub_weights[j] < 1:
                                                sub_weights[j] = 1
                                                sub_weights[i] -= 1
                                        
                                        extreme_weights[main_ind] = {'sub_weights': dict(zip(subs_list, sub_weights))}
                                    else:
                                        # 其他主指标随机选择一个组合
                                        random_sub_weight = random.choice(sub_weights_combinations[main_ind])
                                        extreme_weights[main_ind] = {'sub_weights': random_sub_weight}
                                
                                # 验证生成的极端组合是否有效
                                valid_extreme = True
                                for main_ind, sub_config in extreme_weights.items():
                                    if sum(sub_config['sub_weights'].values()) != 100 or any(w <= 0 for w in sub_config['sub_weights'].values()):
                                        valid_extreme = False
                                        break
                                
                                if valid_extreme:
                                    combinations.append(extreme_weights)
            else:
                # 普通模式：遍历笛卡尔积
                print("[普通模式] 遍历笛卡尔积生成子权重组合")
                current = 0
                for combination in itertools.product(*sub_weights_lists):
                    sub_weights_config = {}
                    for i, main_indicator in enumerate(main_indicators):
                        sub_weights_config[main_indicator] = {'sub_weights': combination[i]}
                    combinations.append(sub_weights_config)
                    
                    current += 1
                    if current >= max_combinations:
                        print(f"已达到最大组合数限制: {max_combinations}")
                        break
            
            # 去重
            seen = set()
            unique_combinations = []
            for combo in combinations:
                key = tuple(sorted((k, tuple(sorted(v['sub_weights'].items()))) for k, v in combo.items()))
                if key not in seen:
                    seen.add(key)
                    unique_combinations.append(combo)
            
            combinations = unique_combinations[:max_combinations]
        
        print(f"子权重组合生成完成，共 {len(combinations)} 个组合")
        return combinations
    
    def _validate_parameter_combination(self, params: Dict[str, Any]) -> bool:
        """
        验证参数组合的有效性

        Args:
            params: 参数组合字典

        Returns:
            bool: 参数组合是否有效
        """
        try:
            # 1. 验证止盈止损逻辑
            stop_profit = params.get('stop_profit_ratio', 0)
            stop_loss = params.get('stop_loss_ratio', 0)
            
            # 止盈必须大于止损
            if stop_profit <= stop_loss:
                print(f"✗ 无效组合：止盈({stop_profit:.2%}) 必须大于止损({stop_loss:.2%})")
                return False
            
            # 止盈和止损必须在合理范围内
            if not (0 < stop_profit <= 1):
                print(f"✗ 无效组合：止盈({stop_profit:.2%}) 必须在0%-100%之间")
                return False
            
            if not (-1 <= stop_loss < 0):
                print(f"✗ 无效组合：止损({stop_loss:.2%}) 必须在-100%-0%之间")
                return False
            
            # 2. 验证权重配置
            weights = params.get('weights_config', {})
            total_weight = sum(weights.values())
            
            # 权重总和必须为100
            # 核心指标权重必须为正数，deepv权重可以为零
            core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
            invalid_weights = [ind for ind in core_indicators if weights.get(ind, 0) <= 0]
            
            if total_weight != 100:
                print(f"✗ 无效组合：权重总和({total_weight}) 必须等于100")
                return False
            elif invalid_weights:
                print(f"✗ 无效组合：核心指标 {', '.join(invalid_weights)} 的权重必须为正数")
                return False
            
            # 3. 验证子权重配置
            sub_weights = params.get('sub_weights_config', {})
            for main_indicator, sub_config in sub_weights.items():
                if 'sub_weights' not in sub_config:
                    print(f"✗ 无效组合：主指标 {main_indicator} 缺少子权重配置")
                    return False
                
                sub_weights_dict = sub_config['sub_weights']
                
                # 子权重总和必须为100且所有子权重为正数
                if sum(sub_weights_dict.values()) != 100 or any(w <= 0 for w in sub_weights_dict.values()):
                    print(f"✗ 无效组合：{main_indicator} 子权重总和({sum(sub_weights_dict.values())}) 必须等于100且所有子权重为正数")
                    return False
            
            return True
            
        except Exception as e:
            print(f"✗ 验证参数组合失败: {e}")
            return False
    
    def _filter_parameter_combinations(self, combinations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        筛选有效的参数组合

        Args:
            combinations: 参数组合列表

        Returns:
            List[Dict[str, Any]]: 有效参数组合列表
        """
        print(f"\n开始筛选参数组合，共 {len(combinations)} 个组合")
        
        valid_combinations = []
        for i, params in enumerate(combinations):
            if i % 100 == 0 and i > 0:
                print(f"已验证 {i} 个组合，有效 {len(valid_combinations)} 个")
            
            if self._validate_parameter_combination(params):
                valid_combinations.append(params)
        
        print(f"筛选完成：{len(valid_combinations)} 个有效组合 (总 {len(combinations)} 个)")
        return valid_combinations
    
    def generate_blueprint(self, test_mode: bool = False, max_sub_combinations: int = 10, blueprint_file: str = "parameter_blueprint.json") -> str:
        """
        生成参数组合蓝图文件，存储所有可能的参数组合
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            blueprint_file: 蓝图文件路径
            
        Returns:
            str: 蓝图文件路径
        """
        print("\n=== 生成参数组合蓝图 ===")
        
        # 生成所有参数组合
        param_combinations = self.generate_parameter_combinations(test_mode, max_sub_combinations)
        
        # 创建蓝图数据结构
        blueprint = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "total_combinations": len(param_combinations),
            "test_mode": test_mode,
            "max_sub_combinations": max_sub_combinations,
            "combinations": []
        }
        
        # 为每个组合分配唯一ID并添加到蓝图
        for i, param in enumerate(param_combinations):
            combination = {
                "id": i + 1,
                "params": param,
                "status": "pending",  # pending, running, completed, failed
                "result": None
            }
            blueprint["combinations"].append(combination)
        
        # 保存蓝图文件
        blueprint_path = os.path.join(current_dir, blueprint_file)
        with open(blueprint_path, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 参数组合蓝图已生成: {blueprint_path}")
        print(f"   总组合数: {len(param_combinations)}")
        print(f"   蓝图文件大小: {os.path.getsize(blueprint_path) / 1024:.2f} KB")
        
        return blueprint_path
    
    def load_blueprint(self, blueprint_file: str = "parameter_blueprint.json") -> Dict[str, Any]:
        """
        加载参数组合蓝图文件
        
        Args:
            blueprint_file: 蓝图文件路径
            
        Returns:
            Dict[str, Any]: 蓝图数据
        """
        blueprint_path = os.path.join(current_dir, blueprint_file)
        
        if not os.path.exists(blueprint_path):
            raise FileNotFoundError(f"蓝图文件不存在: {blueprint_path}")
        
        with open(blueprint_path, 'r', encoding='utf-8') as f:
            blueprint = json.load(f)
        
        print(f"✅ 蓝图文件已加载: {blueprint_path}")
        print(f"   版本: {blueprint.get('version')}")
        print(f"   总组合数: {blueprint.get('total_combinations')}")
        print(f"   生成时间: {blueprint.get('generated_at')}")
        
        # 统计各状态的组合数
        status_counts = {}
        for combo in blueprint['combinations']:
            status = combo['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"   状态统计: {status_counts}")
        
        return blueprint
    
    def get_next_combination(self, blueprint: Dict[str, Any]) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """
        获取下一个待处理的参数组合
        
        Args:
            blueprint: 蓝图数据
            
        Returns:
            Tuple[Optional[int], Optional[Dict[str, Any]]]: (组合ID, 参数组合)，如果没有待处理的组合则返回(None, None)
        """
        for combo in blueprint['combinations']:
            if combo['status'] == 'pending':
                return combo['id'], combo['params']
        return None, None
    
    def update_combination_status(self, blueprint: Dict[str, Any], combo_id: int, status: str, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        更新参数组合的状态和结果
        
        Args:
            blueprint: 蓝图数据
            combo_id: 组合ID
            status: 新状态 (pending, running, completed, failed)
            result: 回测结果（可选）
            
        Returns:
            Dict[str, Any]: 更新后的蓝图数据
        """
        for combo in blueprint['combinations']:
            if combo['id'] == combo_id:
                combo['status'] = status
                combo['result'] = result
                if result is not None:
                    combo['completed_at'] = datetime.now().isoformat()
                break
        return blueprint
    
    def save_blueprint(self, blueprint: Dict[str, Any], blueprint_file: str = "parameter_blueprint.json") -> str:
        """
        保存蓝图文件
        
        Args:
            blueprint: 蓝图数据
            blueprint_file: 蓝图文件路径
            
        Returns:
            str: 保存后的蓝图文件路径
        """
        blueprint_path = os.path.join(current_dir, blueprint_file)
        
        # 更新最后修改时间
        blueprint['last_modified'] = datetime.now().isoformat()
        
        with open(blueprint_path, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, ensure_ascii=False, indent=2)
        
        return blueprint_path
    
    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10, end_date: str = '2025-12-25') -> List[Dict[str, Any]]:
        """
        生成所有参数组合

        Args:
            test_mode: 是否为测试模式（使用最小参数范围，仅生成第一个组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            end_date: 回测终点日期（格式：YYYY-MM-DD）
            
        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        param_ranges = self.define_parameter_ranges(test_mode, max_sub_combinations, end_date=end_date)
        
        # 计算总组合数（用于进度显示）
        total_combinations = (len(param_ranges['backtest_days']) * 
                            len(param_ranges['end_date']) * 
                            len(param_ranges['stop_profit_ratio']) * 
                            len(param_ranges['stop_loss_ratio']) * 
                            len(param_ranges['weights_config']) * 
                            len(param_ranges['sub_weights_config']))
        
        print(f"开始生成参数组合...")
        print(f"预计总组合数: {total_combinations}")
        
        combinations = []
        current_count = 0
        
        # 生成所有可能的组合
        for backtest_days in param_ranges['backtest_days']:
            for end_date in param_ranges['end_date']:
                for stop_profit_ratio in param_ranges['stop_profit_ratio']:
                    for stop_loss_ratio in param_ranges['stop_loss_ratio']:
                        for weights_config in param_ranges['weights_config']:
                            for sub_weights_config in param_ranges['sub_weights_config']:
                                # 确保止盈大于止损
                                if stop_profit_ratio > stop_loss_ratio:
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
                                        'initial_capital': self.initial_capital
                                    }
                                    combinations.append(param_comb)
                                    current_count += 1
                                    
                                    # 每生成1000个组合显示一次进度
                                    if current_count % 1000 == 0:
                                        print(f"已生成 {current_count}/{total_combinations} 个参数组合")
                                    
                                    # 测试模式下仅生成第一个组合
                                    if test_mode and current_count >= 1:
                                        print(f"[测试模式] 仅生成并返回第一个参数组合")
                                        return combinations
        
        print(f"总共生成 {len(combinations)} 个参数组合")
        return combinations
    
    def run_backtest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个参数组合的回测

        Args:
            params: 参数组合
            
        Returns:
            Dict[str, Any]: 回测结果
        """
        temp_config_file = None  # 初始化变量，避免作用域错误
        try:
            import sys
            import os
            import json
            import tempfile
            from datetime import datetime, timedelta
            
            # 设置项目根目录到sys.path
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # 创建策略ID
            strategy_id = f"optimization_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # 计算回测区间
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d')
            start_date = end_date - timedelta(days=params['backtest_days'])
            
            # 准备符合标准回测要求的配置结构
            frontend_config = {
                'backtest': {
                    'initial_capital': params['initial_capital'],
                    'backtest_days': params['backtest_days'],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'max_stocks_to_backtest': 1,
                    'strategy_id': strategy_id,
                    'commission_ratio': 0.0003
                },
                'strategy': {
                    'stop_profit_ratio': params['stop_profit_ratio'],
                    'stop_loss_ratio': params['stop_loss_ratio'],
                    'weights_config': params['weights_config'],
                    'sub_weights_config': params['sub_weights_config'],
                    'strategy_type': '参数优化策略'
                },
                # 添加默认的选股结果（至少包含一个股票）
                'selected_stocks': [
                    {
                        'symbol': '600000.SH',
                        'sec_name': '浦发银行',
                        'industry': '银行',
                        'market_value': 300000000000,
                        'score': 100
                    }
                ]
            }
            
            # 将配置文件保存到求解器目录的config文件夹
            config_file_path = os.path.join(current_dir, 'config', 'current_backtest_config.json')
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(frontend_config, f, ensure_ascii=False, indent=2)
            print(f"✅ 参数配置已更新: {config_file_path}")
            temp_config_file = config_file_path
            
            # 保存原始的sys.argv，避免与gm.api.run()的命令行参数解析冲突
            original_argv = sys.argv.copy()
            
            # 调试：打印当前工作目录和文件路径
            print(f"调试: 当前工作目录={os.getcwd()}")
            print(f"调试: 项目根目录={project_root}")
            
            try:
                # 使用标准回测函数运行回测
                print("🔄 开始执行回测...")
                import backtest_runner
                backtest_runner.run_backtest(config_path=temp_config_file)
                print("✅ 回测执行完成")
            except ImportError as e:
                print(f"⚠️ 导入backtest_runner失败: {e}")
                try:
                    from .backtest_runner import run_backtest
                    run_backtest(config_path=temp_config_file)
                    print("✅ 回测执行完成（本地导入）")
                except Exception as e2:
                    print(f"❌ 本地导入回测失败: {e2}")
                    raise
            except Exception as e:
                print(f"❌ 回测执行失败: {e}")
                raise
            finally:
                # 恢复原始的sys.argv
                sys.argv = original_argv
            
            # 从文件中读取回测结果
            report_file = os.path.join(current_dir, 'backtest_report.json')  # 使用绝对路径确保正确读取
            report = {}
            
            if os.path.exists(report_file):
                try:
                    print(f"调试: parameter_optimizer - 尝试读取报告文件: {report_file}")
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    print(f"调试: parameter_optimizer - 成功读取报告文件，内容: {json.dumps(report, ensure_ascii=False, indent=2)}")
                    # 删除结果文件，避免影响下一次回测
                    os.unlink(report_file)
                    print(f"调试: parameter_optimizer - 已删除临时报告文件: {report_file}")
                except Exception as e:
                    print(f"调试: parameter_optimizer - 读取报告文件失败: {e}")
                    import traceback
                    traceback.print_exc()
                    report = {}
            else:
                print(f"调试: parameter_optimizer - 报告文件不存在: {report_file}")
            
            # 从报告中提取需要的结果
            performance_metrics = report.get('performance_metrics', {})
            trade_statistics = report.get('trade_statistics', {})
            
            # 返回结果
            return {
            **(params or {}),
            'total_return': performance_metrics.get('total_return', 0.0),
            'annual_return': performance_metrics.get('annual_return', 0.0),
            'max_drawdown': performance_metrics.get('max_drawdown', 0.0),
            'sharpe_ratio': performance_metrics.get('sharpe_ratio', 0.0),
            'trades_count': trade_statistics.get('total_trades', 0),
            'win_rate': trade_statistics.get('win_rate', 0.0)
        }
            
        except Exception as e:
            print(f"回测失败: {e}")
            return {
                **(params or {}),
                'total_return': -100.0,  # 失败时返回极低收益率
                'annual_return': -100.0,
                'max_drawdown': -100.0,
                'sharpe_ratio': 0.0,
                'trades_count': 0,
                'win_rate': 0.0
            }
        finally:
            # 不再删除配置文件，因为它是持久化的参数配置文件
            if temp_config_file:
                print(f"✅ 参数组合配置已保留: {temp_config_file}")
    
    def run_parallel_optimization(self, param_combinations: List[Dict[str, Any]], num_workers: int = 4, batch_size: int = 50, save_interval: int = 1, blueprint: Optional[Dict[str, Any]] = None, blueprint_file: str = "parameter_blueprint.json") -> List[Dict[str, Any]]:
        """
        排队运行参数优化（支持每10个组合更新一次Excel结果和断点续传）

        Args:
            param_combinations: 参数组合列表
            num_workers: 并行工作进程数（已废弃，保留参数兼容性）
            batch_size: 每批处理的参数组合数（已废弃，保留参数兼容性）
            save_interval: 保存中间结果的批次间隔（已废弃，保留参数兼容性）
            blueprint: 参数组合蓝图数据（用于断点续传）
            blueprint_file: 蓝图文件路径

        Returns:
            List[Dict[str, Any]]: 按收益率排序的结果列表
        """
        total_combinations = len(param_combinations)
        self.start_time = datetime.now()
        all_results = []
        
        print(f"\n=== 排队处理模式 ===")
        print(f"开始排队优化，一个组合一个组合处理")
        print(f"总参数组合数: {total_combinations}")
        print(f"每个组合更新一次Excel结果")
        print(f"支持断点续传: {'是' if blueprint else '否'}")
        print("=" * 50)
        
        # 单个组合逐个处理
        for i, param in enumerate(param_combinations):
            try:
                # 查找当前参数组合在蓝图中的ID
                combo_id = None
                if blueprint:
                    for combo in blueprint['combinations']:
                        if combo['params'] == param:
                            combo_id = combo['id']
                            # 更新状态为running
                            combo['status'] = 'running'
                            combo['started_at'] = datetime.now().isoformat()
                            # 保存更新后的蓝图
                            self.save_blueprint(blueprint, blueprint_file)
                            break
                
                # 处理当前组合
                start_time = datetime.now()
                result = self.run_backtest(param)
                all_results.append(result)
                duration = datetime.now() - start_time
                
                # 计算进度
                processed = i + 1
                progress = (processed / total_combinations) * 100
                
                print(f"\n✅ 组合 {processed}/{total_combinations} 处理完成")
                print(f"   耗时: {duration.total_seconds():.2f} 秒")
                print(f"   累计处理: {processed}/{total_combinations} ({progress:.1f}%)")
                print(f"   已处理组合数: {len(all_results)}")
                print(f"   当前组合总收益率: {result['total_return']:.2f}%")
                
                # 更新蓝图中的组合状态为completed
                if blueprint and combo_id is not None:
                    blueprint = self.update_combination_status(blueprint, combo_id, 'completed', result)
                    self.save_blueprint(blueprint, blueprint_file)
                    print(f"   蓝图已更新: 组合 {combo_id} 状态变更为 'completed'")
                
                # 每1个组合更新一次Excel结果
                if processed % 1 == 0 or processed == total_combinations:
                    self._update_excel_results(all_results)
                
                # 计算剩余时间估计
                if processed > 0:
                    avg_time = (datetime.now() - self.start_time).total_seconds() / processed
                    remaining_time = avg_time * (total_combinations - processed)
                    print(f"   预计剩余时间: {remaining_time:.2f} 秒")
                    
            except Exception as e:
                print(f"\n❌ 组合 {i + 1}/{total_combinations} 处理失败: {e}")
                print("   继续处理下一个组合...")
                
                # 更新蓝图中的组合状态为failed
                if blueprint:
                    combo_id = None
                    for combo in blueprint['combinations']:
                        if combo['params'] == param:
                            combo_id = combo['id']
                            break
                    if combo_id is not None:
                        blueprint = self.update_combination_status(blueprint, combo_id, 'failed')
                        self.save_blueprint(blueprint, blueprint_file)
                        print(f"   蓝图已更新: 组合 {combo_id} 状态变更为 'failed'")
                
                # 添加失败结果
                all_results.append({
                    **param,
                    'total_return': -100.0,
                    'annual_return': -100.0,
                    'max_drawdown': -100.0,
                    'sharpe_ratio': 0.0,
                    'trades_count': 0,
                    'win_rate': 0.0
                })
        
        self.end_time = datetime.now()
        total_duration = self.end_time - self.start_time
        
        # 按总收益率降序排序
        if all_results:
            all_results.sort(key=lambda x: x['total_return'], reverse=True)
            print(f"\n{'='*50}")
            print(f"优化完成！总耗时: {total_duration.total_seconds():.2f} 秒")
            print(f"总共处理 {len(all_results)} 个参数组合")
        
        return all_results
    
    def _update_excel_results(self, results: List[Dict[str, Any]], fixed_file_name: str = "parameter_optimization_results.xlsx"):
        """
        更新固定Excel文件的结果（支持从已有文件读取并追加）
        
        Args:
            results: 回测结果列表
            fixed_file_name: 固定的Excel文件名
        """
        print(f"\n[Excel导出] 开始更新Excel结果文件: {fixed_file_name}")
        print(f"[Excel导出] 待处理结果数量: {len(results)}")
        
        # 获取结果文件的完整路径
        file_path = os.path.join(current_dir, fixed_file_name)
        print(f"[Excel导出] 文件保存路径: {file_path}")
        
        # 转换新结果为DataFrame
        new_df_list = []
        
        for i, result in enumerate(results):
            # 提取参数
            row = {
                '序号': i + 1,
                '回测天数': result['backtest_days'],
                '止盈比例(%)': result['stop_profit_ratio'] * 100,
                '止损比例(%)': result['stop_loss_ratio'] * 100,
                '总收益率(%)': result['total_return'],
                '年化收益率(%)': result['annual_return'],
                '最大回撤(%)': result['max_drawdown'],
                '夏普比率': result['sharpe_ratio'],
                '胜率(%)': result['win_rate'],
                '交易次数': result['trades_count']
            }
            
            # 添加权重配置
            for indicator, weight in result['weights_config'].items():
                row[f'权重_{indicator}'] = weight
            
            # 添加子权重配置
            for main_indicator, sub_config in result['sub_weights_config'].items():
                for sub_indicator, weight in sub_config['sub_weights'].items():
                    row[f'子权重_{main_indicator}_{sub_indicator}'] = weight
            
            new_df_list.append(row)
        
        new_df = pd.DataFrame(new_df_list)
        print(f"[Excel导出] 新结果DataFrame创建完成，包含 {len(new_df)} 条记录")
        
        # 检查文件是否存在
        if os.path.exists(file_path):
            try:
                # 读取现有内容
                existing_df = pd.read_excel(file_path, engine='openpyxl')
                print(f"[Excel导出] 找到已有Excel文件，包含 {len(existing_df)} 条记录")
                
                # 合并新结果和现有结果
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                print(f"[Excel导出] 合并新旧结果，共 {len(combined_df)} 条记录")
                
                # 按总收益率降序排序
                combined_df = combined_df.sort_values(by='总收益率(%)', ascending=False)
                print(f"[Excel导出] 按总收益率降序排序完成")
                
                # 重新分配序号
                combined_df['序号'] = range(1, len(combined_df) + 1)
                print(f"[Excel导出] 重新分配序号完成")
                
                # 导出合并后的结果
                combined_df.to_excel(file_path, index=False, engine='openpyxl')
                print(f"[Excel导出] ✅ Excel文件已更新，当前共 {len(combined_df)} 条记录")
                
            except Exception as e:
                print(f"[Excel导出] ❌ 读取现有Excel文件失败: {e}")
                print("[Excel导出]   将创建新的Excel文件")
                # 导出新结果
                new_df.to_excel(file_path, index=False, engine='openpyxl')
                print(f"[Excel导出] ✅ 新Excel文件已创建，包含 {len(new_df)} 条记录")
        else:
            # 导出新结果
            new_df.to_excel(file_path, index=False, engine='openpyxl')
            print(f"[Excel导出] ✅ 新Excel文件已创建，包含 {len(new_df)} 条记录")
    
    def export_to_excel(self, results: List[Dict[str, Any]], file_path: str = "parameter_optimization_results.xlsx"):
        """
        导出结果到Excel
        
        Args:
            results: 回测结果列表
            file_path: Excel文件路径（默认使用固定文件名）
        """
        # 转换结果为DataFrame
        df_list = []
        
        for i, result in enumerate(results):
            # 提取参数
            row = {
                '序号': i + 1,
                '回测天数': result['backtest_days'],
                '止盈比例(%)': result['stop_profit_ratio'] * 100,
                '止损比例(%)': result['stop_loss_ratio'] * 100,
                '总收益率(%)': result['total_return'],
                '年化收益率(%)': result['annual_return'],
                '最大回撤(%)': result['max_drawdown'],
                '夏普比率': result['sharpe_ratio'],
                '胜率(%)': result['win_rate'],
                '交易次数': result['trades_count']
            }
            
            # 添加权重配置
            for indicator, weight in result['weights_config'].items():
                row[f'权重_{indicator}'] = weight
            
            # 添加子权重配置
            for main_indicator, sub_config in result['sub_weights_config'].items():
                for sub_indicator, weight in sub_config['sub_weights'].items():
                    row[f'子权重_{main_indicator}_{sub_indicator}'] = weight
            
            df_list.append(row)
        
        df = pd.DataFrame(df_list)
        
        # 导出到Excel
        df.to_excel(file_path, index=False, engine='openpyxl')
        print(f"结果已导出到 {file_path}")

def main():
    """主函数"""
    print("=" * 60)
    print("参数暴力求解器")
    print("=" * 60)
    
    import argparse
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='参数暴力求解器')
    parser.add_argument('--max-combinations', type=int, default=1000, help='最大参数组合数（用于测试，0表示不限制）')
    parser.add_argument('--num-workers', type=int, default=4, help='并行工作进程数')
    parser.add_argument('--batch-size', type=int, default=50, help='每批处理的参数组合数')
    parser.add_argument('--save-interval', type=int, default=1, help='保存中间结果的批次间隔')
    parser.add_argument('--weight-step', type=int, default=20, help='权重配置的步长（百分比）')
    parser.add_argument('--sub-weight-step', type=int, default=20, help='子权重配置的步长（百分比）')
    parser.add_argument('--test-first', action='store_true', help='只测试第一个参数组合的完整流程')
    parser.add_argument('--blueprint', type=str, default="parameter_blueprint.json", help='参数组合蓝图文件名')
    parser.add_argument('--generate-only', action='store_true', help='仅生成蓝图文件，不执行回测')
    
    args = parser.parse_args()
    
    # 创建优化器实例
    optimizer = ParameterOptimizer()
    
    # 检查蓝图文件是否存在
    blueprint_path = os.path.join(current_dir, args.blueprint)
    blueprint_exists = os.path.exists(blueprint_path)
    
    if blueprint_exists:
        print(f"\n蓝图文件已存在: {args.blueprint}")
        print("将从上次的进度继续优化")
        # 加载蓝图文件
        blueprint = optimizer.load_blueprint(args.blueprint)
    else:
        print(f"\n蓝图文件不存在，将生成新的蓝图文件: {args.blueprint}")
        # 生成蓝图文件
        blueprint_path = optimizer.generate_blueprint(args.test_first, blueprint_file=args.blueprint)
        # 加载生成的蓝图文件
        blueprint = optimizer.load_blueprint(args.blueprint)
    
    # 如果仅生成蓝图文件，不执行回测
    if args.generate_only:
        print("\n仅生成蓝图文件模式，已完成。")
        print(f"蓝图文件路径: {blueprint_path}")
        print(f"总组合数: {blueprint['total_combinations']}")
        print("使用 --blueprint 参数指定此文件可继续优化。")
        print("=" * 60)
        return
    
    # 并行运行优化（支持从蓝图文件获取待处理组合和断点续传）
    print("\n正在运行优化（支持断点续传）...")
    
    # 获取待处理的参数组合
    param_combinations = []
    for combo in blueprint['combinations']:
        if combo['status'] == 'pending':
            param_combinations.append(combo['params'])
    
    print(f"待处理的参数组合数: {len(param_combinations)}")
    
    # 限制组合数量（可选，用于测试）
    if args.max_combinations > 0 and len(param_combinations) > args.max_combinations:
        print(f"组合数量过多，仅测试前 {args.max_combinations} 个组合")
        param_combinations = param_combinations[:args.max_combinations]
    
    if not param_combinations:
        print("\n所有参数组合都已处理完成！")
        print("=" * 60)
        return
    
    # 运行优化（传递蓝图信息以支持断点续传）
    results = optimizer.run_parallel_optimization(
        param_combinations,
        num_workers=args.num_workers,
        batch_size=args.batch_size,
        save_interval=args.save_interval,
        blueprint=blueprint,
        blueprint_file=args.blueprint
    )
    
    # 导出最终结果到固定Excel文件
    output_file = "parameter_optimization_results.xlsx"
    optimizer.export_to_excel(results, output_file)
    
    print("=" * 60)
    print("优化完成！")
    if results:
        print(f"最佳组合总收益率: {results[0]['total_return']:.2f}%")
        print(f"最佳组合年化收益率: {results[0]['annual_return']:.2f}%")
        print("最佳组合参数:")
        print(f"  - 回测天数: {results[0]['backtest_days']}")
        print(f"  - 止盈比例: {results[0]['stop_profit_ratio']*100:.1f}%")
        print(f"  - 止损比例: {results[0]['stop_loss_ratio']*100:.1f}%")
        print(f"  - 权重配置: {results[0]['weights_config']}")
        print(f"  - 子权重配置: {results[0]['sub_weights_config']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
