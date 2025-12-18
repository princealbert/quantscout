#!/usr/bin/env python
# coding=utf-8
"""
权重配置组件 - 策略权重配置界面（支持配置管理器集成）
"""

import streamlit as st
from typing import Dict, Any

# 导入配置管理器
from emgm.strategy_engine.config_manager import get_current_config


def display_weight_configuration(strategy_type: str) -> Dict[str, Any]:
    """显示权重配置面板"""
    
    # 检查是否已加载配置
    current_config = get_current_config()
    config_loaded = current_config is not None and len(current_config) > 0
    
    # 初始化session state中的权重值
    if 'weights_initialized' not in st.session_state:
        default_weights = {
            'kdj_j': 25,
            'trend': 25,
            'deepv': 10,
            'volume': 8,
            'fundamental': 8,
            'position': 4,
            'risk_reward': 20
        }
        for key, value in default_weights.items():
            slider_key = f"{key}_weight"
            if slider_key not in st.session_state:
                st.session_state[slider_key] = value
        st.session_state.weights_initialized = True
    
    # 检测配置是否刚刚加载，需要同步滑块值
    if st.session_state.get('config_just_loaded', False):
        print("🔄 [WEIGHT_CONFIG] 检测到配置刚加载，同步滑块值")
        if current_config and config_loaded:
            weights = current_config.get('weights', {})
            for key, value in weights.items():
                # 统一使用{key}_weight格式
                slider_key = f"{key}_weight"
                current_value = st.session_state.get(slider_key)
                
                if current_value != value:
                    st.session_state[slider_key] = value
                    print(f"🎛️ [WEIGHT_CONFIG] 同步滑块 {slider_key}: {current_value} -> {value}")
        
        # 清除标记，避免重复同步
        st.session_state.config_just_loaded = False
        
        # 强制页面刷新，确保滑块同步生效
        st.rerun()
    
    # 从session state获取权重值（统一使用{key}_weight格式）
    default_weights = {
        'kdj_j': st.session_state.get('kdj_j_weight', 25),
        'trend': st.session_state.get('trend_weight', 25),
        'deepv': st.session_state.get('deepv_weight', 10),
        'volume': st.session_state.get('volume_weight', 8),
        'fundamental': st.session_state.get('fundamental_weight', 8),
        'position': st.session_state.get('position_weight', 4),
        'risk_reward': st.session_state.get('risk_reward_weight', 20)
    }
    
    st.markdown('<div class="section-header">⚖️ 权重配置</div>', unsafe_allow_html=True)
    
    # 显示配置加载状态
    if config_loaded:
        config_name = current_config.get('config_name', '默认配置') if current_config else '默认配置'
        st.success(f"✅ 已加载配置: {config_name}")
    
    with st.container():
        st.markdown("<div class='param-card'>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**技术指标权重**")
            kdj_weight = st.slider("KDJ J值权重", 0, 50, default_weights['kdj_j'], key="kdj_j_weight")
            trend_weight = st.slider("趋势权重", 0, 50, default_weights['trend'], key="trend_weight")
            deepv_weight = st.slider("深V信号权重", 0, 20, default_weights['deepv'], key="deepv_weight")
        
        with col2:
            st.markdown("**市场数据权重**")
            volume_weight = st.slider("成交量权重", 0, 20, default_weights['volume'], key="volume_weight")
            fundamental_weight = st.slider("基本面权重", 0, 20, default_weights['fundamental'], key="fundamental_weight")
            position_weight = st.slider("位置权重", 0, 10, default_weights['position'], key="position_weight")
        
        with col3:
            st.markdown("**风险控制权重**")
            risk_reward_weight = st.slider("盈亏比权重", 0, 40, default_weights['risk_reward'], key="risk_reward_weight")
            
            # 显示权重总和
            total_weight = kdj_weight + trend_weight + deepv_weight + volume_weight + fundamental_weight + position_weight + risk_reward_weight
            
            # 显示权重状态
            weight_status = "✅ 正常" if total_weight == 100 else f"⚠️ 异常 ({total_weight}/100)"
            weight_delta = f"{total_weight-100}" if total_weight != 100 else "✓"
            
            st.metric("权重总和", f"{total_weight}/100", delta=weight_delta)
            
            # 显示权重状态提示
            if total_weight != 100:
                st.warning("权重总和应为100，请调整权重设置")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 获取子指标权重配置
        main_weights = {
            'kdj_j': kdj_weight,
            'trend': trend_weight,
            'deepv': deepv_weight,
            'volume': volume_weight,
            'fundamental': fundamental_weight,
            'position': position_weight,
            'risk_reward': risk_reward_weight
        }
        
        # 显示子指标权重配置（可折叠）
        with st.expander("🔧 高级配置 - 子指标权重"):
            from strategy_controller.ui.sub_weight_config import display_sub_weight_configuration
            
            # 无论是否加载配置，都显示子指标配置界面
            # 如果已加载配置，传递配置中的子权重信息
            if current_config and config_loaded:
                sub_weights_config = current_config.get('sub_weights', {})
                # 更新session state中的子权重配置
                st.session_state.sub_weights_config = sub_weights_config
                # 显示子指标配置界面，传递已加载的配置
                display_sub_weight_configuration(main_weights, sub_weights_config)
            else:
                sub_weights_config = display_sub_weight_configuration(main_weights)
                # 将子权重配置保存到session state
                st.session_state.sub_weights_config = sub_weights_config
            
            # 显示应用状态
            if st.session_state.get('sub_weights_config'):
                st.success("✅ 子指标权重配置已保存")
        
        return main_weights


def get_weights_from_session() -> Dict[str, int]:
    """从session state获取当前权重配置"""
    
    # 从session state获取滑块值（统一使用{key}_weight格式）
    weights = {
        'kdj_j': st.session_state.get('kdj_j_weight', 25),
        'trend': st.session_state.get('trend_weight', 25),
        'deepv': st.session_state.get('deepv_weight', 10),
        'volume': st.session_state.get('volume_weight', 8),
        'fundamental': st.session_state.get('fundamental_weight', 8),
        'position': st.session_state.get('position_weight', 4),
        'risk_reward': st.session_state.get('risk_reward_weight', 20)
    }
    
    return weights


def get_sub_weights_from_session() -> Dict[str, Any]:
    """从session state获取子权重配置"""
    return st.session_state.get('sub_weights_config', {})