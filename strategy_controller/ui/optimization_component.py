#!/usr/bin/env python
# coding=utf-8
"""
配置组件 - 提供策略配置功能（已移除优化器，保持功能归一）
"""

import streamlit as st
from typing import Dict, List, Any


def display_configuration_panel() -> None:
    """
    显示配置面板（已移除优化器功能）
    """
    
    st.markdown("---")
    st.subheader("⚙️ 策略配置")
    
    # 配置说明
    st.info("💡 当前使用标准配置管理器，确保配置统一管理，避免功能重叠")
    
    # 显示当前配置状态
    if st.session_state.get('weights_config'):
        st.success("✅ 当前已应用配置管理器权重")
        
        # 显示配置详情
        with st.expander("📊 当前配置详情"):
            st.write(f"**权重配置**: {st.session_state.weights_config}")
            if st.session_state.get('sub_weights_config'):
                st.write(f"**子权重配置**: {st.session_state.sub_weights_config}")
            
            # 显示配置来源
            if st.session_state.get('is_optimized'):
                st.warning("⚠️ 注意：当前配置可能包含历史优化信息，建议使用配置管理器重新设置")
            else:
                st.success("✅ 配置来自标准配置管理器")
    else:
        st.warning("⚠️ 请使用侧边栏配置管理器设置权重")
        
        # 提供快速跳转
        if st.button("📋 打开配置管理器", type="secondary"):
            st.info("请在左侧边栏中使用配置管理器设置权重配置")


def get_configuration_options() -> List[Dict[str, Any]]:
    """获取配置选项列表"""
    
    # 返回标准配置选项
    return [
        {
            "id": "standard",
            "name": "标准配置",
            "description": "使用配置管理器统一管理权重配置",
            "risk_level": "中",
            "recommended_for": "确保配置统一性和一致性"
        }
    ]