#!/usr/bin/env python
# coding=utf-8
"""
报告生成器 - 生成和保存选股报告
"""

import os
import json
from datetime import datetime
from typing import Dict, List
import streamlit as st


def save_report(results: List[Dict], strategy_type: str, weights: Dict, params: Dict):
    """保存报告"""
    if not results:
        return
    
    os.makedirs('reports', exist_ok=True)
    
    # 生成HTML报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = f'reports/strategy_report_{timestamp}.html'
    
    # 简单HTML报告模板
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>{strategy_type} - 选股报告</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .stock-table {{ width: 100%; border-collapse: collapse; }}
            .stock-table th, .stock-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .stock-table th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{strategy_type}</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>筛选数量: {len(results)} 只</p>
        </div>
        
        <h2>权重配置</h2>
        <pre>{json.dumps(weights, indent=2, ensure_ascii=False)}</pre>
        
        <h2>选股结果</h2>
        <table class="stock-table">
            <thead>
                <tr>
                    <th>排名</th>
                    <th>股票代码</th>
                    <th>股票名称</th>
                    <th>收盘价</th>
                    <th>J值</th>
                    <th>综合评分</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for i, stock in enumerate(results):
        html_content += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{stock['symbol']}</td>
                    <td>{stock.get('sec_name', 'N/A')}</td>
                    <td>{stock['close']:.2f}</td>
                    <td>{stock['kdj_j']:.2f}</td>
                    <td>{stock.get('total_score', 0):.1f}</td>
                </tr>
        """
    
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    st.success(f"报告已保存: {html_file}")