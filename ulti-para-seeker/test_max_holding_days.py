#!/usr/bin/env python
# coding=utf-8
"""
测试最大持仓天数参数是否正确生成
"""

from algorithms.brute_force import BruteForceOptimizer
from algorithms.genetic import GeneticOptimizer
from algorithms.particle_swarm import ParticleSwarmOptimizer

def test_brute_force():
    """测试暴力搜索算法"""
    print("\n=== 测试暴力搜索算法 ===")
    optimizer = BruteForceOptimizer()
    params = optimizer.generate_parameter_combinations(
        test_mode=True,
        max_holding_days_min=1,
        max_holding_days_max=3,
        max_holding_days_step=1
    )
    print(f"参数组合数量: {len(params)}")
    if params:
        print(f"第一个组合: {params[0]}")
        print(f"是否包含max_holding_days: {'max_holding_days' in params[0]}")
        if 'max_holding_days' in params[0]:
            print(f"max_holding_days值: {params[0]['max_holding_days']}")
    return bool(params and 'max_holding_days' in params[0])

def test_genetic():
    """测试遗传算法"""
    print("\n=== 测试遗传算法 ===")
    optimizer = GeneticOptimizer()
    params = optimizer.generate_parameter_combinations(
        test_mode=True,
        max_holding_days_min=1,
        max_holding_days_max=3,
        max_holding_days_step=1
    )
    print(f"参数组合数量: {len(params)}")
    if params:
        print(f"第一个组合: {params[0]}")
        print(f"是否包含max_holding_days: {'max_holding_days' in params[0]}")
        if 'max_holding_days' in params[0]:
            print(f"max_holding_days值: {params[0]['max_holding_days']}")
    return bool(params and 'max_holding_days' in params[0])

def test_particle_swarm():
    """测试粒子群算法"""
    print("\n=== 测试粒子群算法 ===")
    optimizer = ParticleSwarmOptimizer()
    params = optimizer.generate_parameter_combinations(
        test_mode=True,
        max_holding_days_min=1,
        max_holding_days_max=3,
        max_holding_days_step=1
    )
    print(f"参数组合数量: {len(params)}")
    if params:
        print(f"第一个组合: {params[0]}")
        print(f"是否包含max_holding_days: {'max_holding_days' in params[0]}")
        if 'max_holding_days' in params[0]:
            print(f"max_holding_days值: {params[0]['max_holding_days']}")
    return bool(params and 'max_holding_days' in params[0])

if __name__ == "__main__":
    print("开始测试最大持仓天数参数生成...")
    
    brute_force_result = test_brute_force()
    genetic_result = test_genetic()
    particle_swarm_result = test_particle_swarm()
    
    print("\n=== 测试结果 ===")
    print(f"暴力搜索算法: {'通过' if brute_force_result else '失败'}")
    print(f"遗传算法: {'通过' if genetic_result else '失败'}")
    print(f"粒子群算法: {'通过' if particle_swarm_result else '失败'}")
    
    if brute_force_result and genetic_result and particle_swarm_result:
        print("\n🎉 所有算法测试通过！")
    else:
        print("\n❌ 部分算法测试失败！")
