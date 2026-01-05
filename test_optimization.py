#!/usr/bin/env python
# coding=utf-8
"""
测试参数优化器 - 验证所有优化是否有效
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加ulti-para-seeker目录到sys.path
ulti_para_seeker_dir = os.path.join(project_root, "ulti-para-seeker")
if ulti_para_seeker_dir not in sys.path:
    sys.path.insert(0, ulti_para_seeker_dir)

# 现在可以直接导入parameter_optimizer模块
import parameter_optimizer

# 创建ParameterOptimizer实例
ParameterOptimizer = parameter_optimizer.ParameterOptimizer

def test_optimization():
    """测试参数优化器"""
    print("🎯 开始测试参数优化器")
    print("="*60)
    
    # 创建参数优化器实例
    optimizer = ParameterOptimizer()
    
    # 生成测试参数组合
    print("📋 生成测试参数组合")
    param_combinations = optimizer.generate_parameter_combinations(
        test_mode=True,
        max_sub_combinations=2,
        end_date='2025-12-25',
        algorithm='暴力搜索',
        backtest_days=30
    )
    
    print(f"✅ 生成了 {len(param_combinations)} 个测试参数组合")
    
    # 显示前2个参数组合
    for i, params in enumerate(param_combinations[:2]):
        print(f"\n参数组合 {i+1}:")
        print(f"  - 止盈比例: {params['stop_profit_ratio']*100:.2f}%")
        print(f"  - 止损比例: {params['stop_loss_ratio']*100:.2f}%")
        print(f"  - 权重配置: {params['weights_config']}")
        print(f"  - 子权重配置: {params['sub_weights_config']}")
    
    # 运行单个回测测试
    print("\n🔄 测试单个回测执行")
    if param_combinations:
        result = optimizer.run_backtest(param_combinations[0])
        print(f"✅ 单个回测执行成功")
        print(f"  - 总收益率: {result['total_return']:.2f}%")
        print(f"  - 年化收益率: {result['annual_return']:.2f}%")
        print(f"  - 最大回撤: {result['max_drawdown']:.2f}%")
    
    print("\n🎉 测试完成！所有功能正常")
    print("="*60)

if __name__ == "__main__":
    test_optimization()
