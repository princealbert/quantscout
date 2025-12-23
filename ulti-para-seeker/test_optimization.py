#!/usr/bin/env python3
"""
测试参数优化模块的修改效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parameter_optimizer import ParameterOptimizer

def test_deepv_weight_zero():
    """测试deepv权重是否为零"""
    print("=== 测试 deepv 权重设置 ===")
    opt = ParameterOptimizer()
    params = opt.generate_parameter_combinations(test_mode=True)
    
    print(f"生成的参数组合数量: {len(params)}")
    if not params:
        print("错误：未生成任何参数组合")
        return False
    
    # 检查deepv权重
    has_zero_deepv = all(param['weights_config'].get('deepv', 0) == 0 for param in params)
    print(f"所有组合中的deepv权重是否为零: {has_zero_deepv}")
    
    if not has_zero_deepv:
        print("错误：存在deepv权重不为零的组合")
        return False
    
    # 检查deepv子权重（如果存在）
    has_deepv_subweight = any('deepv' in param.get('sub_weights_config', {}) for param in params)
    print(f"组合中是否包含deepv子权重: {has_deepv_subweight}")
    
    if has_deepv_subweight:
        print("错误：存在包含deepv子权重的组合")
        return False
    
    print("✓ deepv权重测试通过")
    return True

def test_parameter_ranges():
    """测试参数范围是否缩小"""
    print("\n=== 测试参数范围 ===")
    opt = ParameterOptimizer()
    ranges = opt.define_parameter_ranges()
    
    # 检查止盈范围
    stop_profit = ranges['stop_profit_ratio']
    print(f"止盈比例范围: {[round(p*100, 1) for p in stop_profit]}%")
    if min(stop_profit) != 0.03 or max(stop_profit) != 0.15 or len(stop_profit) != 7:
        print("错误：止盈比例范围不符合预期（3%-15%，步长2%）")
        return False
    
    # 检查止损范围
    stop_loss = ranges['stop_loss_ratio']
    print(f"止损比例范围: {[round(l*100, 1) for l in stop_loss]}%")
    if min(stop_loss) != -0.05 or max(stop_loss) != -0.01 or len(stop_loss) != 5:
        print("错误：止损比例范围不符合预期（-5%--1%，步长1%）")
        return False
    
    print("✓ 参数范围测试通过")
    return True

def test_combination_validation():
    """测试参数组合验证逻辑"""
    print("\n=== 测试参数组合验证 ===")
    opt = ParameterOptimizer()
    
    # 测试有效的组合（deepv权重为零）
    valid_comb = {
        'stop_profit_ratio': 0.05,
        'stop_loss_ratio': -0.03,
        'weights_config': {
            'kdj_j': 20,
            'trend': 20,
            'volume': 15,
            'fundamental': 15,
            'position': 10,
            'risk_reward': 20,
            'deepv': 0
        },
        'sub_weights_config': {
            'kdj_j': {'sub_weights': {'j_0_20': 50, 'j_-10_0': 50}},
            'trend': {'sub_weights': {'up_trend': 60, 'volume_price_rise': 40}},
            'volume': {'sub_weights': {'big_volume': 70, 'volume_anomaly': 30}},
            'fundamental': {'sub_weights': {'pe_positive': 50, 'pe_low': 50}},
            'position': {'sub_weights': {'above_white': 100}},
            'risk_reward': {'sub_weights': {'risk_ratio': 40, 'reward_ratio': 60}}
        }
    }
    
    is_valid = opt._validate_parameter_combination(valid_comb)
    print(f"有效组合验证结果: {is_valid}")
    
    if not is_valid:
        print("错误：有效的组合被拒绝")
        return False
    
    print("✓ 参数组合验证测试通过")
    return True

def main():
    """主测试函数"""
    print("开始测试参数优化模块的修改...")
    
    test_results = []
    test_results.append(('deepv权重测试', test_deepv_weight_zero()))
    test_results.append(('参数范围测试', test_parameter_ranges()))
    test_results.append(('组合验证测试', test_combination_validation()))
    
    print("\n=== 测试结果汇总 ===")
    passed = sum(1 for name, result in test_results if result)
    failed = sum(1 for name, result in test_results if not result)
    
    for name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总测试数: {len(test_results)}, 通过: {passed}, 失败: {failed}")
    
    return passed == len(test_results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
