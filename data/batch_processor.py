# coding=utf-8
"""
批量处理模块 - 重新设计的高效并行漏斗式筛选流程
优化目标：将50分钟运行时间缩短到10-15分钟
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# 添加项目根目录到Python路径，确保模块导入正常
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加ulti-para-seeker目录到Python路径，确保日志模块导入正常
ulti_para_seeker_dir = os.path.join(project_root, "ulti-para-seeker")
if ulti_para_seeker_dir not in sys.path:
    sys.path.insert(0, ulti_para_seeker_dir)

# 导入日志模块
from utils.logger import logger

from data.stock_data_provider import StockDataProvider
from indicators.kdj_calculator import KDJCalculator
from indicators.trend_indicators import TrendIndicators
from indicators.deepv_calculator import DeepVCalculator
from indicators.s1_filter import S1Filter
from indicators.speculation_filter import SpeculationFilter
from scoring.comprehensive_scorer import ComprehensiveScorer
from cache import stock_cache
from cache.preload_manager import preload_manager


class ScreeningOrderConfig:
    """筛选顺序配置类"""
    
    # 可用的筛选顺序配置
    ORDERS = {
        "default": {
            "name": "默认顺序",
            "description": "基础信息 → PE/市值 → KDJ → 趋势",
            "efficiency": "标准效率 (基准)",
            "steps": ["basic_info", "pe_mv", "kdj", "trend"]
        },
        "fast_kpi": {
            "name": "快速指标优先",
            "description": "KDJ → 基础信息 → PE/市值 → 趋势",
            "efficiency": "预计提升3-7倍 (推荐)",
            "steps": ["kdj", "basic_info", "pe_mv", "trend"]
        },
        "conservative": {
            "name": "保守筛选",
            "description": "基础信息 → PE/市值 → 趋势 → KDJ",
            "efficiency": "预计降低20-30% (质量优先)",
            "steps": ["basic_info", "pe_mv", "trend", "kdj"]
        },
        "aggressive": {
            "name": "激进筛选",
            "description": "KDJ → 趋势 → 基础信息 → PE/市值",
            "efficiency": "预计提升5-10倍 (风险较高)",
            "steps": ["kdj", "trend", "basic_info", "pe_mv"]
        }
    }
    
    @classmethod
    def get_available_orders(cls):
        """获取可用的筛选顺序列表"""
        return list(cls.ORDERS.keys())
    
    @classmethod
    def get_order_info(cls, order_type: str) -> Dict[str, Any]:
        """获取筛选顺序的详细信息"""
        return cls.ORDERS.get(order_type, cls.ORDERS["default"])
    
    @classmethod
    def validate_order(cls, order_type: str) -> bool:
        """验证筛选顺序是否有效"""
        return order_type in cls.ORDERS


class BatchProcessor:
    """高效批量处理器 - 重新设计为真正并行漏斗式筛选"""
    
    def __init__(self, batch_size=1000, max_workers=8, custom_weights=None, sub_weights_config=None, enable_smart_optimization=True):
        self.batch_size = batch_size
        self.max_workers = max_workers
        
        # 记录实际接收到的权重配置 - 已注释
        # logger.info(f"[BATCH_PROCESSOR] 接收到的权重配置: {custom_weights}")
        # logger.info(f"[BATCH_PROCESSOR] 接收到的子权重配置: {sub_weights_config}")
        
        self.weights_config = custom_weights
        self.sub_weights_config = sub_weights_config
        self.enable_smart_optimization = enable_smart_optimization
        
        # 进度显示相关
        self._last_progress_message = ""
        
        # 初始化各个组件
        self.data_provider = StockDataProvider()
        self.kdj_calculator = KDJCalculator()
        self.trend_indicators = TrendIndicators()
        self.deepv_calculator = DeepVCalculator()
        self.s1_filter = S1Filter()  # S1筛选器
        self.speculation_filter = SpeculationFilter()  # 投机炒作筛选器
        self.comprehensive_scorer = ComprehensiveScorer(custom_weights, sub_weights_config)
    
    def _update_progress(self, message: str, end: str = "\r"):
        """单行更新进度显示，避免日志过多"""
        # 清空上一条消息
        if self._last_progress_message:
            print(" " * len(self._last_progress_message), end="\r")
        
        # 显示新消息
        print(message, end=end)
        self._last_progress_message = message
        
    def _finalize_progress(self):
        """完成进度显示，换行显示最终结果"""
        if self._last_progress_message:
            print(" " * len(self._last_progress_message), end="\r")
            self._last_progress_message = ""
    
    def process_batch_parallel(self, symbols: List[str], trade_date: str, batch_id=None) -> List[Dict[str, Any]]:
        """真正并行的批次处理 - 优化性能和日志输出"""
        batch_prefix = f"[第{batch_id}批] " if batch_id else ""
        
        # 第一步：并行获取所有股票的基础信息（PE、市值等）
        basic_info_start = time.time()
        
        # 使用批量获取方式替代单只股票获取
        batch_start = time.time()
        batch_results = self.data_provider.get_stock_basic_info_batch(symbols, trade_date, batch_prefix)
        
        # 转换为列表格式
        all_stocks_info = list(batch_results.values())
        
        batch_time = time.time() - batch_start
        basic_info_time = time.time() - basic_info_start
        
        if not all_stocks_info:
            return []
        
        if not all_stocks_info:
            logger.error(f"{batch_prefix}❌ 无法获取任何股票基础信息")
            return []
        
        # 第二步：并行PE和市值筛选（内存中快速筛选）
        pe_mv_start = time.time()
        
        pe_mv_passed = []
        for stock_info in all_stocks_info:
            pe = stock_info.get('pe', 100)
            a_mv = stock_info.get('a_mv', 0)
            
            # 放宽筛选条件
            if (0 < pe < 100 and a_mv > 50 * 1e8):
                pe_mv_passed.append(stock_info)
        
        pe_mv_time = time.time() - pe_mv_start
        
        if not pe_mv_passed:
            return []
        
        # 第三步：并行KDJ筛选（真正的计算密集型操作）
        kdj_start = time.time()
        
        kdj_passed = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, 12)) as executor:
            future_to_stock = {
                executor.submit(self._process_kdj_only, stock_info['symbol'], trade_date, stock_info, batch_prefix): stock_info 
                for stock_info in pe_mv_passed
            }
            
            completed = 0
            total_kdj = len(pe_mv_passed)
            for future in as_completed(future_to_stock):
                stock_info = future_to_stock[future]
                try:
                    result = future.result()
                    if result is not None:
                        kdj_passed.append(result)
                except Exception:
                    pass
                
                completed += 1
        
        kdj_time = time.time() - kdj_start
        
        if not kdj_passed:
            return []
        
        # 第四步：并行趋势筛选和综合评分
        trend_start = time.time()
        
        final_results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_stock = {
                executor.submit(self._process_trend_and_scoring, stock, batch_prefix): stock 
                for stock in kdj_passed
            }
            
            completed = 0
            total_trend = len(kdj_passed)
            for future in as_completed(future_to_stock):
                stock = future_to_stock[future]
                try:
                    result = future.result()
                    if result is not None:
                        final_results.append(result)
                except Exception:
                    pass
                
                completed += 1
        
        trend_time = time.time() - trend_start
        
        return final_results
    
    def _get_basic_info_only(self, symbol: str, trade_date: str, batch_prefix: str = "") -> Dict[str, Any]:
        """仅获取股票基础信息（PE、市值等）"""
        try:
            basic_info = self.data_provider.get_stock_basic_info(symbol, trade_date, batch_prefix)
            return basic_info
        except Exception:
            return None
    
    def _process_kdj_only(self, symbol: str, trade_date: str, basic_info: Dict[str, Any] = None, batch_prefix: str = "") -> Dict[str, Any]:
        """仅处理KDJ指标、S1筛选和投机筛选，避免不必要的复杂计算"""
        try:
            # 如果未提供基础信息，则获取
            if basic_info is None:
                basic_info = self.data_provider.get_stock_basic_info(symbol, trade_date, batch_prefix)
            
            pe = basic_info.get('pe', 100)
            a_mv = basic_info.get('a_mv', 0)
            
            # 二次验证PE和市值（避免数据变化）
            if not (0 < pe < 100 and a_mv > 50 * 1e8):
                return None
            
            # 获取股票K线数据（减少数据量，提高速度）
            df = self.data_provider.get_stock_kline_data(symbol, trade_date, days=180, batch_prefix=batch_prefix)  # 仅需要180天数据
            if df.empty or len(df) < 30:
                return None
            
            # 提取价格序列
            closes = df['close'].tolist()
            highs = df['high'].tolist()
            lows = df['low'].tolist()
            
            # 计算KDJ指标
            kdj_data = self.kdj_calculator.calculate_kdj(closes, highs, lows)
            j_value = kdj_data.get('kdj_j', 50)
            
            # KDJ筛选条件
            if j_value >= 20:  # J值必须小于20
                return None
            
            # S1筛选：排除前期高点出现放量绿柱的股票
            s1_passed, s1_result = self.s1_filter.filter_stock(df)
            if not s1_passed:
                # S1未通过，记录日志（可选）并返回None
                logger.debug(f"{batch_prefix}{symbol} S1筛选未通过: {s1_result.get('s1_reason', '未知原因')}")
                return None
            
            # 投机炒作筛选：排除一字涨停板游资炒作的股票（不使用波动率条件，避免误杀主升浪）
            speculation_passed, speculation_result = self.speculation_filter.filter_stock(df)
            if not speculation_passed:
                # 投机炒作未通过，记录日志并返回None
                logger.debug(f"{batch_prefix}{symbol} 投机炒作筛选未通过: {speculation_result.get('reason', '未知原因')}")
                return None
            
            # 返回基础数据，供后续趋势筛选使用
            return {
                'symbol': symbol,
                'sec_name': basic_info['sec_name'],
                'trade_date': trade_date,
                'close': df['close'].iloc[-1],
                'kdj_j': j_value,
                'pe': pe,
                'a_mv': a_mv,
                's1_result': s1_result,  # 保留S1筛选结果
                'speculation_result': speculation_result,  # 保留投机筛选结果
                'df': df  # 保留数据框
            }
            
        except Exception:
            return None
    
    def _process_trend_and_scoring(self, stock_data: Dict[str, Any], batch_prefix: str = "") -> Dict[str, Any]:
        """处理趋势指标和综合评分"""
        try:
            df = stock_data['df']
            
            # 计算趋势指标
            zhi_xing_data = self.trend_indicators.compute_zhi_xing_overlays(df)
            white_line = zhi_xing_data.get('white_line')
            yellow_line = zhi_xing_data.get('yellow_line')
            
            # 硬性条件：白线必须在黄线上方
            if white_line is None or yellow_line is None or white_line <= yellow_line:
                return None
            
            # 计算深V信号
            deepv_data = self.deepv_calculator.compute_deep_v(df)
            
            # 分析成交量趋势
            volume_analysis = self.trend_indicators.analyze_volume_trend(df)
            
            # 检查成交量阈值
            volume_threshold = self.data_provider.check_volume_threshold(df)
            
            # 合并所有数据
            stock_data.update({
                'zhi_xing': zhi_xing_data,
                'deepv': deepv_data,
                'volume_analysis': volume_analysis,
                'volume_threshold': volume_threshold
            })
            
            # 计算综合评分
            score_details = self.comprehensive_scorer.calculate_comprehensive_score(stock_data)
            stock_data.update(score_details)
            
            return stock_data
            
        except Exception:
            return None
    
    def process_stock_batch(self, symbols: List[str], trade_date: str) -> List[Dict[str, Any]]:
        """高效并行漏斗式筛选流程 - 同时处理所有批次"""
        return self.process_batch_parallel(symbols, trade_date)
    
    def process_all_stocks_parallel(self, all_symbols: List[str], trade_date: str, batch_size: int = None) -> List[Dict[str, Any]]:
        """真正并行处理全部股票池 - 同时处理多个批次（智能优化）"""
        if batch_size is None:
            batch_size = self.batch_size
        
        # 智能优化：根据股票总数和CPU核心数调整批次大小
        total_stocks = len(all_symbols)
        optimal_batch_size = self._calculate_optimal_batch_size(total_stocks, batch_size)
        
        if optimal_batch_size != batch_size:
            logger.info(f"⚡ 智能优化：批次大小从 {batch_size} 调整为 {optimal_batch_size}")
            batch_size = optimal_batch_size
        
        logger.info(f"🚀 开始真正并行处理 {total_stocks} 只股票，批次大小: {batch_size}")
        
        # 动态计算批次数量
        total_batches = (total_stocks + batch_size - 1) // batch_size
        # 智能调整并行线程数，避免资源浪费
        effective_workers = min(self.max_workers, total_batches)
        
        logger.info(f"📊 将股票池分成 {total_batches} 个批次，使用 {effective_workers} 个线程并行处理")
        logger.info(f"💡 效率分析：CPU利用率 {effective_workers/self.max_workers*100:.0f}%，批次负载均衡度 {total_batches/effective_workers:.1f}")
        
        # 全局统计变量
        total_processed = 0
        
        # 并行处理所有批次 - 使用ThreadPoolExecutor并行处理批次
        all_results = []
        
        # 创建批次列表
        batches = []
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(all_symbols))
            batch_symbols = all_symbols[start_idx:end_idx]
            batches.append((batch_num+1, batch_symbols))
        
        # 使用ThreadPoolExecutor并行处理批次
        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            # 提交所有批次任务
            future_to_batch = {
                executor.submit(self.process_batch_parallel, batch_symbols, trade_date, batch_id): (batch_id, len(batch_symbols))
                for batch_id, batch_symbols in batches
            }
            
            # 处理结果
            for future in as_completed(future_to_batch):
                batch_id, batch_symbol_count = future_to_batch[future]
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                    
                    # 更新已处理股票计数
                    total_processed += len(batch_results)
                    logger.info(f"[第{batch_id}批] ✅ 批次 {batch_id}/{total_batches} 完成: 处理 {batch_symbol_count} 只股票，找到 {len(batch_results)} 只候选股票")
                    logger.info(f"[进度统计] 已处理 {total_processed}/{len(all_symbols)} 只股票 ({total_processed/len(all_symbols)*100:.1f}%)")
                    
                except Exception as e:
                    logger.error(f"[第{batch_id}批] ❌ 批次处理失败: {e}")
        
        logger.info(f"🎉 并行处理完成: 从 {len(all_symbols)} 只股票中筛选出 {len(all_results)} 只候选股票")
        logger.info(f"📈 处理统计: 已处理 {len(all_symbols)} 只股票，筛选出 {len(all_results)} 只候选股票")
        return all_results
    
    def _calculate_optimal_batch_size(self, total_stocks: int, user_batch_size: int) -> int:
        """智能计算最优批次大小 - 综合考虑计算效率和资源利用率"""
        
        # 如果不启用智能优化，直接返回用户设置的批次大小
        if not self.enable_smart_optimization:
            print("🔧 智能批次优化已禁用，使用用户设置的批次大小")
            return user_batch_size
        
        # 阶段一：基于筛选条件的计算复杂度分析
        # PE/市值筛选通过率约20%，KDJ筛选通过率约50%，趋势筛选通过率约30%
        pe_mv_pass_rate = 0.20    # 20%通过
        kdj_pass_rate = 0.50      # 50%通过  
        trend_pass_rate = 0.30    # 30%通过
        
        # 阶段二：基于计算复杂度的权重分配
        # PE/市值计算复杂度：低（API调用 + 简单比较）
        # KDJ计算复杂度：中（技术指标计算）
        # 趋势+评分计算复杂度：高（多种技术指标 + 复杂算法）
        complexity_weights = {
            'pe_mv': 1.0,     # 基础权重
            'kdj': 3.0,       # 3倍复杂度
            'trend': 8.0      # 8倍复杂度
        }
        
        # 阶段三：智能批次大小计算
        # 目标：最小化总计算量 = 批次数量 × 每个批次的平均计算量
        
        # 计算当前用户设置的批次数
        current_batches = (total_stocks + user_batch_size - 1) // user_batch_size
        
        # 防止除零错误
        if current_batches == 0:
            current_batches = 1
        
        # 计算每个批次的期望计算量
        avg_batch_size = total_stocks / current_batches
        
        # 计算每个批次的平均计算量（加权求和）
        expected_computations = (
            avg_batch_size * complexity_weights['pe_mv'] +  # 所有股票都要计算PE/市值
            avg_batch_size * pe_mv_pass_rate * complexity_weights['kdj'] +  # 通过PE/市值的股票计算KDJ
            avg_batch_size * pe_mv_pass_rate * kdj_pass_rate * complexity_weights['trend']  # 通过KDJ的股票计算趋势
        )
        
        # 阶段四：考虑并行效率的优化
        # 基本原则：确保批次数 >= 线程数，但不要过多
        min_batches = max(1, self.max_workers)  # 至少要有足够的批次让所有线程工作
        max_batches = min_batches * 4           # 批次数不要超过线程数的4倍
        
        # 计算当前配置的总计算量
        current_total_computation = current_batches * expected_computations
        
        # 寻找最优批次大小
        candidate_batch_sizes = []
        
        # 生成候选批次大小（在合理范围内）
        for test_batch_size in [200, 500, 800, 1000, 1200, 1500, 1800, 2000]:
            test_batches = (total_stocks + test_batch_size - 1) // test_batch_size
            
            # 检查是否在合理范围内
            if min_batches <= test_batches <= max_batches:
                test_avg_batch = total_stocks / test_batches
                test_computation = (
                    test_avg_batch * complexity_weights['pe_mv'] +
                    test_avg_batch * pe_mv_pass_rate * complexity_weights['kdj'] +
                    test_avg_batch * pe_mv_pass_rate * kdj_pass_rate * complexity_weights['trend']
                )
                test_total = test_batches * test_computation
                
                candidate_batch_sizes.append({
                    'batch_size': test_batch_size,
                    'batches': test_batches,
                    'total_computation': test_total,
                    'efficiency_ratio': current_total_computation / test_total if test_total > 0 else 0
                })
        
        # 如果没有合适的候选，使用基于线程数的简单策略
        if not candidate_batch_sizes:
            if current_batches < min_batches:
                optimal_batch_size = (total_stocks + min_batches - 1) // min_batches
                print(f"🔧 批次优化：增加批次大小到 {optimal_batch_size}（确保有足够批次）")
                return optimal_batch_size
            elif current_batches > max_batches:
                optimal_batch_size = (total_stocks + max_batches - 1) // max_batches
                print(f"🔧 批次优化：减少批次大小到 {optimal_batch_size}（避免过多小批次）")
                return optimal_batch_size
            else:
                return user_batch_size
        
        # 选择最优批次大小（最小化总计算量）
        best_candidate = min(candidate_batch_sizes, key=lambda x: x['total_computation'])
        
        # 只有当效率提升超过10%时才调整
        efficiency_gain = best_candidate['efficiency_ratio'] - 1.0
        if efficiency_gain > 0.1:  # 10%效率提升阈值
            print(f"🔧 智能优化：批次大小从 {user_batch_size} 调整为 {best_candidate['batch_size']}")
            print(f"   - 批次数: {current_batches} → {best_candidate['batches']}")
            print(f"   - 计算效率提升: {efficiency_gain*100:.1f}%")
            print(f"   - 预期总计算量减少: {(current_total_computation - best_candidate['total_computation'])/current_total_computation*100:.1f}%")
            return best_candidate['batch_size']
        else:
            print(f"🔧 当前批次大小 {user_batch_size} 已接近最优（效率提升仅 {efficiency_gain*100:.1f}%）")
            return user_batch_size
    
    def filter_stocks(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """最终筛选（已在前面的流程中完成）"""
        # 由于筛选已在流程中完成，直接返回
        return stocks