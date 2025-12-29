#!/usr/bin/env python
# coding=utf-8
"""
测试ReportGenerator是否能正确生成包含sharpe_ratio和win_rate字段的报告
"""

import sys
import os
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from report_generator import ReportGenerator

class MockStrategy:
    """模拟策略类"""
    def __init__(self):
        self.initial_capital = 60000.0
        self.trading_records = []
        self.portfolio_values = [
            {'value': 60000, 'date': '2025-12-01'},
            {'value': 61000, 'date': '2025-12-02'},
            {'value': 62500, 'date': '2025-12-03'}
        ]
        
        class MockParams:
            stop_profit_ratio = 0.02
            stop_loss_ratio = -0.01
        
        self.params = MockParams()

def test_report_fields():
    """测试报告字段是否完整"""
    print("=== 测试ReportGenerator报告字段完整性 ===")
    
    # 创建模拟策略和报告生成器
    strategy = MockStrategy()
    report_generator = ReportGenerator()
    
    # 生成详细报告
    print("1. 生成详细报告...")
    detailed_report = report_generator.generate_detailed_report(strategy)
    
    # 检查报告字段
    print("2. 检查报告字段...")
    print(f"报告包含的键: {list(detailed_report.keys())}")
    
    # 检查关键字段
    required_fields = ['sharpe_ratio', 'win_rate', 'annual_return', 'max_drawdown']
    missing_fields = [field for field in required_fields if field not in detailed_report]
    
    if missing_fields:
        print(f"✗ 缺少字段: {missing_fields}")
        return False
    else:
        print(f"✓ 所有必要字段都存在: {required_fields}")
    
    # 打印字段值
    print("3. 关键字段值:")
    for field in required_fields:
        print(f"   {field}: {detailed_report[field]}")
    
    # 保存测试报告
    print("4. 保存测试报告...")
    report_generator._save_report_to_file(detailed_report)
    
    return True

if __name__ == "__main__":
    success = test_report_fields()
    if success:
        print("\n✅ 测试通过！ReportGenerator能正确生成包含所有关键字段的报告。")
    else:
        print("\n❌ 测试失败！ReportGenerator生成的报告缺少关键字段。")
        sys.exit(1)
