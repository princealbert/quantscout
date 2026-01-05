#!/usr/bin/env python
# coding=utf-8

from core.optimizer_manager import OptimizerManager

# 创建优化器管理器实例
manager = OptimizerManager()

# 第一步：使用粒子群算法生成5个组合
print("=== 第一步：使用粒子群算法生成5个组合 ===")
blueprint_path = manager.generate_blueprint(
    test_mode=True,
    max_sub_combinations=5,
    algorithm='粒子群算法',
    force_new_blueprint=True
)

import json
import os

# 读取蓝图文件
with open(blueprint_path, 'r', encoding='utf-8') as f:
    blueprint = json.load(f)

print(f'粒子群算法生成的蓝图包含的组合数: {len(blueprint["combinations"])}')
print(f'蓝图使用的算法: {blueprint["algorithm"]}')
print(f'蓝图的max_sub_combinations: {blueprint["max_sub_combinations"]}')

# 第二步：使用遗传算法生成5个组合（增量更新）
print("\n=== 第二步：使用遗传算法生成5个组合（增量更新） ===")
blueprint_path = manager.generate_blueprint(
    test_mode=True,
    max_sub_combinations=5,
    algorithm='遗传算法'
)

# 读取更新后的蓝图文件
with open(blueprint_path, 'r', encoding='utf-8') as f:
    blueprint = json.load(f)

print(f'遗传算法增量更新后蓝图包含的组合数: {len(blueprint["combinations"])}')
print(f'蓝图使用的算法: {blueprint["algorithm"]}')
print(f'蓝图的max_sub_combinations: {blueprint["max_sub_combinations"]}')

# 验证组合数是否为10
if len(blueprint['combinations']) == 10:
    print("\n✅ 测试通过！蓝图成功增量更新，包含了两种算法的10个组合")
else:
    print(f"\n❌ 测试失败！蓝图只包含了 {len(blueprint['combinations'])} 个组合，期望10个")

# 清理测试文件
os.remove(blueprint_path)
print(f'\n测试文件已清理: {blueprint_path}')