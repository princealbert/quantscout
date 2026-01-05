#!/usr/bin/env python
# coding=utf-8

from core.optimizer_manager import OptimizerManager

# 创建优化器管理器实例
manager = OptimizerManager()

# 生成蓝图
blueprint_path = manager.generate_blueprint(
    test_mode=True,
    max_sub_combinations=5,
    algorithm='粒子群算法'
)

print(f'生成的蓝图路径: {blueprint_path}')

# 读取蓝图文件并检查组合数
import json
import os

if os.path.exists(blueprint_path):
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
    print(f'蓝图中包含的组合数: {len(blueprint["combinations"])}')
    print(f'蓝图中设置的最大组合数: {blueprint["max_sub_combinations"]}')
else:
    print('蓝图文件未生成')
