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

# 检查是否通过 streamlit run 命令运行
if 'streamlit' not in sys.modules:
    print("请使用 streamlit run 命令运行此应用程序:")
    print(f"streamlit run {os.path.abspath(__file__)}")
    sys.exit(1)

import streamlit as st

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入参数优化器
from parameter_optimizer import ParameterOptimizer

# 从Excel文件读取回测结果
def read_results_from_excel(excel_path):
    import pandas as pd
    
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_path)
        
        results = []
        for index, row in df.iterrows():
            # 转换权重配置格式
            weights_config = {
                'kdj_j': row['权重_kdj_j'],
                'trend': row['权重_trend'],
                'volume': row['权重_volume'],
                'fundamental': row['权重_fundamental'],
                'position': row['权重_position'],
                'risk_reward': row['权重_risk_reward']
            }
            
            # 构建结果字典
            result = {
                'id': row['序号'],
                'stop_profit_ratio': row['止盈比例(%)'] / 100,  # 转换为小数形式
                'stop_loss_ratio': -row['止损比例(%)'] / 100,  # 转换为小数形式（负数表示亏损）
                'weights_config': weights_config,
                'total_return_rate': row['总收益率(%)'] / 100,  # 转换为小数形式
                'annual_return': row['年化收益率(%)'] / 100,  # 转换为小数形式
                'max_drawdown': row['最大回撤(%)'] / 100,  # 转换为小数形式
                'trades_count': row['交易次数'],
                # 注意：Excel中可能没有这些字段，需要根据实际情况调整
                'sharpe_ratio': row['夏普比率'] if '夏普比率' in row else 0.0,
                'win_rate': row['胜率(%)'] if '胜率(%)' in row else 0.0
            }
            results.append(result)
        
        return results
    except Exception as e:
        raise Exception(f"读取Excel文件失败: {str(e)}")


# 配置页面
st.set_page_config(
    page_title="参数优化器",
    page_icon="📈",
    layout="wide"
)

# 设置中文
st.markdown("<h1 style='text-align: center;'>参数优化器</h1>", unsafe_allow_html=True)

# 初始化优化器实例
optimizer = ParameterOptimizer()

# 侧边栏：算法选择和参数设置
st.sidebar.header("算法配置")

# 算法选择
algorithm = st.sidebar.selectbox(
    "选择优化算法",
    ["暴力搜索", "遗传算法"]
)

# 测试模式
is_test_mode = st.sidebar.checkbox("测试模式", value=False)

# 高级权重模式
use_advanced_weights = st.sidebar.checkbox("高级权重配置", value=True)

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

# 回测终点日期
end_date = st.sidebar.date_input(
    "回测终点日期",
    value=datetime.now(),
    min_value=datetime.now() - timedelta(days=365),
    max_value=datetime.now()
).strftime("%Y-%m-%d")

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
            weights_config_count = len(optimizer._generate_weights_combinations(core_indicators, 100, weight_step, min_weight=5, max_weight=95))
            
            # 估算子权重配置数量
            sub_weights_config_count = len(optimizer._generate_sub_weights_combinations(is_test_mode, max_sub_combinations, use_advanced_mode=use_advanced_weights))
            
            # 计算总组合数
            total_combinations = len(stop_profit_ratio) * len(stop_loss_ratio) * weights_config_count * sub_weights_config_count
            
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
            blueprint_path = optimizer.generate_blueprint(test_mode=is_test_mode, max_sub_combinations=max_sub_combinations)
            st.info(f"参数蓝图已保存到: {blueprint_path}")
            
        except Exception as e:
            st.error(f"生成参数组合失败: {e}")

# 显示蓝图进度
st.header("蓝图进度")

# 加载蓝图文件
blueprint_file = st.text_input("蓝图文件路径", value="parameter_blueprint.json")

if st.button("加载蓝图"):
    try:
        blueprint = optimizer.load_blueprint(blueprint_file)
        
        # 显示蓝图基本信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总组合数", blueprint.get("total_combinations", 0))
        with col2:
            st.metric("生成时间", blueprint.get("generated_at", "未知"))
        with col3:
            st.metric("版本", blueprint.get("version", "未知"))
            
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

# 运行优化
st.header("运行优化")

# 自动显示结果的标志
show_results = False

