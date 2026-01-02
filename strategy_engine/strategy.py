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
        # 导入参数配置系统
        from config.strategy_params import StrategyParams
        
        # 使用传入参数或默认参数
        self.params = strategy_params if strategy_params else StrategyParams()
        
        # 设置基础参数
        self.initial_capital = self.params.initial_capital
        self.commission_ratio = self.params.commission_ratio
        self.trading_records = []
        self.portfolio_values = []
        self.daily_returns = []
    
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
                
                # 限制股票池大小，加快测试 - 使用参数化配置
                if self.params.stock_pool_limit is not None:
                    stock_pool = stock_pool[:self.params.stock_pool_limit]
                    print(f"[{current_date}] 股票池大小: {len(stock_pool)}只 (已限制)")
                else:
                    print(f"[{current_date}] 股票池大小: {len(stock_pool)}只 (全量)")
                
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
            
            if cash_value > current_price * 100:  # 至少能买100股
                print(f"买入条件满足: 现金{cash_value:.2f}元, 股价{current_price:.2f}元")
                return True
            
            return False
            
        except Exception as e:
            print(f"买入判断失败: {e}")
            return False
    
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
            from gm.api import current
            
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
            
            # 止盈止损条件 - 使用参数化配置
            profit_ratio = (current_price - buy_price) / buy_price
            
            # 使用参数化配置的止盈止损比例
            stop_profit_ratio = self.params.stop_profit_ratio
            stop_loss_ratio = self.params.stop_loss_ratio
            
            if profit_ratio >= stop_profit_ratio:  # 止盈
                print(f"止盈触发: 盈利{profit_ratio*100:.2f}% (阈值{stop_profit_ratio*100:.2f}%)")
                return True
            elif profit_ratio <= stop_loss_ratio:  # 止损
                print(f"止损触发: 亏损{profit_ratio*100:.2f}% (阈值{stop_loss_ratio*100:.2f}%)")
                return True
            
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
            
            portfolio_value = cash_value
            
            # 加上持仓市值
            for position in account.positions():
                # 安全获取持仓量
                volume = position.volume
                volume_value = float(volume.value) if hasattr(volume, 'value') else float(volume)
                
                # 只计算有持仓的股票
                if volume_value > 0:
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
                        
                        # 计算持仓市值
                        position_value = current_price * volume_value
                        portfolio_value += position_value
            
            # 防止组合价值异常增长（异常大的值可能是计算错误）
            # 组合价值不应超过初始资金的10倍，除非有明确的盈利
            if portfolio_value > self.initial_capital * 10:
                # 检查是否真的有这么多持仓
                actual_positions = sum([float(pos.volume.value) if hasattr(pos.volume, 'value') else float(pos.volume) for pos in account.positions()])
                if actual_positions < self.initial_capital * 5 / 100:  # 假设股价不超过100元
                    # 持仓量不足以支持这么高的组合价值，说明计算有误
                    print(f"⚠️  警告: 组合价值异常高 ({portfolio_value:.2f}元)，已调整为合理值")
                    # 使用初始资金作为合理值
                    return self.initial_capital
            
            return portfolio_value
            
        except Exception as e:
            print(f"计算组合价值失败: {e}")
            return self.initial_capital