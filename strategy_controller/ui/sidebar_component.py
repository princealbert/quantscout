#!/usr/bin/env python
# coding=utf-8
"""
侧边栏组件 - 策略选择和筛选参数配置
"""

import streamlit as st
from typing import Dict, Any


def display_strategy_selector():
    """显示策略选择器"""
    st.markdown('<div class="section-header">📊 策略选择</div>', unsafe_allow_html=True)
    
    strategy = st.radio(
        "选择选股策略",
        ["z哥综合策略 (KDJ+知行趋势+深V信号)"],
        index=0,
        horizontal=True
    )
    
    return strategy


def display_screening_parameters() -> Dict[str, Any]:
    """显示筛选参数"""
    st.markdown('<div class="section-header">🔧 筛选参数</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='param-card'>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**基础设置**")
            max_results = st.slider("最大显示数量", 10, 100, 30)
            skip_st = st.checkbox("跳过ST股票", value=True)
            test_mode = st.checkbox("测试模式（仅处理100只股票）", value=False)
        
        with col2:
            st.markdown("**处理设置**")
            batch_size = st.slider("分批大小", 100, 2000, 1000, step=100)
            max_workers = st.slider("并行线程数", 1, 10, 6)
            
        with col3:
            st.markdown("**股票池范围**")
            stock_pool_type = st.radio(
                "股票池范围",
                ["全量A股", "沪深300", "自定义股票池"],
                index=0
            )
            
            if stock_pool_type == "自定义股票池":
                custom_symbols = st.text_area("输入股票代码（每行一个）", "SHSE.600036\nSHSE.601318\nSZSE.000001")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        return {
            'max_results': max_results,
            'skip_st': skip_st,
            'test_mode': test_mode,
            'batch_size': batch_size,
            'max_workers': max_workers,
            'stock_pool_type': stock_pool_type,
            'custom_symbols': custom_symbols if stock_pool_type == "自定义股票池" else None
        }