#!/usr/bin/env python
# coding=utf-8

from core.optimizer_manager import OptimizerManager

# 创建优化器管理器实例
manager = OptimizerManager()

# 第一次生成蓝图，生成5个组合
print("=== 第一次生成蓝图 ===")
blueprint_path = manager.generate_blueprint(
    test_mode=True,
    max_sub_combinations=5,
    algorithm='粒子群算法'
)

import json
import os

with open(blueprint_path, 'r', encoding='utf-8') as f:
    blueprint = json.load(f)
print(f'蓝图中包含的组合数: {len(blueprint["combinations"])}')

# 第二次生成蓝图，测试增量更新
print("\n=== 第二次生成蓝图（增量更新） ===")
blueprint_path = manager.generate_blueprint(
    test_mode=True,
    max_sub_combinations=8,  # 增加到8个组合
    algorithm='粒子群算法'
)

with open(blueprint_path, 'r', encoding='utf-8') as f:
    blueprint = json.load(f)
print(f'蓝图中包含的组合数: {len(blueprint["combinations"])}')
print(f'蓝图中设置的最大组合数: {blueprint["max_sub_combinations"]}')