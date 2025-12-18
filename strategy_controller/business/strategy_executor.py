#!/usr/bin/env python
# coding=utf-8
"""
策略执行器 - 核心策略执行逻辑（修复异步线程问题）
"""

import streamlit as st
import time
import sys
import os
from typing import Dict, List, Any, Callable

# 添加项目根目录到Python路径，确保可以正确导入utils模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from emgm.strategy_controller.utils.logger import logger
from emgm.strategy_controller.utils.time_formatter import format_time

# 导入选股策略（带错误处理）- 更新为重构后的模块
try:
    # 导入重构后的策略模块
    from emgm.strategies.zge_strategy import ZGeStrategyScreener, run_zge_strategy_screener
    STRATEGY_IMPORT_SUCCESS = True
except ImportError as e:
    print(f"[WARNING] 策略模块导入失败: {e}")
    print("[WARNING] 部分功能可能不可用，请检查依赖包")
    STRATEGY_IMPORT_SUCCESS = False
    
    # 创建空的占位类
    class ZGeStrategyScreener:
        def __init__(self, batch_size=500, max_workers=6, weights_config=None):
            self.batch_size = batch_size
            self.max_workers = max_workers
            self.weights_config = weights_config
        
        def get_latest_trading_date(self):
            # 使用正确的交易日获取逻辑
            import datetime
            try:
                current_date = datetime.datetime.now()
                
                if current_date.weekday() < 5:  # 周一到周五
                    current_time = current_date.time()
                    trading_start = datetime.time(9, 0)
                    trading_end = datetime.time(15, 0)
                    
                    if trading_start <= current_time <= trading_end:
                        yesterday = current_date - datetime.timedelta(days=1)
                        return yesterday.strftime("%Y-%m-%d")
                    else:
                        return current_date.strftime("%Y-%m-%d")
                else:
                    days_to_friday = (current_date.weekday() - 4) % 7
                    if days_to_friday == 0:
                        return current_date.strftime("%Y-%m-%d")
                    else:
                        friday = current_date - datetime.timedelta(days=days_to_friday)
                        return friday.strftime("%Y-%m-%d")
                    
            except Exception as e:
                yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
                return yesterday.strftime("%Y-%m-%d")
        
        def get_stock_pool(self, skip_st=True):
            return []
        
        def process_stock_batch(self, symbols, trade_date):
            return []
        
        def filter_stocks(self, stocks):
            return []
    
    def run_zge_strategy_screener(*args, **kwargs):
        st.error("策略模块不可用")
        return []


def create_weighted_screener(weights: Dict[str, int], params: Dict[str, Any], sub_weights_config: Dict[str, Any] = None) -> ZGeStrategyScreener:
    """创建带权重配置的选股器"""
    # 参数验证和类型转换
    batch_size = int(params.get('batch_size', 500))
    max_workers = int(params.get('max_workers', 6))
    
    # 记录子权重配置信息
    if sub_weights_config:
        print(f"[STRATEGY_EXECUTOR] 子权重配置: {sub_weights_config}")
        logger.debug(f"子权重配置: {sub_weights_config}")
    else:
        print("[STRATEGY_EXECUTOR] 子权重配置: 未启用")
        logger.debug("子权重配置: 未启用")
    
    # 直接通过构造函数传递参数，避免传递不存在的参数
    screener = ZGeStrategyScreener(
        batch_size=batch_size,
        max_workers=max_workers,
        weights_config=weights,
        sub_weights_config=sub_weights_config
    )
    
    return screener


