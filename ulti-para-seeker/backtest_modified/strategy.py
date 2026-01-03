#!/usr/bin/env python
# coding=utf-8
"""
策略逻辑模块 - 优化器专属策略实现
依赖统一的strategy_engine.strategy，只保留优化器专属功能
"""

from typing import Dict, Any, Optional

# 导入日志模块（如果需要）
try:
    from utils.logger import logger
    has_logger = True
except ImportError:
    has_logger = False

# 导入统一的策略实现
from strategy_engine.strategy import BacktestStrategy as BaseBacktestStrategy


class OptimizerBacktestStrategy(BaseBacktestStrategy):
    """
    优化器回测策略类 - 继承自基础策略类，添加优化器专属功能
    """
    
    def __init__(self, strategy_params=None):
        """
        初始化回测参数
        
        Args:
            strategy_params: 策略参数配置对象
        """
        # 调用父类初始化
        super().__init__(strategy_params)
        
        # 优化器专属初始化
        if has_logger:
            logger.info("OptimizerBacktestStrategy初始化完成")
    
    def get_top_stock(self, context) -> Optional[Dict[str, str]]:
        """
        获取当日综合评分最高的股票 - 针对优化器优化
        集成现有的zge选股系统
        
        Returns:
            Dict: 包含股票代码和名称的字典，如果没有符合条件的股票则返回None
        """
        try:
            # 使用基础方法获取股票
            top_stock = super().get_top_stock(context)
            
            if has_logger:
                logger.debug(f"get_top_stock返回结果={top_stock}")
            
            return top_stock
            
        except Exception as e:
            if has_logger:
                logger.error(f"选股失败: {e}")
            else:
                print(f"选股失败: {e}")
            return None
    
    def should_buy(self, context, symbol: str) -> bool:
        """
        判断是否应该买入 - 针对优化器优化
        
        Args:
            context: 策略上下文
            symbol: 股票代码
            
        Returns:
            bool: 是否买入
        """
        try:
            result = super().should_buy(context, symbol)
            
            if has_logger:
                logger.debug(f"should_buy判断结果={result}")
            
            return result
            
        except Exception as e:
            if has_logger:
                logger.error(f"买入判断失败: {e}")
            else:
                print(f"买入判断失败: {e}")
            return False
    
    def should_sell(self, context, symbol: str, buy_price: float) -> bool:
        """
        判断是否应该卖出 - 针对优化器优化
        
        Args:
            context: 策略上下文
            symbol: 股票代码
            buy_price: 买入价格
            
        Returns:
            bool: 是否卖出
        """
        try:
            result = super().should_sell(context, symbol, buy_price)
            
            if has_logger:
                logger.debug(f"should_sell判断结果={result}")
            
            return result
            
        except Exception as e:
            if has_logger:
                logger.error(f"卖出判断失败: {e}")
            else:
                print(f"卖出判断失败: {e}")
            return False
    
    def daily_strategy(self, context):
        """
        每日策略执行 - 针对优化器优化
        """
        current_date = context.now.strftime('%Y-%m-%d')
        if has_logger:
            logger.info(f"\n📅 交易日: {current_date}")
            logger.debug(f"daily_strategy开始执行")
        else:
            print(f"\n📅 交易日: {current_date}")
            print(f"daily_strategy开始执行")
        
        # 调用父类的每日策略执行
        super().daily_strategy(context)
