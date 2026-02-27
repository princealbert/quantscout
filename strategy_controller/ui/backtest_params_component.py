#!/usr/bin/env python
# coding=utf-8
"""
回测参数设置组件 - 提供统一的回测参数设置界面
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime

# 导入回测参数管理器
from strategy_controller.utils.backtest_params_manager import backtest_params_manager


def display_backtest_params(config: Optional[Dict[str, Any]] = None, 
                           show_range_settings: bool = False) -> Dict[str, Any]:
    """
    显示回测参数设置界面
    
    Args:
        config: 初始参数配置，如果为None则使用默认值
        show_range_settings: 是否显示参数范围设置（用于参数求解器）
        
    Returns:
        Dict[str, Any]: 用户设置的回测参数
    """
    # 获取默认参数
    default_params = backtest_params_manager.get_params()
    
    # 使用传入的配置或默认配置
    params = config.copy() if config else default_params.copy()
    
    # 回测配置选项
    st.markdown("### ⚙️ 回测参数配置")
    
    # 回测天数
    col1, col2, col3 = st.columns(3)
    
    with col1:
        backtest_days = st.selectbox(
            "回测天数",
            [10, 30, 60, 90, 180, 360],
            index=[10, 30, 60, 90, 180, 360].index(params.get("backtest_days", 90)),
            help="选择回测的时间长度"
        )
        params["backtest_days"] = backtest_days
    
    with col2:
        end_date = st.date_input(
            "回测终止日期",
            value=datetime.now(),
            max_value=datetime.now(),
            help="选择回测的终止日期，默认是当前日期"
        )
        params["end_date"] = end_date.strftime("%Y-%m-%d")
    
    with col3:
        max_stocks = st.selectbox(
            "回测股票数量",
            [1, 2, 3, 5, 10],
            index=[1, 2, 3, 5, 10].index(params.get("max_stocks", 1)),
            help="选择排名前几的股票进行回测"
        )
        params["max_stocks"] = max_stocks
    
    # 初始资金配置
    initial_capital = st.number_input(
        "初始资金（元）",
        min_value=params.get("initial_capital_range", {}).get("min", 10000),
        max_value=params.get("initial_capital_range", {}).get("max", 1000000),
        value=params.get("initial_capital", 100000),
        step=params.get("initial_capital_range", {}).get("step", 10000),
        help="回测的初始资金"
    )
    params["initial_capital"] = initial_capital
    
    # 持仓天数配置（仅在非参数范围设置模式下显示）
    if not show_range_settings:
        max_holding_days = st.selectbox(
            "最大持仓天数",
            [1, 2, 3, 5, 7, 10, 15, 20, 25, 30, 45, 60, 90, 120, 180, 270, 365],
            index=[1, 2, 3, 5, 7, 10, 15, 20, 25, 30, 45, 60, 90, 120, 180, 270, 365].index(params.get("max_holding_days", 5)),
            help="设置最大持仓期限，买入当天不计算，达到该天数时自动卖出"
        )
        params["max_holding_days"] = max_holding_days
    
    # 止盈止损配置（仅在非参数范围设置模式下显示）
    if not show_range_settings:
        col4, col5 = st.columns(2)
        
        with col4:
            stop_profit = st.slider(
                "止盈比例 (%)",
                params.get("stop_profit_range", {}).get("min", 1.0),
                params.get("stop_profit_range", {}).get("max", 1000.0),
                params.get("stop_profit", 3.0),
                params.get("stop_profit_range", {}).get("step", 1.0),
                help="当盈利达到该比例时自动卖出"
            )
            params["stop_profit"] = stop_profit
        
        with col5:
            stop_loss = st.slider(
                "止损比例 (%)",
                params.get("stop_loss_range", {}).get("min", -20.0),
                params.get("stop_loss_range", {}).get("max", -1.0),
                params.get("stop_loss", -2.0),
                params.get("stop_loss_range", {}).get("step", 0.5),
                help="当亏损达到该比例时自动卖出"
            )
            params["stop_loss"] = stop_loss
    
    # 参数范围设置（用于参数求解器）
    if show_range_settings:
        st.markdown("---")
        st.markdown("### 🔧 参数范围设置")
        
        # 止盈范围设置
        st.subheader("止盈设置")
        col6, col7, col8 = st.columns(3)
        
        with col6:
            stop_profit_min = st.slider(
                "止盈最小值 (%)",
                min_value=1,
                max_value=1000,
                value=3,
                step=1
            )
            params["stop_profit_min"] = stop_profit_min
        
        with col7:
            stop_profit_max = st.slider(
                "止盈最大值 (%)",
                min_value=1,
                max_value=1000,
                value=15,
                step=1
            )
            params["stop_profit_max"] = stop_profit_max
        
        with col8:
            stop_profit_step = st.slider(
                "止盈步长 (%)",
                min_value=1,
                max_value=50,
                value=2,
                step=1
            )
            params["stop_profit_step"] = stop_profit_step
        
        # 止损范围设置
        st.subheader("止损设置")
        col9, col10, col11 = st.columns(3)
        
        with col9:
            stop_loss_min = st.slider(
                "止损最小值 (-%)",
                min_value=1,
                max_value=10,
                value=1,
                step=1
            )
            params["stop_loss_min"] = stop_loss_min
        
        with col10:
            stop_loss_max = st.slider(
                "止损最大值 (-%)",
                min_value=1,
                max_value=10,
                value=5,
                step=1
            )
            params["stop_loss_max"] = stop_loss_max
        
        with col11:
            stop_loss_step = st.slider(
                "止损步长 (-%)",
                min_value=1,
                max_value=5,
                value=1,
                step=1
            )
            params["stop_loss_step"] = stop_loss_step
        
        # 权重步长设置
        weight_step = st.slider(
            "权重步长 (%)",
            min_value=5,
            max_value=20,
            value=10,
            step=5
        )
        params["weight_step"] = weight_step
        
        # 最大持仓天数范围设置
        st.subheader("最大持仓天数设置")
        col12, col13, col14 = st.columns(3)
        
        with col12:
            max_holding_days_min = st.slider(
                "最大持仓天数最小值",
                min_value=1,
                max_value=365,
                value=1,
                step=1
            )
            params["max_holding_days_min"] = max_holding_days_min
        
        with col13:
            max_holding_days_max = st.slider(
                "最大持仓天数最大值",
                min_value=1,
                max_value=365,
                value=30,
                step=1
            )
            params["max_holding_days_max"] = max_holding_days_max
        
        with col14:
            max_holding_days_step = st.slider(
                "最大持仓天数步长",
                min_value=1,
                max_value=5,
                value=1,
                step=1
            )
            params["max_holding_days_step"] = max_holding_days_step
    
    # 回测参数说明
    st.info("💡 回测将使用选股结果中排名靠前的股票，基于东财掘金API进行历史回测")
    
    return params


def get_backtest_params_config() -> Dict[str, Any]:
    """
    获取回测参数配置
    
    Returns:
        Dict[str, Any]: 回测参数配置
    """
    return backtest_params_manager.get_params()


def validate_backtest_params(params: Dict[str, Any]) -> bool:
    """
    验证回测参数的有效性
    
    Args:
        params: 回测参数配置
        
    Returns:
        bool: 参数是否有效
    """
    return backtest_params_manager.validate_params(params)
