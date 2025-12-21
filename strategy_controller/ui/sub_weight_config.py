#!/usr/bin/env python
# coding=utf-8
"""
子指标权重配置组件 - 支持精细化配置各个指标的子指标权重
"""

import streamlit as st
from typing import Dict, Any, List, Tuple


class SubWeightConfig:
    """子指标权重配置类"""
    
    def __init__(self):
        # 定义各个指标的子指标结构
        self.sub_indicators = {
            'kdj_j': {
                'name': 'KDJ J值',
                'sub_weights': {
                    'j_0_20': ('J值0-20区间', 1),
                    'j_-10_0': ('J值-10-0区间', 2),
                    'j_-20_-10': ('J值-20--10区间', 3),
                    'j_-30_-20': ('J值-30--20区间', 4),
                    'j_below_-30': ('J值<-30区间', 5)
                },
                'description': 'J值越低，权重越高，表示超卖程度越严重'
            },
            'trend': {
                'name': '趋势指标',
                'sub_weights': {
                    'up_trend': ('白线在黄线上方且斜率向上', 2),
                    'volume_price_rise': ('价随量升', 1),
                    'volume_contraction': ('缩量下跌', 1)
                },
                'description': '趋势向上且配合量能变化为佳'
            },
            'volume': {
                'name': '成交量指标',
                'sub_weights': {
                    'big_volume': ('放巨量', 2),
                    'volume_anomaly': ('成交量异动', 2),
                    'volume_breathing': ('成交量呼吸节奏', 1)
                },
                'description': '量价配合是技术分析的关键'
            },
            'fundamental': {
                'name': '基本面指标',
                'sub_weights': {
                    'pe_positive': ('PE为正', 1),
                    'pe_low': ('PE<60', 2),
                    'market_cap': ('流通市值>100亿', 1),
                    'volume_threshold': ('日均成交量>8000万股', 1)
                },
                'description': '基本面稳健是长期投资的基础'
            },
            'position': {
                'name': '位置指标',
                'sub_weights': {
                    'above_white': ('白线上方', 3),
                    'between_lines': ('碗里（黄白线之间）', 2),
                    'below_yellow': ('黄线下方', 1)
                },
                'description': '股价相对黄白线的位置决定安全边际'
            }
        }
    
    def get_sub_indicators_config(self, main_weights: Dict[str, int]) -> Dict[str, Any]:
        """根据主权重计算子指标权重配置"""
        sub_config = {}
        
        for main_key, main_weight in main_weights.items():
            if main_key in self.sub_indicators:
                sub_config[main_key] = {
                    'total_weight': main_weight,
                    'sub_weights': self._calculate_sub_weights(main_key, main_weight)
                }
        
        return sub_config
    
    def _calculate_sub_weights(self, main_key: str, main_weight: int) -> Dict[str, int]:
        """计算子指标权重"""
        if main_key not in self.sub_indicators:
            return {}
        
        sub_indicators = self.sub_indicators[main_key]['sub_weights']
        base_total = sum(weight for _, weight in sub_indicators.values())
        
        if base_total == 0:
            return {}
        
        scale_factor = main_weight / base_total
        dynamic_weights = {}
        
        for sub_key, (name, base_weight) in sub_indicators.items():
            dynamic_weights[sub_key] = int(base_weight * scale_factor)
        
        return dynamic_weights


def display_sub_weight_configuration(main_weights: Dict[str, int], existing_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """显示子指标权重配置面板（优化版）
    
    Args:
        main_weights: 主权重配置
        existing_config: 已存在的子权重配置（可选）
    """
    st.markdown('<div class="section-header">🔧 子指标权重配置</div>', unsafe_allow_html=True)
    
    config = SubWeightConfig()
    
    # 如果存在现有配置，使用现有配置；否则根据主权重计算
    if existing_config:
        sub_config = existing_config
    else:
        sub_config = config.get_sub_indicators_config(main_weights)
    
    # 创建选项卡界面
    tab_names = list(config.sub_indicators.keys())
    tabs = st.tabs([config.sub_indicators[tab]['name'] for tab in tab_names])
    
    final_sub_config = {}
    
    for i, tab in enumerate(tabs):
        main_key = tab_names[i]
        main_weight = main_weights.get(main_key, 0)
        
        with tab:
            st.markdown(f"**{config.sub_indicators[main_key]['description']}**")
            st.markdown(f"*主权重: {main_weight}分*")
            
            if main_key in sub_config:
                sub_weights = sub_config[main_key]['sub_weights']
                
                # 直接显示滑块，移除重复的文字列表显示
                st.markdown("**子指标权重调整**")
                
                for sub_key, weight in sub_weights.items():
                    if sub_key in config.sub_indicators[main_key]['sub_weights']:
                        name, _ = config.sub_indicators[main_key]['sub_weights'][sub_key]
                        # 优先使用session state中的值，如果存在的话
                        slider_key = f"sub_weight_{main_key}_{sub_key}"
                        
                        # 首先检查session state中是否有值
                        if slider_key in st.session_state:
                            session_value = st.session_state[slider_key]
                            print(f"🎛️ [SUB_WEIGHT] 使用session state值: {slider_key} = {session_value}")
                        else:
                            # 如果没有，使用现有配置中的值，并同时设置到session state中
                            session_value = weight
                            st.session_state[slider_key] = session_value
                            print(f"🎛️ [SUB_WEIGHT] 使用现有配置值并设置到session state: {slider_key} = {session_value}")
                        
                        adjusted_weight = st.slider(
                            f"{name}权重",
                            min_value=0,
                            max_value=main_weight,
                            value=session_value,
                            key=slider_key,
                            help=f"调整{name}的权重分配，总权重不能超过{main_weight}分"
                        )
                        sub_weights[sub_key] = adjusted_weight
                        
                        # 实时显示当前权重值
                        st.caption(f"当前权重: {adjusted_weight}分")
                
                # 验证权重总和
                sub_total = sum(sub_weights.values())
                if sub_total != main_weight:
                    st.warning(f"⚠️ 子权重总和为{sub_total}，与主权重{main_weight}不匹配")
                    st.info("💡 建议调整权重使总和等于主权重")
                else:
                    st.success(f"✅ 权重配置正确，总和: {sub_total}分")
                
                final_sub_config[main_key] = {
                    'total_weight': main_weight,
                    'sub_weights': sub_weights
                }
            else:
                st.info("该指标暂无子指标配置")
    
    return final_sub_config


def apply_sub_weights_to_scoring(sub_weights_config: Dict[str, Any]) -> Dict[str, Any]:
    """将子权重配置应用到评分系统"""
    # 这里可以修改权重评分器的动态权重计算
    # 目前返回配置供后续处理
    return {
        'sub_weights': sub_weights_config,
        'modified_at': '前端子权重配置已应用'
    }