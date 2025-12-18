#!/usr/bin/env python
# coding=utf-8
"""
z哥选股策略回测系统 - 解耦重构版
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
    # 导入参数配置系统
    from config.strategy_params import get_current_params
    
    # 获取当前策略参数（从配置文件加载的）
    strategy_params = get_current_params()
    
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
    
    print("🎯 z哥选股策略回测系统 - 解耦重构版")
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
    parser = argparse.ArgumentParser(description='z哥选股策略回测系统')
    parser.add_argument('-c', '--config', type=str, help='指定前端生成的JSON配置文件路径')
    
    # 解析命令行参数
    args, _ = parser.parse_known_args()
    
    # 检查是否是测试模式
    is_test_mode = len(sys.argv) > 1 and sys.argv[1] == 'test'
    
    if is_test_mode:
        quick_test()
    else:
        # 恢复原始的sys.argv，避免与gm.api的run()函数冲突
        sys.argv = original_argv
        
        # 获取固定配置文件路径
        fixed_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "current_backtest_config.json")
        
        # 确定要使用的配置文件路径
        config_path = args.config if args.config else fixed_config_path
        
        # 使用统一的回测执行函数
        run_backtest(config_path=config_path)


# 快速测试函数
def quick_test():
    """快速测试函数 - 用于验证模块功能"""
    try:
        from strategy_engine import ConfigManager, ReportGenerator
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
        
        print("\n🎉 所有模块测试通过！解耦重构成功！")
        
    except Exception as e:
        print(f"❌ 模块测试失败: {e}")


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'test':
    # 运行测试模式
    quick_test()