if st.button("开始优化"):
    try:
        # 加载或生成蓝图
        if os.path.exists(blueprint_file):
            blueprint = optimizer.load_blueprint(blueprint_file)
        else:
            # 生成蓝图文件
            blueprint_path = optimizer.generate_blueprint(test_mode=is_test_mode, max_sub_combinations=max_sub_combinations)
            # 加载生成的蓝图
            blueprint = optimizer.load_blueprint(blueprint_file)
        
        # 开始优化
        st.info("开始参数优化...")
        
        # 确保blueprint是字典类型
        if not isinstance(blueprint, dict):
            st.error(f"蓝图数据格式错误，预期字典类型，实际得到: {type(blueprint)}")
            raise TypeError(f"蓝图数据格式错误，预期字典类型，实际得到: {type(blueprint)}")
        
        # 实际执行优化过程
        for combo in blueprint['combinations']:
            if combo['status'] == 'pending':
                # 更新状态为运行中
                optimizer.update_combination_status(blueprint, combo['id'], 'running')
                optimizer.save_blueprint(blueprint, blueprint_file)
                
                # 执行实际回测
                try:
                    # 调用实际的回测方法
                    result = optimizer.run_backtest(combo['params'])
                    
                    # 转换结果格式以匹配预期
                    formatted_result = {
                        'total_return_rate': result.get('total_return', 0.0) / 100,  # 转换为小数形式
                        'max_drawdown': result.get('max_drawdown', 0.0) / 100,  # 转换为小数形式
                        'sharpe_ratio': result.get('sharpe_ratio', 0.0),  # 从回测结果中获取
                        'annual_return': result.get('annual_return', 0.0) / 100,  # 转换为小数形式
                        'win_rate': result.get('win_rate', 0.0) / 100  # 转换为小数形式
                    }
                except Exception as e:
                    st.error(f"回测失败: {e}")
                    # 生成失败结果
                    formatted_result = {
                        'total_return_rate': -1.0,  # 转换为小数形式
                        'max_drawdown': -1.0,  # 转换为小数形式
                        'sharpe_ratio': 0.0,
                        'annual_return': -1.0,  # 转换为小数形式
                        'win_rate': 0.0
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
        # 设置自动显示结果的标志
        show_results = True
        
    except Exception as e:
        st.error(f"运行优化失败: {e}")

# 显示回测结果
st.header("回测结果")

# 如果点击了查看按钮或者优化完成，显示结果
if st.button("查看回测结果") or show_results:
    try:
        # 从Excel文件读取结果
        excel_file = os.path.join(current_dir, "parameter_optimization_results.xlsx")
        
        if os.path.exists(excel_file):
            # 直接读取Excel文件
            df = pd.read_excel(excel_file, engine='openpyxl')
            
            if not df.empty:
                # 确保所有数值列都有正确的格式
                df['序号'] = df['序号'].astype(int)
                df['总收益率(%)'] = df['总收益率(%)'].round(2)
                df['年化收益率(%)'] = df['年化收益率(%)'].round(2)
                df['最大回撤(%)'] = df['最大回撤(%)'].round(2)
                df['夏普比率'] = df['夏普比率'].round(2)
                df['胜率(%)'] = df['胜率(%)'].round(2)
                
                # 显示表格
                st.dataframe(df)
                
                # 显示图表
                st.subheader("收益率分布")
                if '总收益率(%)' in df.columns:
                    st.bar_chart(df[['序号', '总收益率(%)']].set_index('序号'))
                
                # 显示最优结果
                st.subheader("最优参数组合")
                # 找到总收益率最高的行
                best_result = df.loc[df['总收益率(%)'].idxmax()]
                
                st.write("参数配置:")
                st.write(f"回测天数: {best_result['回测天数']}天")
                st.write(f"止盈比例: {best_result['止盈比例(%)']}%")
                st.write(f"止损比例: {best_result['止损比例(%)']}%")
                
                # 显示权重配置
                st.write("权重配置:")
                weight_columns = [col for col in df.columns if col.startswith('权重_')]
                for col in weight_columns:
                    indicator_name = col.replace('权重_', '')
                    st.write(f"  {indicator_name}: {best_result[col]}%")
                
                # 显示子权重配置
                sub_weight_columns = [col for col in df.columns if col.startswith('子权重_')]
                if sub_weight_columns:
                    st.write("子权重配置:")
                    for col in sub_weight_columns:
                        indicator_name = col.replace('子权重_', '')
                        st.write(f"  {indicator_name}: {best_result[col]}%")
                
                st.write("回测结果:")
                st.write(f"总收益率: {best_result['总收益率(%)']}%")
                st.write(f"年化收益率: {best_result['年化收益率(%)']}%")
                st.write(f"最大回撤: {best_result['最大回撤(%)']}%")
                st.write(f"夏普比率: {best_result['夏普比率']:.2f}")
                st.write(f"胜率: {best_result['胜率(%)']}%")
                st.write(f"交易次数: {best_result['交易次数']}")
            else:
                st.info("Excel文件为空")
        else:
            st.info("Excel文件不存在，尚未生成回测结果")
            
    except Exception as e:
        st.error(f"查看回测结果失败: {e}")
        import traceback
        traceback.print_exc()

# 页脚信息
st.markdown("<p style='text-align: center; color: gray;'>参数优化器 © 2024</p>", unsafe_allow_html=True)
