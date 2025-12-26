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
        
        # 验证子权重配置
        sub_weights = params.get('sub_weights_config', {})
        if not validate_sub_weights_config(sub_weights):
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
    for indicator in core_indicators:
        weights.setdefault(indicator, 10)  # 默认10%
    weights.setdefault('deepv', 0)  # deepv默认0%
    
    # 重新计算权重总和为100
    total_weight = sum(weights.values())
    if total_weight != 100:
        # 按比例调整权重
        scale = 100.0 / total_weight
        for indicator in weights:
            weights[indicator] = int(round(weights[indicator] * scale))
        
        # 确保总和精确为100
        total_weight = sum(weights.values())
        if total_weight < 100:
            # 增加最大权重指标的权重
            max_indicator = max(weights, key=weights.get)
            weights[max_indicator] += (100 - total_weight)
        elif total_weight > 100:
            # 减少最小权重指标的权重
            min_indicator = min(weights, key=weights.get)
            weights[min_indicator] -= (total_weight - 100)
    
    # 确保子权重配置存在基本结构
    sub_weights = formatted.setdefault('sub_weights_config', {})
    
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
