#!/usr/bin/env python
# coding=utf-8
"""
回测组件 - 提供发送策略到回测系统的功能（增强版）
"""

import streamlit as st
import json
import os
import tempfile
from typing import Dict, List, Any
from datetime import datetime

# 导入策略API
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# API可用性检查
API_AVAILABLE = False
# 暂时禁用API模式，使用备用方案


def display_backtest_button(strategy_results: List[Dict[str, Any]], 
                          strategy_type: str, 
                          weights_config: Dict[str, int],
                          sub_weights_config: Dict[str, Any] = None) -> None:
    """
    显示发送到回测按钮
    
    Args:
        strategy_results: 选股结果列表
        strategy_type: 策略类型
        weights_config: 权重配置
        sub_weights_config: 子权重配置
    """
    
    if not strategy_results:
        st.warning("暂无选股结果，无法进行回测")
        return
    
    st.markdown("---")
    st.subheader("🔬 策略回测")
    
    # 显示选股结果摘要
    with st.expander("📊 选股结果摘要", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("选股数量", len(strategy_results))
        with col2:
            avg_score = sum(s.get('total_score', 0) for s in strategy_results) / len(strategy_results)
            st.metric("平均评分", f"{avg_score:.1f}")
        with col3:
            st.metric("最佳股票", f"{strategy_results[0]['symbol']}")
    
    # 回测配置选项
    col1, col2, col3 = st.columns(3)
    
    with col1:
        backtest_days = st.selectbox(
            "回测天数",
            [30, 60, 90, 180],
            index=2,
            help="选择回测的时间长度"
        )
    
    with col2:
        initial_capital = st.number_input(
            "初始资金（元）",
            min_value=10000,
            max_value=1000000,
            value=100000,
            step=10000,
            help="回测的初始资金"
        )
    
    with col3:
        max_stocks = st.selectbox(
            "回测股票数量",
            [1, 3, 5, 10],
            index=0,
            help="选择排名前几的股票进行回测"
        )
    
    # 回测参数说明
    st.info("💡 回测将使用选股结果中排名靠前的股票，基于东财掘金API进行历史回测")
    
    # 发送到回测按钮
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 发送到回测", type="primary", use_container_width=True):
            _execute_backtest(
                strategy_results[:max_stocks],
                strategy_type,
                weights_config,
                sub_weights_config,
                backtest_days,
                initial_capital
            )
    
    with col2:
        if st.button("❓ 帮助", use_container_width=True):
            _show_backtest_help()


def _execute_backtest(stocks_to_backtest: List[Dict[str, Any]],
                     strategy_type: str,
                     weights_config: Dict[str, int],
                     sub_weights_config: Dict[str, Any],
                     backtest_days: int,
                     initial_capital: float) -> None:
    """
    执行回测操作
    
    Args:
        stocks_to_backtest: 要回测的股票列表
        strategy_type: 策略类型
        weights_config: 权重配置
        sub_weights_config: 子权重配置
        backtest_days: 回测天数
        initial_capital: 初始资金
    """
    
    # 显示回测进度
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 步骤1: 准备回测配置
        status_text.text("正在准备回测配置...")
        progress_bar.progress(20)
        
        # 详细的调试日志 - 参数传递检查
        print("\n" + "="*80)
        print("🔍 DEBUG: 回测参数传递检查")
        print("="*80)
        print(f"[DEBUG] 策略类型: {strategy_type}")
        print(f"[DEBUG] 回测天数: {backtest_days}")
        print(f"[DEBUG] 初始资金: {initial_capital}")
        print(f"[DEBUG] 股票数量: {len(stocks_to_backtest)}")
        print(f"[DEBUG] 权重配置类型: {type(weights_config)}")
        print(f"[DEBUG] 权重配置内容: {weights_config}")
        print(f"[DEBUG] 子权重配置类型: {type(sub_weights_config)}")
        print(f"[DEBUG] 子权重配置内容: {sub_weights_config}")
        print(f"[DEBUG] 股票列表前3只: {[stock['symbol'] for stock in stocks_to_backtest[:3]]}")
        
        # 检查权重配置的完整性
        if weights_config:
            total_weight = sum(weights_config.values())
            print(f"[DEBUG] 权重配置总分数: {total_weight}")
            print(f"[DEBUG] 权重配置项数: {len(weights_config)}")
            for key, value in weights_config.items():
                print(f"[DEBUG]   {key}: {value}")
        
        if sub_weights_config:
            print(f"[DEBUG] 子权重配置项数: {len(sub_weights_config)}")
            for key, value in sub_weights_config.items():
                print(f"[DEBUG]   {key}: {value}")
        
        print("="*80 + "\n")
        
        # 使用API创建回测包
        backtest_params = {
            "backtest_days": backtest_days,
            "initial_capital": initial_capital,
            "max_stocks": len(stocks_to_backtest)
        }
        
        # 直接使用备用方案（API暂时禁用）
        print("[DEBUG] 开始创建回测配置...")
        backtest_config = _create_backtest_config(
            stocks_to_backtest,
            strategy_type,
            weights_config,
            sub_weights_config,
            backtest_days,
            initial_capital
        )
        
        # 检查配置创建结果
        print(f"[DEBUG] 回测配置创建完成，类型: {type(backtest_config)}")
        print(f"[DEBUG] 配置结构: backtest_info={backtest_config.get('backtest_info', {})}")
        print(f"[DEBUG] 策略配置: strategy_config={backtest_config.get('strategy_config', {})}")
        print(f"[DEBUG] 股票数量: {len(backtest_config.get('selected_stocks', []))}")
        
        # 生成回测脚本
        print("[DEBUG] 开始生成回测脚本...")
        backtest_script_path = _generate_backtest_script(backtest_config)
        print(f"[DEBUG] 回测脚本生成完成，路径: {backtest_script_path}")
        
        result = {
            "config_path": "使用备用方案生成",
            "script_path": backtest_script_path,
            "api_status": {"status": "fallback"},
            "backtest_params": backtest_params
        }
        
        # 步骤2: 显示结果
        status_text.text("正在生成回测包...")
        progress_bar.progress(80)
        
        _display_backtest_results(result)
        
        # 完成
        progress_bar.progress(100)
        status_text.text("✅ 回测包生成完成！")
        
        st.success("回测包生成成功！")
        
    except Exception as e:
        progress_bar.progress(0)
        status_text.text(f"❌ 回测失败: {str(e)}")
        st.error(f"回测执行失败: {str(e)}")


def _create_backtest_config(stocks_to_backtest: List[Dict[str, Any]],
                           strategy_type: str,
                           weights_config: Dict[str, int],
                           sub_weights_config: Dict[str, Any],
                           backtest_days: int,
                           initial_capital: float) -> Dict[str, Any]:
    """创建回测配置文件"""
    
    config = {
        "backtest_info": {
            "strategy_type": strategy_type,
            "backtest_days": backtest_days,
            "initial_capital": initial_capital,
            "created_at": datetime.now().isoformat(),
            "selected_stocks_count": len(stocks_to_backtest)
        },
        "strategy_config": {
            "weights": weights_config,
            "sub_weights": sub_weights_config or {}
        },
        "selected_stocks": [
            {
                "symbol": stock["symbol"],
                "sec_name": stock["sec_name"],
                "total_score": stock.get("total_score", 0),
                "close_price": stock.get("close", 0),
                "kdj_j": stock.get("kdj_j", 0),
                "position_desc": stock.get("position_desc", "未知")
            }
            for stock in stocks_to_backtest
        ]
    }
    
    return config


def _generate_backtest_script(config: Dict[str, Any]) -> str:
    """
    生成回测配置JSON文件
    """
    
    # 使用全局的项目根目录路径
    backtest_dir = os.path.join(project_root, "backtest_output")
    
    # 确保目录存在
    os.makedirs(backtest_dir, exist_ok=True)
    
    # 生成JSON配置文件路径
    config_filename = f"backtest_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    config_path = os.path.join(backtest_dir, config_filename)
    
    # 调试信息：检查配置内容
    print("\n" + "="*60)
    print("🔍 DEBUG: 配置生成前检查")
    print("="*60)
    print(f"[DEBUG] 配置类型: {type(config)}")
    print(f"[DEBUG] 配置键: {list(config.keys())}")
    print(f"[DEBUG] backtest_info: {config.get('backtest_info', {})}")
    print(f"[DEBUG] strategy_config: {config.get('strategy_config', {})}")
    print(f"[DEBUG] weights_config存在: {'weights' in config.get('strategy_config', {})}")
    print(f"[DEBUG] sub_weights_config存在: {'sub_weights' in config.get('strategy_config', {})}")
    
    if 'strategy_config' in config:
        weights = config['strategy_config'].get('weights', {})
        sub_weights = config['strategy_config'].get('sub_weights', {})
        print(f"[DEBUG] 权重配置内容: {weights}")
        print(f"[DEBUG] 子权重配置内容: {sub_weights}")
        print(f"[DEBUG] 权重配置类型: {type(weights)}")
        print(f"[DEBUG] 子权重配置类型: {type(sub_weights)}")
    print("="*60 + "\n")
    
    # 构造完整的JSON配置结构
    backtest_config = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "backtest": {
            "initial_capital": config['backtest_info']['initial_capital'],
            "backtest_days": config['backtest_info']['backtest_days'],
            "max_stocks_to_backtest": config['backtest_info']['selected_stocks_count'],
            "strategy_id": f"zge_strategy_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        },
        "strategy": {
            "strategy_type": config['backtest_info']['strategy_type'],
            "weights_config": config['strategy_config']['weights'],
            "sub_weights_config": config['strategy_config']['sub_weights']
        },
        "selected_stocks": config['selected_stocks'],
        "meta": {
            "generated_by": "backtest_component.py",
            "file_path": config_path,
            "project_root": project_root
        }
    }
    
    # 保存JSON配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(backtest_config, f, ensure_ascii=False, indent=2)
    
    # 同时更新固定的配置文件（供main.py直接读取）
    fixed_config_path = os.path.join(project_root, "config", "current_backtest_config.json")
    with open(fixed_config_path, 'w', encoding='utf-8') as f:
        json.dump(backtest_config, f, ensure_ascii=False, indent=2)
    
    print(f"[DEBUG] 回测配置文件已生成: {config_path}")
    print(f"[DEBUG] 固定配置文件已更新: {fixed_config_path}")
    print(f"[DEBUG] 配置文件格式: JSON")
    print(f"[DEBUG] 配置内容: {json.dumps(backtest_config, ensure_ascii=False, indent=2)}")
    
    return config_path


def _launch_backtest(script_path: str) -> Dict[str, Any]:
    """启动回测系统"""
    
    # 这里返回模拟结果，实际实现需要调用真正的回测系统
    result = {
        "status": "success",
        "message": "回测脚本已生成，请手动运行或使用东财掘金客户端执行",
        "script_path": script_path,
        "backtest_info": {
            "execution_time": datetime.now().isoformat(),
            "recommendation": "建议使用东财掘金客户端加载生成的脚本进行回测"
        }
    }
    
    return result


def _display_backtest_results(result: Dict[str, Any]) -> None:
    """显示回测结果"""
    
    st.markdown("### 📊 回测包生成结果")
    
    if result.get("api_status", {}).get("status") != "fallback":
        # API模式：显示完整的回测包信息
        st.success("✅ 回测包生成成功！")
        
        # 显示文件信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"📄 配置文件: {result.get('config_path', 'N/A')}")
        
        with col2:
            st.info(f"🐍 回测脚本: {result.get('script_path', 'N/A')}")
        
        # 显示API状态
        api_status = result.get("api_status", {})
        st.info(f"🔧 API状态: {api_status.get('status', 'unknown')}, "
                f"配置文件: {api_status.get('config_files_count', 0)}个, "
                f"脚本文件: {api_status.get('script_files_count', 0)}个")
        
    else:
        # 备用模式：显示基础信息
        st.warning("⚠️ 使用备用模式生成回测脚本")
        st.info(f"🐍 回测脚本: {result.get('script_path', 'N/A')}")
    
    # 显示操作说明
    with st.expander("📋 如何运行回测"):
        st.markdown("""
        1. **打开东财掘金客户端**
        2. **加载主策略脚本**: 在客户端中打开项目根目录下的`main.py`
        3. **配置API Token**: 确保已在`token_config.py`中配置好有效的API token
        4. **运行回测**: 执行`main.py`开始回测
        5. **查看结果**: 回测完成后查看详细报告
        
        💡 **温馨提示**: 
        - 确保已安装东财掘金Python SDK
        - 需要有有效的API token
        - 回测期间请保持网络连接
        - `main.py`会自动从固定配置文件读取策略参数
        - 每次点击回测按钮都会更新固定配置文件
        """)
    
    # 显示快速操作按钮
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 打开脚本目录"):
            import subprocess
            try:
                script_path = result.get("script_path")
                if script_path and script_path != "API不可用，使用备用方案":
                    script_dir = os.path.dirname(script_path)
                    subprocess.Popen(f'explorer "{script_dir}"')
                    st.success("已打开脚本所在目录")
                else:
                    st.warning("无法确定脚本路径")
            except Exception as e:
                st.error(f"无法打开目录: {e}")
    
    with col2:
        if st.button("📄 查看脚本内容"):
            try:
                script_path = result.get("script_path")
                if script_path and script_path != "API不可用，使用备用方案":
                    with open(script_path, 'r', encoding='utf-8') as f:
                        script_content = f.read()
                    st.code(script_content, language="python")
                else:
                    st.warning("无法读取脚本内容")
            except Exception as e:
                st.error(f"无法读取脚本: {e}")
    
    # 显示高级功能
    with st.expander("🔧 高级功能"):
        st.markdown("""
        ### 批量回测功能
        - **多策略对比**: 可以同时回测多个策略配置
        - **参数优化**: 自动测试不同参数组合
        - **结果分析**: 生成详细的回测报告
        
        ### 自动化功能
        - **定时回测**: 定期自动执行回测
        - **结果推送**: 回测结果自动发送到邮箱
        - **性能监控**: 实时监控策略表现
        
        💡 **开发中功能**: 这些功能将在后续版本中逐步实现
        """)


def _show_backtest_help() -> None:
    """显示回测帮助信息"""
    
    st.markdown("### 📚 回测帮助")
    
    st.markdown("""
    #### 🎯 什么是回测？
    回测是通过历史数据验证策略有效性的过程。系统会模拟在历史期间执行您的策略，评估其表现。
    
    #### ⚙️ 参数说明
    - **回测天数**: 选择回测的时间范围，建议选择60-180天以获得更可靠的测试结果
    - **初始资金**: 回测时使用的起始资金，会影响仓位计算和收益率计算
    - **回测股票数量**: 选择排名前几的股票进行回测，建议1-3只获得更精准的测试
    
    #### 🚀 如何使用回测结果？
    1. 回测完成后会生成Python脚本
    2. 在东财掘金客户端中打开该脚本
    3. 配置您的API token
    4. 运行脚本开始回测
    5. 查看详细的回测报告和指标
    
    #### 💡 注意事项
    - 确保已安装东财掘金Python SDK
    - 需要有有效的API token
    - 回测期间请保持网络连接稳定
    - 回测结果仅供参考，不构成投资建议
    """)


def display_backtest_quick_start() -> None:
    """显示快速开始回测的选项"""
    
    st.markdown("---")
    st.subheader("⚡ 快速回测")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📈 测试默认策略", use_container_width=True):
            st.info("即将开发默认策略测试功能")
    
    with col2:
        if st.button("🔄 对比多个配置", use_container_width=True):
            st.info("即将开发多配置对比功能")