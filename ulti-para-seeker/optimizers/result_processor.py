#!/usr/bin/env python
# coding=utf-8
"""
结果处理器 - 负责优化结果的导出、可视化和分析
"""

import pandas as pd
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class ResultProcessor:
    """
    结果处理器 - 负责优化结果的导出、可视化和分析
    """
    
    def __init__(self, current_dir: str = None):
        """
        初始化结果处理器
        
        Args:
            current_dir: 当前工作目录，默认为None
        """
        # 默认使用项目根目录（ulti-para-seeker），确保与app.py保持一致
        default_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.current_dir = current_dir or default_dir
    
    def export_to_excel(self, results: List[Dict[str, Any]], file_path: str = "parameter_optimization_results.xlsx"):
        """
        导出结果到Excel
        
        Args:
            results: 回测结果列表
            file_path: Excel文件路径
        """
        print(f"\n[Excel导出] 开始导出结果到Excel: {file_path}")
        print(f"[Excel导出] 待处理结果数量: {len(results)}")
        
        # 转换新结果为DataFrame，添加去重逻辑
        df_list = []
        
        # 创建用于去重的集合
        seen_results = set()
        
        for i, result in enumerate(results):
            # 提取参数，添加安全检查，处理缺少字段的情况
            
            # 创建用于去重的唯一标识符（基于关键参数组合）
            key_params = (
                result.get('backtest_days', 90),
                result.get('start_date', ''),
                result.get('end_date', ''),
                result.get('stop_profit_ratio', 0.0),
                result.get('stop_loss_ratio', 0.0),
                tuple(sorted(result.get('weights_config', {}).items())),
                tuple(sorted((main_ind, tuple(sorted(sub_config['sub_weights'].items()))) 
                           for main_ind, sub_config in result.get('sub_weights_config', {}).items() 
                           if isinstance(sub_config, dict) and 'sub_weights' in sub_config))
            )
            
            # 如果该结果已经处理过，则跳过
            if key_params in seen_results:
                continue
            seen_results.add(key_params)
            
            # 跳过无效结果（总收益率为-100%的失败结果）
            if result.get('total_return', 0.0) <= -100:
                continue
            
            row = {
                '回测天数': result.get('backtest_days', 90),  # 默认90天
                '回测起始日期': result.get('start_date', ''),
                '回测终止日期': result.get('end_date', ''),
                '止盈比例(%)': result.get('stop_profit_ratio', 0.0) * 100,
                '止损比例(%)': abs(result.get('stop_loss_ratio', 0.0) * 100),  # 显示为正数
                '总收益率(%)': result.get('total_return', 0.0),
                '年化收益率(%)': result.get('annual_return', 0.0),
                '最大回撤(%)': result.get('max_drawdown', 0.0),
                '夏普比率': result.get('sharpe_ratio', 0.0),
                '胜率(%)': result.get('win_rate', 0.0),
                '交易次数': result.get('trades_count', 0)
            }
            
            # 添加权重配置，添加安全检查
            weights_config = result.get('weights_config', {})
            for indicator, weight in weights_config.items():
                row[f'权重_{indicator}'] = weight
            
            # 添加子权重配置，添加安全检查
            sub_weights_config = result.get('sub_weights_config', {})
            for main_indicator, sub_config in sub_weights_config.items():
                if isinstance(sub_config, dict) and 'sub_weights' in sub_config:
                    for sub_indicator, weight in sub_config['sub_weights'].items():
                        row[f'子权重_{main_indicator}_{sub_indicator}'] = weight
            
            df_list.append(row)
        
        # 创建DataFrame
        new_df = pd.DataFrame(df_list)
        print(f"[Excel导出] 新结果DataFrame创建完成，包含 {len(new_df)} 条记录")
        
        # 检查文件是否存在，如果存在则读取已有内容
        combined_df = new_df
        if os.path.exists(file_path):
            print(f"[Excel导出] 检测到文件已存在，正在读取已有内容...")
            try:
                # 读取已有内容
                existing_df = pd.read_excel(file_path)
                print(f"[Excel导出] 已有内容包含 {len(existing_df)} 条记录")
                
                # 合并新旧数据
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                print(f"[Excel导出] 合并后包含 {len(combined_df)} 条记录")
            except Exception as e:
                print(f"[Excel导出] 读取已有文件失败: {e}，将创建新文件")
        
        # 去重，确保没有重复行
        # 使用所有列作为去重依据
        combined_df = combined_df.drop_duplicates()
        print(f"[Excel导出] 去重后包含 {len(combined_df)} 条记录")
        
        # 跳过空数据
        if combined_df.empty:
            print("[Excel导出] ❌ 没有有效结果可导出")
            return
        
        # 定义固定的列顺序，确保回测指标字段放在一起
        # 基本参数
        base_columns = ['序号', '回测天数', '回测起始日期', '回测终止日期', '止盈比例(%)', '止损比例(%)']
        
        # 回测指标（放在一起）
        metric_columns = ['总收益率(%)', '年化收益率(%)', '最大回撤(%)', '夏普比率', '胜率(%)', '交易次数']
        
        # 权重配置列
        weight_columns = [col for col in combined_df.columns if col.startswith('权重_')]
        
        # 子权重配置列
        sub_weight_columns = [col for col in combined_df.columns if col.startswith('子权重_')]
        
        # 构建完整的列顺序
        column_order = base_columns + metric_columns + weight_columns + sub_weight_columns
        
        # 确保所有列都包含在column_order中
        for col in combined_df.columns:
            if col not in column_order:
                column_order.append(col)
        
        # 按总收益率降序排序
        combined_df = combined_df.sort_values(by='总收益率(%)', ascending=False)
        print(f"[Excel导出] 按总收益率降序排序完成")
        
        # 重新分配序号
        combined_df['序号'] = range(1, len(combined_df) + 1)
        print(f"[Excel导出] 重新分配序号完成")
        
        # 按固定顺序重新排列列
        combined_df = combined_df[column_order]
        print(f"[Excel导出] 列顺序调整完成: {column_order}")
        
        # 保存到Excel文件
        combined_df.to_excel(file_path, index=False, engine='openpyxl')
        print(f"[Excel导出] ✅ 结果已导出到 {file_path}")
    
    def _update_excel_results(self, results: List[Dict[str, Any]], fixed_file_name: str = "parameter_optimization_results.xlsx"):
        """
        更新固定Excel文件的结果（支持从已有文件读取并追加）
        
        Args:
            results: 回测结果列表
            fixed_file_name: 固定的Excel文件名
        """
        # 调用export_to_excel方法，实现相同的功能
        file_path = os.path.join(self.current_dir, fixed_file_name)
        self.export_to_excel(results, file_path)
    
    def save_results(self, results: List[Dict[str, Any]], output_file: str = "parameter_optimization_results.json"):
        """
        保存结果到JSON文件
        
        Args:
            results: 回测结果列表
            output_file: 输出文件名
        """
        print(f"\n[结果保存] 开始保存结果到JSON文件: {output_file}")
        
        # 创建结果目录（如果不存在）
        results_dir = os.path.dirname(output_file)
        if results_dir and not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        # 保存结果到JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"[结果保存] ✅ 结果已保存到 {output_file}")
        print(f"[结果保存] 共保存 {len(results)} 条记录")
    
    def visualize_yield_distribution(self, results: List[Dict[str, Any]], output_file: str = "yield_distribution.html") -> None:
        """
        可视化收益率分布
        
        Args:
            results: 回测结果列表
            output_file: 输出HTML文件名
        """
        print(f"\n[收益率可视化] 开始生成收益率分布直方图...")
        
        # 提取总收益率数据
        yields = [result.get('total_return', 0.0) for result in results if result.get('total_return', 0.0) > -100]
        
        if not yields:
            print("[收益率可视化] ❌ 没有有效收益率数据可可视化")
            return
        
        # 创建子图，添加直方图和箱线图
        fig = make_subplots(rows=2, cols=1, 
                          specs=[[{'type': 'histogram'}], [{'type': 'box'}]],
                          shared_xaxes=True,
                          vertical_spacing=0.1,
                          subplot_titles=('收益率分布直方图', '收益率箱线图'))
        
        # 添加直方图
        fig.add_trace(
            go.Histogram(x=yields, 
                        nbinsx=50,
                        name='收益率分布',
                        marker_color='lightblue',
                        opacity=0.8,
                        hovertemplate='<b>收益率: %{x:.2f}%</b><br>数量: %{y}<extra></extra>'),
            row=1, col=1
        )
        
        # 添加箱线图
        fig.add_trace(
            go.Box(x=yields, 
                  name='收益率分布',
                  boxpoints='all',
                  jitter=0.3,
                  pointpos=-1.8,
                  marker_color='lightgreen',
                  hovertemplate='<b>收益率: %{x:.2f}%</b><extra></extra>'),
            row=2, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title={'text': '参数组合收益率分布', 'x': 0.5, 'xanchor': 'center'},
            xaxis_title='总收益率 (%)',
            yaxis_title='数量',
            showlegend=False,
            template='plotly_white',
            autosize=True,
            height=600
        )
        
        # 更新子图布局
        fig.update_xaxes(title_text='总收益率 (%)', row=1, col=1)
        fig.update_xaxes(title_text='总收益率 (%)', row=2, col=1)
        fig.update_yaxes(title_text='数量', row=1, col=1)
        fig.update_yaxes(title_text='', row=2, col=1)
        
        # 保存为HTML文件
        output_path = os.path.join(self.current_dir, output_file)
        fig.write_html(output_path, auto_open=False)
        print(f"[收益率可视化] ✅ 收益率分布已保存到: {output_path}")
    
    def get_best_result(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取最佳结果
        
        Args:
            results: 回测结果列表
            
        Returns:
            Dict[str, Any]: 最佳结果
        """
        if not results:
            return {}
        
        # 按总收益率降序排序
        sorted_results = sorted(results, key=lambda x: x['total_return'], reverse=True)
        
        return sorted_results[0]
