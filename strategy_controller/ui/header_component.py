#!/usr/bin/env python
# coding=utf-8
"""
头部组件模块 - 页面配置和头部显示
"""

import streamlit as st
import sys
import os


def setup_page():
    """设置页面配置"""
    # 在Streamlit环境中避免重定向标准输出
    # 仅通过环境变量设置编码
    
    st.set_page_config(
        page_title="QuantScout量化选股系统",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 自定义CSS样式
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2c3e50;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .param-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #3498db;
    }
    .stock-card {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    .positive { color: #00aa00; font-weight: bold; }
    .negative { color: #ff4444; font-weight: bold; }
    .neutral { color: #666666; }
    .weight-slider { margin: 15px 0; }
    .log-window {
        background-color: #1e1e1e;
        color: #d4d4d4;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #3c3c3c;
    }
    .log-timestamp {
        color: #6a9955;
    }
    .log-info {
        color: #569cd6;
    }
    .log-warning {
        color: #d7ba7d;
    }
    .log-error {
        color: #f44747;
    }
    .log-success {
        color: #4ec9b0;
    }
    .log-debug {
        color: #9cdcfe;
    }
    </style>
    """, unsafe_allow_html=True)


def display_header():
    """显示页面头部"""
    st.markdown('<div class="main-header">🎯 QuantScout量化选股系统</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("**集成KDJ指标、知行趋势线、深V信号的智能选股系统**")
        st.markdown("*支持实时权重调整、策略配置和结果可视化*")


# 强制设置UTF-8编码以解决Windows GBK编码问题
def setup_encoding():
    """设置编码环境，避免在Streamlit环境中重定向标准输出"""
    # 设置环境变量强制使用UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # 仅设置环境变量，不进行标准输出重定向
    # 这可以避免"I/O operation on closed file"错误
    if sys.platform.startswith('win'):
        # Windows系统下设置UTF-8环境
        try:
            import locale
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except:
                try:
                    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
                except:
                    pass  # 如果设置失败，继续运行
        except:
            pass  # 如果locale不可用，继续运行

# 调用编码设置
setup_encoding()