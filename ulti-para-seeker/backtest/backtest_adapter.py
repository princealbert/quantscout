#!/usr/bin/env python
# coding=utf-8
"""
回测适配器 - 统一回测接口，简化回测集成
用于将参数优化器与不同的回测引擎集成
"""

import os
import sys
from typing import Dict, Any

# 添加项目根目录到sys.path，确保能找到统一的回测引擎
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class BacktestAdapter:
    """
    回测适配器类 - 统一回测接口
    """
    
    @staticmethod
    def run_backtest(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个参数组合的回测
        
        Args:
            params: 参数组合
            
        Returns:
            Dict[str, Any]: 回测结果
        """
        # 导入回测执行模块
        from .runner import run_optimizer_backtest
        
        # 转换参数格式为回测引擎所需格式
        backtest_config = BacktestAdapter._convert_params_to_backtest_config(params)
        
        # 运行回测
        return run_optimizer_backtest(config=backtest_config, generate_charts=False)
    
    @staticmethod
    def _convert_params_to_backtest_config(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        将参数组合转换为回测引擎所需的配置格式
        
        Args:
            params: 参数组合
            
        Returns:
            Dict[str, Any]: 回测配置
        """
        # 转换参数格式
        converted_params = params.copy()
        
        # 转换止盈止损比例从百分位格式（如3表示3%）到千分位格式（如0.03）
        if 'stop_profit_ratio' in converted_params:
            profit = converted_params['stop_profit_ratio']
            # 如果是百分位格式（大于1），转换为千分位格式
            if isinstance(profit, (int, float)) and profit >= 1:
                converted_params['stop_profit_ratio'] = profit / 100.0
        
        if 'stop_loss_ratio' in converted_params:
            loss = converted_params['stop_loss_ratio']
            # 如果是百分位格式（绝对值大于等于1），转换为千分位格式
            if isinstance(loss, (int, float)) and abs(loss) >= 1:
                converted_params['stop_loss_ratio'] = loss / 100.0
        
        # 基础配置
        backtest_config = {
            "strategy_params": converted_params,
            "generate_charts": False,
            "is_cycle_mode": True
        }
        
        # 添加回测时间配置
        from datetime import datetime, timedelta
        end_date = params.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        backtest_days = params.get('backtest_days', 90)
        
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=backtest_days)
        
        backtest_config.update({
            "start_date": start_dt.strftime('%Y-%m-%d'),
            "end_date": end_date,
            "backtest_days": backtest_days
        })
        
        return backtest_config
    
    @staticmethod
    def validate_backtest_config(config: Dict[str, Any]) -> bool:
        """
        验证回测配置的有效性
        
        Args:
            config: 回测配置
            
        Returns:
            bool: 配置是否有效
        """
        try:
            # 验证必要的配置项
            if 'strategy_params' not in config:
                return False
            
            params = config['strategy_params']
            
            # 验证参数组合的有效性
            from algorithms.base import BaseOptimizer
            return BaseOptimizer().validate_parameters(params)
        except Exception:
            return False
    
    @staticmethod
    def get_supported_backtest_engines() -> list:
        """
        获取支持的回测引擎列表
        
        Returns:
            list: 支持的回测引擎列表
        """
        return [
            "strategy_engine_backtest",  # 基于strategy_engine的统一回测引擎
        ]
