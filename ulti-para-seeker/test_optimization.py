#!/usr/bin/env python
# coding=utf-8
"""
参数优化测试脚本
用于验证参数优化流程是否正常工作
"""

import os
import sys
import json
import tempfile
import datetime
from parameter_optimizer import ParameterOptimizer

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_parameter_optimization():
    """测试参数优化流程"""
    print("="*60)
    print("🎯 测试参数优化流程")
    print("="*60)
    
    # 创建优化器实例
    optimizer = ParameterOptimizer()
    
    # 生成测试蓝图
    print("\n1. 生成参数蓝图...")
    blueprint_path = optimizer.generate_blueprint(test_mode=True, max_sub_combinations=1)
    print(f"✅ 蓝图生成成功: {blueprint_path}")
    
    # 加载蓝图
    blueprint = optimizer.load_blueprint(blueprint_path)
    print(f"\n2. 蓝图信息:")
    print(f"   - 总组合数: {blueprint['total_combinations']}")
    print(f"   - 版本: {blueprint['version']}")
    print(f"   - 生成时间: {blueprint['generated_at']}")
    
    # 获取第一个参数组合
    if blueprint['total_combinations'] > 0:
        first_combo = blueprint['combinations'][0]
        print(f"\n3. 第一个参数组合:")
        print(f"   - ID: {first_combo['id']}")
        print(f"   - 状态: {first_combo['status']}")
        print(f"   - 参数: {json.dumps(first_combo['params'], ensure_ascii=False, indent=2)}")
        
        # 测试回测运行
        print("\n4. 测试回测运行...")
        try:
            result = optimizer.run_backtest(first_combo['params'])
            print(f"✅ 回测运行成功")
            print(f"   - 总收益率: {result.get('total_return', 0.0)}%")
            print(f"   - 最大回撤: {result.get('max_drawdown', 0.0)}%")
            print(f"   - 年化收益率: {result.get('annual_return', 0.0)}%")
            return True
        except Exception as e:
            print(f"❌ 回测运行失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("\n❌ 蓝图中没有参数组合")
        return False

if __name__ == "__main__":
    test_parameter_optimization()
