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


class OptimizedReportGenerator:
    """优化版报告生成器 - 负责生成基础回测报告（无可视化图表）"""
    
    def __init__(self, params, initial_capital):
        """初始化优化版报告生成器
        
        Args:
            params: 策略参数
            initial_capital: 初始资金
        """
        self.params = params
        self.initial_capital = initial_capital
    
    def generate_basic_report(self, context, indicator_data):
        """
        生成基础回测报告
        
        Args:
            context: 回测上下文
            indicator_data: 指标数据
        """
        print(f"调试: report_generator.generate_basic_report - 开始生成回测报告")
        
        # 获取账户信息
        account_info = context.account()
        
        # 计算最终资金（现金+持仓市值）
        final_capital = 0.0
        
        # 安全获取现金数值
        cash = account_info.cash
        if isinstance(cash, dict):
            # 优先使用可用资金
            cash_value = float(cash.get('available', 0.0))
        elif hasattr(cash, 'available'):
            cash_value = float(cash.available)
        elif hasattr(cash, 'value'):
            cash_value = float(cash.value)
        elif hasattr(cash, 'amount'):
            cash_value = float(cash.amount)
        else:
            # 尝试直接转换，如果失败则使用安全默认值
            cash_value = float(cash) if cash else 0.0
        
        final_capital += cash_value
        
        # 加上持仓市值
        try:
            positions = account_info.positions()
            for position in positions:
                # 获取持仓数量
                volume = position.volume
                if hasattr(volume, 'value'):
                    volume_value = float(volume.value)
                else:
                    volume_value = float(volume) if volume else 0.0
                
                # 获取持仓价格
                price = position.price
                if hasattr(price, 'value'):
                    price_value = float(price.value)
                else:
                    price_value = float(price) if price else 0.0
                
                # 加上持仓市值
                final_capital += price_value * volume_value
        except Exception as e:
            print(f"调试: report_generator.generate_basic_report - 获取持仓信息失败: {e}")
        
        # 确保self.initial_capital不为None
        initial_capital = 0.0 if self.initial_capital is None else float(self.initial_capital)
        print(f"调试: report_generator.generate_basic_report - 账户信息: 初始资金={initial_capital:.2f}元, 最终资金={final_capital:.2f}元")
        
        # 计算总收益率
        total_return = 0.0
        if initial_capital > 0:
            total_return = (final_capital - initial_capital) / initial_capital * 100
        print(f"调试: report_generator.generate_basic_report - 总收益率: {total_return:.2f}%")
        
        # 简单计算年化收益率（基于回测天数）
        annual_return = 0.0
        backtest_days = getattr(self.params, 'backtest_days', 1)
        if backtest_days > 0:
            annual_return = total_return / (backtest_days / 365)
        print(f"调试: report_generator.generate_basic_report - 年化收益率: {annual_return:.2f}%")
        
        # 计算交易次数
        # 优先使用strategy.trading_records，因为context.history().transactions可能为空
        trades = []
        if hasattr(self, 'trading_records') and self.trading_records:
            trades = self.trading_records
            print(f"调试: report_generator.generate_basic_report - 使用strategy.trading_records，交易记录数: {len(trades)}")
        else:
            trades = context.history().transactions
            print(f"调试: report_generator.generate_basic_report - 使用context.history().transactions，交易记录数: {len(trades)}")
        trades_count = len(trades)
        
        # 计算胜率
        win_rate = 0.0
        if trades_count > 1:
            # 将交易记录转换为DataFrame以便计算
            import pandas as pd
            trades_df = pd.DataFrame(trades)
            
            buy_trades = trades_df[trades_df['action'] == 'BUY']
            sell_trades = trades_df[trades_df['action'] == 'SELL']
            
            if len(buy_trades) > 0 and len(sell_trades) > 0:
                win_trades = 0
                total_trades = len(sell_trades)
                
                for i, sell_trade in sell_trades.iterrows():
                    symbol = sell_trade['symbol']
                    # 找到对应的买入交易
                    matching_buys = buy_trades[buy_trades['symbol'] == symbol]
                    if not matching_buys.empty:
                        buy_trade = matching_buys.iloc[-1]  # 使用最后一次买入
                        if sell_trade['price'] > buy_trade['price']:
                            win_trades += 1
                
                win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0.0
        print(f"调试: report_generator.generate_basic_report - 胜率: {win_rate:.2f}%")
        
        # 计算夏普比率（简化版）
        sharpe_ratio = 0.0
        try:
            # 获取组合价值数据用于计算夏普比率
            if indicator_data and isinstance(indicator_data, dict):
                portfolio_values = indicator_data.get('portfolio_values', [])
                if portfolio_values and len(portfolio_values) > 1:
                    import pandas as pd
                    import numpy as np
                    
                    # 计算日收益率
                    values = [float(pv['value']) for pv in portfolio_values if 'value' in pv]
                    if len(values) > 1:
                        returns = np.diff(values) / values[:-1]
                        
                        # 年化收益率
                        annual_return_val = annual_return / 100  # 转换为小数
                        
                        # 计算年化波动率
                        annualized_volatility = returns.std() * np.sqrt(252)
                        
                        if annualized_volatility > 0:
                            # 无风险利率假设为2%
                            risk_free_rate = 0.02
                            sharpe_ratio = (annual_return_val - risk_free_rate) / annualized_volatility
        except Exception as e:
            print(f"调试: report_generator.generate_basic_report - 计算夏普比率失败: {e}")
        print(f"调试: report_generator.generate_basic_report - 夏普比率: {sharpe_ratio:.2f}")
        
        # 打印基本报告信息
        # 确保所有报告数据字段都不为None，避免后续处理错误
        max_drawdown = 0.0
        if indicator_data and isinstance(indicator_data, dict):
            max_drawdown_value = indicator_data.get('max_drawdown', 0)
            max_drawdown = 0.0 if max_drawdown_value is None else float(max_drawdown_value)
        
        # 从params获取值时添加安全检查
        strategy_id = getattr(self.params, 'strategy_id', 'default_strategy_id')
        stop_profit_ratio = getattr(self.params, 'stop_profit_ratio', 0.0)
        stop_loss_ratio = getattr(self.params, 'stop_loss_ratio', 0.0)
        backtest_days = getattr(self.params, 'backtest_days', 0)
        
        report_data = {
            "strategy_id": strategy_id,
            "initial_capital": initial_capital,
            "final_capital": final_capital,
            "total_return": total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "win_rate": win_rate,
            "trades_count": trades_count,
            "stop_profit_ratio": stop_profit_ratio,
            "stop_loss_ratio": stop_loss_ratio,
            "backtest_days": backtest_days,
            "trading_records": trades,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        print(f"调试: report_generator.generate_basic_report - 完整报告数据: {json.dumps(report_data, ensure_ascii=False, indent=2)}")
        
        # 打印基本报告
        print(f"\n回测完成: 总收益率 {total_return:.2f}%, 年化收益率 {annual_return:.2f}%, 交易次数 {trades_count}")
        
        # 保存报告到文件
        self._save_report_to_file(report_data)
        
        return report_data
    
    def _save_report_to_file(self, report_data: Dict[str, Any], save_path: str = None):
        """保存报告到文件"""
        try:
            print(f"调试: report_generator._save_report_to_file - 开始保存报告到文件")
            
            # 创建报告目录
            report_dir = "backtest_reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
                print(f"调试: report_generator._save_report_to_file - 创建报告目录: {report_dir}")
            
            # 生成带时间戳的文件名，用于长期保存
            timestamp = report_data.get("timestamp", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            file_name = f"{report_dir}/backtest_report_{timestamp}.json"
            print(f"调试: report_generator._save_report_to_file - 保存时间戳报告到: {file_name}")
            
            # 保存到带时间戳的文件
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"调试: report_generator._save_report_to_file - 时间戳报告保存成功")
            
            # 同时保存一个固定名称的文件，用于参数优化器快速读取
            fixed_file_name = "backtest_report.json"
            print(f"调试: report_generator._save_report_to_file - 保存固定名称报告到: {fixed_file_name}")
            
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
            
            print(f"调试: report_generator._save_report_to_file - 优化后报告内容: {json.dumps(optimized_report, ensure_ascii=False, indent=2)}")
            
            with open(fixed_file_name, 'w', encoding='utf-8') as f:
                json.dump(optimized_report, f, ensure_ascii=False, indent=2, default=str)
            print(f"调试: report_generator._save_report_to_file - 固定名称报告保存成功")
            
        except Exception as e:
            print(f"调试: report_generator._save_report_to_file - 保存报告失败: {e}")
            import traceback
            traceback.print_exc()


class ReportGenerator:
    """报告生成器 - 负责生成各种类型的回测报告"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.plt_style = 'seaborn-v0_8-whitegrid'
        
    def _save_report_to_file(self, report_data: Dict[str, Any]):
        """保存报告到文件"""
        try:
            print(f"调试: report_generator._save_report_to_file - 开始保存报告到文件")
            
            # 创建报告目录
            report_dir = "backtest_reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
                print(f"调试: report_generator._save_report_to_file - 创建报告目录: {report_dir}")
            
            # 生成带时间戳的文件名，用于长期保存
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"{report_dir}/backtest_report_{timestamp}.json"
            print(f"调试: report_generator._save_report_to_file - 保存时间戳报告到: {file_name}")
            
            # 保存到带时间戳的文件
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"调试: report_generator._save_report_to_file - 时间戳报告保存成功")
            
            # 同时保存一个固定名称的文件，用于参数优化器快速读取
            fixed_file_name = "backtest_report.json"
            print(f"调试: report_generator._save_report_to_file - 保存固定名称报告到: {fixed_file_name}")
            
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
            
            print(f"调试: report_generator._save_report_to_file - 优化后报告内容: {json.dumps(optimized_report, ensure_ascii=False, indent=2)}")
            
            with open(fixed_file_name, 'w', encoding='utf-8') as f:
                json.dump(optimized_report, f, ensure_ascii=False, indent=2, default=str)
            print(f"调试: report_generator._save_report_to_file - 固定名称报告保存成功")
            
        except Exception as e:
            print(f"调试: report_generator._save_report_to_file - 保存报告失败: {e}")
            import traceback
            traceback.print_exc()
    
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
            
            # 构建基础报告数据
            return {
                'initial_capital': initial_value,
                'final_value': final_value,
                'total_return': total_return,
                'annual_return': annual_return_pct,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': 0.0,  # 添加默认夏普比率
                'win_rate': 0.0,  # 添加默认胜率
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
        print(f"止盈比例: {strategy.params.stop_profit_ratio*100:.2f}%")
        print(f"止损比例: {strategy.params.stop_loss_ratio*100:.2f}%")
        
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
            'sharpe_ratio': 0.0,  # 添加默认夏普比率
            'win_rate': 0.0,  # 添加默认胜率
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
        
        # 计算胜率
        print(f"[报告生成] 开始计算胜率")
        if len(trades_df) > 1:
            buy_trades = trades_df[trades_df['action'] == 'BUY']
            sell_trades = trades_df[trades_df['action'] == 'SELL']
            print(f"[报告生成] 买入交易数: {len(buy_trades)}, 卖出交易数: {len(sell_trades)}")
            
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
                print(f"[报告生成] 胜率计算完成: 盈利交易数={win_trades}, 总交易数={total_trades}, 胜率={win_rate:.2f}%")
            else:
                win_rate = 0
                print(f"[报告生成] 买入或卖出交易数不足，无法计算胜率")
        else:
            win_rate = 0
            print(f"[报告生成] 交易记录数不足，无法计算胜率")
        
        # 计算夏普比率（简化版）
        print(f"[报告生成] 开始计算夏普比率")
        portfolio_df['daily_return'] = portfolio_df['value'].pct_change()
        daily_returns = portfolio_df['daily_return'].dropna()
        
        if len(daily_returns) > 0:
            annualized_return = basic_report['annual_return'] / 100
            annualized_volatility = daily_returns.std() * np.sqrt(252)
            print(f"[报告生成] 日收益率记录数: {len(daily_returns)}, 年化收益率: {annualized_return:.4f}, 年化波动率: {annualized_volatility:.4f}")
            
            if annualized_volatility > 0:
                sharpe_ratio = annualized_return / annualized_volatility
                print(f"[报告生成] 夏普比率计算完成: {sharpe_ratio:.2f}")
            else:
                sharpe_ratio = 0
                print(f"[报告生成] 年化波动率为0，夏普比率设置为0")
        else:
            sharpe_ratio = 0
            print(f"[报告生成] 日收益率记录不足，夏普比率设置为0")
        
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
        """保存报告到文件"""
        try:
            if not file_path:
                # 生成带时间戳的文件名，用于长期保存
                timestamp = report_data.get("timestamp", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
                report_dir = "backtest_reports"
                if not os.path.exists(report_dir):
                    os.makedirs(report_dir)
                file_path = f"{report_dir}/backtest_report_{timestamp}.json"
                
                # 同时保存一个固定名称的文件，用于参数优化器快速读取
                fixed_file_name = "backtest_report.json"
                with open(fixed_file_name, 'w', encoding='utf-8') as f:
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
                    json.dump(optimized_report, f, ensure_ascii=False, indent=2, default=str)
                print(f"✅ 固定名称报告已保存到: {fixed_file_name}")

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


def generate_backtest_summary(strategy) -> str:
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
交易次数: 0次
止盈比例: {getattr(strategy.params, 'stop_profit_ratio', 0.0)*100:.2f}%
止损比例: {getattr(strategy.params, 'stop_loss_ratio', 0.0)*100:.2f}%
{'=' * 40}
"""
    
    # 生成基础报告
    report_generator = ReportGenerator()
    basic_report = report_generator.generate_basic_report(strategy)
    
    # 构建摘要文本
    summary = f"""
回测摘要
{'=' * 40}
初始资金: {basic_report['initial_capital']:,.2f}元
最终资金: {basic_report['final_capital']:,.2f}元
总收益率: {basic_report['total_return']:.2f}%
年化收益率: {basic_report['annual_return']:.2f}%
最大回撤: {basic_report['max_drawdown']:.2f}%
交易次数: {basic_report['trades_count']}次
止盈比例: {basic_report['stop_profit_ratio']*100:.2f}%
止损比例: {basic_report['stop_loss_ratio']*100:.2f}%
{'=' * 40}
"""
    
    return summary
