#!/usr/bin/env python
# coding=utf-8
"""
测试所有修复功能的脚本
"""

import os
import sys
import json
import pandas as pd
import time
from datetime import datetime

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入参数优化器
from parameter_optimizer import ParameterOptimizer
from report_generator import OptimizedReportGenerator

def test_excel_update():
    """测试Excel更新功能"""
    print("\n=== 测试Excel更新功能 ===")
    
    excel_file = os.path.join(current_dir, "parameter_optimization_results.xlsx")
    
    # 检查文件是否存在
    if os.path.exists(excel_file):
        # 获取文件大小
        file_size = os.path.getsize(excel_file)
        print(f"Excel文件存在: {excel_file}")
        print(f"文件大小: {file_size} 字节")
        
        # 读取Excel内容
        try:
            df = pd.read_excel(excel_file)
            print(f"Excel表格行数: {len(df)}")
            print(f"Excel表格列数: {len(df.columns)}")
            print(f"Excel表格列名: {list(df.columns)}")
            
            # 检查是否包含夏普比率和胜率字段
            if '夏普比率' in df.columns and '胜率(%)' in df.columns:
                print("✓ 包含夏普比率和胜率字段")
            else:
                print("✗ 缺少夏普比率或胜率字段")
                
            # 显示前几行数据
            print("Excel表格前3行数据:")
            print(df.head(3))
            
            return True
        except Exception as e:
            print(f"读取Excel失败: {e}")
            return False
    else:
        print(f"Excel文件不存在: {excel_file}")
        return False

def test_json_report():
    """测试JSON报告生成功能"""
    print("\n=== 测试JSON报告生成功能 ===")
    
    # 查找最新的JSON报告
    backtest_reports_dir = os.path.join(current_dir, "backtest_reports")
    if os.path.exists(backtest_reports_dir):
        json_files = [f for f in os.listdir(backtest_reports_dir) if f.endswith(".json")]
        if json_files:
            # 按修改时间排序，获取最新的文件
            json_files.sort(key=lambda x: os.path.getmtime(os.path.join(backtest_reports_dir, x)), reverse=True)
            latest_json = os.path.join(backtest_reports_dir, json_files[0])
            
            print(f"最新的JSON报告: {latest_json}")
            
            try:
                with open(latest_json, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                
                # 检查报告内容
                print(f"报告包含的键: {list(report.keys())}")
                
                # 检查交易记录
                if 'trading_records' in report:
                    trades_count = len(report['trading_records'])
                    print(f"交易记录数量: {trades_count}")
                    if trades_count > 0:
                        print("✓ 包含交易记录")
                        print(f"第一条交易记录: {report['trading_records'][0]}")
                    else:
                        print("✗ 交易记录为空")
                else:
                    print("✗ 缺少交易记录字段")
                
                # 检查夏普比率和胜率
                if 'sharpe_ratio' in report and 'win_rate' in report:
                    print(f"夏普比率: {report['sharpe_ratio']}")
                    print(f"胜率: {report['win_rate']}")
                    print("✓ 包含夏普比率和胜率字段")
                else:
                    print("✗ 缺少夏普比率或胜率字段")
                
                # 检查年化收益率和最大回撤
                if 'annual_return' in report and 'max_drawdown' in report:
                    print(f"年化收益率: {report['annual_return']}")
                    print(f"最大回撤: {report['max_drawdown']}")
                    print("✓ 包含年化收益率和最大回撤字段")
                else:
                    print("✗ 缺少年化收益率或最大回撤字段")
                
                return True
            except Exception as e:
                print(f"读取JSON报告失败: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print(f"backtest_reports目录中没有JSON文件")
            return False
    else:
        print(f"backtest_reports目录不存在: {backtest_reports_dir}")
        return False

def test_parameter_optimizer():
    """测试参数优化器"""
    print("\n=== 测试参数优化器 ===")
    
    try:
        optimizer = ParameterOptimizer()
        
        # 测试回测失败时的字段完整性
        print("测试回测失败时的字段完整性...")
        failed_result = optimizer.run_backtest(None)
        required_fields = ['sharpe_ratio', 'win_rate', 'annual_return', 'max_drawdown', 'trades_count']
        for field in required_fields:
            if field in failed_result:
                print(f"✓ 包含字段 {field}: {failed_result[field]}")
            else:
                print(f"✗ 缺少字段 {field}")
        
        return True
    except Exception as e:
        print(f"测试参数优化器失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始测试所有修复功能...")
    
    # 测试Excel更新
    excel_test = test_excel_update()
    
    # 测试JSON报告
    json_test = test_json_report()
    
    # 测试参数优化器
    optimizer_test = test_parameter_optimizer()
    
    # 总结测试结果
    print("\n=== 测试结果总结 ===")
    if excel_test and json_test and optimizer_test:
        print("✓ 所有测试通过！")
        return True
    else:
        print("✗ 部分测试失败！")
        return False

if __name__ == "__main__":
    main()
