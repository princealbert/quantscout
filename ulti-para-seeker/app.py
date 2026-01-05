#!/usr/bin/env python
# coding=utf-8
"""
参数优化器 Streamlit UI
"""

import os
import sys
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入日志系统
from utils.logger import logger

# 检查是否通过 streamlit run 命令运行
if 'streamlit' not in sys.modules:
    logger.info("请使用 streamlit run 命令运行此应用程序:")
    logger.info(f"streamlit run {os.path.abspath(__file__)}")
    sys.exit(1)

import streamlit as st

# 导入参数优化器
from core import OptimizerManager




# 配置页面
st.set_page_config(
    page_title="参数优化器",
    page_icon="📈",
    layout="wide"
)

# 设置中文
st.markdown("<h1 style='text-align: center;'>参数优化器</h1>", unsafe_allow_html=True)

# 初始化优化器实例
optimizer = OptimizerManager()

# 侧边栏：算法选择和参数设置
st.sidebar.header("算法配置")

# 算法选择
algorithm = st.sidebar.selectbox(
    "选择优化算法",
    ["暴力搜索", "遗传算法", "粒子群算法"]
)

# 测试模式
is_test_mode = st.sidebar.checkbox("测试模式", value=False)

# 高级权重模式
use_advanced_weights = st.sidebar.checkbox("高级权重配置", value=True)

if use_advanced_weights:
    # 重点指标选择
    st.sidebar.subheader("高级权重配置")
    core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
    selected_focus_indicators = st.sidebar.multiselect(
        "选择重点指标",
        core_indicators,
        default=['kdj_j', 'trend'],
        help="选择需要重点关注的指标，这些指标在权重生成时会获得更高的权重"
    )
    
    # 权重因子设置
    focus_weight_factor = st.sidebar.slider(
        "重点指标权重因子",
        min_value=1.1,
        max_value=3.0,
        value=1.5,
        step=0.1,
        help="重点指标的权重放大倍数，值越大，重点指标获得的权重越高"
    )
else:
    # 默认值
    selected_focus_indicators = ['kdj_j', 'trend']
    focus_weight_factor = 1.5

# 最大子权重组合数
max_sub_combinations = st.sidebar.slider(
    "最大子权重组合数",
    min_value=1,
    max_value=50,
    value=10,
    step=1
)

# 止盈止损范围设置
col1, col2 = st.sidebar.columns(2)

with col1:
    st.subheader("止盈设置")
    stop_profit_min = st.slider(
        "止盈最小值 (%)",
        min_value=1,
        max_value=20,
        value=3,
        step=1
    )
    stop_profit_max = st.slider(
        "止盈最大值 (%)",
        min_value=1,
        max_value=20,
        value=15,
        step=1
    )
    stop_profit_step = st.slider(
        "止盈步长 (%)",
        min_value=1,
        max_value=5,
        value=2,
        step=1
    )

with col2:
    st.subheader("止损设置")
    stop_loss_min = st.slider(
        "止损最小值 (-%)",
        min_value=1,
        max_value=10,
        value=1,
        step=1
    )
    stop_loss_max = st.slider(
        "止损最大值 (-%)",
        min_value=1,
        max_value=10,
        value=5,
        step=1
    )
    stop_loss_step = st.slider(
        "止损步长 (-%)",
        min_value=1,
        max_value=5,
        value=1,
        step=1
    )

# 权重步长
weight_step = st.sidebar.slider(
    "权重步长 (%)",
    min_value=5,
    max_value=20,
    value=10,
    step=5
)

# 初始资金设置
initial_capital = st.sidebar.number_input(
    "初始资金",
    min_value=10000,
    max_value=1000000,
    value=60000,
    step=1000,
    help="设置回测的初始资金，范围：1万-100万"
)

# 回测终点日期
end_date = st.sidebar.date_input(
    "回测终点日期",
    value=datetime.now(),
    min_value=datetime.now() - timedelta(days=365),
    max_value=datetime.now()
).strftime("%Y-%m-%d")

# 回测天数
backtest_days = st.sidebar.number_input(
    "回测天数",
    min_value=3,
    max_value=365,
    value=90,
    step=1,
    help="设置回测天数，范围：3-365天"
)

# 主面板：显示信息和结果
st.header("参数组合分析")

