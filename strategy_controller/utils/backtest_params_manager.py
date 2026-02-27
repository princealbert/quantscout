#!/usr/bin/env python
# coding=utf-8
"""
回测参数配置管理模块 - 集中管理所有回测相关参数
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class BacktestParamsManager:
    """
    回测参数配置管理类
    负责回测参数的定义、验证、加载和保存
    """
    
    def __init__(self):
        """
        初始化回测参数管理器
        """
        self.default_params = self._get_default_params()
        self.current_params = self.default_params.copy()
    
    def _get_default_params(self) -> Dict[str, Any]:
        """
        获取默认回测参数
        
        Returns:
            Dict[str, Any]: 默认回测参数配置
        """
        return {
            "backtest_days": 90,
            "backtest_days_range": {
                "min": 3,
                "max": 365,
                "step": 1
            },
            "initial_capital": 100000,
            "initial_capital_range": {
                "min": 10000,
                "max": 1000000,
                "step": 10000
            },
            "max_stocks": 1,
            "max_stocks_range": {
                "min": 1,
                "max": 10,
                "step": 1
            },
            "stop_profit": 3.0,
            "stop_profit_range": {
                "min": 1.0,
                "max": 1000.0,
                "step": 1.0
            },
            "stop_loss": -2.0,
            "stop_loss_range": {
                "min": -20.0,
                "max": -1.0,
                "step": 0.5
            },
            "max_holding_days": 5,
            "max_holding_days_range": {
                "min": 1,
                "max": 365,
                "step": 1
            },
            "end_date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        验证回测参数的有效性
        
        Args:
            params: 回测参数配置
            
        Returns:
            bool: 参数是否有效
        """
        try:
            # 验证回测天数
            backtest_days = params.get("backtest_days")
            if backtest_days:
                min_days = self.default_params["backtest_days_range"]["min"]
                max_days = self.default_params["backtest_days_range"]["max"]
                if not (min_days <= backtest_days <= max_days):
                    return False
            
            # 验证初始资金
            initial_capital = params.get("initial_capital")
            if initial_capital:
                min_capital = self.default_params["initial_capital_range"]["min"]
                max_capital = self.default_params["initial_capital_range"]["max"]
                if not (min_capital <= initial_capital <= max_capital):
                    return False
            
            # 验证回测股票数量
            max_stocks = params.get("max_stocks")
            if max_stocks:
                min_stocks = self.default_params["max_stocks_range"]["min"]
                max_stocks_val = self.default_params["max_stocks_range"]["max"]
                if not (min_stocks <= max_stocks <= max_stocks_val):
                    return False
            
            # 验证止盈比例
            stop_profit = params.get("stop_profit")
            if stop_profit:
                min_profit = self.default_params["stop_profit_range"]["min"]
                max_profit = self.default_params["stop_profit_range"]["max"]
                if not (min_profit <= stop_profit <= max_profit):
                    return False
            
            # 验证止损比例
            stop_loss = params.get("stop_loss")
            if stop_loss:
                min_loss = self.default_params["stop_loss_range"]["min"]
                max_loss = self.default_params["stop_loss_range"]["max"]
                if not (min_loss <= stop_loss <= max_loss):
                    return False
            
            # 验证最大持仓天数
            max_holding_days = params.get("max_holding_days")
            if max_holding_days:
                min_max_holding_days = self.default_params["max_holding_days_range"]["min"]
                max_max_holding_days = self.default_params["max_holding_days_range"]["max"]
                if not (min_max_holding_days <= max_holding_days <= max_max_holding_days):
                    return False
            
            return True
        except Exception:
            return False
    
    def load_params(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        从文件加载回测参数配置
        
        Args:
            file_path: 参数配置文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 加载的参数配置，如果加载失败返回None
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    params = json.load(f)
                if self.validate_params(params):
                    self.current_params = params
                    return params
        except Exception:
            pass
        return None
    
    def save_params(self, params: Dict[str, Any], file_path: str) -> bool:
        """
        保存回测参数配置到文件
        
        Args:
            params: 回测参数配置
            file_path: 参数配置文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if self.validate_params(params):
                # 确保目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # 保存参数
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(params, f, ensure_ascii=False, indent=2)
                
                self.current_params = params
                return True
        except Exception:
            pass
        return False
    
    def get_params(self) -> Dict[str, Any]:
        """
        获取当前回测参数配置
        
        Returns:
            Dict[str, Any]: 当前回测参数配置
        """
        return self.current_params
    
    def get_param_range(self, param_name: str) -> Optional[Dict[str, int]]:
        """
        获取参数的取值范围
        
        Args:
            param_name: 参数名称
            
        Returns:
            Optional[Dict[str, int]]: 参数取值范围，如果参数不存在返回None
        """
        range_key = f"{param_name}_range"
        if range_key in self.default_params:
            return self.default_params[range_key]
        return None
    
    def update_params(self, params: Dict[str, Any]) -> bool:
        """
        更新回测参数配置
        
        Args:
            params: 要更新的参数配置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 验证参数有效性
            if not self.validate_params(params):
                return False
            
            # 更新参数
            self.current_params.update(params)
            return True
        except Exception:
            return False


# 创建全局回测参数管理器实例
backtest_params_manager = BacktestParamsManager()