def run_strategy(strategy_type: str, weights: Dict[str, int], params: Dict[str, Any], 
                 progress_callback: Callable[[float], None] = None, 
                 status_callback: Callable[[str], None] = None,
                 sub_weights_config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """运行选股策略（使用回调函数更新UI，避免异步线程问题）"""
    start_time = time.time()
    
    # 记录实际接收到的参数 - 增强调试信息
    print(f"[STRATEGY_EXECUTOR] 策略执行器接收到的参数:")
    print(f"[STRATEGY_EXECUTOR] 策略类型: {strategy_type}")
    print(f"[STRATEGY_EXECUTOR] 权重配置: {weights}")
    print(f"[STRATEGY_EXECUTOR] 筛选参数: {params}")
    
    logger.debug(f"策略执行器接收到的参数:")
    logger.debug(f"原始策略类型: {strategy_type}")
    logger.debug(f"原始权重配置: {weights}")
    logger.debug(f"原始筛选参数: {params}")
    
    # 仅在参数完全为空时使用默认值
    if not isinstance(weights, dict) or len(weights) == 0:
        weights = {
            'kdj_j': 25,
            'trend': 25,
            'deepv': 10,
            'volume': 8,
            'fundamental': 8,
            'position': 4,
            'risk_reward': 20
        }
        logger.warning("权重配置为空，使用默认值")
    
    if not isinstance(params, dict) or len(params) == 0:
        params = {
            'max_results': 30,
            'skip_st': True,
            'test_mode': False,
            'batch_size': 1000,
            'max_workers': 6,
            'stock_pool_type': '全量A股'
        }
        logger.warning("筛选参数为空，使用默认值")
    
    # 清空日志
    logger.clear()
    logger.info("🎯 开始执行选股策略")
    logger.debug(f"策略类型: {strategy_type}")
    logger.debug(f"权重配置: {weights}")
    logger.debug(f"筛选参数: {params}")
    
    try:
        # 标准化策略类型
        if strategy_type == "zge_comprehensive":
            strategy_type = "z哥综合策略 (KDJ+知行趋势+深V信号)"
            
        if strategy_type == "z哥综合策略 (KDJ+知行趋势+深V信号)":
            # 创建带权重配置的选股器
            logger.info("🔧 创建选股器实例")
            screener = create_weighted_screener(weights, params, sub_weights_config)
            
            # 获取最新的交易日
            logger.info("📅 获取交易日数据")
            trade_date = screener.get_latest_trading_date()
            logger.debug(f"交易日: {trade_date}")
            
            # 使用回调函数更新状态
            elapsed_time = time.time() - start_time
            if status_callback:
                status_callback(f"{format_time(elapsed_time)} - 正在获取股票池数据... (交易日: {trade_date})")
            if progress_callback:
                progress_callback(0.1)
            
            # 获取股票池
            stock_pool_type = params.get('stock_pool_type', '全量A股')
            custom_symbols = params.get('custom_symbols', None)
            logger.info(f"📊 获取股票池数据 (股票池类型: {stock_pool_type})")
            
            if custom_symbols:
                logger.debug(f"自定义股票池: {custom_symbols}")
            
            stock_pool = screener.get_stock_pool(
                skip_st=params.get('skip_st', True), 
                stock_pool_type=stock_pool_type,
                custom_symbols=custom_symbols
            )
            logger.info(f"获取到 {len(stock_pool)} 只股票")
            
            elapsed_time = time.time() - start_time
            if status_callback:
                status_callback(f"{format_time(elapsed_time)} - 获取到 {len(stock_pool)} 只股票，开始分批处理...")
            if progress_callback:
                progress_callback(0.2)
            
            if params.get('test_mode', False):
                stock_pool = stock_pool[:100]
                logger.info(f"测试模式：仅处理前 {len(stock_pool)} 只股票")
                elapsed_time = time.time() - start_time
                if status_callback:
                    status_callback(f"{format_time(elapsed_time)} - 测试模式：仅处理前 {len(stock_pool)} 只股票")
            
            # 使用真正的并行处理所有股票
            logger.info(f"🚀 开始真正并行处理 {len(stock_pool)} 只股票...")
            elapsed_time = time.time() - start_time
            
            if status_callback:
                status_callback(f"{format_time(elapsed_time)} - 开始真正并行处理 {len(stock_pool)} 只股票...")
            if progress_callback:
                progress_callback(0.3)
            
            # 使用BatchProcessor的并行处理功能
            try:
                # 访问batch_processor实例
                batch_processor = screener.batch_processor
                
                # 调用真正并行的批次处理
                all_stocks = batch_processor.process_all_stocks_parallel(stock_pool, trade_date, batch_size=screener.batch_size)
                
                elapsed_time = time.time() - start_time
                logger.info(f"🎉 并行处理完成: 从 {len(stock_pool)} 只股票中筛选出 {len(all_stocks)} 只候选股票")
                
                if status_callback:
                    status_callback(f"{format_time(elapsed_time)} - 并行处理完成，找到 {len(all_stocks)} 只候选股票")
                if progress_callback:
                    progress_callback(0.8)
                    
            except Exception as e:
                logger.error(f"并行处理失败，回退到串行处理: {e}")
                
                # 回退到串行分批处理
                total_batches = (len(stock_pool) + screener.batch_size - 1) // screener.batch_size
                all_stocks = []
                batch_start_time = time.time()
                
                logger.info(f"开始串行分批处理，共 {total_batches} 个批次，批次大小: {screener.batch_size}")
                
                for batch_num in range(total_batches):
                    start_idx = batch_num * screener.batch_size
                    end_idx = min(start_idx + screener.batch_size, len(stock_pool))
                    batch_symbols = stock_pool[start_idx:end_idx]
                    
                    # 更新批次状态和时间估算
                    elapsed_time = time.time() - start_time
                    batch_elapsed = time.time() - batch_start_time
                    
                    # 计算预估剩余时间
                    if batch_num > 0:
                        avg_batch_time = batch_elapsed / batch_num
                        remaining_batches = total_batches - batch_num
                        estimated_remaining = avg_batch_time * remaining_batches
                        time_estimate = f" | 预估剩余: {format_time(estimated_remaining)}"
                    else:
                        time_estimate = " | 正在计算预估时间..."
                    
                    # 使用进度方式输出日志（避免个股维度的详细日志）
                    logger.info(f"[批次 {batch_num + 1}/{total_batches}] 进度: {((batch_num + 1) / total_batches) * 100:.1f}% | 耗时: {format_time(elapsed_time)}{time_estimate}")
                    
                    if status_callback:
                        status_callback(f"{format_time(elapsed_time)}{time_estimate} - 正在处理第 {batch_num + 1}/{total_batches} 批次")
                    
                    # 计算批次进度 (Streamlit进度条范围是0.0-1.0)
                    batch_progress = 0.2 + (batch_num / total_batches) * 0.6  # 20% + 批次处理占60%
                    if progress_callback:
                        progress_callback(batch_progress)
                    
                    # 处理当前批次
                    batch_results = screener.process_stock_batch(batch_symbols, trade_date)
                    
                    # 筛选符合条件的股票
                    batch_filtered = screener.filter_stocks(batch_results)
                    
                    if batch_filtered:
                        all_stocks.extend(batch_filtered)
                        elapsed_time = time.time() - start_time
                        logger.info(f"[批次 {batch_num + 1}/{total_batches}] 找到 {len(batch_filtered)} 只符合条件的股票")
                        
                        if status_callback:
                            status_callback(f"{format_time(elapsed_time)} - 第 {batch_num + 1} 批次找到 {len(batch_filtered)} 只符合条件的股票")
                    else:
                        logger.debug(f"[批次 {batch_num + 1}] 未找到符合条件的股票")
                    
                    # 如果已经找到足够多的股票，提前结束
                    if len(all_stocks) >= params.get('max_results', 50) * 2:
                        elapsed_time = time.time() - start_time
                        logger.info(f"已找到 {len(all_stocks)} 只候选股票，提前结束处理")
                        if status_callback:
                            status_callback(f"{format_time(elapsed_time)} - 已找到 {len(all_stocks)} 只候选股票，提前结束处理")
                        break
                        
                elapsed_time = time.time() - start_time
                logger.info(f"🎉 串行处理完成: 从 {len(stock_pool)} 只股票中筛选出 {len(all_stocks)} 只候选股票")
                
                if status_callback:
                    status_callback(f"{format_time(elapsed_time)} - 串行处理完成，找到 {len(all_stocks)} 只候选股票")
                if progress_callback:
                    progress_callback(0.8)
            
            # 排序和筛选
            elapsed_time = time.time() - start_time
            logger.info(f"开始排序和筛选，共 {len(all_stocks)} 只候选股票")
            if status_callback:
                status_callback(f"{format_time(elapsed_time)} - 正在对 {len(all_stocks)} 只候选股票进行排序...")
            if progress_callback:
                progress_callback(0.85)
            
            all_stocks.sort(key=lambda x: x.get('total_score', 0), reverse=True)
            final_results = all_stocks[:params.get('max_results', 50)]
            
            elapsed_time = time.time() - start_time
            logger.success(f"排序完成！最终筛选出 {len(final_results)} 只股票")
            logger.info(f"总耗时: {format_time(elapsed_time)}")
            
            # 记录最终结果
            for i, stock in enumerate(final_results[:10]):  # 只记录前10只
                logger.info(f"排名 {i+1}: {stock['symbol']} - 评分: {stock.get('total_score', 0):.1f}, J值: {stock['kdj_j']:.2f}")
            
            if status_callback:
                status_callback(f"{format_time(elapsed_time)} - 排序完成，最终筛选出 {len(final_results)} 只股票")
            if progress_callback:
                progress_callback(0.95)
            
            return final_results
        
    except Exception as e:
        import traceback
        import sys
        
        # 获取详细的错误堆栈信息
        error_details = traceback.format_exc()
        
        # 强制刷新输出缓冲区，确保错误信息立即显示
        print(f"[ERROR] 策略执行失败: {str(e)}", flush=True)
        print(f"[ERROR] 错误类型: {type(e).__name__}", flush=True)
        print(f"[ERROR] 错误堆栈:\n{error_details}", flush=True)
        
        # 检查是否是模块导入错误
        if "ModuleNotFoundError" in str(type(e).__name__):
            print(f"[ERROR] 模块导入错误: 可能是缺少依赖包或模块路径问题", flush=True)
            print(f"[ERROR] 建议检查 requirements.txt 中的依赖包是否已安装", flush=True)
        
        # 记录详细的错误信息
        logger.error(f"策略执行失败: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误详情:\n{error_details}")
        
        if status_callback:
            status_callback(f"策略执行失败: {str(e)}")
        
        # 强制退出以显示错误
        sys.stdout.flush()
        sys.stderr.flush()
        
        return []