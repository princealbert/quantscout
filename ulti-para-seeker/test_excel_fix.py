#!/usr/bin/env python
# coding=utf-8
"""
测试Excel导出修复是否有效
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入参数优化器
from parameter_optimizer import ParameterOptimizer

def test_excel_export_fix():
    """测试Excel导出修复"""
    print("开始测试Excel导出修复...")
    
    # 创建参数优化器实例
    optimizer = ParameterOptimizer()
    
    # 创建一个模拟的失败结果
    test_result = {
        'id': 1,
        'backtest_days': 90,
        'stop_profit_ratio': 0.05,
        'stop_loss_ratio': -0.03,
        'total_return': -100.0,
        'annual_return': -100.0,
        'max_drawdown': -100.0,
        'sharpe_ratio': 0.0,
        'trades_count': 0,
        'win_rate': 0.0,
        'weights_config': {
            'kdj_j': 20,
            'trend': 20,
            'volume': 20,
            'fundamental': 10,
            'position': 10,
            'risk_reward': 20
        },
        'sub_weights_config': {
            'kdj_j': {'sub_weights': {'short': 50, 'medium': 30, 'long': 20}},
            'trend': {'sub_weights': {'short': 40, 'medium': 40, 'long': 20}}
        }
    }
    
    # 测试_update_excel_results函数
    print("测试_update_excel_results函数...")
    try:
        optimizer._update_excel_results([test_result])
        print("✅ _update_excel_results测试通过")
        
        # 检查Excel文件是否生成
        excel_path = os.path.join(current_dir, "parameter_optimization_results.xlsx")
        if os.path.exists(excel_path):
            print(f"✅ Excel文件已生成: {excel_path}")
            print(f"   文件大小: {os.path.getsize(excel_path)} 字节")
        else:
            print("❌ Excel文件未生成")
            
    except Exception as e:
        print(f"❌ _update_excel_results测试失败: {e}")
    
    # 测试export_to_excel函数
    print("\n测试export_to_excel函数...")
    try:
        test_file = os.path.join(current_dir, "test_export.xlsx")
        optimizer.export_to_excel([test_result], test_file)
        print("✅ export_to_excel测试通过")
        
        # 检查Excel文件是否生成
        if os.path.exists(test_file):
            print(f"✅ 测试Excel文件已生成: {test_file}")
            print(f"   文件大小: {os.path.getsize(test_file)} 字节")
            # 清理测试文件
            os.remove(test_file)
            print("   测试文件已清理")
        else:
            print("❌ 测试Excel文件未生成")
            
    except Exception as e:
        print(f"❌ export_to_excel测试失败: {e}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_excel_export_fix()
