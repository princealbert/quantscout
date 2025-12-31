#!/usr/bin/env python
# coding=utf-8
"""
测试修复后的Excel导出功能
"""

import os
import tempfile
import pandas as pd
from parameter_optimizer import ParameterOptimizer


def test_excel_export():
    """测试Excel导出功能"""
    print("=== 测试修复后的Excel导出功能 ===")
    
    # 创建优化器实例
    optimizer = ParameterOptimizer()
    
    # 生成测试数据
    test_results = [
        {
            'backtest_days': 90,
            'start_date': '2025-01-01',
            'end_date': '2025-03-31',
            'stop_profit_ratio': 0.05,
            'stop_loss_ratio': -0.02,
            'total_return': 15.5,
            'annual_return': 20.3,
            'max_drawdown': -5.2,
            'sharpe_ratio': 1.8,
            'win_rate': 65.0,
            'trades_count': 15,
            'weights_config': {
                'kdj_j': 30,
                'trend': 25,
                'volume': 20,
                'fundamental': 15,
                'position': 10,
                'risk_reward': 10
            },
            'sub_weights_config': {
                'kdj_j': {'sub_weights': {'j_0_20': 20, 'j_-10_0': 20, 'j_-20_-10': 20, 'j_-30_-20': 20, 'j_below_-30': 20}},
                'trend': {'sub_weights': {'up_trend': 34, 'volume_price_rise': 33, 'volume_contraction': 33}},
                'volume': {'sub_weights': {'big_volume': 34, 'volume_anomaly': 33, 'volume_breathing': 33}},
                'fundamental': {'sub_weights': {'pe_positive': 25, 'pe_low': 25, 'market_cap': 25, 'volume_threshold': 25}},
                'position': {'sub_weights': {'above_white': 34, 'between_lines': 33, 'below_yellow': 33}}
            }
        },
        {
            'backtest_days': 90,
            'start_date': '2025-01-01',
            'end_date': '2025-03-31',
            'stop_profit_ratio': 0.06,
            'stop_loss_ratio': -0.03,
            'total_return': 12.8,
            'annual_return': 18.5,
            'max_drawdown': -4.8,
            'sharpe_ratio': 1.6,
            'win_rate': 62.0,
            'trades_count': 12,
            'weights_config': {
                'kdj_j': 25,
                'trend': 30,
                'volume': 15,
                'fundamental': 15,
                'position': 10,
                'risk_reward': 5
            },
            'sub_weights_config': {
                'kdj_j': {'sub_weights': {'j_0_20': 20, 'j_-10_0': 20, 'j_-20_-10': 20, 'j_-30_-20': 20, 'j_below_-30': 20}},
                'trend': {'sub_weights': {'up_trend': 34, 'volume_price_rise': 33, 'volume_contraction': 33}},
                'volume': {'sub_weights': {'big_volume': 34, 'volume_anomaly': 33, 'volume_breathing': 33}},
                'fundamental': {'sub_weights': {'pe_positive': 25, 'pe_low': 25, 'market_cap': 25, 'volume_threshold': 25}},
                'position': {'sub_weights': {'above_white': 34, 'between_lines': 33, 'below_yellow': 33}}
            }
        },
        # 添加一个重复的结果，测试去重功能
        {
            'backtest_days': 90,
            'start_date': '2025-01-01',
            'end_date': '2025-03-31',
            'stop_profit_ratio': 0.05,
            'stop_loss_ratio': -0.02,
            'total_return': 15.5,
            'annual_return': 20.3,
            'max_drawdown': -5.2,
            'sharpe_ratio': 1.8,
            'win_rate': 65.0,
            'trades_count': 15,
            'weights_config': {
                'kdj_j': 30,
                'trend': 25,
                'volume': 20,
                'fundamental': 15,
                'position': 10,
                'risk_reward': 10
            },
            'sub_weights_config': {
                'kdj_j': {'sub_weights': {'j_0_20': 20, 'j_-10_0': 20, 'j_-20_-10': 20, 'j_-30_-20': 20, 'j_below_-30': 20}},
                'trend': {'sub_weights': {'up_trend': 34, 'volume_price_rise': 33, 'volume_contraction': 33}},
                'volume': {'sub_weights': {'big_volume': 34, 'volume_anomaly': 33, 'volume_breathing': 33}},
                'fundamental': {'sub_weights': {'pe_positive': 25, 'pe_low': 25, 'market_cap': 25, 'volume_threshold': 25}},
                'position': {'sub_weights': {'above_white': 34, 'between_lines': 33, 'below_yellow': 33}}
            }
        },
        # 添加一个失败的结果，测试跳过功能
        {
            'backtest_days': 90,
            'start_date': '2025-01-01',
            'end_date': '2025-03-31',
            'stop_profit_ratio': 0.04,
            'stop_loss_ratio': -0.01,
            'total_return': -100.0,  # 失败结果
            'annual_return': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'win_rate': 0.0,
            'trades_count': 0,
            'weights_config': {
                'kdj_j': 20,
                'trend': 20,
                'volume': 20,
                'fundamental': 20,
                'position': 10,
                'risk_reward': 10
            },
            'sub_weights_config': {
                'kdj_j': {'sub_weights': {'j_0_20': 20, 'j_-10_0': 20, 'j_-20_-10': 20, 'j_-30_-20': 20, 'j_below_-30': 20}},
                'trend': {'sub_weights': {'up_trend': 34, 'volume_price_rise': 33, 'volume_contraction': 33}}
            }
        }
    ]
    
    # 测试_update_excel_results方法
    print("\n1. 测试_update_excel_results方法...")
    temp_file = tempfile.mktemp(suffix='.xlsx')
    try:
        optimizer._update_excel_results(test_results, temp_file)
        print(f"✅ _update_excel_results方法调用成功，文件已生成: {temp_file}")
        
        # 检查生成的Excel文件
        df = pd.read_excel(temp_file, engine='openpyxl')
        print(f"   生成的Excel文件包含 {len(df)} 条记录")
        print(f"   列数: {len(df.columns)}")
        print(f"   子权重列数: {len([col for col in df.columns if col.startswith('子权重_')])}")
        
        # 检查是否有重复行
        if len(df) == 2:  # 应该只有2条有效记录，重复的和失败的都被过滤了
            print("✅ 去重功能正常，重复结果被过滤")
        else:
            print(f"❌ 去重功能异常，期望2条记录，实际得到 {len(df)} 条")
        
        # 检查止损比例是否显示为正数
        if df['止损比例(%)'].min() >= 0:
            print("✅ 止损比例显示为正数，符合预期")
        else:
            print("❌ 止损比例显示为负数，不符合预期")
        
        # 检查是否有空行
        if df.isnull().sum().sum() == 0:
            print("✅ 没有空值，数据完整")
        else:
            print(f"❌ 存在空值: {df.isnull().sum().sum()} 个")
        
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"   临时文件已清理: {temp_file}")
    
    # 测试export_to_excel方法
    print("\n2. 测试export_to_excel方法...")
    temp_file2 = tempfile.mktemp(suffix='.xlsx')
    try:
        optimizer.export_to_excel(test_results, temp_file2)
        print(f"✅ export_to_excel方法调用成功，文件已生成: {temp_file2}")
        
        # 检查生成的Excel文件
        df2 = pd.read_excel(temp_file2, engine='openpyxl')
        print(f"   生成的Excel文件包含 {len(df2)} 条记录")
        print(f"   列数: {len(df2.columns)}")
        
        # 检查是否有重复行
        if len(df2) == 2:  # 应该只有2条有效记录，重复的和失败的都被过滤了
            print("✅ 去重功能正常，重复结果被过滤")
        else:
            print(f"❌ 去重功能异常，期望2条记录，实际得到 {len(df2)} 条")
        
        # 检查是否有空行
        if df2.isnull().sum().sum() == 0:
            print("✅ 没有空值，数据完整")
        else:
            print(f"❌ 存在空值: {df2.isnull().sum().sum()} 个")
        
    finally:
        if os.path.exists(temp_file2):
            os.remove(temp_file2)
            print(f"   临时文件已清理: {temp_file2}")
    
    print("\n=== 测试完成 ===")
    return True

if __name__ == "__main__":
    test_excel_export()