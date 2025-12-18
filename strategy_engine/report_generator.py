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
        if not strategy.trading_records:
            print("没有交易记录，无法生成报告")
            return {}
        
        # 转换为DataFrame
        trades_df = pd.DataFrame(strategy.trading_records)
        portfolio_df = pd.DataFrame(strategy.portfolio_values, columns=['date', 'value'])
        
        # 计算回测指标
        initial_value = strategy.initial_capital
        final_value = portfolio_df['value'].iloc[-1] if len(portfolio_df) > 0 else initial_value
        
        total_return = (final_value - initial_value) / initial_value * 100
        
        # 计算年化收益率
        if len(portfolio_df) > 1:
            days = (portfolio_df['date'].iloc[-1] - portfolio_df['date'].iloc[0]).days
            if days > 0:
                annual_return = (final_value / initial_value) ** (365 / days) - 1
                annual_return_pct = annual_return * 100
            else:
                annual_return_pct = 0
        else:
            annual_return_pct = 0
        
        # 计算最大回撤
        portfolio_df['peak'] = portfolio_df['value'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['value'] - portfolio_df['peak']) / portfolio_df['peak'] * 100
        max_drawdown = portfolio_df['drawdown'].min()
        
        # 打印报告
        print("\n" + "="*60)
        print("📊 回测报告")
        print("="*60)
        print(f"初始资金: {initial_value:,.2f}元")
        print(f"最终资金: {final_value:,.2f}元")
        print(f"总收益率: {total_return:.2f}%")
        print(f"年化收益率: {annual_return_pct:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"交易次数: {len(trades_df)}次")
        
        # 显示交易记录
        if len(trades_df) > 0:
            print("\n交易记录:")
            print("-" * 80)
            for _, trade in trades_df.iterrows():
                action = "买入" if trade['action'] == 'BUY' else "卖出"
                print(f"{trade['date'].strftime('%Y-%m-%d')} {action} {trade['symbol']} "
                      f"{trade['quantity']}股 @ {trade['price']:.2f}元")
        
        report_data = {
            'initial_capital': initial_value,
            'final_value': final_value,
            'total_return': total_return,
            'annual_return': annual_return_pct,
            'max_drawdown': max_drawdown,
            'trades_count': len(trades_df),
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
        
        # 计算胜率
        if len(trades_df) > 1:
            buy_trades = trades_df[trades_df['action'] == 'BUY']
            sell_trades = trades_df[trades_df['action'] == 'SELL']
            
            if len(buy_trades) > 0 and len(sell_trades) > 0:
                # 简单计算胜率（需要更复杂的逻辑）
                win_trades = 0
                total_trades = len(sell_trades)
                
                for i, sell_trade in sell_trades.iterrows():
                    symbol = sell_trade['symbol']
                    # 找到对应的买入交易
                    buy_trade = buy_trades[buy_trades['symbol'] == symbol].iloc[0]
                    if buy_trade['price'] < sell_trade['price']:
                        win_trades += 1
                
                win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
            else:
                win_rate = 0
        else:
            win_rate = 0
        
        # 计算夏普比率（简化版）
        portfolio_df['daily_return'] = portfolio_df['value'].pct_change()
        daily_returns = portfolio_df['daily_return'].dropna()
        
        if len(daily_returns) > 0:
            annualized_return = basic_report['annual_return'] / 100
            annualized_volatility = daily_returns.std() * np.sqrt(252)
            
            if annualized_volatility > 0:
                sharpe_ratio = annualized_return / annualized_volatility
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        detailed_report = {
            **basic_report,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'average_trade_return': basic_report['total_return'] / basic_report['trades_count'] if basic_report['trades_count'] > 0 else 0,
            'max_consecutive_losses': self._calculate_max_consecutive_losses(trades_df),
            'volatility': daily_returns.std() * 100 if len(daily_returns) > 0 else 0
        }
        
        # 打印详细报告
        print("\n" + "="*60)
        print("📊 详细回测报告")
        print("="*60)
        print(f"胜率: {win_rate:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"平均每笔交易收益率: {detailed_report['average_trade_return']:.2f}%")
        print(f"最大连续亏损次数: {detailed_report['max_consecutive_losses']}")
        print(f"波动率: {detailed_report['volatility']:.2f}%")
        
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
    
    def generate_visualization(self, strategy, save_path: str = None):
        """
        生成可视化图表
        
        Args:
            strategy: 策略实例
            save_path: 图表保存路径
        """
        if not strategy.portfolio_values:
            print("没有组合价值数据，无法生成图表")
            return
        
        try:
            # 设置图表样式
            plt.style.use(self.plt_style)
            
            # 创建图表
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('z哥选股策略回测分析', fontsize=16, fontweight='bold')
            
            # 准备数据
            portfolio_df = pd.DataFrame(strategy.portfolio_values, columns=['date', 'value'])
            portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
            portfolio_df = portfolio_df.set_index('date')
            portfolio_df['cumulative_return'] = (portfolio_df['value'] / strategy.initial_capital - 1) * 100
            
            # 1. 组合净值曲线
            axes[0, 0].plot(portfolio_df.index, portfolio_df['value'], linewidth=2, color='#2E86AB')
            axes[0, 0].set_title('组合净值曲线', fontsize=12, fontweight='bold')
            axes[0, 0].set_ylabel('净值（元）')
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # 2. 累计收益率
            axes[0, 1].plot(portfolio_df.index, portfolio_df['cumulative_return'], linewidth=2, color='#A23B72')
            axes[0, 1].set_title('累计收益率', fontsize=12, fontweight='bold')
            axes[0, 1].set_ylabel('收益率（%）')
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # 3. 最大回撤
            portfolio_df['peak'] = portfolio_df['value'].cummax()
            portfolio_df['drawdown'] = (portfolio_df['value'] - portfolio_df['peak']) / portfolio_df['peak'] * 100
            
            axes[1, 0].fill_between(portfolio_df.index, portfolio_df['drawdown'], 0, 
                                  alpha=0.3, color='#F18F01', label='回撤')
            axes[1, 0].plot(portfolio_df.index, portfolio_df['drawdown'], linewidth=1, color='#F18F01')
            axes[1, 0].set_title('最大回撤', fontsize=12, fontweight='bold')
            axes[1, 0].set_ylabel('回撤（%）')
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].tick_params(axis='x', rotation=45)
            axes[1, 0].legend()
            
            # 4. 交易统计（如果有交易记录）
            if strategy.trading_records:
                trades_df = pd.DataFrame(strategy.trading_records)
                trade_dates = pd.to_datetime(trades_df['date'])
                trade_counts = trade_dates.value_counts().sort_index()
                
                axes[1, 1].bar(trade_counts.index, trade_counts.values, 
                             color='#C73E1D', alpha=0.7)
                axes[1, 1].set_title('每日交易次数', fontsize=12, fontweight='bold')
                axes[1, 1].set_ylabel('交易次数')
                axes[1, 1].grid(True, alpha=0.3)
                axes[1, 1].tick_params(axis='x', rotation=45)
            else:
                axes[1, 1].text(0.5, 0.5, '无交易记录', 
                              horizontalalignment='center', verticalalignment='center',
                              transform=axes[1, 1].transAxes, fontsize=12)
                axes[1, 1].set_title('每日交易次数', fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            
            # 保存图表
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"✅ 图表已保存到: {save_path}")
            
            plt.show()
            
        except Exception as e:
            print(f"❌ 生成图表失败: {e}")


def generate_backtest_summary(strategy) -> str:
    """
    生成回测摘要（文本格式）
    
    Args:
        strategy: 策略实例
        
    Returns:
        str: 回测摘要文本
    """
    generator = ReportGenerator()
    report = generator.generate_basic_report(strategy)
    
    if not report:
        return "暂无回测数据"
    
    summary = f"""
🎯 z哥选股策略回测摘要
====================

📊 基础指标
- 初始资金: {report['initial_capital']:,.2f}元
- 最终资金: {report['final_value']:,.2f}元  
- 总收益率: {report['total_return']:.2f}%
- 年化收益率: {report['annual_return']:.2f}%
- 最大回撤: {report['max_drawdown']:.2f}%
- 交易次数: {report['trades_count']}次

💡 策略表现评估
- 收益率表现: {'优秀' if report['total_return'] > 20 else '良好' if report['total_return'] > 0 else '一般' if report['total_return'] > -10 else '较差'}
- 风险控制: {'优秀' if report['max_drawdown'] > -5 else '良好' if report['max_drawdown'] > -10 else '一般' if report['max_drawdown'] > -20 else '较差'}

⚠️ 注意事项
- 回测结果仅供参考，不构成投资建议
- 实际交易可能因市场条件变化而有所不同
"""
    
    return summary