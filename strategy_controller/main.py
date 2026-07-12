import streamlit as st
import os
import sys
from datetime import datetime
from typing import Dict, List

# 添加项目根目录到Python路径，确保可以正确导入utils模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入各模块
from strategy_controller.ui.header_component import setup_page, display_header
from strategy_controller.ui.sidebar_component import display_strategy_selector, display_screening_parameters
from strategy_controller.ui.weight_config import display_weight_configuration, get_weights_from_session, get_sub_weights_from_session
from strategy_controller.ui.config_manager import display_config_manager
from strategy_controller.ui.backtest_component import display_backtest_button
from strategy_controller.ui.optimization_component import display_configuration_panel
from strategy_controller.ui.token_component import display_token_config
from strategy_controller.presentation.data_table import display_stock_results
from strategy_controller.business.strategy_executor import run_strategy
from strategy_controller.business.report_generator import save_report
from strategy_controller.utils.logger import logger


def main():
    """主函数 - 整合所有模块"""
    setup_page()
    display_header()
    
    # 初始化session state
    if 'strategy_results' not in st.session_state:
        st.session_state.strategy_results = []
    if 'last_run_time' not in st.session_state:
        st.session_state.last_run_time = None
    if 'weights_config' not in st.session_state:
        st.session_state.weights_config = {
            'kdj_j': 25,
            'trend': 25,
            'deepv': 10,
            'volume': 8,
            'fundamental': 8,
            'position': 4,
            'risk_reward': 20
        }
    if 'screening_params' not in st.session_state:
        st.session_state.screening_params = {'max_results': 30, 'skip_st': True, 'test_mode': False, 'batch_size': 1000, 'max_workers': 6, 'stock_pool_type': '全量A股'}
    if 'strategy_type' not in st.session_state:
        st.session_state.strategy_type = "多维综合策略 (KDJ+知行趋势+深V信号)"
    
    # 侧边栏控制面板
    with st.sidebar:
        st.title("🎛️ 控制面板")
        
        # Token配置（放在最前面，因为会影响所有功能）
        display_token_config()
        
        # 配置管理
        st.markdown("---")
        current_weights = get_weights_from_session()
        current_sub_weights = get_sub_weights_from_session()
        display_config_manager(current_weights, current_sub_weights)
        
        st.markdown("---")
        
        # 策略选择
        strategy_type = display_strategy_selector()
        st.session_state.strategy_type = strategy_type  # 实时保存到session state
        
        # 权重配置 - 始终显示权重配置组件，但根据配置加载状态设置初始值
        weights_config = display_weight_configuration(strategy_type)
        # print(f"[MAIN] 当前权重配置: {weights_config}")
        
        st.session_state.weights_config = weights_config  # 实时保存到session state
        
        # 配置面板（已移除优化器功能）
        if strategy_type == "多维综合策略 (KDJ+知行趋势+深V信号)":
            display_configuration_panel()
        
        # 筛选参数
        screening_params = display_screening_parameters()
        st.session_state.screening_params = screening_params  # 实时保存到session state
        
        # 调试信息：显示当前session state中的参数
        if st.checkbox("显示调试信息", value=False):
            st.write("当前Session State中的参数:")
            st.write(f"策略类型: {st.session_state.strategy_type}")
            st.write(f"权重配置: {st.session_state.weights_config}")
            st.write(f"筛选参数: {st.session_state.screening_params}")
        
        # 调试信息：显示当前策略配置
        if st.checkbox("显示详细调试信息", value=False):
            st.write("当前策略配置详情:")
            st.write(f"策略类型: {st.session_state.get('strategy_type', '未设置')}")
            st.write(f"权重配置: {st.session_state.get('weights_config', {})}")
            st.write(f"子权重配置: {st.session_state.get('sub_weights_config', {})}")
            st.write(f"是否优化: {st.session_state.get('is_optimized', False)}")
            st.write(f"优化类型: {st.session_state.get('active_strategy_type', '未设置')}")
            st.write(f"市场状况: {st.session_state.get('active_market_condition', '未设置')}")
            st.write(f"优化配置: {st.session_state.get('optimization_config', {})}")
        
        # 执行按钮
        if st.button("🚀 开始选股", type="primary", use_container_width=True):
            # 设置策略运行状态
            st.session_state.strategy_running = True
            st.session_state.strategy_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.current_progress = 0
            st.session_state.status_message = "正在初始化选股器..."
            st.session_state.strategy_thread_started = False
            
            # 记录详细的策略配置信息
            logger.info(f"开始选股时的策略配置: 策略类型={st.session_state.get('strategy_type', '未设置')}, 权重配置={st.session_state.get('weights_config', {})}")
            
            # 立即显示进度条和状态
            st.rerun()
        
        # 保存报告按钮
        if st.session_state.strategy_results:
            if st.button("💾 保存报告", use_container_width=True):
                save_report(
                    st.session_state.strategy_results,
                    strategy_type,
                    st.session_state.weights_config,
                    screening_params
                )
    
    # 主内容区域
    if st.session_state.strategy_results:
        if st.session_state.last_run_time:
            st.info(f"📅 上次筛选时间: {st.session_state.last_run_time}")
        
        display_stock_results(st.session_state.strategy_results, strategy_type)
        
        # 显示回测按钮
        display_backtest_button(
            st.session_state.strategy_results,
            strategy_type,
            st.session_state.weights_config,
            st.session_state.get('sub_weights_config', None)
        )
    else:
        # 显示使用说明
        st.info("💡 请先在左侧配置策略参数，然后点击『开始选股』按钮")
        
        # 显示历史报告
        try:
            report_files = [f for f in os.listdir('reports') if f.startswith('strategy_report_')]
            if report_files:
                st.sidebar.info(f"📁 历史报告: {len(report_files)} 个")
        except:
            pass
    
    # 同步执行策略逻辑
    if st.session_state.get('strategy_running', False):
        # 创建进度条和状态指示器
        progress_bar = st.progress(st.session_state.get('current_progress', 0))
        status_text = st.text(st.session_state.get('status_message', '正在运行...'))
        
        # 在函数作用域内定义回调函数
        def update_progress(progress):
            st.session_state.current_progress = progress * 100  # 转换为百分比用于显示
            progress_bar.progress(progress)  # Streamlit需要0.0-1.0的值
        
        def update_status(message):
            st.session_state.status_message = message
            status_text.text(message)
        
        # 同步执行策略
        try:
            strategy_type = st.session_state.get('strategy_type', "多维综合策略 (KDJ+知行趋势+深V信号)")
            weights_config = st.session_state.get('weights_config', {})
            screening_params = st.session_state.get('screening_params', {})
            sub_weights_config = st.session_state.get('sub_weights_config', None)
            
            logger.info(f"开始执行策略: {strategy_type}")
            logger.info(f"股票池类型: {screening_params.get('stock_pool_type', '全量A股')}")
            
            # 记录传递给策略执行器的参数
            logger.info(f"传递给策略执行器的参数: 策略类型={strategy_type}, 权重配置={weights_config}, 子权重配置={sub_weights_config}")
            
            results = run_strategy(
                strategy_type,
                weights_config,
                screening_params,
                progress_callback=update_progress,
                status_callback=update_status,
                sub_weights_config=sub_weights_config
            )
                
            # 更新结果
            st.session_state.strategy_results = results
            st.session_state.last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.current_progress = 100
            st.session_state.status_message = f"筛选完成！共找到 {len(results) if results else 0} 只股票"
            st.session_state.strategy_running = False
            
            logger.info(f"策略执行完成，结果数量: {len(results) if results else 0}")
            
        except Exception as e:
            st.session_state.current_progress = 0
            error_msg = str(e)
            
            # 提供用户友好的错误提示
            friendly_error_msg = "策略执行失败"
            
            # 根据错误类型提供更具体的提示
            if "token" in error_msg.lower() or "api" in error_msg.lower():
                friendly_error_msg = "API连接失败，请检查Token配置是否正确"
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                friendly_error_msg = "网络连接失败，请检查网络状态"
            elif "gm" in error_msg.lower() or "juejin" in error_msg.lower():
                friendly_error_msg = "东财掘金终端连接失败，请确保终端已启动"
            elif "timeout" in error_msg.lower():
                friendly_error_msg = "请求超时，请稍后重试"
            elif "permission" in error_msg.lower() or "auth" in error_msg.lower():
                friendly_error_msg = "权限不足，请检查Token权限"
            
            st.session_state.status_message = f"筛选失败: {friendly_error_msg}"
            st.session_state.strategy_running = False
            st.error(f"{friendly_error_msg}\n\n详细错误: {error_msg}")
            logger.error(f"策略执行失败: {error_msg}")
        
        # 触发重绘
        st.rerun()


if __name__ == "__main__":
    main()