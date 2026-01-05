#!/usr/bin/env python
# coding=utf-8
"""
回测执行模块 - 统一回测引擎的包装器
用于兼容参数优化器的调用，实际使用strategy_engine中的统一回测引擎
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any
# 移除gm.api的全局导入，避免全局状态问题

# 添加项目根目录到sys.path，确保能找到统一的回测引擎
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入统一的回测引擎
try:
    from strategy_engine.backtest_runner import BacktestRunner as UnifiedBacktestRunner
    from strategy_engine.backtest_runner import run_backtest as unified_run_backtest
except ImportError as e:
    print(f"从strategy_engine.backtest_runner导入失败: {e}")
    # 尝试直接导入
    import sys
    sys.path.append(os.path.join(project_root, 'strategy_engine'))
    from backtest_runner import BacktestRunner as UnifiedBacktestRunner
    from backtest_runner import run_backtest as unified_run_backtest


class OptimizerBacktestRunner(UnifiedBacktestRunner):
    """
    优化器回测执行器 - 继承自统一回测引擎，添加优化器专属功能
    """
    
    def __init__(self, strategy_params=None, generate_charts=False):
        """
        初始化回测执行器
        
        Args:
            strategy_params: 策略参数配置对象
            generate_charts: 是否生成图表，参数优化时默认不生成
        """
        # 调用统一回测引擎的初始化方法，禁用图表生成
        super().__init__(strategy_params=strategy_params, generate_charts=generate_charts)
        print(f"🔄 使用统一回测引擎，图表生成: {'开启' if generate_charts else '关闭'}")


# 导出优化器专用的回测函数
def run_optimizer_backtest(config: Dict[str, Any] = None, config_path: str = None, generate_charts=False):
    """
    运行回测的主函数 - 统一回测引擎的包装器
    
    Args:
        config: 回测配置参数
        config_path: 前端生成的JSON配置文件路径
        generate_charts: 是否生成图表，参数优化时默认不生成
    """
    # 调用统一回测引擎的run_backtest函数，指定为循环回测模式
    return unified_run_backtest(config=config, config_path=config_path, generate_charts=generate_charts, is_cycle_mode=True)
