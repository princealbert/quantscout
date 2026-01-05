#!/usr/bin/env python
# coding=utf-8
"""
参数工具模块 - 提供参数处理相关的工具函数
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta


def validate_stop_profit_loss(stop_profit_ratio: float, stop_loss_ratio: float) -> bool:
    """
    验证止盈止损比例的有效性
    
    Args:
        stop_profit_ratio: 止盈比例 (0, 1]
        stop_loss_ratio: 止损比例 [-1, 0)
    
    Returns:
        bool: 参数是否有效
    """
    return (0 < stop_profit_ratio <= 1) and (-1 <= stop_loss_ratio < 0) and (stop_profit_ratio > stop_loss_ratio)


def validate_weights_config(weights_config: Dict[str, int]) -> bool:
    """
    验证权重配置的有效性
    
    Args:
        weights_config: 权重配置字典
    
    Returns:
        bool: 参数是否有效
    """
    # 检查总权重是否为100
    if sum(weights_config.values()) != 100:
        return False
    
    # 检查核心指标权重是否在5%-95%之间
    core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
    for indicator in core_indicators:
        if indicator in weights_config:
            if not (5 <= weights_config[indicator] <= 95):
                return False
    
    # deepv权重可以为0-100
    if 'deepv' in weights_config:
        if not (0 <= weights_config['deepv'] <= 100):
            return False
    
    return True


def validate_sub_weights_config(sub_weights_config: Dict[str, Dict[str, Any]]) -> bool:
    """
    验证子权重配置的有效性
    
    Args:
        sub_weights_config: 子权重配置字典
    
    Returns:
        bool: 参数是否有效
    """
    for main_indicator, sub_config in sub_weights_config.items():
        if 'sub_weights' not in sub_config:
            return False
        
        sub_weights = sub_config['sub_weights']
        if sum(sub_weights.values()) != 100:
            return False
        
        # 子权重必须在5%-90%之间
        for sub_indicator, weight in sub_weights.items():
            if not (5 <= weight <= 90):
                return False
    
    return True


def validate_parameter_combination(params: Dict[str, Any]) -> bool:
    """
    验证完整参数组合的有效性
    
    Args:
        params: 参数组合字典
    
    Returns:
        bool: 参数组合是否有效
    """
    try:
        # 验证止盈止损
        stop_profit = params.get('stop_profit_ratio', 0)
        stop_loss = params.get('stop_loss_ratio', 0)
        if not validate_stop_profit_loss(stop_profit, stop_loss):
            return False
        
        # 验证主权重配置
        weights = params.get('weights_config', {})
        if not validate_weights_config(weights):
            return False
        
        # 验证子权重配置 - 如果存在则验证，否则跳过
        sub_weights = params.get('sub_weights_config', {})
        if sub_weights and not validate_sub_weights_config(sub_weights):
            return False
        
        # 验证回测天数
        backtest_days = params.get('backtest_days', 0)
        if not (1 <= backtest_days <= 365):
            return False
        
        # 验证终点日期
        end_date_str = params.get('end_date', '')
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # 验证日期是否合理
            if end_date > datetime.now() or end_date < datetime(2000, 1, 1):
                return False
        except ValueError:
            return False
        
        # 验证初始资金
        initial_capital = params.get('initial_capital', 0)
        if not (10000 <= initial_capital <= 100000000):
            return False
        
        return True
    except Exception:
        return False


def calculate_start_date(end_date_str: str, backtest_days: int) -> str:
    """
    根据终点日期和回测天数计算起始日期
    
    Args:
        end_date_str: 终点日期 (YYYY-MM-DD)
        backtest_days: 回测天数
    
    Returns:
        str: 起始日期 (YYYY-MM-DD)
    """
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    start_date = end_date - timedelta(days=backtest_days)
    return start_date.strftime('%Y-%m-%d')


def format_parameter_combination(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化参数组合，确保所有必要字段存在
    
    Args:
        params: 参数组合字典
    
    Returns:
        Dict[str, Any]: 格式化后的参数组合
    """
    formatted = params.copy()
    
    # 确保止盈止损比例存在
    formatted.setdefault('stop_profit_ratio', 0.05)
    formatted.setdefault('stop_loss_ratio', -0.02)
    
    # 确保权重配置存在并包含所有核心指标
    core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
    weights = formatted.setdefault('weights_config', {})
    
    # 先设置deepv权重为0，不参与后续调整
    weights['deepv'] = 0
    
    # 设置核心指标的默认权重
    for indicator in core_indicators:
        weights.setdefault(indicator, 10)  # 默认10%
    
    # 只调整核心指标的权重，确保总和为100
    core_weights = {ind: weights[ind] for ind in core_indicators}
    core_total = sum(core_weights.values())
    
    if core_total != 100:
        # 按比例调整核心指标权重
        scale = 100.0 / core_total
        for indicator in core_indicators:
            weights[indicator] = int(round(weights[indicator] * scale))
        
        # 再次计算核心指标总和
        core_total = sum(weights[ind] for ind in core_indicators)
        
        # 确保核心指标总和精确为100
        if core_total < 100:
            # 增加最大权重的核心指标
            max_indicator = max(core_indicators, key=lambda x: weights[x])
            weights[max_indicator] += (100 - core_total)
        elif core_total > 100:
            # 减少最小权重的核心指标
            min_indicator = min(core_indicators, key=lambda x: weights[x])
            weights[min_indicator] -= (core_total - 100)
    
    # 确保子权重配置存在且有值
    from utils.weight_utils import generate_default_sub_weights
    formatted.setdefault('sub_weights_config', generate_default_sub_weights())
    
    # 其他默认值
    formatted.setdefault('backtest_days', 90)
    formatted.setdefault('end_date', datetime.now().strftime('%Y-%m-%d'))
    formatted.setdefault('initial_capital', 60000)
    
    return formatted


