#!/usr/bin/env python
# coding=utf-8
"""
回测执行模块 - 负责回测的配置和执行
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from gm.api import *


class BacktestRunner:
    """回测执行器 - 负责回测的配置和执行"""
    
    def __init__(self, strategy_params=None):
        """
        初始化回测执行器
        
        Args:
            strategy_params: 策略参数配置对象
        """
        # 导入参数配置系统
        from config.strategy_params import StrategyParams
        
        # 使用传入参数或默认参数
        self.params = strategy_params if strategy_params else StrategyParams()
        
        # 导入策略类
        from .strategy import BacktestStrategy
        self.strategy = BacktestStrategy(strategy_params)
    
    def init(self, context):
        """策略初始化"""
        # 创建策略实例 - 使用参数化配置
        context.strategy = self.strategy
        
        # 设置每日定时任务
        schedule(schedule_func=self.daily_strategy, date_rule='1d', time_rule='09:30:00')
        
        # 显示参数配置信息
        params = self.params
        print("🎯 z哥选股策略回测系统初始化完成")
        print(f"💰 初始资金: {params.initial_capital:,}元")
        print(f"📊 佣金比例: {params.commission_ratio*10000}‱")
        print(f"📈 止盈比例: {params.stop_profit_ratio*100:.2f}%")
        print(f"📉 止损比例: {params.stop_loss_ratio*100:.2f}%")
        print(f"📅 回测天数: {params.backtest_days}天")
    
    def daily_strategy(self, context):
        """每日策略执行"""
        current_date = context.now.strftime('%Y-%m-%d')
        print(f"\n📅 交易日: {current_date}")
        
        strategy = context.strategy
        
        # 检查是否有持仓需要卖出
        account = context.account()
        has_position = False
        current_position = None
        needs_new_selection = False
        
        # 正确检查持仓：遍历所有持仓，找到实际有持仓的股票
        positions = account.positions()
        actual_positions = []
        
        for position in positions:
            # 安全获取持仓量
            volume = position.volume
            volume_value = float(volume.value) if hasattr(volume, 'value') else float(volume)
            
            if volume_value > 0:
                actual_positions.append(position)
                has_position = True
                current_position = position
                break
        
        # 如果有实际持仓，检查是否应该卖出
        if has_position and current_position:
            symbol = current_position.symbol
            # 这里简化处理，实际应该记录买入价格
            vwap = current_position.vwap
            # 安全获取持仓均价
            buy_price = float(vwap.value) if hasattr(vwap, 'value') else float(vwap)  # 使用持仓均价作为买入价
            
            if strategy.should_sell(context, symbol, buy_price):
                self._execute_sell(context, symbol)
                needs_new_selection = True  # 卖出后需要重新选股
                has_position = False
            else:
                print(f"✅ 持仓 {symbol} 无操作，跳过选股流程，提高回测效率")
        else:
            needs_new_selection = True  # 没有持仓，需要选股
        
        # 如果需要重新选股（没有持仓或刚卖出持仓），尝试买入
        if needs_new_selection:
            # 获取当日评分最高的股票
            top_stock = strategy.get_top_stock(context)
            
            if top_stock and strategy.should_buy(context, top_stock['symbol']):
                self._execute_buy(context, top_stock)
        
        # 记录当日组合价值
        portfolio_value = strategy.calculate_portfolio_value(context)
        
        # 确保portfolio_value是数值类型
        if isinstance(portfolio_value, dict):
            portfolio_value_num = portfolio_value.get('value', portfolio_value.get('total', 100000))
        else:
            portfolio_value_num = portfolio_value
        
        # 确保组合价值不会异常增长（防止重复计算）
        # 获取当前账户的实际资产
        account = context.account()
        
        # 安全获取现金数值
        cash = account.cash
        if isinstance(cash, dict):
            cash_value = float(cash.get('available', 0.0))
        elif hasattr(cash, 'available'):
            cash_value = float(cash.available)
        elif hasattr(cash, 'value'):
            cash_value = float(cash.value)
        elif hasattr(cash, 'amount'):
            cash_value = float(cash.amount)
        else:
            cash_value = float(cash) if cash else 0.0
        
        # 计算实际持仓市值
        positions_value = 0.0
        for position in account.positions():
            symbol = position.symbol
            from gm.api import current
            current_data = current(symbol)
            if current_data:
                # 安全获取价格数值
                price_data = current_data[0]['price']
                if hasattr(price_data, 'value'):
                    current_price = float(price_data.value)
                else:
                    current_price = float(price_data) if price_data else 0.0
                
                # 安全获取持仓量
                volume = position.volume
                volume_value = float(volume.value) if hasattr(volume, 'value') else float(volume)
                
                positions_value += current_price * volume_value
        
        # 使用实际计算的组合价值，避免异常增长
        actual_portfolio_value = cash_value + positions_value
        
        strategy.portfolio_values.append({
            'date': context.now,
            'value': actual_portfolio_value
        })
        
        print(f"💰 当日组合价值: {actual_portfolio_value:,.2f}元")
    
    def _execute_buy(self, context, stock_info: Dict[str, str]) -> bool:
        """执行买入操作"""
        try:
            symbol = stock_info['symbol']
            sec_name = stock_info.get('sec_name', symbol)
            
            # 获取当前价格
            current_data = current(symbol)
            if not current_data:
                return False
                
            # 安全获取价格数值
            price_data = current_data[0]['price']
            if hasattr(price_data, 'value'):
                current_price = float(price_data.value)
            else:
                current_price = float(price_data) if price_data else 0.0
            
            # 计算可买入数量（全仓买入）
            cash = context.account().cash
            
            # 安全获取现金数值 - 根据文档，cash是dict类型
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
            
            commission = cash_value * self.params.commission_ratio
            available_cash = cash_value - commission
            
            # 计算可买入股数（100股为单位）
            quantity = int(available_cash / current_price / 100) * 100
            
            if quantity <= 0:
                print("资金不足，无法买入")
                return False
            
            # 执行买入
            order_volume(symbol=symbol, volume=quantity, side=OrderSide_Buy, 
                        order_type=OrderType_Market, position_effect=PositionEffect_Open)
            
            # 记录交易
            trade_record = {
                'date': context.now,
                'symbol': symbol,
                'sec_name': sec_name,
                'action': 'BUY',
                'price': current_price,
                'quantity': quantity,
                'amount': current_price * quantity
            }
            self.strategy.trading_records.append(trade_record)
            
            print(f"买入成功: {symbol} ({sec_name}) {quantity}股, 价格{current_price:.2f}元")
            return True
            
        except Exception as e:
            print(f"买入失败: {e}")
            return False
    
    def _execute_sell(self, context, symbol: str) -> bool:
        """执行卖出操作"""
        try:
            # 获取持仓 - 使用positions()方法获取所有持仓，然后筛选
            positions = context.account().positions(symbol=symbol)
            if not positions:
                print(f"没有{symbol}的持仓")
                return False
            
            # 获取第一个持仓（通常只有一个）
            position = positions[0]
            
            # 安全获取持仓量
            volume = position.volume
            volume_value = float(volume.value) if hasattr(volume, 'value') else float(volume)
            
            if volume_value <= 0:
                print(f"没有{symbol}的持仓")
                return False
            
            # 获取当前价格
            current_data = current(symbol)
            if not current_data:
                return False
                
            # 安全获取价格数值
            price_data = current_data[0]['price']
            if hasattr(price_data, 'value'):
                current_price = float(price_data.value)
            else:
                current_price = float(price_data) if price_data else 0.0
            
            # 安全获取持仓量
            volume = position.volume
            volume_value = float(volume.value) if hasattr(volume, 'value') else float(volume)
            
            # 执行卖出（清仓）- volume参数需要int类型
            # 只有在回测期间才执行卖出操作，避免回测结束后调用已停止的服务
            try:
                order_volume(symbol=symbol, volume=int(volume_value), side=OrderSide_Sell, 
                            order_type=OrderType_Market, position_effect=PositionEffect_Close)
            except Exception as order_error:
                # 捕获回测服务调用错误
                error_msg = str(order_error)
                if "回测服务调用错误" in error_msg or "1018" in error_msg:
                    print(f"回测服务已结束，跳过卖出操作: {symbol}")
                    return False
                else:
                    # 其他错误继续抛出
                    raise
            
            # 尝试获取股票名称
            sec_name = symbol
            # 从最新的买入记录中查找该股票的名称
            for trade in reversed(self.strategy.trading_records):
                if trade['symbol'] == symbol and trade['action'] == 'BUY':
                    sec_name = trade.get('sec_name', symbol)
                    break
            
            # 记录交易
            trade_record = {
                'date': context.now,
                'symbol': symbol,
                'sec_name': sec_name,
                'action': 'SELL',
                'price': current_price,
                'quantity': volume_value,
                'amount': current_price * volume_value
            }
            self.strategy.trading_records.append(trade_record)
            
            print(f"卖出成功: {symbol} ({sec_name}) {volume_value}股, 价格{current_price:.2f}元")
            return True
            
        except Exception as e:
            print(f"卖出失败: {e}")
            return False
    
    def on_backtest_finished(self, context, indicator):
        """回测结束回调"""
        print("\n" + "="*60)
        print("🎯 回测完成")
        print("="*60)
        
        # 显示回测指标
        if indicator:
            print(f"最终净值: {indicator.get('pnl_ratio', 0)*100:.2f}%")
            print(f"年化收益率: {indicator.get('annualized_return', 0)*100:.2f}%")
            print(f"最大回撤: {indicator.get('max_drawdown', 0)*100:.2f}%")
        
        # 回测结束时不执行强制平仓操作，因为回测服务已停止接受新订单
        # 回测引擎会自动处理所有未平仓头寸
        
        # 生成基础报告（不再生成Excel报告）
        try:
            from .report_generator import ReportGenerator
            report_generator = ReportGenerator()
            # 生成并保存基础报告
            import os
            from datetime import datetime
            report_data = report_generator.generate_basic_report(self.strategy)
            
            # 创建backtest_reports目录（如果不存在）
            project_root = os.path.dirname(os.path.dirname(__file__))
            reports_dir = os.path.join(project_root, 'backtest_reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")[:-3]  # 保留毫秒
            report_file = os.path.join(reports_dir, f'backtest_report_{timestamp}.json')
            
            # 保存到带时间戳的文件
            report_generator._save_report_to_file(report_data, report_file)
            
            # 同时保存到固定名称文件，兼容参数优化器
            fixed_report_file = os.path.join(project_root, 'backtest_report.json')
            report_generator._save_report_to_file(report_data, fixed_report_file)
            
            print(f"✅ 回测报告已生成: {report_file}")
            print(f"✅ 固定名称报告已保存到: {fixed_report_file}")
        except Exception as e:
            print(f"生成报告失败: {e}")


def run_backtest(config: Dict[str, Any] = None, config_path: str = None):
    """
    运行回测的主函数
    
    Args:
        config: 回测配置参数
        config_path: 前端生成的JSON配置文件路径
    """
    # 检查是否提供了前端配置文件路径
    if config_path:
        try:
            from strategy_engine.config_manager import FrontendConfigLoader
            
            # 加载前端配置文件
            frontend_config = FrontendConfigLoader.load_frontend_config(config_path)
            if frontend_config:
                # 验证前端配置
                validation_result = FrontendConfigLoader.validate_frontend_config(frontend_config)
                if validation_result['is_valid']:
                    print("✅ 前端配置验证通过")
                    
                    # 转换为策略参数格式
                    strategy_params = FrontendConfigLoader.convert_to_strategy_params(frontend_config)
                    
                    # 显示配置信息
                    print("🎯 z哥选股策略回测系统 - 前端配置模式")
                    print("="*50)
                    print(f"💰 初始资金: {strategy_params.get('initial_capital', 100000):,}元")
                    print(f"📊 佣金比例: {strategy_params.get('commission_ratio', 0.0003)*10000}‱")
                    print(f"📈 止盈比例: {strategy_params.get('stop_profit_ratio', 0.03)*100:.2f}%")
                    print(f"📉 止损比例: {strategy_params.get('stop_loss_ratio', -0.02)*100:.2f}%")
                    print(f"📅 回测天数: {strategy_params.get('backtest_days', 90)}天")
                    print(f"🎯 策略ID: {strategy_params.get('strategy_id', 'zge_strategy')}")
                    print(f"📈 回测股票数量: {strategy_params.get('max_stocks_to_backtest', 1)}只")
                    print("="*50)
                    
                    # 计算回测期间
                    end_date = datetime.now()
                    #end_date = datetime(2025, 12, 30)
                    start_date = end_date - timedelta(days=strategy_params.get('backtest_days', 90))
                    
                    # 导入参数配置系统
                    from config.strategy_params import set_current_params
                    
                    # 设置当前策略参数
                    set_current_params(strategy_params)
                    
                    # 获取当前策略参数
                    from config.strategy_params import get_current_params
                    params = get_current_params()
                    
                else:
                    print("❌ 前端配置验证失败:")
                    for issue in validation_result['issues']:
                        print(f"   - {issue}")
                    return
        except Exception as e:
            print(f"❌ 加载前端配置失败: {e}")
            return
    else:
        # 使用参数化配置系统
        try:
            from config.strategy_params import get_current_params
            
            # 获取当前策略参数
            params = get_current_params()
            
            print("🎯 z哥选股策略回测系统 - 参数化配置")
            print("="*50)
            print(f"💰 初始资金: {params.initial_capital:,}元")
            print(f"📊 佣金比例: {params.commission_ratio*10000}‱")
            print(f"📈 止盈比例: {params.stop_profit_ratio*100:.2f}%")
            print(f"📉 止损比例: {params.stop_loss_ratio*100:.2f}%")
            print(f"📅 回测天数: {params.backtest_days}天")
            print(f"🎯 策略ID: {params.strategy_id}")
            print(f"📊 股票池限制: {params.stock_pool_limit}只")
            print(f"📈 回测股票数量: {params.max_stocks_to_backtest}只")
            print("="*50)
            
            # 计算回测期间
            end_date = datetime.now()
            start_date = end_date - timedelta(days=params.backtest_days)
            
        except ImportError as e:
            print(f"⚠️ 参数配置系统导入失败，使用默认参数: {e}")
            # 使用默认参数作为后备
            from config.strategy_params import default_params
            params = default_params
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=params.backtest_days)
    
    # 使用token管理器获取token
    try:
        from strategy_engine.token_manager import get_token
        actual_token = get_token()
        print(f"✅ Token验证通过，长度: {len(actual_token)}位")
    except Exception as e:
        print(f"❌ Token配置错误: {e}")
        print("请检查token_config.py文件中的TOKEN配置")
        return
    
    # 运行回测
    run(
        strategy_id=params.strategy_id,
        filename='main.py',
        mode=MODE_BACKTEST,
        token=actual_token,
        backtest_start_time=start_date.strftime('%Y-%m-%d 09:30:00'),
        backtest_end_time=end_date.strftime('%Y-%m-%d 15:00:00'),
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=params.initial_capital,
        backtest_commission_ratio=params.commission_ratio,
        backtest_slippage_ratio=0.0001
    )