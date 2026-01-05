#!/usr/bin/env python
# coding=utf-8

from core.optimizer_manager import OptimizerManager

# 创建优化器管理器实例
manager = OptimizerManager()

# 生成蓝图
print("=== 生成蓝图 ===")
blueprint_path = manager.generate_blueprint(
    test_mode=True,
    max_sub_combinations=3,
    algorithm='粒子群算法',
    force_new_blueprint=True
)

import json
import os

# 读取蓝图文件
with open(blueprint_path, 'r', encoding='utf-8') as f:
    blueprint = json.load(f)

print(f'初始蓝图包含的组合数: {len(blueprint["combinations"])}')

# 更新第一个组合的状态
print("\n=== 更新组合状态 ===")
updated_blueprint = manager.update_combination_status(blueprint, 1, 'running')

# 保存更新后的蓝图
print("\n=== 保存蓝图 ===")
saved_path = manager.save_blueprint(updated_blueprint, 'test_blueprint.json')
print(f'蓝图保存路径: {saved_path}')

# 验证保存是否成功
with open(saved_path, 'r', encoding='utf-8') as f:
    saved_blueprint = json.load(f)

print(f'保存的蓝图包含的组合数: {len(saved_blueprint["combinations"])}')
print(f'第一个组合的状态: {saved_blueprint["combinations"][0]["status"]}')

# 清理测试文件
os.remove(saved_path)
print(f'\n测试文件已清理: {saved_path}')