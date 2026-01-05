#!/usr/bin/env python
# coding=utf-8
"""
报告生成模块 - 负责生成回测报告和分析结果
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, List
from datetime import datetime


class ReportGenerator:
    """报告生成器 - 负责生成各种类型的回测报告"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.plt_style = 'seaborn-v0_8-whitegrid'
        
    def generate_basic_report(self, strategy) -> Dict[str, Any]:
        """
        生成基础回测报告
        
        Args:
            strategy: 策略实例
            
        Returns:
            Dict[str, Any]: 回测报告数据
        """
        # 计算回测指标 - 添加空值检查
        initial_value = strategy.initial_capital
        initial_value = 0.0 if initial_value is None else float(initial_value)
        
        # 即使没有交易记录，也检查组合价值变化
        final_value = initial_value
        if hasattr(strategy, 'portfolio_values') and strategy.portfolio_values:
            try:
                # 获取最后一个组合价值
                last_portfolio = strategy.portfolio_values[-1]
                if isinstance(last_portfolio, dict) and 'value' in last_portfolio:
                    final_value = last_portfolio['value']
                    final_value = 0.0 if final_value is None else float(final_value)
            except (IndexError, TypeError, KeyError):
                final_value = initial_value
        
        # 如果没有交易记录但有组合价值变化
        if not strategy.trading_records:
            print("没有交易记录，基于组合价值变化生成报告")
            
            total_return = (final_value - initial_value) / initial_value * 100 if initial_value > 0 else 0.0
            annual_return_pct = 0  # 默认年化收益率为0
            max_drawdown = 0  # 默认最大回撤为0
            sharpe_ratio = 0.0  # 默认夏普比率为0
            win_rate = 0.0  # 默认胜率为0
            
            # 构建基础报告数据
            return {
                'initial_capital': initial_value,
                'final_value': final_value,
                'total_return': total_return,
                'annual_return': annual_return_pct,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'win_rate': win_rate,
                'trades_count': 0,
                'stop_profit_ratio': getattr(strategy.params, 'stop_profit_ratio', 0.0),
                'stop_loss_ratio': getattr(strategy.params, 'stop_loss_ratio', 0.0),
                'weights_config': getattr(strategy.params, 'weights_config', None),
                'sub_weights_config': getattr(strategy.params, 'sub_weights_config', None),
                'backtest_days': getattr(strategy.params, 'backtest_days', 0),
                'strategy_type': getattr(strategy.params, 'strategy_type', '参数优化策略'),
                'trading_records': [],
                'portfolio_values': getattr(strategy, 'portfolio_values', [])
            }
        
        # 转换为DataFrame
        trades_df = pd.DataFrame(strategy.trading_records)
        portfolio_df = pd.DataFrame(strategy.portfolio_values, columns=['date', 'value'])
        
        # 计算回测指标 - 添加空值检查
        initial_value = strategy.initial_capital
        initial_value = 0.0 if initial_value is None else float(initial_value)
        
        final_value = 0.0
        if len(portfolio_df) > 0:
            final_value = portfolio_df['value'].iloc[-1]
            final_value = 0.0 if pd.isna(final_value) else float(final_value)
        else:
            final_value = initial_value
        
        total_return = (final_value - initial_value) / initial_value * 100 if initial_value > 0 else 0.0
        
        # 计算年化收益率
        annual_return_pct = 0
        if len(portfolio_df) > 1 and initial_value > 0:
            try:
                days = (portfolio_df['date'].iloc[-1] - portfolio_df['date'].iloc[0]).days
                if days > 0 and final_value > 0:
                    # 考虑回测天数影响，避免短期回测年化收益率过高
                    # 回测天数少于10天，不计算年化收益率
                    if days < 10:
                        annual_return_pct = 0
                    else:
                        annual_return = (final_value / initial_value) ** (365 / days) - 1
                        annual_return_pct = annual_return * 100
            except (TypeError, IndexError):
                annual_return_pct = 0
        
        # 计算最大回撤
        max_drawdown = 0
        if not portfolio_df.empty:
            try:
                portfolio_df['peak'] = portfolio_df['value'].cummax()
                portfolio_df['drawdown'] = (portfolio_df['value'] - portfolio_df['peak']) / portfolio_df['peak'] * 100
                max_drawdown = portfolio_df['drawdown'].min() if not pd.isna(portfolio_df['drawdown'].min()) else 0
            except (TypeError, ValueError):
                max_drawdown = 0
        
        # 计算胜率
        win_rate = 0.0
        if len(trades_df) > 1:
            # 将交易按顺序配对：BUY后跟着SELL，形成完整的交易对
            win_trades = 0
            total_trades = 0
            
            # 遍历交易记录，按顺序配对BUY和SELL
            i = 0
            while i < len(trades_df) - 1:
                buy_trade = trades_df.iloc[i]
                if buy_trade['action'] == 'BUY':
                    # 寻找对应的SELL交易
                    for j in range(i + 1, len(trades_df)):
                        sell_trade = trades_df.iloc[j]
                        if sell_trade['action'] == 'SELL' and sell_trade['symbol'] == buy_trade['symbol']:
                            # 找到配对的交易对
                            total_trades += 1
                            if buy_trade['price'] < sell_trade['price']:
                                win_trades += 1
                            i = j + 1  # 跳过已处理的交易
                            break
                    else:
                        # 没有找到对应的SELL交易，跳过该BUY
                        i += 1
                else:
                    # 不是BUY交易，继续
                    i += 1
            
            win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 计算夏普比率（简化版）
        sharpe_ratio = 0.0
        portfolio_df['daily_return'] = portfolio_df['value'].pct_change()
        daily_returns = portfolio_df['daily_return'].dropna()
        
        if len(daily_returns) > 0:
            annualized_return = annual_return_pct / 100
            annualized_volatility = daily_returns.std() * np.sqrt(252)
            
            if annualized_volatility > 0:
                sharpe_ratio = annualized_return / annualized_volatility
        
        report_data = {
            'initial_capital': initial_value,
            'final_value': final_value,
            'total_return': total_return,
            'annual_return': annual_return_pct,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'trades_count': len(trades_df),
            'stop_profit_ratio': strategy.params.stop_profit_ratio,
            'stop_loss_ratio': strategy.params.stop_loss_ratio,
            'weights_config': strategy.params.weights_config,
            'sub_weights_config': strategy.params.sub_weights_config,
            'backtest_days': strategy.params.backtest_days,
            'strategy_type': strategy.params.strategy_type,
            'trading_records': trades_df.to_dict('records'),
            'portfolio_values': portfolio_df.to_dict('records')
        }
        
        return report_data
    
    def generate_detailed_report(self, strategy, save_path: str = None) -> Dict[str, Any]:
        """
        生成详细回测报告
        
        Args:
            strategy: 策略实例
            save_path: 报告保存路径
            
        Returns:
            Dict[str, Any]: 详细报告数据
        """
        basic_report = self.generate_basic_report(strategy)
        
        if not basic_report:
            return {}
        
        # 计算更多指标
        trades_df = pd.DataFrame(strategy.trading_records)
        portfolio_df = pd.DataFrame(strategy.portfolio_values, columns=['date', 'value'])
        
        # 计算胜率 - 已在basic_report中计算
        # 计算夏普比率 - 已在basic_report中计算
        
        # 计算平均每笔交易收益率
        average_trade_return = basic_report['total_return'] / basic_report['trades_count'] if basic_report['trades_count'] > 0 else 0
        
        # 计算最大连续亏损次数
        max_consecutive_losses = self._calculate_max_consecutive_losses(trades_df)
        
        # 计算波动率
        portfolio_df['daily_return'] = portfolio_df['value'].pct_change()
        daily_returns = portfolio_df['daily_return'].dropna()
        volatility = daily_returns.std() * 100 if len(daily_returns) > 0 else 0
        
        detailed_report = {
            **basic_report,
            'average_trade_return': average_trade_return,
            'max_consecutive_losses': max_consecutive_losses,
            'volatility': volatility
        }
        
        # 打印详细报告
        print("\n" + "="*60)
        print("📊 详细回测报告")
        print("="*60)
        print(f"胜率: {basic_report['win_rate']:.2f}%")
        print(f"夏普比率: {basic_report['sharpe_ratio']:.2f}")
        print(f"平均每笔交易收益率: {average_trade_return:.2f}%")
        print(f"最大连续亏损次数: {max_consecutive_losses}")
        print(f"波动率: {volatility:.2f}%")
        
        # 保存报告到文件
        if save_path:
            self._save_report_to_file(detailed_report, save_path)
        
        return detailed_report
    
    def _calculate_max_consecutive_losses(self, trades_df: pd.DataFrame) -> int:
        """计算最大连续亏损次数"""
        if len(trades_df) < 2:
            return 0
        
        max_losses = 0
        current_losses = 0
        
        for i in range(0, len(trades_df)-1, 2):
            if i+1 < len(trades_df):
                buy_trade = trades_df.iloc[i]
                sell_trade = trades_df.iloc[i+1]
                
                if buy_trade['action'] == 'BUY' and sell_trade['action'] == 'SELL':
                    if sell_trade['price'] < buy_trade['price']:
                        current_losses += 1
                        max_losses = max(max_losses, current_losses)
                    else:
                        current_losses = 0
        
        return max_losses
    
    def _save_report_to_file(self, report_data: Dict[str, Any], file_path: str):
        """保存报告到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"✅ 报告已保存到: {file_path}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            # 同时保存到项目根目录下的固定名称文件，兼容参数优化器
            try:
                import os
                import sys
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                # 检查是否在参数优化器的子进程中运行
                if 'ulti-para-seeker' in sys.argv[0] or 'optimizers' in sys.path[0]:
                    # 使用固定名称的报告文件，供参数优化器读取
                    fixed_report_path = os.path.join(project_root, 'backtest_report.json')
                    with open(fixed_report_path, 'w', encoding='utf-8') as f:
                        json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
                    print(f"✅ 固定名称报告已保存到: {fixed_report_path}")
            except Exception as e2:
                print(f"❌ 保存固定名称报告失败: {e2}")
    
    def generate_visualization(self, strategy, save_path: str = None):
        """
        生成可视化图表 - 调用backtest_charts模块实现
        
        Args:
            strategy: 策略实例
            save_path: 图表保存路径
        """
        if not strategy.portfolio_values:
            print("没有组合价值数据，无法生成图表")
            return
        
        try:
            # 导入backtest_charts模块
            from .backtest_charts import BacktestAnalyzer
            
            # 创建分析器实例
            analyzer = BacktestAnalyzer(strategy.trading_records, strategy.portfolio_values, strategy.initial_capital)
            
            # 绘制组合净值曲线
            analyzer.plot_portfolio_curve(save_path)
            
            # 绘制交易分析图表
            analyzer.plot_trading_analysis(save_path)
            
        except Exception as e:
            print(f"❌ 生成图表失败: {e}")
            import traceback
            traceback.print_exc()

    def generate_backtest_summary(self, strategy) -> str:
        """
        生成回测摘要（文本格式）
        
        Args:
            strategy: 策略实例
            
        Returns:
            str: 回测摘要文本
        """
        # 即使没有交易记录，也生成基础回测摘要
        if not strategy.trading_records:
            initial_value = strategy.initial_capital
            initial_value = 0.0 if initial_value is None else float(initial_value)
            
            return f"""
