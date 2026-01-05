#!/usr/bin/env python
# coding=utf-8
"""
报告生成模块 - 负责参数优化器专属的报告生成
依赖统一的strategy_engine.report_generator，只保留优化器专属功能
"""

import os
import time
import json
from typing import Dict, Any
from datetime import datetime

# 导入统一的报告生成器
from strategy_engine.report_generator import ReportGenerator as BaseReportGenerator


class OptimizerReportGenerator(BaseReportGenerator):
    """
    优化器报告生成器 - 继承自基础报告生成器，添加优化器专属功能
    """
    
    def _save_report_to_file(self, report_data: Dict[str, Any], file_path: str = None):
        """
        保存报告到文件 - 针对优化器的特殊处理
        
        Args:
            report_data: 报告数据
            file_path: 报告保存路径，默认为None（自动生成带时间戳的文件名）
        """
        try:
            # 取消固定名称报告功能，只生成带时间戳的报告
            # # 始终保存固定名称的文件，用于参数优化器快速读取
            # # 但添加时间延迟，确保不同参数组合的结果不会被覆盖
            # current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # fixed_file_name = os.path.join(current_dir, "backtest_report.json")
            # 
            # # 转换报告数据格式，使其与parameter_optimizer.py的预期一致
            # optimized_report = {
            #     "performance_metrics": {
            #         "total_return": report_data.get("total_return", 0.0),
            #         "annual_return": report_data.get("annual_return", 0.0),
            #         "max_drawdown": report_data.get("max_drawdown", 0.0),
            #         "sharpe_ratio": report_data.get("sharpe_ratio", 0.0)
            #     },
            #     "trade_statistics": {
            #         "total_trades": report_data.get("trades_count", 0),
            #         "win_rate": report_data.get("win_rate", 0.0)
            #     }
            # }
            # 
            # # 确保不同参数组合的结果不会被覆盖，添加短暂延迟
            # time.sleep(0.1)  # 100毫秒延迟
            # 
            # # 保存固定名称报告文件
            # with open(fixed_file_name, 'w', encoding='utf-8') as f:
            #     json.dump(optimized_report, f, ensure_ascii=False, indent=2, default=str)
            # print(f"✅ 固定名称报告已保存到: {fixed_file_name}")
            # print(f"✅ 固定名称报告内容: {json.dumps(optimized_report, ensure_ascii=False, indent=2)}")
            
            # 生成带时间戳的文件名，用于长期保存
            if not file_path:
                # 强制使用正确的时间戳格式，避免文件名包含空格
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")  # 添加微秒，确保唯一性
                # 项目根目录下的backtest_reports目录
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                report_dir = os.path.join(project_root, "backtest_reports")
                if not os.path.exists(report_dir):
                    os.makedirs(report_dir)
                file_path = os.path.join(report_dir, f"backtest_report_{timestamp}.json")

            # 确保带时间戳的报告文件包含所有必要字段
            report_data['sharpe_ratio'] = report_data.get('sharpe_ratio', 0.0)
            report_data['win_rate'] = report_data.get('win_rate', 0.0)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"✅ 报告已保存到: {file_path}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            import traceback
            traceback.print_exc()

    def generate_detailed_report(self, strategy, save_path: str = None) -> Dict[str, Any]:
        """
        生成详细回测报告 - 针对优化器的特殊处理
        
        Args:
            strategy: 策略实例
            save_path: 报告保存路径
            
        Returns:
            Dict[str, Any]: 详细报告数据
        """
        print(f"[优化器报告生成] 开始生成详细回测报告")
        # 使用基础生成方法
        basic_report = self.generate_basic_report(strategy)
        
        if not basic_report:
            print(f"[优化器报告生成] 基础报告生成失败，无法生成详细报告")
            return {}
        
        # 计算更多指标
        from pandas import DataFrame
        trades_df = DataFrame(strategy.trading_records)
        
        # 计算平均每笔交易收益率
        average_trade_return = basic_report['total_return'] / basic_report['trades_count'] if basic_report['trades_count'] > 0 else 0
        
        # 计算最大连续亏损次数
        max_consecutive_losses = self._calculate_max_consecutive_losses(trades_df)
        
        detailed_report = {
            **basic_report,
            'average_trade_return': average_trade_return,
            'max_consecutive_losses': max_consecutive_losses,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 保存报告到文件
        self._save_report_to_file(detailed_report, save_path)
        
        return detailed_report
