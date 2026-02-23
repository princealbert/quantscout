#!/usr/bin/env python
# coding=utf-8
"""
回测参数配置一致性验证测试
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入回测参数管理器
from strategy_controller.utils.backtest_params_manager import backtest_params_manager


def test_param_definitions():
    """
    测试参数定义的一致性
    """
    print("=== 测试参数定义的一致性 ===")
    
    # 获取默认参数
    default_params = backtest_params_manager.get_params()
    
    # 验证所有必要的参数都已定义
    required_params = [
        "backtest_days",
        "backtest_days_range",
        "initial_capital",
        "initial_capital_range",
        "max_stocks",
        "max_stocks_range",
        "stop_profit",
        "stop_profit_range",
        "stop_loss",
        "stop_loss_range",
        "end_date"
    ]
    
    missing_params = []
    for param in required_params:
        if param not in default_params:
            missing_params.append(param)
    
    if missing_params:
        print(f"❌ 缺少参数定义: {missing_params}")
        return False
    else:
        print("✅ 所有必要参数都已定义")
        return True


def test_param_validation():
    """
    测试参数验证逻辑的一致性
    """
    print("\n=== 测试参数验证逻辑的一致性 ===")
    
    # 测试有效参数
    valid_params = {
        "backtest_days": 90,
        "initial_capital": 100000,
        "max_stocks": 1,
        "stop_profit": 3.0,
        "stop_loss": -2.0,
        "end_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    if backtest_params_manager.validate_params(valid_params):
        print("✅ 有效参数验证通过")
    else:
        print("❌ 有效参数验证失败")
        return False
    
    # 测试无效参数
    invalid_params = {
        "backtest_days": 1000,  # 超出范围
        "initial_capital": 5000,  # 超出范围
        "max_stocks": 15,  # 超出范围
        "stop_profit": 0.5,  # 超出范围
        "stop_loss": -25.0,  # 超出范围
        "end_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    if not backtest_params_manager.validate_params(invalid_params):
        print("✅ 无效参数验证通过")
    else:
        print("❌ 无效参数验证失败")
        return False
    
    return True


def test_param_persistence():
    """
    测试参数配置的持久化功能
    """
    print("\n=== 测试参数配置的持久化功能 ===")
    
    # 创建测试参数
    test_params = {
        "backtest_days": 60,
        "initial_capital": 50000,
        "max_stocks": 3,
        "stop_profit": 5.0,
        "stop_loss": -3.0,
        "end_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    # 测试保存功能
    test_file = os.path.join(project_root, "test_backtest_params.json")
    try:
        if backtest_params_manager.save_params(test_params, test_file):
            print("✅ 参数保存成功")
        else:
            print("❌ 参数保存失败")
            return False
        
        # 测试加载功能
        loaded_params = backtest_params_manager.load_params(test_file)
        if loaded_params:
            print("✅ 参数加载成功")
            
            # 验证加载的参数与原始参数一致
            for key, value in test_params.items():
                if key in loaded_params and loaded_params[key] == value:
                    print(f"  ✅ {key}: {value}")
                else:
                    print(f"  ❌ {key}: 预期 {value}, 实际 {loaded_params.get(key)}")
                    return False
        else:
            print("❌ 参数加载失败")
            return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    return True


def test_param_ranges():
    """
    测试参数范围的一致性
    """
    print("\n=== 测试参数范围的一致性 ===")
    
    # 验证参数范围设置
    param_ranges = {
        "backtest_days": backtest_params_manager.get_param_range("backtest_days"),
        "initial_capital": backtest_params_manager.get_param_range("initial_capital"),
        "max_stocks": backtest_params_manager.get_param_range("max_stocks"),
        "stop_profit": backtest_params_manager.get_param_range("stop_profit"),
        "stop_loss": backtest_params_manager.get_param_range("stop_loss")
    }
    
    missing_ranges = []
    for param, range_config in param_ranges.items():
        if not range_config:
            missing_ranges.append(param)
        else:
            print(f"✅ {param} 范围设置: {range_config}")
    
    if missing_ranges:
        print(f"❌ 缺少参数范围设置: {missing_ranges}")
        return False
    else:
        return True


def main():
    """
    主测试函数
    """
    print("开始回测参数配置一致性验证测试...\n")
    
    # 运行所有测试
    tests = [
        test_param_definitions,
        test_param_validation,
        test_param_persistence,
        test_param_ranges
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # 汇总测试结果
    print("\n=== 测试结果汇总 ===")
    if all(results):
        print("🎉 所有测试通过！参数配置一致性验证成功。")
        return 0
    else:
        print("❌ 部分测试失败，请检查参数配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