# 计算并显示组合数和预计耗时
if st.button("生成参数组合"):
    with st.spinner("正在生成参数组合..."):
        try:
            # 生成参数范围
            stop_profit_ratio = [x/100 for x in range(stop_profit_min, stop_profit_max+1, stop_profit_step)]
            stop_loss_ratio = [-x/100 for x in range(stop_loss_min, stop_loss_max+1, stop_loss_step)]
            
            # 估算权重配置数量
            core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
            
            # 使用用户选择的权重步长
            weight_step_actual = weight_step
            
            # 基础权重组合
            base_weights = optimizer._generate_weights_combinations(core_indicators, 100, weight_step_actual, min_weight=5, max_weight=95)
            
            # 高级模式下添加自定义权重组合
            if use_advanced_weights:
                custom_weights = optimizer._generate_custom_weights_combinations(
                    core_indicators, 100, weight_step_actual,
                    focus_indicators=selected_focus_indicators,
                    focus_weight_factor=focus_weight_factor
                )
                # 合并并去重
                all_weights = base_weights + custom_weights
                seen = set()
                unique_weights = []
                for combo in all_weights:
                    key = tuple(sorted(combo.items()))
                    if key not in seen:
                        seen.add(key)
                        unique_weights.append(combo)
                weights_config_count = len(unique_weights)
            else:
                weights_config_count = len(base_weights)
            
            # 估算子权重配置数量
            sub_weights_config_count = len(optimizer._generate_sub_weights_combinations(is_test_mode, max_combinations=max_sub_combinations, use_advanced_mode=use_advanced_weights))
            
            # 计算总组合数
            base_combinations = len(stop_profit_ratio) * len(stop_loss_ratio) * weights_config_count * sub_weights_config_count
            
            # 根据选择的算法调整组合数
            if algorithm == "暴力搜索":
                total_combinations = base_combinations
                logger.info(f"[暴力搜索] 生成全部 {base_combinations} 个参数组合")
            elif algorithm == "遗传算法":
                # 遗传算法最终会根据max_sub_combinations选择固定数量的组合
                # 前端显示全量组合数，便于用户了解参数空间大小
                total_combinations = base_combinations
                logger.info(f"[遗传算法] 生成 {base_combinations} 个参数组合，将从中选择 {max_sub_combinations} 个进行优化")
            elif algorithm == "粒子群算法":
                # 粒子群算法最终会根据max_sub_combinations选择固定数量的组合
                # 前端显示全量组合数，便于用户了解参数空间大小
                total_combinations = base_combinations
                logger.info(f"[粒子群算法] 生成 {base_combinations} 个参数组合，将从中选择 {max_sub_combinations} 个进行优化")
            
            # 估算计算时间（假设每个组合需要10秒）
            estimated_time = total_combinations * 10
            hours, remainder = divmod(estimated_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # 显示结果
            st.success(f"参数组合生成完成！")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("总参数组合数", f"{total_combinations:,}")
            with col2:
                st.metric("预计计算时间", f"{int(hours)}小时 {int(minutes)}分钟 {int(seconds)}秒")
                
            # 生成蓝图
            blueprint_path = optimizer.generate_blueprint(
                test_mode=is_test_mode,
                max_sub_combinations=max_sub_combinations,
                algorithm=algorithm,
                end_date=end_date,
                stop_profit_min=stop_profit_min,
                stop_profit_max=stop_profit_max,
                stop_profit_step=stop_profit_step,
                stop_loss_min=stop_loss_min,
                stop_loss_max=stop_loss_max,
                stop_loss_step=stop_loss_step,
                weight_step=weight_step,
                use_advanced_weights=use_advanced_weights,
                focus_indicators=selected_focus_indicators,
                focus_weight_factor=focus_weight_factor,
                initial_capital=initial_capital,
                backtest_days=backtest_days
            )
            st.info(f"参数蓝图已保存到: {blueprint_path}")
            
        except Exception as e:
            st.error(f"生成参数组合失败: {e}")

# 蓝图管理
st.header("蓝图管理")

# 使用标签页组织蓝图管理功能
tab1, tab2, tab3 = st.tabs(["查看蓝图", "加载蓝图", "管理蓝图"])

# 标签页1: 查看蓝图列表
with tab1:
    st.subheader("蓝图文件列表")
    
    if st.button("刷新蓝图列表"):
        st.rerun()
    
    blueprints = optimizer.list_blueprints()
    
    if blueprints:
        st.info(f"共找到 {len(blueprints)} 个蓝图文件")
        
        for bp in blueprints:
            with st.expander(f"{bp['filename']} ({bp['size_kb']} KB)"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总组合数", bp.get('total_combinations', 0))
                with col2:
                    st.metric("算法", bp.get('algorithm', '未知'))
                with col3:
                    st.metric("版本", bp.get('version', '未知'))
                
                st.write(f"创建时间: {bp['created_at']}")
                st.write(f"修改时间: {bp['modified_at']}")
                
                if bp.get('is_index'):
                    st.info("这是一个分拆的蓝图索引文件")
                else:
                    st.info("这是一个完整的蓝图文件")
                
                if 'error' in bp:
                    st.error(f"读取错误: {bp['error']}")
    else:
        st.info("暂无蓝图文件")

# 标签页2: 加载蓝图
with tab2:
    st.subheader("加载蓝图")
    
    # 加载蓝图文件
    blueprint_file = st.text_input("蓝图文件路径", value="parameter_blueprint.json", key="load_blueprint_input")
    
    if st.button("加载蓝图"):
        try:
            blueprint = optimizer.load_blueprint(blueprint_file, load_all=False)
            
            # 显示蓝图基本信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总组合数", blueprint.get("total_combinations", 0))
            with col2:
                st.metric("生成时间", blueprint.get("generated_at", "未知"))
            with col3:
                st.metric("版本", blueprint.get("version", "未知"))
            
            # 检查是否为分拆的蓝图文件
            if blueprint.get("files"):
                st.info(f"这是一个分拆的蓝图文件，包含 {len(blueprint['files'])} 个子文件")
                
                # 显示子文件信息
                st.subheader("子文件信息")
                for file_info in blueprint["files"]:
                    sub_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_info['file'])
                    file_exists = "✅" if os.path.exists(sub_file_path) else "❌"
                    st.write(f"{file_exists} {file_info['file']}: ID {file_info['start_id']}-{file_info['end_id']}, 共 {file_info['count']} 个组合")
                
                # 遍历所有子文件统计各状态的组合数
                status_counts = {}
                for sub_file_info in blueprint['files']:
                    sub_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), sub_file_info['file'])
                    if os.path.exists(sub_file_path):
                        with open(sub_file_path, 'r', encoding='utf-8') as f:
                            sub_blueprint = json.load(f)
                        for combo in sub_blueprint['combinations']:
                            status = combo['status']
                            status_counts[status] = status_counts.get(status, 0) + 1
            else:
                # 统计各状态的组合数
                status_counts = {}
                for combo in blueprint['combinations']:
                    status = combo['status']
                    status_counts[status] = status_counts.get(status, 0) + 1
                
            # 显示进度条
            if "completed" in status_counts and "total_combinations" in blueprint:
                completed = status_counts["completed"]
                total = blueprint["total_combinations"]
                progress = completed / total
                
                st.progress(progress)
                st.write(f"已完成: {completed}/{total} 个组合 ({progress:.1%})")
            
            # 显示状态统计
            st.subheader("状态统计")
            for status, count in status_counts.items():
                st.write(f"{status}: {count}个")
                
        except Exception as e:
            st.error(f"加载蓝图失败: {e}")