def estimate_total_combinations(param_ranges: Dict[str, List[Any]]) -> int:
    """
    估计参数组合总数
    
    Args:
        param_ranges: 参数范围字典
    
    Returns:
        int: 估计的总组合数
    """
    total = 1
    for param_name, param_list in param_ranges.items():
        total *= len(param_list)
    return total


def estimate_backtest_time(total_combinations: int, avg_backtest_time_seconds: int = 900) -> str:
    """
    估计回测总时间
    
    Args:
        total_combinations: 总组合数
        avg_backtest_time_seconds: 单个组合平均回测时间（秒）
    
    Returns:
        str: 格式化的回测时间估计
    """
    total_seconds = total_combinations * avg_backtest_time_seconds
    
    days = total_seconds // (24 * 3600)
    hours = (total_seconds % (24 * 3600)) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if days > 0:
        return f"{days}天 {hours}小时 {minutes}分钟"
    elif hours > 0:
        return f"{hours}小时 {minutes}分钟 {seconds}秒"
    elif minutes > 0:
        return f"{minutes}分钟 {seconds}秒"
    else:
        return f"{seconds}秒"


def generate_param_hash(params: Dict[str, Any]) -> str:
    """
    生成参数组合的唯一哈希值，用于查重
    
    Args:
        params: 参数组合字典
    
    Returns:
        str: 参数组合的唯一哈希值
    """
    import hashlib
    
    # 提取用于生成哈希的关键参数
    hash_data = {
        'stop_profit_ratio': params.get('stop_profit_ratio', 0),
        'stop_loss_ratio': params.get('stop_loss_ratio', 0),
        'weights_config': params.get('weights_config', {}),
        'sub_weights_config': params.get('sub_weights_config', {})
    }
    
    # 对权重配置进行排序，确保相同权重配置生成相同哈希
    if isinstance(hash_data['weights_config'], dict):
        hash_data['weights_config'] = dict(sorted(hash_data['weights_config'].items()))
    
    # 对子权重配置进行排序
    if isinstance(hash_data['sub_weights_config'], dict):
        sorted_sub_weights = {}
        for main_ind, sub_config in sorted(hash_data['sub_weights_config'].items()):
            if isinstance(sub_config, dict) and 'sub_weights' in sub_config:
                sorted_sub_weights[main_ind] = {
                    'sub_weights': dict(sorted(sub_config['sub_weights'].items()))
                }
            else:
                sorted_sub_weights[main_ind] = sub_config
        hash_data['sub_weights_config'] = sorted_sub_weights
    
    # 将数据转换为JSON字符串，确保一致性
    import json
    hash_str = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
    
    # 生成SHA256哈希
    return hashlib.sha256(hash_str.encode()).hexdigest()


def remove_duplicate_combinations(combinations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    移除重复的参数组合
    
    Args:
        combinations: 参数组合列表
    
    Returns:
        List[Dict[str, Any]]: 去重后的参数组合列表
    """
    seen_hashes = set()
    unique_combinations = []
    
    for combo in combinations:
        combo_hash = generate_param_hash(combo)
        if combo_hash not in seen_hashes:
            seen_hashes.add(combo_hash)
            unique_combinations.append(combo)
    
    return unique_combinations
