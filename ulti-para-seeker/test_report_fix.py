#!/usr/bin/env python
# coding=utf-8
"""
测试报告生成器修复效果
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 创建一个模拟的策略类用于测试
class MockStrategy:
    def __init__(self):
        self.initial_capital = 100000.0
        self.params = type('Params', (), {'stop_profit_ratio': 0.02, 'stop_loss_ratio': -0.01})()
        
        # 创建一些模拟的交易记录
        self.trading_records = [
            {
                'date': datetime.now() - timedelta(days=10),
                'symbol': '600000.SH',
                'action': 'BUY',
                'price': 10.0,
                'quantity': 1000,
                'amount': 10000.0
            },
            {
                'date': datetime.now() - timedelta(days=5),
                'symbol': '600000.SH',
                'action': 'SELL',
                'price': 11.0,
                'quantity': 1000,
                'amount': 11000.0
            },
            {
                'date': datetime.now() - timedelta(days=4),
                'symbol': '600001.SH',
                'action': 'BUY',
                'price': 20.0,
                'quantity': 500,
                'amount': 10000.0
            },
            {
                'date': datetime.now() - timedelta(days=1),
                'symbol': '600001.SH',
                'action': 'SELL',
                'price': 19.5,
                'quantity': 500,
                'amount': 9750.0
            }
        ]
        
        # 创建一些模拟的组合价值记录
        self.portfolio_values = [
            {'date': datetime.now() - timedelta(days=10), 'value': 100000.0},
            {'date': datetime.now() - timedelta(days=9), 'value': 100500.0},
            {'date': datetime.now() - timedelta(days=8), 'value': 101000.0},
            {'date': datetime.now() - timedelta(days=7), 'value': 100800.0},
            {'date': datetime.now() - timedelta(days=6), 'value': 100900.0},
            {'date': datetime.now() - timedelta(days=5), 'value': 101100.0},
            {'date': datetime.now() - timedelta(days=4), 'value': 101100.0},
            {'date': datetime.now() - timedelta(days=3), 'value': 101000.0},
            {'date': datetime.now() - timedelta(days=2), 'value': 100900.0},
            {'date': datetime.now() - timedelta(days=1), 'value': 100850.0}
        ]

def test_report_generator():
    """测试ReportGenerator类"""
    print("=== 测试ReportGenerator类 ===")
    
    try:
        from report_generator import ReportGenerator
        
        # 创建模拟策略
        strategy = MockStrategy()
        
        # 创建报告生成器
        report_generator = ReportGenerator()
        
        # 生成详细报告
        report_data = report_generator.generate_detailed_report(strategy)
        
        print(f"报告包含的键: {list(report_data.keys())}")
        
        # 检查是否包含夏普比率和胜率字段
        if 'sharpe_ratio' in report_data and 'win_rate' in report_data:
            print(f"夏普比率: {report_data['sharpe_ratio']}")
            print(f"胜率: {report_data['win_rate']}")
            print("✓ 包含夏普比率和胜率字段")
        else:
            print("✗ 缺少夏普比率或胜率字段")
        
        # 检查其他关键指标
        for field in ['total_return', 'annual_return', 'max_drawdown', 'trades_count']:
            if field in report_data:
                print(f"{field}: {report_data[field]}")
            else:
                print(f"✗ 缺少字段 {field}")
        
        # 检查交易记录
        if 'trading_records' in report_data:
            print(f"交易记录数量: {len(report_data['trading_records'])}")
        else:
            print("✗ 缺少交易记录字段")
        
        # 保存报告到文件
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        test_report_file = f"test_report_{timestamp}.json"
        with open(test_report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"测试报告已保存到: {test_report_file}")
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_report_generator()