# 标签页3: 管理蓝图
with tab3:
    st.subheader("蓝图管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.warning("⚠️ 删除操作不可恢复，请谨慎操作！")
        
        if st.button("清空所有蓝图文件", type="primary"):
            if st.session_state.get('confirm_clear', False):
                deleted_count = optimizer.clear_blueprints()
                st.success(f"已删除 {deleted_count} 个蓝图文件")
                st.session_state['confirm_clear'] = False
                st.rerun()
            else:
                st.session_state['confirm_clear'] = True
                st.error("请再次点击确认删除所有蓝图文件！")
    
    with col2:
        st.subheader("删除特定蓝图文件")
        
        blueprints = optimizer.list_blueprints()
        if blueprints:
            blueprint_to_delete = st.selectbox(
                "选择要删除的蓝图文件",
                options=[bp['filename'] for bp in blueprints],
                format_func=lambda x: f"{x} ({next(bp['size_kb'] for bp in blueprints if bp['filename'] == x)} KB)"
            )
            
            if st.button("删除选中的蓝图文件"):
                if st.session_state.get('confirm_delete', False):
                    success = optimizer.delete_blueprint(blueprint_to_delete)
                    if success:
                        st.success(f"已删除蓝图文件: {blueprint_to_delete}")
                        st.session_state['confirm_delete'] = False
                        st.rerun()
                    else:
                        st.error(f"删除蓝图文件失败: {blueprint_to_delete}")
                else:
                    st.session_state['confirm_delete'] = True
                    st.error(f"请再次点击确认删除 {blueprint_to_delete}！")
        else:
            st.info("暂无蓝图文件可删除")

# 运行优化
st.header("运行优化")

# 蓝图文件选择
blueprints = optimizer.list_blueprints()
blueprint_options = [bp['filename'] for bp in blueprints] if blueprints else []

if blueprint_options:
    blueprint_file = st.selectbox(
        "选择要优化的蓝图文件",
        options=blueprint_options,
        format_func=lambda x: f"{x} ({next(bp['size_kb'] for bp in blueprints if bp['filename'] == x)} KB)"
    )
else:
    st.warning("暂无蓝图文件，请先生成参数组合")
    blueprint_file = st.text_input("蓝图文件路径", value="parameter_blueprint.json", key="run_optimization_input")

# 自动显示结果的标志
show_results = False

if st.button("开始优化"):
    try:
        # 加载蓝图
        script_dir = os.path.dirname(os.path.abspath(__file__))
        blueprint_path = os.path.join(script_dir, blueprint_file)
        
        if not os.path.exists(blueprint_path):
            st.error(f"蓝图文件不存在: {blueprint_path}")
            st.error(f"当前工作目录: {os.getcwd()}")
            st.error(f"脚本目录: {script_dir}")
            st.stop()
        
        blueprint = optimizer.load_blueprint(blueprint_file)
        
        # 开始优化
        st.info("开始参数优化...")
        
        # 确保blueprint是字典类型
        if not isinstance(blueprint, dict):
            st.error(f"蓝图数据格式错误，预期字典类型，实际得到: {type(blueprint)}")
            raise TypeError(f"蓝图数据格式错误，预期字典类型，实际得到: {type(blueprint)}")
        
        # 检查是否为分拆的蓝图文件
        is_split_blueprint = blueprint.get('files') is not None
        
        if is_split_blueprint:
            st.info(f"这是一个分拆的蓝图文件，包含 {len(blueprint['files'])} 个子文件")
        
        # 实际执行优化过程
        if is_split_blueprint:
            # 分拆的蓝图文件，遍历所有子文件
            for sub_file_info in blueprint['files']:
                sub_file_path = os.path.join(current_dir, sub_file_info['file'])
                if not os.path.exists(sub_file_path):
                    st.warning(f"子文件不存在: {sub_file_info['file']}")
                    continue
                
                # 加载子文件
                with open(sub_file_path, 'r', encoding='utf-8') as f:
                    sub_blueprint = json.load(f)
                
                # 处理子文件中的组合
                for combo in sub_blueprint['combinations']:
                    if combo['status'] == 'pending':
                        # 更新状态为运行中
                        optimizer.update_combination_status(blueprint, combo['id'], 'running')
                        
                        # 执行实际回测
                        try:
                            # 调用实际的回测方法
                            result = optimizer.run_backtest(combo['params'])
                            
                            # 保留完整的结果，包括原始参数
                            formatted_result = result
                        except Exception as e:
                            st.error(f"回测失败: {e}")
                            # 生成失败结果，包含原始参数
                            formatted_result = {
                                **combo['params'],
                                'total_return': -100.0,
                                'annual_return': -100.0,
                                'max_drawdown': -100.0,
                                'sharpe_ratio': 0.0,
                                'win_rate': 0.0,
                                'trades_count': 0
                            }
                        
                        # 更新状态为已完成
                        optimizer.update_combination_status(blueprint, combo['id'], 'completed', formatted_result)
                        

                        
                        # 更新进度
                        completed = optimizer._count_completed_combinations(blueprint)
                        total = blueprint['total_combinations']
                        progress = completed / total
                        st.progress(progress)
                        st.write(f"已完成 {completed}/{total} 个组合...")
                        
                        # 测试模式下仅处理一个组合
                        if is_test_mode:
                            break
                
                # 测试模式下仅处理一个子文件
                if is_test_mode:
                    break
        else:
            # 非分拆的蓝图文件，直接遍历组合
            for combo in blueprint['combinations']:
                if combo['status'] == 'pending':
                    # 更新状态为运行中
                    optimizer.update_combination_status(blueprint, combo['id'], 'running')
                    optimizer.save_blueprint(blueprint, blueprint_file)
                    
                    # 执行实际回测
                    try:
                        # 调用实际的回测方法
                        result = optimizer.run_backtest(combo['params'])
                        
                        # 保留完整的结果，包括原始参数
                        formatted_result = result
                    except Exception as e:
                        st.error(f"回测失败: {e}")
                        # 生成失败结果，包含原始参数
                        formatted_result = {
                            **combo['params'],
                            'total_return': -100.0,
                            'annual_return': -100.0,
                            'max_drawdown': -100.0,
                            'sharpe_ratio': 0.0,
                            'win_rate': 0.0,
                            'trades_count': 0
                        }
                    
                    # 更新状态为已完成
                    optimizer.update_combination_status(blueprint, combo['id'], 'completed', formatted_result)
                    optimizer.save_blueprint(blueprint, blueprint_file)
                    

                    
                    # 更新进度
                    completed = sum(1 for c in blueprint['combinations'] if c['status'] == 'completed')
                    total = blueprint['total_combinations']
                    progress = completed / total
                    st.progress(progress)
                    st.write(f"已完成 {completed}/{total} 个组合...")
                    
                    # 测试模式下仅处理一个组合
                    if is_test_mode:
                        break
        
        st.success("参数优化完成！")
        
        # 导出结果到Excel
        if 'all_completed_results' in locals() and all_completed_results:
            # 从所有蓝图文件中收集已完成的结果
            all_completed_results = []
            
            # 获取所有蓝图文件
            blueprints = optimizer.list_blueprints()
            
            for bp in blueprints:
                bp_path = os.path.join(current_dir, bp['filename'])
                if os.path.exists(bp_path):
                    try:
                        blueprint = optimizer.load_blueprint(bp['filename'], load_all=True)
                        
                        # 检查是否为分拆的蓝图文件
                        if blueprint.get('files'):
                            # 分拆的蓝图文件，遍历所有子文件
                            for sub_file_info in blueprint['files']:
                                sub_file_path = os.path.join(current_dir, sub_file_info['file'])
                                if os.path.exists(sub_file_path):
                                    with open(sub_file_path, 'r', encoding='utf-8') as f:
                                        sub_blueprint = json.load(f)
                                    for combo in sub_blueprint['combinations']:
                                        if combo['status'] == 'completed' and combo['result']:
                                            all_completed_results.append(combo['result'])
                        else:
                            # 完整的蓝图文件，直接遍历组合
                            for combo in blueprint['combinations']:
                                if combo['status'] == 'completed' and combo['result']:
                                    all_completed_results.append(combo['result'])
                    except Exception as e:
                        st.warning(f"读取蓝图文件 {bp['filename']} 失败: {e}")
            
            if all_completed_results:
                # 导出结果到Excel
                output_file = "parameter_optimization_results.xlsx"
                optimizer.export_to_excel(all_completed_results, output_file)
                st.info(f"回测结果已导出到Excel文件: {output_file}")
        
        # 设置自动显示结果的标志
        show_results = True
        
    except Exception as e:
        st.error(f"运行优化失败: {e}")

# 显示回测结果
st.header("回测结果")

# 初始化session_state
if 'show_results' not in st.session_state:
    st.session_state['show_results'] = False
if 'best_result' not in st.session_state:
    st.session_state['best_result'] = None
if 'save_result' not in st.session_state:
    st.session_state['save_result'] = None
if 'weight_columns' not in st.session_state:
    st.session_state['weight_columns'] = []
if 'sub_weight_columns' not in st.session_state:
    st.session_state['sub_weight_columns'] = []

# 查看回测结果按钮
if st.button("查看回测结果") or show_results:
    st.session_state['show_results'] = True
    
    try:
        # 从所有蓝图文件中收集已完成的结果
        all_completed_results = []
        
        # 获取所有蓝图文件
        blueprints = optimizer.list_blueprints()
        
        for bp in blueprints:
            bp_path = os.path.join(current_dir, bp['filename'])
            if os.path.exists(bp_path):
                try:
                    blueprint = optimizer.load_blueprint(bp['filename'], load_all=True)
                    
                    # 检查是否为分拆的蓝图文件
                    if blueprint.get('files'):
                        # 分拆的蓝图文件，遍历所有子文件
                        for sub_file_info in blueprint['files']:
                            sub_file_path = os.path.join(current_dir, sub_file_info['file'])
                            if os.path.exists(sub_file_path):
                                with open(sub_file_path, 'r', encoding='utf-8') as f:
                                    sub_blueprint = json.load(f)
                                for combo in sub_blueprint['combinations']:
                                    if combo['status'] == 'completed' and combo['result']:
                                        all_completed_results.append(combo['result'])
                    else:
                        # 完整的蓝图文件，直接遍历组合
                        for combo in blueprint['combinations']:
                            if combo['status'] == 'completed' and combo['result']:
                                all_completed_results.append(combo['result'])
                except Exception as e:
                    st.warning(f"读取蓝图文件 {bp['filename']} 失败: {e}")
        
        if all_completed_results:
            # 将结果转换为DataFrame
            df_list = []
            seen_results = set()
            
            for i, result in enumerate(all_completed_results):
                # 创建用于去重的唯一标识符
                key_params = (
                    result.get('backtest_days', 90),
                    result.get('start_date', ''),
                    result.get('end_date', ''),
                    result.get('stop_profit_ratio', 0.0),
                    result.get('stop_loss_ratio', 0.0),
                    tuple(sorted(result.get('weights_config', {}).items())),
                    tuple(
                        (main_ind, tuple(sorted(sub_config['sub_weights'].items())))
                        for main_ind, sub_config in (result.get('sub_weights_config', {}) or {}).items()
                        if isinstance(sub_config, dict) and 'sub_weights' in sub_config and isinstance(sub_config['sub_weights'], dict)
                    )
                )
                
                if key_params in seen_results:
                    continue
                seen_results.add(key_params)
                
                # 跳过无效结果，只跳过那些明显错误的结果（远低于-100%）
                if result.get('total_return', 0.0) < -101:
                    continue
                
                row = {
                    '回测天数': result.get('backtest_days', 90),
                    '回测起始日期': result.get('start_date', ''),
                    '回测终止日期': result.get('end_date', ''),
                    '止盈比例(%)': result.get('stop_profit_ratio', 0.0) * 100,
                    '止损比例(%)': abs(result.get('stop_loss_ratio', 0.0) * 100),
                    '总收益率(%)': result.get('total_return', 0.0),
                    '年化收益率(%)': result.get('annual_return', 0.0),
                    '最大回撤(%)': result.get('max_drawdown', 0.0),
                    '夏普比率': result.get('sharpe_ratio', 0.0),
                    '胜率(%)': result.get('win_rate', 0.0),
                    '交易次数': result.get('trades_count', 0)
                }
                
                # 添加权重配置
                weights_config = result.get('weights_config', {})
                for indicator, weight in weights_config.items():
                    row[f'权重_{indicator}'] = weight
                
                # 添加子权重配置
                sub_weights_config = result.get('sub_weights_config', {})
                for main_indicator, sub_config in sub_weights_config.items():
                    if isinstance(sub_config, dict) and 'sub_weights' in sub_config:
                        for sub_indicator, weight in sub_config['sub_weights'].items():
                            row[f'子权重_{main_indicator}_{sub_indicator}'] = weight
                
                df_list.append(row)
            
            # 创建DataFrame
            df = pd.DataFrame(df_list)
            
            if not df.empty:
                # 确保所有数值列都有正确的格式
                if '序号' in df.columns:
                    df['序号'] = df['序号'].astype(int)
                if '总收益率(%)' in df.columns:
                    df['总收益率(%)'] = df['总收益率(%)'].round(2)
                if '年化收益率(%)' in df.columns:
                    df['年化收益率(%)'] = df['年化收益率(%)'].round(2)
                if '最大回撤(%)' in df.columns:
                    df['最大回撤(%)'] = df['最大回撤(%)'].round(2)
                if '夏普比率' in df.columns:
                    df['夏普比率'] = df['夏普比率'].round(2)
                else:
                    df['夏普比率'] = 0.0
                if '胜率(%)' in df.columns:
                    df['胜率(%)'] = df['胜率(%)'].round(2)
                else:
                    df['胜率(%)'] = 0.0
                
                # 添加序号列
                df['序号'] = range(1, len(df) + 1)
                
                # 按总收益率降序排序
                df = df.sort_values(by='总收益率(%)', ascending=False)
                
                # 显示表格
                st.dataframe(df)
                
                # 显示图表
                st.subheader("收益率分布")
                if '总收益率(%)' in df.columns:
                    # 使用直方图显示收益率分布
                    import plotly.express as px
                    import numpy as np
                    
                    # 计算收益率的最小值和最大值
                    min_return = df['总收益率(%)'].min()
                    max_return = df['总收益率(%)'].max()
                    
                    # 创建收益率区间（直方图的 bins）
                    bins = np.linspace(min_return, max_return, 20)  # 20个区间
                    
                    # 使用plotly创建直方图
                    fig = px.histogram(
                        df, 
                        x='总收益率(%)', 
                        nbins=20, 
                        title='收益率分布直方图',
                        labels={'总收益率(%)': '收益率(%)', 'count': '组合数'},
                        color_discrete_sequence=['#1f77b4']
                    )
                    
                    # 设置图表布局
                    fig.update_layout(
                        xaxis_title='收益率(%)',
                        yaxis_title='组合数',
                        bargap=0.1,
                        showlegend=False
                    )
                    
                    # 显示图表
                    st.plotly_chart(fig, use_container_width=True)
                
                # 显示最优结果
                st.subheader("最优参数组合")
                # 找到总收益率最高的行
                best_result = df.loc[df['总收益率(%)'].idxmax()]
                
                # 保存到session_state
                st.session_state['best_result'] = best_result
                
                # 保存权重列信息
                weight_columns = [col for col in df.columns if col.startswith('权重_')]
                sub_weight_columns = [col for col in df.columns if col.startswith('子权重_')]
                st.session_state['weight_columns'] = weight_columns
                st.session_state['sub_weight_columns'] = sub_weight_columns
                
                # 创建一个醒目的卡片布局展示最优结果
                with st.container(border=True):
                    # 使用列布局展示关键参数
                    st.markdown("### 参数配置")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("回测天数", f"{best_result['回测天数']}天")
                    with col2:
                        st.metric("止盈比例", f"{best_result['止盈比例(%)']}%")
                    with col3:
                        st.metric("止损比例", f"{best_result['止损比例(%)']}%")
                    
                    # 显示权重配置
                    st.markdown("### 权重配置")
                    weight_data = []
                    for col in weight_columns:
                        indicator_name = col.replace('权重_', '')
                        weight_data.append({
                            "指标": indicator_name,
                            "权重": f"{best_result[col]}%"
                        })
                    weight_df = pd.DataFrame(weight_data)
                    st.dataframe(weight_df, use_container_width=True, hide_index=True)
                    
                    # 显示子权重配置
                    if sub_weight_columns:
                        st.markdown("### 子权重配置")
                        sub_weight_data = []
                        for col in sub_weight_columns:
                            indicator_name = col.replace('子权重_', '')
                            sub_weight_data.append({
                                "指标": indicator_name,
                                "子权重": f"{best_result[col]}%"
                            })
                        sub_weight_df = pd.DataFrame(sub_weight_data)
                        st.dataframe(sub_weight_df, use_container_width=True, hide_index=True)
                    
                    # 显示回测结果
                    st.markdown("### 回测结果")
                    result_col1, result_col2, result_col3 = st.columns(3)
                    with result_col1:
                        st.metric("总收益率", f"{best_result.get('总收益率(%)', 0)}%")
                        st.metric("年化收益率", f"{best_result.get('年化收益率(%)', 0)}%")
                    with result_col2:
                        st.metric("最大回撤", f"{best_result.get('最大回撤(%)', 0)}%")
                        st.metric("夏普比率", f"{best_result.get('夏普比率', 0):.2f}")
                    with result_col3:
                        st.metric("胜率", f"{best_result.get('胜率(%)', 0)}%")
                        st.metric("交易次数", f"{best_result.get('交易次数', 0)}")
        else:
            st.info("尚未生成回测结果")
            st.session_state['show_results'] = False
            st.session_state['best_result'] = None
            st.session_state['weight_columns'] = []
            st.session_state['sub_weight_columns'] = []
            
    except Exception as e:
        st.error(f"查看回测结果失败: {e}")
        import traceback
        traceback.print_exc()
        st.session_state['show_results'] = False
        st.session_state['best_result'] = None
        st.session_state['weight_columns'] = []
        st.session_state['sub_weight_columns'] = []

# 发送到策略控制器功能 - 独立于查看结果按钮
if st.session_state['show_results'] and st.session_state['best_result'] is not None:
    # 获取保存的数据
    best_result = st.session_state['best_result']
    weight_columns = st.session_state['weight_columns']
    sub_weight_columns = st.session_state['sub_weight_columns']
    
    def save_to_strategy_controller():
        # 导入logger
        from utils.logger import logger
        
        logger.info("开始执行保存到策略控制器功能")
        
        try:
            # 1. 直接测试文件写入权限
            test_path = "c:\\Users\\Administrator\\.emgm3\\projects\\1593121d-dda9-11f0-8409-e89c2599a417\\test_write.txt"
            logger.info(f"测试写入路径: {test_path}")
            
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write("测试写入成功")
            logger.info("测试文件写入成功")
            
            # 2. 读取现有配置文件
            file_name = "weight_configs.json"
            save_path = os.path.join("c:\\Users\\Administrator\\.emgm3\\projects\\1593121d-dda9-11f0-8409-e89c2599a417\\web\\configs", file_name)
            
            logger.info(f"实际保存路径: {save_path}")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            logger.info(f"确保目录存在: {os.path.dirname(save_path)}")
            
            # 读取现有配置
            existing_configs = {}
            if os.path.exists(save_path):
                logger.info(f"读取现有配置文件: {save_path}")
                with open(save_path, 'r', encoding='utf-8') as f:
                    existing_configs = json.load(f)
                logger.info(f"现有配置包含 {len(existing_configs)} 个配置项")
            else:
                logger.warning(f"配置文件不存在，将创建新文件: {save_path}")
            
            # 3. 构建新的配置
            import uuid
            from datetime import datetime
            
            # 生成唯一ID
            config_id = str(uuid.uuid4())
            logger.info(f"生成配置ID: {config_id}")
            
            # 构建权重配置（转换为整数）
            weights = {}
            logger.info("开始构建权重配置")
            for col in weight_columns:
                indicator_name = col.replace('权重_', '')
                weight_value = int(best_result[col])
                weights[indicator_name] = weight_value
                logger.info(f"权重: {indicator_name} = {weight_value}")
            
            # 构建子权重配置
            sub_weights = {}
            logger.info("开始构建子权重配置")
            for col in sub_weight_columns:
                # 解析子权重字段名，格式为：子权重_指标_子指标
                parts = col.split('_')
                if len(parts) < 4:
                    logger.warning(f"无效的子权重字段名: {col}")
                    continue
                
                # 提取指标名和子指标名
                indicator_name = parts[1]
                sub_indicator_name = '_'.join(parts[2:])
                sub_weight_value = int(best_result[col])
                
                # 确保指标的子权重结构存在
                if indicator_name not in sub_weights:
                    sub_weights[indicator_name] = {
                        "total_weight": 100,
                        "sub_weights": {}
                    }
                
                # 添加子权重值（整数）
                sub_weights[indicator_name]["sub_weights"][sub_indicator_name] = sub_weight_value
                logger.info(f"子权重: {indicator_name}.{sub_indicator_name} = {sub_weight_value}")
            
            # 4. 构建完整的配置对象
            new_config = {
                "id": config_id,
                "name": f"{datetime.now().strftime('%Y%m%d')}_最优组合",
                "description": f"由参数优化器生成的最优组合，生成时间：{datetime.now().isoformat()}",
                "weights": weights,
                "sub_weights": sub_weights,
                "created_at": datetime.now().isoformat(),
                "is_default": False,
                "backtest_params": {
                    "stop_profit_ratio": best_result['止盈比例(%)'] / 100,
                    "stop_loss_ratio": -best_result['止损比例(%)'] / 100,
                    "backtest_days": int(best_result['回测天数']),
                    "initial_capital": 60000,
                    "commission_ratio": 0.0003
                }
            }
            
            logger.info(f"构建完成新配置: {new_config['name']}")
            logger.debug(f"新配置详情: {json.dumps(new_config, ensure_ascii=False, indent=2)}")
            
            # 5. 添加新配置到现有配置中
            existing_configs[config_id] = new_config
            logger.info(f"新配置已添加到现有配置中")
            
            # 6. 保存更新后的配置文件
            logger.info(f"开始保存配置文件到: {save_path}")
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(existing_configs, f, ensure_ascii=False, indent=2)
            logger.info(f"配置文件保存成功: {save_path}")
            
            # 验证文件是否保存成功
            if os.path.exists(save_path):
                logger.info(f"文件保存成功，大小: {os.path.getsize(save_path)} 字节")
            
            return save_path
        except Exception as e:
            logger.error(f"保存到策略控制器失败: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
    
    # 保存按钮
    st.markdown("---")
    st.subheader("策略控制器操作")
    
    if st.button("发送到策略控制器", type="primary"):
        with st.spinner("正在保存最优参数组合..."):
            try:
                save_path = save_to_strategy_controller()
                st.session_state['save_result'] = ("success", f"最优参数组合已保存到: {save_path}")
                st.success(st.session_state['save_result'][1])
            except Exception as e:
                error_msg = f"保存失败: {e}"
                st.session_state['save_result'] = ("error", error_msg)
                st.error(error_msg)
                st.exception(e)
    
    # 显示保存结果
    if st.session_state['save_result']:
        result_type, result_msg = st.session_state['save_result']
        if result_type == "success":
            st.success(result_msg)
        else:
            st.error(result_msg)

# 页脚信息
st.markdown("<p style='text-align: center; color: gray;'>参数优化器 © 2024</p>", unsafe_allow_html=True)
