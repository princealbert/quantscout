#!/usr/bin/env python
# coding=utf-8
"""
策略逻辑模块 - 纯策略逻辑实现
负责策略的买卖决策、选股逻辑等核心业务
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional


class BacktestStrategy:
    """回测策略类 - 纯策略逻辑实现"""
    
    def __init__(self, strategy_params=None):
        """
        初始化回测参数
        
        Args:
            strategy_params: 策略参数配置对象
        """
        # 灵活导入参数配置系统
        try:
            from .config.strategy_params import StrategyParams
        except ImportError:
            from config.strategy_params import StrategyParams
        
        # 使用传入参数或默认参数
        self.params = strategy_params if strategy_params else StrategyParams()
        
        # 设置基础参数
        self.commission_ratio = self.params.commission_ratio
        self.trading_records = []
        self.portfolio_values = []
        self.daily_returns = []
        
        # 从参数中获取初始资金
        self.initial_capital = self.params.initial_capital
        print(f"BacktestStrategy初始化 - 从params获取初始资金={self.initial_capital}")
        
        # 记录接收的参数
        print(f"策略初始化完成")
        print(f"止盈比例={self.params.stop_profit_ratio}")
        print(f"止损比例={self.params.stop_loss_ratio}")
        print(f"权重配置={self.params.weights_config}")
        print(f"子权重配置={self.params.sub_weights_config}")
        print(f"股票池限制={self.params.stock_pool_limit}")
        
        # 缓存机制 - 用于提高性能
        self._price_cache = {}
        self._last_cache_date = None
    
    def get_top_stock(self, context) -> Optional[Dict[str, str]]:
        """
        获取当日综合评分最高的股票
        集成现有的zge选股系统
        
        Returns:
            Dict: 包含股票代码和名称的字典，如果没有符合条件的股票则返回None
        """
        try:
            # 获取当前日期
            current_date = context.now.strftime('%Y-%m-%d')
            
            # 尝试调用现有的选股系统
            try:
                import json
                import os
                from strategies.zge_strategy import ZGeStrategyScreener
                from scoring.comprehensive_scorer import ComprehensiveScorer
                
                # 加载权重配置 - 使用参数化配置
                weights_config = self.params.weights_config
                sub_weights_config = self.params.sub_weights_config
                
                # 如果参数中没有配置权重，尝试从文件加载
                if not weights_config:
                    weights_configs = self.params.load_weights_from_file()
                    if weights_configs:
                        weights_config = weights_configs.get('weights_config')
                        sub_weights_config = weights_configs.get('sub_weights_config')
                        print(f"[{current_date}] 成功加载权重配置")
                        print(f"[{current_date}] 权重配置: {weights_config}")
                        print(f"[{current_date}] 子权重配置: {sub_weights_config}")
                    else:
                        print(f"[{current_date}] 使用默认权重配置")
                
                # 创建选股器实例
                screener = ZGeStrategyScreener(
                    batch_size=100,  # 小批量处理，适应回测环境
                    max_workers=2,   # 减少线程数，避免资源竞争
                    weights_config=weights_config,  # 使用碗选股策略权重
                    sub_weights_config=sub_weights_config
                )
                
                # 获取真实股票池（调用选股系统的get_stock_pool方法）
                current_date = context.now.strftime('%Y-%m-%d')
                print(f"[{current_date}] 获取真实股票池...")
                stock_pool = screener.get_stock_pool(skip_st=True, stock_pool_type='全量A股')
                
                if not stock_pool:
                    print(f"[{current_date}] 无法获取股票池")
                    return None
                
                print(f"[{current_date}] 股票池大小: {len(stock_pool)}只")
                
                # 处理股票数据
                processed_stocks = screener.process_stock_batch(stock_pool, current_date)
                
                if processed_stocks:
                    print(f"[{current_date}] 处理完成的股票数量: {len(processed_stocks)}只")
                    
                    # 按综合评分排序（选股系统已经计算了评分）
                    scored_stocks = sorted(processed_stocks, 
                                         key=lambda x: x.get('total_score', 0), 
                                         reverse=True)
                    
                    if scored_stocks and scored_stocks[0].get('total_score', 0) > 0:
                        top_stock = scored_stocks[0]
                        symbol = top_stock.get('symbol')
                        score = top_stock.get('total_score', 0)
                        sec_name = top_stock.get('sec_name', '未知股票')
                        
                        print(f"[{current_date}] 选股结果: {symbol} ({sec_name}), 评分: {score:.2f}")
                        return {
                            'symbol': symbol,
                            'sec_name': sec_name
                        }
                    else:
                        print(f"[{current_date}] 未找到符合条件的股票")
                        return None
                else:
                    print(f"[{current_date}] 无法获取股票数据")
                    return None
                    
            except ImportError as e:
                print(f"选股系统导入失败，使用备用方案: {e}")
                # 备用方案：使用参数化配置的股票列表
                import random
                selected_symbol = random.choice(self.params.fallback_stocks)
                
                print(f"[{current_date}] 备用选股结果: {selected_symbol}")
                return {
                    'symbol': selected_symbol,
                    'sec_name': selected_symbol  # 备用方案下，股票名称使用代码
                }
            
        except Exception as e:
            print(f"选股失败: {e}")
            return None
    
    def should_buy(self, context, symbol: str) -> bool:
        """
        判断是否应该买入
        
        Args:
            context: 策略上下文
            symbol: 股票代码
            
        Returns:
            bool: 是否买入
        """
        try:
            from gm.api import current
            
            # 获取当前价格
            current_data = current(symbol)
            if not current_data:
                print(f"should_buy - 获取价格失败，current_data={current_data}")
                return False
                
            # 安全获取价格数值
            price_data = current_data[0]['price']
            if hasattr(price_data, 'value'):
                current_price = float(price_data.value)
            else:
                current_price = float(price_data) if price_data else 0.0
            
            # 简单买入条件：有资金且价格合理
            account = context.account()
            
            # 正确获取现金余额的方式
            cash = account.cash
            
            # 尝试安全获取现金数值 - 根据文档，cash是dict类型
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
            
            print(f"should_buy - 现金={cash_value:.2f}元, 股价={current_price:.2f}元, 需要资金={current_price*100:.2f}元")
            
            if cash_value > current_price * 100:  # 至少能买100股
                print(f"买入条件满足: 现金{cash_value:.2f}元, 股价{current_price:.2f}元")
                return True
            else:
                print(f"买入条件不满足: 现金{cash_value:.2f}元不足购买100股")
                return False
            
        except Exception as e:
            print(f"买入判断失败: {e}")
            return False
    
    def _get_stock_price(self, symbol: str, context) -> float:
        """
        获取股票价格，带缓存机制
        
        Args:
            symbol: 股票代码
            context: 策略上下文
            
        Returns:
            float: 股票当前价格
        """
        from gm.api import current
        
        # 检查缓存是否有效（同一天内缓存有效）
        current_date = context.now.strftime('%Y-%m-%d')
        if self._last_cache_date != current_date:
            # 新的一天，清空缓存
            self._price_cache.clear()
            self._last_cache_date = current_date
        
        # 检查缓存中是否有该股票的价格
        if symbol in self._price_cache:
            return self._price_cache[symbol]
        
        # 缓存中没有，调用current获取价格
        current_data = current(symbol)
        if not current_data:
            return 0.0
            
        # 安全获取价格数值
        price_data = current_data[0]['price']
        if hasattr(price_data, 'value'):
            current_price = float(price_data.value)
        else:
            current_price = float(price_data) if price_data else 0.0
        
        # 保存到缓存
        self._price_cache[symbol] = current_price
        return current_price
    
    def should_sell(self, context, symbol: str, buy_price: float) -> bool:
        """
        判断是否应该卖出
        
        Args:
            context: 策略上下文
            symbol: 股票代码
            buy_price: 买入价格
            
        Returns:
            bool: 是否卖出
        """
        try:
            # 获取当前价格（使用缓存）
            current_price = self._get_stock_price(symbol, context)
            if current_price <= 0:
                print(f"should_sell - 获取价格失败")
                return False
            
            print(f"should_sell - 当前价格={current_price:.2f}元, 买入价格={buy_price:.2f}元")
            
            # 止盈止损条件 - 使用参数化配置
            profit_ratio = (current_price - buy_price) / buy_price
            
            # 使用参数化配置的止盈止损比例
            stop_profit_ratio = self.params.stop_profit_ratio
            stop_loss_ratio = self.params.stop_loss_ratio
            
            print(f"should_sell - 收益率={profit_ratio*100:.2f}%, 止盈阈值={stop_profit_ratio*100:.2f}%, 止损阈值={stop_loss_ratio*100:.2f}%")
            
            if profit_ratio >= stop_profit_ratio:  # 止盈
                print(f"止盈触发: 盈利{profit_ratio*100:.2f}% (阈值{stop_profit_ratio*100:.2f}%)")
                return True
            elif profit_ratio <= stop_loss_ratio:  # 止损
                print(f"止损触发: 亏损{profit_ratio*100:.2f}% (阈值{stop_loss_ratio*100:.2f}%)")
                return True
            else:
                print(f"should_sell - 未达到止盈止损条件")
                return False
            
        except Exception as e:
            print(f"卖出判断失败: {e}")
            return False
    
    def calculate_portfolio_value(self, context) -> float:
        """计算组合价值"""
        try:
            account = context.account()
            
            # 安全获取现金数值 - 根据文档，cash是dict类型
            cash = account.cash
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
    
            # 初始化初始资金 - 如果还没有设置的话（作为后备方案）
            if self.initial_capital is None:
                self.initial_capital = cash_value
                print(f"调试: 初始资金已从账户现金设置为={self.initial_capital:.2f}元")
            else:
                # 如果initial_capital已经设置，确保它是数值类型
                self.initial_capital = float(self.initial_capital) if self.initial_capital else 0.0
    
            portfolio_value = cash_value
                
            # 加上持仓市值
            for position in account.positions():
                symbol = position.symbol
                # 使用带缓存的价格获取方法
                current_price = self._get_stock_price(symbol, context)
                
                if current_price > 0:
                    # 安全获取持仓量
                    volume = position.volume
                    volume_value = float(volume.value) if hasattr(volume, 'value') else float(volume)
                    
                    portfolio_value += current_price * volume_value
                
            # 防止组合价值异常增长（异常大的值可能是计算错误）
            # 组合价值不应超过初始资金的100倍，这是一个更合理的上限
            if portfolio_value > self.initial_capital * 100:
                # 检查持仓市值总和
                positions_value = 0
                for position in account.positions():
                    symbol = position.symbol
                    # 使用带缓存的价格获取方法
                    current_price = self._get_stock_price(symbol, context)
                    
                    if current_price > 0:
                        # 安全获取持仓量
                        volume = position.volume
                        volume_value = float(volume.value) if hasattr(volume, 'value') else float(volume)
                        
                        positions_value += current_price * volume_value
                
                # 如果持仓市值远小于组合价值，说明计算有误
                if positions_value < portfolio_value * 0.5:  # 持仓市值应至少占组合价值的50%
                    print(f"⚠️  警告: 组合价值异常高 ({portfolio_value:.2f}元)，已调整为合理值")
                    # 使用持仓市值+现金作为合理值
                    return cash_value + positions_value
            
            return portfolio_value
            
        except Exception as e:
            print(f"计算组合价值失败: {e}")
            # 确保返回值是数值类型
            return float(self.initial_capital) if self.initial_capital else 0.0
    
    def daily_strategy(self, context):
        """每日策略执行"""
        current_date = context.now.strftime('%Y-%m-%d')
        print(f"\n📅 交易日: {current_date}")
        print(f"daily_strategy开始执行")
        
        # 检查是否有持仓需要卖出
        account = context.account()
        has_position = False
        current_position = None
        
        positions = account.positions()
        print(f"持仓检查 - 持仓数量={len(positions)}")
        
        for position in positions:
            # 安全获取持仓量
            volume = position.volume
            volume_value = float(volume.value) if hasattr(volume, 'value') else float(volume)
            
            print(f"持仓检查 - 股票代码={position.symbol}, 持仓量={volume_value}")
            
            if volume_value > 0:
                has_position = True
                current_position = position
                print(f"发现持仓 - {position.symbol}, 持仓量={volume_value}")
                break
        
        print(f"持仓检查完成 - 结果={has_position}")
        
        # 如果有持仓，检查是否应该卖出
        if has_position and current_position:
            symbol = current_position.symbol
            # 这里简化处理，实际应该记录买入价格
            vwap = current_position.vwap
            # 安全获取持仓均价
            buy_price = float(vwap.value) if hasattr(vwap, 'value') else float(vwap)  # 使用持仓均价作为买入价
            
            if self.should_sell(context, symbol, buy_price):
                self._execute_sell(context, symbol)
                has_position = False
        
        # 如果没有持仓，尝试买入
        if not has_position:
            print(f"无持仓，开始选股流程")
            # 获取当日评分最高的股票
            top_stock = self.get_top_stock(context)
            
            print(f"get_top_stock返回结果={top_stock}")
            
            if top_stock:
                print(f"选股成功，开始判断买入条件 - 股票代码={top_stock['symbol']}")
                buy_decision = self.should_buy(context, top_stock['symbol'])
                print(f"should_buy判断结果={buy_decision}")
                
                if buy_decision:
                    print(f"买入条件满足，执行买入操作")
                    buy_result = self._execute_buy(context, top_stock)
                    print(f"_execute_buy返回结果={buy_result}")
            else:
                print(f"选股失败，没有符合条件的股票")
        
        # 记录当日组合价值
        portfolio_value = self.calculate_portfolio_value(context)
        
        # 确保portfolio_value是数值类型
        if isinstance(portfolio_value, dict):
            portfolio_value_num = portfolio_value.get('value', portfolio_value.get('total', 100000))
        else:
            portfolio_value_num = portfolio_value
        
        self.portfolio_values.append({
            'date': context.now,
            'value': portfolio_value_num
        })
        
        print(f"💰 当日组合价值: {portfolio_value_num:,.2f}元")
    
    def _execute_buy(self, context, stock_info: Dict[str, str]) -> bool:
        """执行买入操作"""
        try:
            symbol = stock_info['symbol']
            sec_name = stock_info.get('sec_name', symbol)
            
            print(f"_execute_buy - 开始执行买入操作，股票代码={symbol}, 名称={sec_name}")
            
            # 获取当前价格
            from gm.api import current
            current_data = current(symbol)
            if not current_data:
                print(f"_execute_buy - 获取价格失败")
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
        
            # 计算可买入数量（全仓买入）
            commission = cash_value * self.commission_ratio
            available_cash = cash_value - commission
            
            # 计算可买入股数（100股为单位）
            quantity = int(available_cash / current_price / 100) * 100
            
            print(f"_execute_buy - 佣金={commission:.2f}元, 可用资金={available_cash:.2f}元, 可买数量={quantity}股")
            
            if quantity <= 0:
                print("资金不足，无法买入")
                return False
            
            # 执行买入
            from gm.api import order_volume, OrderSide_Buy, OrderType_Market, PositionEffect_Open
            print(f"_execute_buy - 执行订单: {symbol}, 数量={quantity}, 类型=买入")
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
            self.trading_records.append(trade_record)
            
            print(f"买入成功: {symbol} ({sec_name}) {quantity}股, 价格{current_price:.2f}元")
            return True
            
        except Exception as e:
            print(f"买入失败: {e}")
            return False
    
    def _execute_sell(self, context, symbol: str) -> bool:
        """执行卖出操作"""
        try:
            # 获取持仓 - 使用positions()方法获取所有持仓，然后筛选
            from gm.api import current, order_volume, OrderSide_Sell, OrderType_Market, PositionEffect_Close
            print(f"_execute_sell - 开始执行卖出操作，股票代码={symbol}")
            positions = context.account().positions(symbol=symbol)
            print(f"_execute_sell - 持仓数量={len(positions)}")
            if not positions:
                print(f"没有{symbol}的持仓")
                return False
            
            # 获取第一个持仓（通常只有一个）
            position = positions[0]
            
            # 安全获取持仓量
            volume = position.volume
            volume_value = float(volume.value) if hasattr(volume, 'value') else float(volume)
            
            print(f"_execute_sell - 持仓数量={volume_value}股")
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
                print(f"_execute_sell - 执行订单: {symbol}, 数量={int(volume_value)}, 类型=卖出")
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
            for trade in reversed(self.trading_records):
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
            self.trading_records.append(trade_record)
            
            print(f"卖出成功: {symbol} ({sec_name}) {volume_value}股, 价格{current_price:.2f}元")
            return True
            
        except Exception as e:
            print(f"卖出失败: {e}")
            return False