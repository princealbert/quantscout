#!/usr/bin/env python
# coding=utf-8
"""
回测结果分析器
分析回测结果，生成可视化报告
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 设置matplotlib中文字体，使用系统默认中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']  # 设置中文显示
plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题


class BacktestAnalyzer:
    """回测结果分析器"""
    
    def __init__(self, trading_records: List[Dict], portfolio_values: List[Dict], initial_capital: float):
        """
        初始化分析器
        
        Args:
            trading_records: 交易记录列表
            portfolio_values: 组合价值历史
            initial_capital: 初始资金
        """
        self.trading_records = trading_records
        self.portfolio_values = portfolio_values
        self.initial_capital = initial_capital
        
        # 转换为DataFrame
        self.trades_df = pd.DataFrame(trading_records)
        self.portfolio_df = pd.DataFrame(portfolio_values)
        
        # 计算分析指标
        self.analysis_results = self._calculate_metrics()
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """计算回测指标"""
        results = {}
        
        if len(self.portfolio_df) == 0:
            return results
        
        # 基本指标
        initial_value = self.initial_capital
        final_value = self.portfolio_df['value'].iloc[-1]
        
        results['initial_capital'] = initial_value
        results['final_value'] = final_value
        results['total_return'] = (final_value - initial_value) / initial_value * 100
        
        # 年化收益率
        if len(self.portfolio_df) > 1:
            # 使用交易天数而非日历天数
            trading_days = len(self.portfolio_df) - 1
            if trading_days > 0:
                # 使用252个交易日作为年化基数
                annual_return = (final_value / initial_value) ** (252 / trading_days) - 1
                results['annual_return'] = annual_return * 100
                results['trading_days'] = trading_days
            else:
                results['annual_return'] = 0
                results['trading_days'] = 0
        
        # 最大回撤
        if len(self.portfolio_df) > 0:
            self.portfolio_df['peak'] = self.portfolio_df['value'].cummax()
            self.portfolio_df['drawdown'] = (self.portfolio_df['value'] - self.portfolio_df['peak']) / self.portfolio_df['peak'] * 100
            results['max_drawdown'] = self.portfolio_df['drawdown'].min()
        
        # 交易统计
        results['total_trades'] = len(self.trades_df)
        
        if len(self.trades_df) > 0:
            # 盈利交易统计
            buy_trades = self.trades_df[self.trades_df['action'] == 'BUY']
            sell_trades = self.trades_df[self.trades_df['action'] == 'SELL']
            
            # 计算每笔交易的盈亏
            trade_profits = []
            for i in range(min(len(buy_trades), len(sell_trades))):
                buy_trade = buy_trades.iloc[i]
                sell_trade = sell_trades.iloc[i]
                
                if buy_trade['symbol'] == sell_trade['symbol']:
                    profit = (sell_trade['price'] - buy_trade['price']) * buy_trade['quantity']
                    profit_ratio = (sell_trade['price'] - buy_trade['price']) / buy_trade['price'] * 100
                    trade_profits.append({
                        'symbol': buy_trade['symbol'],
                        'sec_name': buy_trade.get('sec_name', buy_trade['symbol']),
                        'profit': profit,
                        'profit_ratio': profit_ratio,
                        'buy_date': buy_trade['date'],
                        'sell_date': sell_trade['date']
                    })
            
            if trade_profits:
                profits_df = pd.DataFrame(trade_profits)
                results['winning_trades'] = len(profits_df[profits_df['profit'] > 0])
                results['losing_trades'] = len(profits_df[profits_df['profit'] <= 0])
                results['win_rate'] = results['winning_trades'] / len(profits_df) * 100
                results['avg_profit'] = profits_df['profit'].mean()
                results['avg_profit_ratio'] = profits_df['profit_ratio'].mean()
                results['total_profit'] = profits_df['profit'].sum()
        
        # 夏普比率（简化版）
        if len(self.portfolio_df) > 1:
            daily_returns = self.portfolio_df['value'].pct_change().dropna()
            if len(daily_returns) > 0:
                results['avg_daily_return'] = daily_returns.mean() * 100
                results['std_daily_return'] = daily_returns.std() * 100
                
                # 简化夏普比率（假设无风险利率为0）
                if results['std_daily_return'] > 0:
                    results['sharpe_ratio'] = results['avg_daily_return'] / results['std_daily_return']
                else:
                    results['sharpe_ratio'] = 0
        
        return results
    
    def generate_text_report(self) -> str:
        """生成文本报告"""
        report = []
        report.append("=" * 70)
        report.append("📊 QuantScout选股策略回测报告")
        report.append("=" * 70)
        
        # 基本指标
        report.append(f"初始资金: {self.analysis_results.get('initial_capital', 0):,.2f}元")
        report.append(f"最终资金: {self.analysis_results.get('final_value', 0):,.2f}元")
        report.append(f"总收益率: {self.analysis_results.get('total_return', 0):.2f}%")
        report.append(f"年化收益率: {self.analysis_results.get('annual_return', 0):.2f}%")
        report.append(f"最大回撤: {self.analysis_results.get('max_drawdown', 0):.2f}%")
        
        # 交易统计
        report.append(f"交易天数: {self.analysis_results.get('trading_days', 0)}天")
        report.append(f"总交易次数: {self.analysis_results.get('total_trades', 0)}次")
        
        if 'winning_trades' in self.analysis_results:
            report.append(f"盈利交易: {self.analysis_results['winning_trades']}次")
            report.append(f"亏损交易: {self.analysis_results['losing_trades']}次")
            report.append(f"胜率: {self.analysis_results.get('win_rate', 0):.2f}%")
            report.append(f"平均每笔盈利: {self.analysis_results.get('avg_profit', 0):.2f}元")
            report.append(f"平均收益率: {self.analysis_results.get('avg_profit_ratio', 0):.2f}%")
        
        # 风险指标
        if 'sharpe_ratio' in self.analysis_results:
            report.append(f"夏普比率: {self.analysis_results['sharpe_ratio']:.2f}")
        
        # 策略评价
        total_return = self.analysis_results.get('total_return', 0)
        max_drawdown = abs(self.analysis_results.get('max_drawdown', 0))
        
        if total_return > 20 and max_drawdown < 10:
            evaluation = "优秀"
        elif total_return > 10 and max_drawdown < 15:
            evaluation = "良好"
        elif total_return > 0:
            evaluation = "一般"
        else:
            evaluation = "需改进"
        
        report.append(f"策略评价: {evaluation}")
        
        return "\n".join(report)
    
    def plot_portfolio_curve(self, save_path: str = None):
        """绘制组合净值曲线"""
        if len(self.portfolio_df) == 0:
            print("没有组合数据可绘制")
            return
        
        plt.figure(figsize=(12, 8))
        
        # 组合净值曲线
        plt.subplot(2, 1, 1)
        plt.plot(self.portfolio_df['date'], self.portfolio_df['value'], 
                label='组合净值', color='blue', linewidth=2)
        plt.axhline(y=self.initial_capital, color='red', linestyle='--', 
                   label=f'初始资金 ({self.initial_capital:,.0f}元)')
        plt.title('QuantScout选股策略 - 组合净值曲线', fontsize=14, fontweight='bold')
        plt.ylabel('组合价值 (元)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 回撤曲线
        plt.subplot(2, 1, 2)
        plt.fill_between(self.portfolio_df['date'], self.portfolio_df['drawdown'], 0, 
                        alpha=0.3, color='red', label='回撤')
        plt.plot(self.portfolio_df['date'], self.portfolio_df['drawdown'], 
                color='red', linewidth=1)
        plt.title('最大回撤', fontsize=14, fontweight='bold')
        plt.ylabel('回撤 (%)', fontsize=12)
        plt.xlabel('日期', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        
        plt.show()
    
    def plot_trading_analysis(self, save_path: str = None):
        """绘制交易分析图表"""
        if len(self.trades_df) == 0:
            print("没有交易数据可分析")
            return
        
        # 提取买卖交易
        buy_trades = self.trades_df[self.trades_df['action'] == 'BUY']
        sell_trades = self.trades_df[self.trades_df['action'] == 'SELL']
        
        if len(buy_trades) == 0 or len(sell_trades) == 0:
            print("交易数据不完整")
            return
        
        plt.figure(figsize=(12, 10))
        
        # 1. 交易时间分布
        plt.subplot(2, 2, 1)
        buy_trades['weekday'] = buy_trades['date'].dt.day_name()
        # 将英文星期转换为中文（只保留工作日）
        weekday_mapping = {
            'Monday': '周一',
            'Tuesday': '周二',
            'Wednesday': '周三',
            'Thursday': '周四',
            'Friday': '周五'
        }
        buy_trades['weekday'] = buy_trades['weekday'].replace(weekday_mapping)
        weekday_counts = buy_trades['weekday'].value_counts()
        # 按周一到周五排序
        weekday_order = ['周一', '周二', '周三', '周四', '周五']
        weekday_counts = weekday_counts.reindex(weekday_order, fill_value=0)
        weekday_counts.plot(kind='bar', color='skyblue')
        plt.title('交易日期分布')
        plt.xlabel('星期')
        plt.ylabel('交易次数')
        plt.xticks(rotation=0)
        
        # 2. 交易金额分布
        plt.subplot(2, 2, 2)
        plt.hist(buy_trades['amount'], bins=10, alpha=0.7, color='lightgreen')
        plt.title('单笔交易金额分布')
        plt.xlabel('交易金额 (元)')
        plt.ylabel('频次')
        
        # 3. 股票交易频次
        plt.subplot(2, 2, 3)
        # 使用股票名称而不是代码
        name_counts = self.trades_df['sec_name'].value_counts().head(10)
        name_counts.plot(kind='bar', color='orange')
        plt.title('股票交易频次 (Top 10)')
        plt.xlabel('股票名称')
        plt.ylabel('交易次数')
        plt.xticks(rotation=45)
        
        # 4. 交易盈亏分析（如果有完整的买卖配对）
        plt.subplot(2, 2, 4)
        # 这里简化处理，实际应该计算每笔交易的盈亏
        if len(buy_trades) == len(sell_trades):
            profits = []
            for i in range(len(buy_trades)):
                profit_ratio = (sell_trades.iloc[i]['price'] - buy_trades.iloc[i]['price']) / buy_trades.iloc[i]['price'] * 100
                profits.append(profit_ratio)
            
            plt.hist(profits, bins=15, alpha=0.7, color='lightcoral')
            plt.axvline(x=0, color='red', linestyle='--', linewidth=2)
            plt.title('交易收益率分布')
            plt.xlabel('收益率 (%)')
            plt.ylabel('频次')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"交易分析图表已保存到: {save_path}")
        
        plt.show()
    
    def generate_excel_report(self, file_path: str):
        """生成Excel格式的详细报告"""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # 1. 汇总表
            summary_data = {
                '指标': ['初始资金', '最终资金', '总收益率', '年化收益率', '最大回撤', 
                       '交易天数', '总交易次数', '胜率', '夏普比率'],
                '数值': [
                    f"{self.analysis_results.get('initial_capital', 0):,.2f}元",
                    f"{self.analysis_results.get('final_value', 0):,.2f}元",
                    f"{self.analysis_results.get('total_return', 0):.2f}%",
                    f"{self.analysis_results.get('annual_return', 0):.2f}%",
                    f"{self.analysis_results.get('max_drawdown', 0):.2f}%",
                    f"{self.analysis_results.get('trading_days', 0)}天",
                    f"{self.analysis_results.get('total_trades', 0)}次",
                    f"{self.analysis_results.get('win_rate', 0):.2f}%",
                    f"{self.analysis_results.get('sharpe_ratio', 0):.2f}"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='策略汇总', index=False)
            
            # 2. 交易记录
            if len(self.trades_df) > 0:
                trades_export = self.trades_df.copy()
                trades_export['date'] = trades_export['date'].dt.strftime('%Y-%m-%d')
                trades_export.to_excel(writer, sheet_name='交易记录', index=False)
            
            # 3. 组合价值历史
            if len(self.portfolio_df) > 0:
                portfolio_export = self.portfolio_df.copy()
                portfolio_export['date'] = portfolio_export['date'].dt.strftime('%Y-%m-%d')
                portfolio_export.to_excel(writer, sheet_name='组合价值', index=False)
        
        print(f"Excel报告已生成: {file_path}")


def analyze_backtest_results(trading_records: List[Dict], portfolio_values: List[Dict], 
                           initial_capital: float = 100000):
    """
    快速分析回测结果的函数
    
    Args:
        trading_records: 交易记录
        portfolio_values: 组合价值历史
        initial_capital: 初始资金
    """
    analyzer = BacktestAnalyzer(trading_records, portfolio_values, initial_capital)
    
    # 生成文本报告
    print(analyzer.generate_text_report())
    
    # 绘制图表
    analyzer.plot_portfolio_curve()
    analyzer.plot_trading_analysis()
    
    return analyzer