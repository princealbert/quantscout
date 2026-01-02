#!/usr/bin/env python
# coding=utf-8
"""
报告生成模块 - 负责生成回测报告和分析结果
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, Any, List
from datetime import datetime
import json


class ReportGenerator:
    """报告生成器 - 负责生成各种类型的回测报告"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.plt_style = 'seaborn-v0_8-whitegrid'    
    
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
夏普比率: {basic_report['sharpe_ratio']:.2f}
胜率: {basic_report['win_rate']:.2f}%
交易次数: {basic_report['trades_count']}次
止盈比例: {basic_report['stop_profit_ratio']*100:.2f}%
止损比例: {basic_report['stop_loss_ratio']*100:.2f}%
{'=' * 40}
"""
        
        return summary
        
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
        
        # 打印报告
        print("\n" + "="*60)
        print("📊 回测报告")
        print("="*60)
        print(f"初始资金: {initial_value:,.2f}元")
        print(f"最终资金: {final_value:,.2f}元")
        print(f"总收益率: {total_return:.2f}%")
        print(f"年化收益率: {annual_return_pct:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"胜率: {win_rate:.2f}%")
        print(f"交易次数: {len(trades_df)}次")
        print(f"止盈比例: {strategy.params.stop_profit_ratio*100:.2f}%")
        print(f"止损比例: {strategy.params.stop_loss_ratio*100:.2f}%")
        
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
        print(f"[报告生成] 开始生成详细回测报告")
        basic_report = self.generate_basic_report(strategy)
        
        if not basic_report:
            print(f"[报告生成] 基础报告生成失败，无法生成详细报告")
            return {}
        
        # 计算更多指标
        trades_df = pd.DataFrame(strategy.trading_records)
        portfolio_df = pd.DataFrame(strategy.portfolio_values, columns=['date', 'value'])
        print(f"[报告生成] 交易记录数: {len(strategy.trading_records)}, 组合价值记录数: {len(strategy.portfolio_values)}")
        
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
            'volatility': volatility,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    
    def _save_report_to_file(self, report_data: Dict[str, Any], file_path: str = None):
        """
        保存报告到文件
        
        Args:
            report_data: 报告数据
            file_path: 报告保存路径，默认为None（自动生成带时间戳的文件名）
        """
        try:
            import os
            import time
            # 始终保存固定名称的文件，用于参数优化器快速读取
            # 但添加时间延迟，确保不同参数组合的结果不会被覆盖
            current_dir = os.path.dirname(os.path.abspath(__file__))
            fixed_file_name = os.path.join(current_dir, "backtest_report.json")
            
            # 转换报告数据格式，使其与parameter_optimizer.py的预期一致
            optimized_report = {
                "performance_metrics": {
                    "total_return": report_data.get("total_return", 0.0),
                    "annual_return": report_data.get("annual_return", 0.0),
                    "max_drawdown": report_data.get("max_drawdown", 0.0),
                    "sharpe_ratio": report_data.get("sharpe_ratio", 0.0)
                },
                "trade_statistics": {
                    "total_trades": report_data.get("trades_count", 0),
                    "win_rate": report_data.get("win_rate", 0.0)
                }
            }
            
            # 确保不同参数组合的结果不会被覆盖，添加短暂延迟
            time.sleep(0.1)  # 100毫秒延迟
            
            # 保存固定名称报告文件
            with open(fixed_file_name, 'w', encoding='utf-8') as f:
                json.dump(optimized_report, f, ensure_ascii=False, indent=2, default=str)
            print(f"✅ 固定名称报告已保存到: {fixed_file_name}")
            print(f"✅ 固定名称报告内容: {json.dumps(optimized_report, ensure_ascii=False, indent=2)}")
            
            # 生成带时间戳的文件名，用于长期保存
            if not file_path:
                # 强制使用正确的时间戳格式，避免文件名包含空格
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")  # 添加微秒，确保唯一性
                report_dir = "backtest_reports"
                if not os.path.exists(report_dir):
                    os.makedirs(report_dir)
                file_path = f"{report_dir}/backtest_report_{timestamp}.json"

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