回测摘要
{'=' * 40}
初始资金: {initial_value:,.2f}元
最终资金: {initial_value:,.2f}元
总收益率: 0.00%
年化收益率: 0.00%
最大回撤: 0.00%
夏普比率: 0.00
胜率: 0.00%
交易次数: 0次
止盈比例: {getattr(strategy.params, 'stop_profit_ratio', 0.0)*100:.2f}%
止损比例: {getattr(strategy.params, 'stop_loss_ratio', 0.0)*100:.2f}%
{'=' * 40}
"""
        
        # 生成基础报告
        basic_report = self.generate_basic_report(strategy)
        
        # 构建摘要文本
        summary = f"""
回测摘要
{'=' * 40}
初始资金: {basic_report['initial_capital']:,.2f}元
最终资金: {basic_report['final_value']:,.2f}元
总收益率: {basic_report['total_return']:.2f}%
年化收益率: {basic_report['annual_return']:.2f}%
最大回撤: {basic_report['max_drawdown']:.2f}%
夏普比率: {basic_report.get('sharpe_ratio', 0.0):.2f}
胜率: {basic_report.get('win_rate', 0.0):.2f}%
交易次数: {basic_report['trades_count']}次
止盈比例: {basic_report['stop_profit_ratio']*100:.2f}%
止损比例: {basic_report['stop_loss_ratio']*100:.2f}%
{'=' * 40}
"""
        
        return summary


def generate_backtest_summary(strategy) -> str:
    """
    生成回测摘要（文本格式） - 模块级函数
    
    Args:
        strategy: 策略实例
        
    Returns:
        str: 回测摘要文本
    """
    generator = ReportGenerator()
    return generator.generate_backtest_summary(strategy)