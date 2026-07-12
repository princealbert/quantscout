#!/usr/bin/env python
# coding=utf-8
"""
QuantScout选股策略回测系统 - 解耦重构版
基于模块化设计的回测系统，职责清晰，易于维护
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目路径，确保可以导入现有模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gm.api import *
from strategy_engine import BacktestRunner, run_backtest
from strategy_engine.config_manager import FrontendConfigLoader


def init(context):
    """策略初始化 - 使用解耦后的策略引擎"""
    # 直接从gm.api的context中获取参数，避免使用全局变量和文件
    # 回测引擎会将参数传递到context中
    strategy_params = getattr(context, 'strategy_params', None)
    
    # 如果context中没有参数，才从配置文件加载（兼容旧模式）
    if not strategy_params:
        try:
            from config.strategy_params import StrategyParams, load_params_from_file
            
            # 尝试从文件加载参数
            file_params = load_params_from_file()
            if file_params:
                strategy_params = file_params
            else:
                # 使用默认参数
                strategy_params = StrategyParams()
        except Exception as e:
            print(f"加载参数失败，使用默认参数: {e}")
            from config.strategy_params import StrategyParams
            strategy_params = StrategyParams()
    
    # 创建回测执行器 - 传递配置参数
    context.runner = BacktestRunner(strategy_params=strategy_params)
    
    # 调用执行器的初始化方法
    context.runner.init(context)


def daily_strategy(context):
    """每日策略执行 - 使用解耦后的策略引擎"""
    context.runner.daily_strategy(context)


def on_backtest_finished(context, indicator):
    """回测结束回调 - 使用解耦后的策略引擎"""
    context.runner.on_backtest_finished(context, indicator)


def on_order_status(context, order):
    """订单状态变化回调 - 使用解耦后的策略引擎"""
    context.runner.on_order_status(context, order)


def on_execution_report(context, execrpt):
    """委托执行回报回调 - 使用解耦后的策略引擎"""
    context.runner.on_execution_report(context, execrpt)


# 快速测试函数
def quick_test():
    """快速测试函数 - 用于验证模块功能"""
    try:
        from strategy_engine.config_manager import ConfigManager
        from strategy_engine.report_generator import ReportGenerator
        from strategy_engine.strategy import BacktestStrategy
        
        print("\n🔧 模块功能测试:")
        
        # 测试配置管理
        config_manager = ConfigManager()
        config = config_manager.load_config()
        print("✅ 配置管理模块: 正常")
        
        # 测试策略模块
        strategy = BacktestStrategy()
        print("✅ 策略模块: 正常")
        
        # 测试报告生成
        report_generator = ReportGenerator()
        print("✅ 报告生成模块: 正常")
        
        # 测试统一回测引擎
        from strategy_engine.backtest_runner import BacktestRunner
        print("✅ 统一回测引擎: 正常")
        
        print("\n🎉 所有模块测试通过！解耦重构成功！")
        
    except Exception as e:
        print(f"❌ 模块测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    """
    策略回测主函数 - 解耦重构版
    
    使用模块化设计，职责清晰：
    - strategy_engine.strategy: 纯策略逻辑
    - strategy_engine.backtest_runner: 回测执行管理  
    - strategy_engine.report_generator: 报告生成
    - strategy_engine.config_manager: 配置管理
    
    参数说明:
    strategy_id: 策略ID，由系统生成
    filename: 文件名，请与本文件名保持一致
    mode: 实时模式:MODE_LIVE 回测模式:MODE_BACKTEST
    token: 绑定计算机的ID，可在系统设置-密钥管理中生成
    backtest_start_time: 回测开始时间
    backtest_end_time: 回测结束时间
    backtest_adjust: 股票复权方式 不复权:ADJUST_NONE 前复权:ADJUST_PREV 后复权:ADJUST_POST
    backtest_initial_cash: 回测初始资金
    backtest_commission_ratio: 回测佣金比例
    backtest_slippage_ratio: 回测滑点比例
    """
    
    import argparse
    import sys
    import os
    
    print("🎯 QuantScout选股策略回测系统 - 解耦重构版")
    print("="*60)
    print("📁 模块化架构:")
    print("  - strategy.py: 纯策略逻辑实现")
    print("  - backtest_runner.py: 回测执行管理")  
    print("  - report_generator.py: 报告生成功能")
    print("  - config_manager.py: 配置管理")
    print("="*60)
    
    # 备份原始的sys.argv
    original_argv = sys.argv.copy()
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='QuantScout选股策略回测系统')
    parser.add_argument('-c', '--config', type=str, help='指定前端生成的JSON配置文件路径')
    parser.add_argument('--params-file', type=str, help='指定策略参数文件路径（用于并行回测）')
    
    # 解析命令行参数
    args, _ = parser.parse_known_args()
    
    # 检查是否是测试模式
    is_test_mode = len(sys.argv) > 1 and sys.argv[1] == 'test'
    
    if is_test_mode:
        quick_test()
    else:
        # 恢复原始的sys.argv，避免与gm.api的run()函数冲突
        sys.argv = original_argv
        
        # 打印当前进程信息和环境变量（用于调试）
        print(f"[MAIN] 进程ID: {os.getpid()}")
        print(f"[MAIN] 当前工作目录: {os.getcwd()}")
        print(f"[MAIN] BACKTEST_PARAMS_FILE环境变量: {os.environ.get('BACKTEST_PARAMS_FILE')}")
        
        # 优先从--params-file参数获取配置文件路径（用于并行回测）
        params_file_path = args.params_file
        
        # 其次从环境变量获取配置文件路径
        env_config_path = os.environ.get('BACKTEST_PARAMS_FILE')
        
        # 获取固定配置文件路径
        fixed_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "current_backtest_config.json")
        
        # 确定要使用的配置文件路径：--params-file > -c/--config > 环境变量 > 固定路径
        config_path = params_file_path if params_file_path else args.config if args.config else env_config_path if env_config_path else fixed_config_path
        
        print(f"[MAIN] 最终使用的配置文件: {config_path}")
        
        # 使用统一的回测执行函数
        report_data = run_backtest(config_path=config_path)
        
        # 检查是否需要将结果保存到指定文件
        result_file_path = os.environ.get('BACKTEST_RESULT_FILE')
        if result_file_path:
            print(f"[MAIN] 检测到BACKTEST_RESULT_FILE环境变量，准备保存结果到: {result_file_path}")
            try:
                import json
                with open(result_file_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
                print(f"[MAIN] ✅ 回测结果已成功保存到: {result_file_path}")
            except Exception as e:
                print(f"[MAIN] ❌ 保存回测结果失败: {e}")
                import traceback
                traceback.print_exc()