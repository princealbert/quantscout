#!/usr/bin/env python
# coding=utf-8
"""
QuantScout 量化选股系统 - 首页

Streamlit 原生多页面架构：
- Home.py: 首页（项目介绍）
- pages/01_策略控制器.py: 选股与回测
- pages/02_参数优化器.py: 参数搜索与优化

启动方式:
    streamlit run Home.py --server.port 8501

功能特性:
- 统一入口（无需启动两个应用）
- 实时日志显示（前端替代终端）
- 公共配置合并（Token + 高级权重）
- 进度监控（解决假死判断问题）
"""

import streamlit as st
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 页面配置
st.set_page_config(
    page_title="QuantScout量化选股系统",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "QuantScout - 基于 KDJ + 趋势 + 深V信号的多维综合选股策略",
    }
)

# 注入全局 CSS
def inject_global_css():
    """注入全局 CSS 样式"""
    st.markdown("""
    <style>
    .main-title {
        color: #1a3a5c;
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        color: #7f8c8d;
        text-align: center;
        font-size: 18px;
        margin-bottom: 1.5rem;
    }
    
    .feature-card {
        padding: 20px;
        background: #f8fafc;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        text-align: center;
        height: 100%;
        color: #2c3e50;
    }
    
    .feature-card h3 {
        color: #1a3a5c;
        margin-bottom: 10px;
    }
    
    .feature-card p {
        color: #7f8c8d;
        font-size: 14px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

inject_global_css()

# 页面内容
st.markdown("""
<div class="main-title">
    QuantScout量化选股系统
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="sub-title">
    基于 KDJ + 趋势 + 深V信号的多维综合选股策略
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# 功能介绍
st.markdown("### 🌟 核心功能")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>🎯 多维选股</h3>
        <p>基于 KDJ + 趋势 + 深V信号的<br>综合评分选股策略</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>⚖️ 权重可调</h3>
        <p>7 大核心指标权重自由调整，<br>重点指标放大机制</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>🔄 参数优化</h3>
        <p>3 种优化算法（暴力/遗传/粒子群），<br>自动寻找最优参数组合</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 快速导航
st.markdown("### 🚀 快速开始")

col1, col2 = st.columns(2)

with col1:
    st.info("**策略控制器**\n\n配置策略参数，执行选股与回测")
    if st.button("📊 前往策略控制器", type="primary", use_container_width=True):
        st.switch_page("pages/01_策略控制器.py")

with col2:
    st.info("**参数优化器**\n\n搜索最优参数组合，提升策略表现")
    if st.button("🔧 前往参数优化器", type="primary", use_container_width=True):
        st.switch_page("pages/02_参数优化器.py")

st.markdown("---")

# 使用说明
with st.expander("📖 使用说明", expanded=False):
    st.markdown("""
    ### 第一步：配置 Token
    1. 在左侧「公共配置」中输入东财掘金 API Token
    2. 点击「保存」Token
    
    ### 第二步：策略选股
    1. 进入「策略控制器」页面
    2. 调整权重配置和筛选参数
    3. 点击「开始选股」
    4. 查看实时进度和日志
    5. 获取选股结果
    
    ### 第三步：参数优化（可选）
    1. 进入「参数优化器」页面
    2. 设置参数范围和优化算法
    3. 点击「开始优化」
    4. 查看最优参数组合
    
    ### 提示
    - 点击页面底部「刷新状态」按钮更新进度
    - 实时日志面板可折叠，不占用主内容区
    - 所有配置在页面切换时自动保持
    """)

# 底部信息
st.markdown("---")
st.caption("QuantScout v1.0 | 基于东财掘金量化平台 | © 2026")
