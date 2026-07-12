import streamlit as st
import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, List

# 添加项目根目录到Python路径，确保可以正确导入utils模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 注入自定义CSS样式（不使用st.set_page_config，因为全局页面配置已在Home.py设置）
def inject_custom_css():
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
    [data-testid="stSidebar"] {
        width: 428px !important;
        min-width: 428px !important;
        max-width: 428px !important;
    }
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
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

# 导入各模块
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
from strategy_controller.utils.log_terminal import start_log_terminal
# 启动后台终端日志窗口（首次启动时弹出独立终端窗口）
start_log_terminal()


def render_strategy_controller_page():
    """主函数 - 整合所有模块"""
    inject_custom_css()
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
        
        # 执行按钮 - 异步执行策略，主线程轮询刷新状态
        is_running = st.session_state.get('strategy_running', False)
        if st.button("🚀 开始选股", type="primary", use_container_width=True, disabled=is_running):
            # 设置运行状态
            st.session_state.strategy_running = True
            st.session_state.current_progress = 0
            st.session_state.status_message = "正在初始化选股器..."
            st.session_state.strategy_error = None
            
            # 捕获当前配置到局部变量
            _strategy_type = st.session_state.get('strategy_type', "多维综合策略 (KDJ+知行趋势+深V信号)")
            _weights_config = st.session_state.get('weights_config', {})
            _screening_params = st.session_state.get('screening_params', {})
            _sub_weights_config = st.session_state.get('sub_weights_config', None)
            
            # 启动异步线程执行策略
            def run_strategy_async():
                try:
                    logger.info(f"开始执行策略: {_strategy_type}")
                    logger.info(f"股票池类型: {_screening_params.get('stock_pool_type', '全量A股')}")
                    
                    def update_progress(progress):
                        st.session_state.current_progress = progress * 100
                        logger.info(f"进度: {int(progress * 100)}%")
                    
                    def update_status(message):
                        st.session_state.status_message = message
                        logger.info(message)
                    
                    results = run_strategy(
                        _strategy_type,
                        _weights_config,
                        _screening_params,
                        progress_callback=update_progress,
                        status_callback=update_status,
                        sub_weights_config=_sub_weights_config
                    )
                    
                    st.session_state.strategy_results = results if results else []
                    st.session_state.last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logger.success(f"策略执行完成，结果数量: {len(results) if results else 0}")
                    
                except Exception as e:
                    error_msg = str(e)
                    st.session_state.strategy_error = error_msg
                    
                    friendly_error_msg = "策略执行失败"
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
                    
                    logger.error(f"策略执行失败: {friendly_error_msg} ({error_msg})")
                finally:
                    st.session_state.strategy_running = False
            
            threading.Thread(target=run_strategy_async, daemon=True).start()
            
            # 立即触发重绘，进入运行中状态
            st.rerun()
        
        # 保存报告按钮
        if st.session_state.strategy_results and not st.session_state.get('strategy_running', False):
            if st.button("💾 保存报告", use_container_width=True):
                save_report(
                    st.session_state.strategy_results,
                    strategy_type,
                    st.session_state.weights_config,
                    screening_params
                )
    
    # 主内容区域
    if st.session_state.get('strategy_running', False):
        # 策略运行中 - 显示进度条和状态消息
        status_msg = st.session_state.get('status_message', '正在执行中...')
        st.info(f"⏳ {status_msg}")
        
        # 进度条
        progress = st.session_state.get('current_progress', 0) / 100
        st.progress(min(progress, 1.0), text=f"进度: {int(min(progress, 1.0) * 100)}%")
        
        st.warning("📺 详细实时日志请查看启动项目的终端窗口")
        
        # 轮询刷新：每1.5秒自动刷新一次页面以更新进度
        time.sleep(1.5)
        st.rerun()
    
    elif st.session_state.get('strategy_error'):
        # 策略执行失败
        error = st.session_state.strategy_error
        friendly_msg = "策略执行失败"
        if "token" in error.lower() or "api" in error.lower():
            friendly_msg = "API连接失败，请检查Token配置是否正确"
        elif "network" in error.lower() or "connection" in error.lower():
            friendly_msg = "网络连接失败，请检查网络状态"
        elif "gm" in error.lower() or "juejin" in error.lower():
            friendly_msg = "东财掘金终端连接失败，请确保终端已启动"
        elif "timeout" in error.lower():
            friendly_msg = "请求超时，请稍后重试"
        st.error(f"❌ {friendly_msg}")
        st.session_state.strategy_error = None
    
    elif st.session_state.strategy_results:
        # 策略执行完成 - 展示结果
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
        # 初始状态 - 显示使用说明
        st.info("💡 请先在左侧配置策略参数，然后点击『开始选股』按钮")
        st.success("📺 实时日志输出在启动项目的终端窗口中，请保持该终端可见")
        
        # 显示历史报告
        try:
            report_files = [f for f in os.listdir('reports') if f.startswith('strategy_report_')]
            if report_files:
                st.sidebar.info(f"📁 历史报告: {len(report_files)} 个")
        except:
            pass


if __name__ == "__main__":
    render_strategy_controller_page()