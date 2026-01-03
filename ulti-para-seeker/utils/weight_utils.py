#!/usr/bin/env python
# coding=utf-8
"""
权重工具模块 - 提供权重配置生成相关的工具函数
"""

import itertools
import random
from typing import Dict, Any, List, Tuple


def generate_weights_combinations(indicators: List[str], total: int, step: int, 
                                min_weight: int = 0, max_weight: int = 100) -> List[Dict[str, int]]:
    """
    生成权重组合
    
    Args:
        indicators: 指标列表
        total: 总权重
        step: 步长
        min_weight: 单个指标最小权重
        max_weight: 单个指标最大权重
        
    Returns:
        权重组合列表
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


def generate_custom_weights_combinations(indicators: List[str], total: int, step: int, 
                                        focus_indicators: List[str] = None, 
                                        focus_weight_factor: float = 1.5) -> List[Dict[str, int]]:
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
    base_combinations = generate_weights_combinations(indicators, total, step)
    
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


def generate_sub_weights_combinations(test_mode: bool = False, max_combinations: int = 10, 
                                    use_advanced_mode: bool = True) -> List[Dict[str, Dict[str, int]]]:
    """
    生成子权重组合

    Args:
        test_mode: 是否为测试模式
        max_combinations: 最大子权重组合数
        use_advanced_mode: 是否使用高级模式

    Returns:
        子权重组合列表
    """
    # 定义每个主指标的子指标
    sub_indicators = {
        'kdj_j': ['j_0_20', 'j_-10_0', 'j_-20_-10', 'j_-30_-20', 'j_below_-30'],
        'position': ['above_white', 'between_lines', 'below_yellow'],
        'volume': ['big_volume', 'volume_anomaly', 'volume_breathing'],
        'fundamental': ['pe_positive', 'pe_low', 'market_cap', 'volume_threshold'],
        'trend': ['up_trend', 'volume_price_rise', 'volume_contraction']
    }

    # 测试模式：只生成一个简单的子权重组合
    if test_mode:
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

        return [simple_sub_weights]

    # 正式模式：生成可控数量的子权重组合

    # 为每个主指标生成子权重组合
    sub_weights_combinations = {}
    for main_indicator, subs in sub_indicators.items():
        # 根据子指标数量选择合适的步长
        num_subs = len(subs)
        if use_advanced_mode:
            # 高级模式：使用更小的步长
            if num_subs == 3:
                step = 5
            elif num_subs == 4:
                step = 5
            else:  # num_subs == 5
                step = 5
        else:
            # 普通模式：使用较大步长
            if num_subs == 3:
                step = 10
            elif num_subs == 4:
                step = 10
            else:  # num_subs == 5
                step = 10

        # 生成子权重组合，限制子权重范围为5%-90%
        sub_weights = generate_weights_combinations(subs, 100, step, min_weight=5, max_weight=90)

        # 提前筛选有效的子权重组合
        valid_sub_weights = []
        for sw in sub_weights:
            if sum(sw.values()) == 100 and all(5 <= w <= 90 for w in sw.values()):
                valid_sub_weights.append(sw)

        sub_weights_combinations[main_indicator] = valid_sub_weights

    # 生成所有主指标的子权重组合的笛卡尔积
    main_indicators = list(sub_weights_combinations.keys())
    sub_weights_lists = [sub_weights_combinations[ind] for ind in main_indicators]

    # 计算总笛卡尔积数量
    total_cartesian = 1
    for sub_list in sub_weights_lists:
        total_cartesian *= len(sub_list)

    # 生成笛卡尔积，但限制数量
    combinations = []

    # 高级模式：使用多种策略生成组合
    if use_advanced_mode and total_cartesian > max_combinations:
        # 策略1: 分层随机采样
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

        # 策略2: 变异策略
        if len(combinations) < max_combinations and len(combinations) > 0:
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
    else:
        # 普通模式：遍历笛卡尔积
        current = 0
        for combination in itertools.product(*sub_weights_lists):
            sub_weights_config = {}
            for i, main_indicator in enumerate(main_indicators):
                sub_weights_config[main_indicator] = {'sub_weights': combination[i]}
            combinations.append(sub_weights_config)

            current += 1
            if current >= max_combinations:
                break

    # 去重
    seen = set()
    unique_combinations = []
    for combo in combinations:
        key = tuple(sorted((k, tuple(sorted(v['sub_weights'].items()))) for k, v in combo.items()))
        if key not in seen:
            seen.add(key)
            unique_combinations.append(combo)

    return unique_combinations[:max_combinations]


def generate_random_weights_config(step: int) -> Dict[str, int]:
    """
    生成随机权重配置
    
    Args:
        step: 权重步长
        
    Returns:
        Dict[str, int]: 权重配置字典
    """
    core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
    num_indicators = len(core_indicators)
    
    # 生成随机权重（确保在5%-95%之间）
    weights = []
    for _ in range(num_indicators):
        weight = random.randrange(5, 96, step)
        weights.append(weight)
    
    # 调整权重总和为100
    total = sum(weights)
    if total != 100:
        # 按比例调整
        scale = 100.0 / total
        weights = [max(5, min(95, int(round(w * scale)))) for w in weights]
        
        # 再次调整总和
        total = sum(weights)
        diff = 100 - total
        if diff > 0:
            # 增加权重最大的指标
            max_index = weights.index(max(weights))
            weights[max_index] = min(95, weights[max_index] + diff)
        elif diff < 0:
            # 减少权重最大的指标
            max_index = weights.index(max(weights))
            weights[max_index] = max(5, weights[max_index] + diff)
    
    # 创建权重配置字典
    weights_config = dict(zip(core_indicators, weights))
    weights_config['deepv'] = 0  # deepv权重设为0
    
    return weights_config


def generate_default_sub_weights() -> Dict[str, Dict[str, int]]:
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
