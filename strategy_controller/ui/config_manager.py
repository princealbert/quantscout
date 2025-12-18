#!/usr/bin/env python
# coding=utf-8
"""
配置管理界面组件 - 在侧边栏显示配置管理功能
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime

# 导入配置管理器
from emgm.strategy_controller.utils.config_manager import ConfigManager

# 创建配置管理器实例
config_manager = ConfigManager()


def display_config_manager(current_weights: Dict[str, int], current_sub_weights: Dict[str, Any] = None):
    """显示配置管理界面"""
    
    st.markdown('<div class="section-header">⚙️ 配置管理</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='param-card'>", unsafe_allow_html=True)
        
        # 配置选择区域
        _display_config_selection()
        
        # 配置操作区域
        _display_config_operations(current_weights, current_sub_weights)
        
        st.markdown("</div>", unsafe_allow_html=True)


def _display_config_selection():
    """显示配置选择区域"""
    
    # 检测是否刚刚删除配置，需要刷新页面
    if st.session_state.get('config_just_deleted', False):
        print("🔄 [CONFIG_SELECTION] 检测到配置刚删除，刷新页面")
        st.session_state.config_just_deleted = False
        st.rerun()
    
    # 获取所有配置
    configs = config_manager.get_all_configs()
    print(f"🔍 [CONFIG_SELECTION] 当前配置数量: {len(configs)}")
    print(f"🔍 [CONFIG_SELECTION] 当前配置ID列表: {[config['config_id'] for config in configs]}")
    
    # 初始化session state中的配置管理状态
    if 'selected_config_id' not in st.session_state:
        st.session_state.selected_config_id = 'default'
    if 'config_loaded' not in st.session_state:
        st.session_state.config_loaded = False
    
    # 配置选择下拉框
    config_options = {}
    for config in configs:
        display_name = f"{config['name']}"
        if config.get('is_default'):
            display_name += " (默认)"
        config_options[config['config_id']] = display_name
    
    # 按创建时间排序配置
    sorted_configs = sorted(configs, key=lambda x: x.get('created_at', ''), reverse=True)
    sorted_config_ids = [config['config_id'] for config in sorted_configs]
    sorted_config_names = [config_options[config_id] for config_id in sorted_config_ids]
    
    # 如果检测到刚删除配置，需要刷新页面
    if st.session_state.get('config_just_deleted', False):
        print("🔄 [CONFIG_SELECTION] 检测到配置刚删除，准备刷新页面")
        # 清除删除标记，在下一次渲染时刷新
        st.session_state.config_just_deleted = False
        st.rerun()
    
    # 配置选择器
    selected_config_name = st.selectbox(
        "选择配置",
        options=sorted_config_names,
        index=sorted_config_names.index(config_options[st.session_state.selected_config_id]) if st.session_state.selected_config_id in config_options else 0,
        key="config_selector"
    )
    
    # 获取选中的配置ID
    selected_config_id = sorted_config_ids[sorted_config_names.index(selected_config_name)]
    
    # 如果配置发生变化，更新选中的配置ID但不自动加载
    if selected_config_id != st.session_state.selected_config_id:
        st.session_state.selected_config_id = selected_config_id
        st.session_state.config_loaded = False
    
    # 显示配置信息
    selected_config = config_manager.get_config(selected_config_id)
    if selected_config:
        st.caption(f"📝 {selected_config.get('description', '暂无描述')}")
        st.caption(f"🕐 创建时间: {_format_datetime(selected_config.get('created_at'))}")
        
        # 显示权重预览
        weights = selected_config.get('weights', {})
        if weights:
            weight_text = ", ".join([f"{k}: {v}" for k, v in weights.items()])
            st.caption(f"⚖️ 主权重: {weight_text}")
        
        # 显示子权重预览
        sub_weights = selected_config.get('sub_weights', {})
        if sub_weights:
            sub_weight_texts = []
            for main_key, sub_config in sub_weights.items():
                if isinstance(sub_config, dict):
                    total = sub_config.get('total_weight', 0)
                    sub_items = sub_config.get('sub_weights', {})
                    if sub_items:
                        items_text = ", ".join([f"{k}: {v}" for k, v in sub_items.items()])
                        sub_weight_texts.append(f"{main_key}({total}): {items_text}")
            
            if sub_weight_texts:
                st.caption(f"🔧 子权重: {'; '.join(sub_weight_texts)}")


def _display_config_operations(current_weights: Dict[str, int], current_sub_weights: Dict[str, Any] = None):
    """显示配置操作区域"""
    
    print(f"🔍 [CONFIG_OPS] 显示配置操作区域，当前配置ID: {st.session_state.get('selected_config_id', 'default')}")
    
    # 检查是否需要显示保存模态框
    if st.session_state.get('show_save_modal', False):
        print("🔍 [CONFIG_OPS] 检测到需要显示保存模态框")
        weights = st.session_state.get('save_modal_weights', {})
        sub_weights = st.session_state.get('save_modal_sub_weights', {})
        
        # 显示保存模态框
        _show_save_config_modal(weights, sub_weights)
        
        # 不要立即清除标记，让模态框保持显示状态
        print("🏷️ [CONFIG_OPS] 保存模态框显示中...")
        return  # 在显示模态框后直接返回
    
    # 检查是否需要显示复制模态框
    if st.session_state.get('show_duplicate_modal', False):
        print("🔍 [CONFIG_OPS] 检测到需要显示复制模态框")
        
        # 显示复制模态框
        _show_duplicate_config_modal()
        
        # 不要立即清除标记，让模态框保持显示状态
        print("🏷️ [CONFIG_OPS] 复制模态框显示中...")
        return  # 在显示模态框后直接返回
    
    # 检查是否需要显示删除模态框
    if st.session_state.get('show_delete_modal', False):
        config_id = st.session_state.get('delete_modal_config_id')
        print(f"🔍 [CONFIG_OPS] 检测到需要显示删除模态框，配置ID: {config_id}")
        
        # 显示删除模态框，但不立即清除标记，让模态框保持显示
        _show_delete_config_modal(config_id)
        
        # 只有在模态框完成操作后（通过st.rerun）才会清除标记
        print("🏷️ [CONFIG_OPS] 删除模态框显示完成")
        return  # 在显示模态框后直接返回，避免执行后续的按钮区域代码
    
    # 操作按钮区域
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 保存当前配置按钮
        save_clicked = st.button("💾 保存", use_container_width=True, key="save_config")
        if save_clicked:
            print("💾 [SAVE] 保存按钮被点击")
            # 设置保存模态框显示标记
            st.session_state.show_save_modal = True
            st.session_state.save_modal_weights = current_weights
            st.session_state.save_modal_sub_weights = current_sub_weights
            print("🏷️ [SAVE] 设置保存模态框标记，准备刷新页面")
            st.rerun()
    
    with col2:
        # 复制配置按钮
        duplicate_clicked = st.button("📋 复制", use_container_width=True, key="duplicate_config")
        if duplicate_clicked:
            print("📋 [DUPLICATE] 复制按钮被点击")
            # 设置复制模态框显示标记
            st.session_state.show_duplicate_modal = True
            print("🏷️ [DUPLICATE] 设置复制模态框标记，准备刷新页面")
            st.rerun()
    
    with col3:
        # 删除配置按钮（不能删除默认配置）
        selected_config_id = st.session_state.selected_config_id
        print(f"🔍 [DELETE_BUTTON] 检查删除按钮状态，配置ID: {selected_config_id}")
        
        if selected_config_id != 'default':
            delete_clicked = st.button("🗑️ 删除", use_container_width=True, key="delete_config")
            print(f"🔍 [DELETE_BUTTON] 删除按钮状态: {delete_clicked}")
            
            if delete_clicked:
                print(f"🗑️ [DELETE] 删除按钮被点击，配置ID: {selected_config_id}")
                # 设置删除模态框显示标记
                st.session_state.show_delete_modal = True
                st.session_state.delete_modal_config_id = selected_config_id
                print(f"🏷️ [DELETE] 设置删除模态框标记: show_delete_modal = True, config_id = {selected_config_id}")
                
                # 立即刷新页面以显示模态框
                print("🔄 [DELETE] 立即刷新页面以显示删除模态框")
                st.rerun()
        else:
            st.button("🗑️ 删除", use_container_width=True, key="delete_config_disabled", disabled=True)
            print("🔒 [DELETE] 默认配置，删除按钮被禁用")
    
    # 加载配置按钮
    if not st.session_state.config_loaded:
        if st.button("🔄 加载配置", type="primary", use_container_width=True, key="load_config"):
            _load_config(st.session_state.selected_config_id)
    else:
        st.success("✅ 配置已加载")


def _show_save_config_modal(current_weights: Dict[str, int], current_sub_weights: Dict[str, Any] = None):
    """显示保存配置模态框"""
    
    with st.form("save_config_form"):
        st.subheader("💾 保存配置")
        
        config_name = st.text_input("配置名称", value=f"配置_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        config_description = st.text_area("配置描述", placeholder="请输入配置描述...")
        
        # 显示当前权重预览
        st.write("当前权重设置:")
        for key, value in current_weights.items():
            st.write(f"- {key}: {value}")
        
        submitted = st.form_submit_button("保存")
        
        if submitted:
            if not config_name.strip():
                st.error("请输入配置名称")
                return
            
            try:
                config_id = config_manager.save_config(
                    name=config_name.strip(),
                    weights=current_weights,
                    sub_weights=current_sub_weights,
                    description=config_description.strip()
                )
                st.success(f"✅ 配置 '{config_name}' 保存成功！")
                
                # 清除所有模态框标记并刷新页面
                st.session_state.selected_config_id = config_id
                st.session_state.show_save_modal = False
                st.session_state.show_duplicate_modal = False
                st.session_state.show_delete_modal = False
                print("🏷️ [SAVE] 清除所有模态框标记")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 保存失败: {str(e)}")


def _show_duplicate_config_modal():
    """显示复制配置模态框"""
    
    selected_config_id = st.session_state.selected_config_id
    selected_config = config_manager.get_config(selected_config_id)
    
    if not selected_config:
        st.error("当前配置不存在")
        return
    
    with st.form("duplicate_config_form"):
        st.subheader("📋 复制配置")
        
        new_name = st.text_input("新配置名称", value=f"{selected_config['name']}_副本")
        new_description = st.text_area("新配置描述", value=selected_config.get('description', ''))
        
        submitted = st.form_submit_button("复制")
        
        if submitted:
            if not new_name.strip():
                st.error("请输入新配置名称")
                return
            
            try:
                print(f"🔍 [DUPLICATE] 开始复制配置: {selected_config_id}")
                print(f"🔍 [DUPLICATE] 新名称: {new_name.strip()}")
                print(f"🔍 [DUPLICATE] 原描述: {selected_config.get('description', '')}")
                print(f"🔍 [DUPLICATE] 新描述: {new_description}")
                
                # 使用新的复制方法，同时处理名称和描述
                # 如果用户没有输入描述，传递None让配置管理器使用默认描述
                description_param = new_description.strip() if new_description and new_description.strip() else None
                print(f"🔍 [DUPLICATE] 最终描述参数: {description_param}")
                
                # 确保描述参数是字符串类型，如果是None则传递空字符串
                final_description_param = description_param if description_param else ""
                print(f"🔍 [DUPLICATE] 最终传递给duplicate_config的描述参数: {final_description_param}")
                
                new_config_id = config_manager.duplicate_config(
                    selected_config_id, 
                    new_name.strip(), 
                    final_description_param
                )
                
                print(f"✅ [DUPLICATE] 复制成功，新配置ID: {new_config_id}")
                st.success(f"✅ 配置复制成功！")
                
                # 清除所有模态框标记并刷新页面
                st.session_state.selected_config_id = new_config_id
                st.session_state.config_loaded = False
                st.session_state.show_duplicate_modal = False
                st.session_state.show_save_modal = False
                st.session_state.show_delete_modal = False
                print("🏷️ [DUPLICATE] 清除所有模态框标记")
                st.rerun()
            except Exception as e:
                print(f"❌ [DUPLICATE] 复制失败: {str(e)}")
                import traceback
                print(f"🔍 [DUPLICATE] 异常详情: {traceback.format_exc()}")
                st.error(f"❌ 复制失败: {str(e)}")


def _show_delete_config_modal(config_id: str):
    """显示删除配置模态框"""
    
    print(f"🔍 [DELETE_MODAL] 显示删除模态框，配置ID: {config_id}")
    
    config = config_manager.get_config(config_id)
    if not config:
        st.error("配置不存在")
        print(f"❌ [DELETE_MODAL] 配置不存在: {config_id}")
        return
    
    st.subheader("🗑️ 删除配置")
    st.warning(f"确定要删除配置 '{config['name']}' 吗？此操作不可恢复。")
    
    # 简单的确认删除机制
    col1, col2 = st.columns(2)
    
    with col1:
        # 确认删除按钮
        if st.button("确认删除", type="primary", use_container_width=True, key=f"confirm_delete_{config_id}"):
            try:
                print(f"🔴 [DELETE] 正在删除配置: {config_id} - {config['name']}")
                
                # 记录删除前的配置数量
                before_count = len(config_manager.get_all_configs())
                print(f"📊 [DELETE] 删除前配置数量: {before_count}")
                
                success = config_manager.delete_config(config_id)
                
                # 记录删除后的配置数量
                after_count = len(config_manager.get_all_configs())
                print(f"📊 [DELETE] 删除后配置数量: {after_count}")
                
                if success:
                    print(f"✅ [DELETE] 配置删除成功: {config_id}")
                    st.success("✅ 配置删除成功！")
                    
                    # 更新session state
                    st.session_state.selected_config_id = 'default'
                    st.session_state.config_loaded = False
                    
                    # 设置删除标记，让页面在下一次渲染时刷新
                    st.session_state.config_just_deleted = True
                    print(f"🏷️ [DELETE] 设置删除标记: config_just_deleted = True")
                    
                    # 直接返回，让页面自动刷新
                    print("🔄 [DELETE] 删除操作完成，等待页面刷新")
                    st.rerun()
                else:
                    st.error("❌ 删除失败")
                    print(f"❌ [DELETE] 配置管理器返回删除失败")
            except Exception as e:
                print(f"❌ [DELETE] 删除失败异常: {str(e)}")
                import traceback
                print(f"🔍 [DELETE] 异常详情: {traceback.format_exc()}")
                st.error(f"❌ 删除失败: {str(e)}")
    
    with col2:
        # 取消按钮
        if st.button("取消", use_container_width=True, key=f"cancel_delete_{config_id}"):
            print(f"❌ [DELETE_MODAL] 用户取消删除")
            st.rerun()


def _load_config(config_id: str):
    """加载配置到当前界面"""
    
    config = config_manager.get_config(config_id)
    if not config:
        st.error("配置不存在")
        return
    
    print(f"🔄 [LOAD] 正在加载配置: {config_id} - {config['name']}")
    
    # 更新session state中的配置
    st.session_state.selected_config_id = config_id
    st.session_state.config_loaded = True
    
    # 更新权重配置
    weights = config.get('weights', {})
    if weights:
        print(f"📊 [LOAD] 更新主权重: {weights}")
        st.session_state.weights_config = weights
        # 直接更新滑块的session state值
        for key, value in weights.items():
            slider_key = f"{key}_weight"
            st.session_state[slider_key] = value
            print(f"🎛️ [LOAD] 设置滑块 {slider_key} = {value}")
    
    # 更新子权重配置
    sub_weights = config.get('sub_weights', {})
    if sub_weights:
        print(f"🔧 [LOAD] 更新子权重: {sub_weights}")
        st.session_state.sub_weights_config = sub_weights
    
    # 设置配置加载标记，用于权重组件检测
    st.session_state.last_loaded_config = config_id
    
    st.success(f"✅ 配置 '{config['name']}' 加载成功！")
    
    # 设置配置加载标记，权重组件会检测到这个标记并同步滑块值
    st.session_state.config_just_loaded = True


def _format_datetime(dt_str: str) -> str:
    """格式化日期时间"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str


def get_current_config() -> Optional[Dict[str, Any]]:
    """获取当前选中的配置"""
    selected_config_id = st.session_state.get('selected_config_id', 'default')
    return config_manager.get_config(selected_config_id)


def is_config_loaded() -> bool:
    """检查配置是否已加载"""
    return st.session_state.get('config_loaded', False)