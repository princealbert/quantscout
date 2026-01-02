#!/usr/bin/env python
# coding=utf-8
"""
暴力优化器 - 使用暴力枚举方法进行参数优化
"""

import itertools
import os
import sys
import json
import time
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from .base_optimizer import BaseOptimizer

# 项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入日志系统
from utils.logger import logger

class BruteForceOptimizer(BaseOptimizer):
    """
    暴力优化器类 - 使用暴力枚举方法进行参数优化
    """
    
    def __init__(self):
        """初始化暴力优化器"""
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
    
    def define_parameter_ranges(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                               use_advanced_weights: bool = True, end_date: str = '2025-12-25',
                               focus_indicators: List[str] = None, focus_weight_factor: float = 1.5) -> Dict[str, List[Any]]:
        """
        定义参数范围

        Args:
            test_mode: 是否为测试模式（只生成一个简单子权重组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            use_advanced_weights: 是否使用高级权重配置模式
            end_date: 回测终点日期（格式：YYYY-MM-DD）
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数

        Returns:
            Dict[str, List[Any]]: 参数范围字典
        """
        logger.info("定义参数范围...")
        logger.info(f"- 回测天数固定为90天，终点日期为{end_date}")
        
        # 根据模式调整参数范围
        if test_mode:
            logger.info("[测试模式] 使用最小参数范围")
            stop_profit_ratio = [0.02]  # 仅测试2%止盈
            stop_loss_ratio = [-0.01]  # 仅测试1%止损
            weight_step = 10  # 使用合理步长以生成有效组合
        else:
            logger.info("- 止盈比例: 3%-15%，步长2%")
            logger.info("- 止损比例: -5%--1%，步长1%")
            if use_advanced_weights:
                logger.info("- 权重配置: 总和100，步长10%")
                weight_step = 10
            else:
                logger.info("- 权重配置: 总和100，步长20%")
                weight_step = 20
            
            # 缩小止盈止损范围以减少组合数量（量化专家建议范围）
            stop_profit_ratio = [x/100 for x in range(3, 16, 2)]  # 3%-15%，步长2%
            stop_loss_ratio = [-x/100 for x in range(1, 6, 1)]  # -5%--1%，步长1%
        
        logger.info("- 子权重配置: 每个主指标子权重总和100")
        
        # 选股策略核心指标（权重配置）
        # 移除deepv指标，将其权重设为零以减少组合数量
        core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
        
        # 生成权重配置
        if test_mode:
            logger.info("[测试模式] 直接生成简单权重组合")
            weights_config = [{
                'kdj_j': 30,
                'trend': 20,
                'volume': 15,
                'fundamental': 15,
                'position': 10,
                'risk_reward': 10
            }]
        elif use_advanced_weights:
            # 高级模式：生成基础组合 + 重点指标加权组合
            logger.info("[高级模式] 使用重点指标加权的权重配置")
            
            # 基础权重组合 - 限制主权重范围为5%-95%，避免极端值
            base_weights = self._generate_weights_combinations(core_indicators, 100, weight_step, min_weight=5, max_weight=95)
            
            # 使用传入的重点指标和权重因子
            if focus_indicators is None:
                focus_indicators = ['kdj_j', 'trend']
            
            kdj_trend_weights = self._generate_custom_weights_combinations(
                core_indicators, 100, weight_step, 
                focus_indicators=focus_indicators, 
                focus_weight_factor=focus_weight_factor
            )
            
            # 合并权重组合并去重
            all_weights = base_weights + kdj_trend_weights
            
            # 去重
            seen = set()
            unique_weights = []
            for combo in all_weights:
                key = tuple(sorted(combo.items()))
                if key not in seen:
                    seen.add(key)
                    unique_weights.append(combo)
            
            weights_config = unique_weights
        else:
            # 普通模式：仅生成基础权重组合 - 限制主权重范围为5%-95%，避免极端值
            weights_config = self._generate_weights_combinations(core_indicators, 100, weight_step, min_weight=5, max_weight=95)
        
        return {
            # 回测天数 - 固定为90天（适合超跌反弹策略）
            'backtest_days': [90],
            
            # 回测终点日期 - 确保所有组合在相同时间段回测
            'end_date': [end_date],
            
            # 止盈比例 - 核心回测参数
            'stop_profit_ratio': stop_profit_ratio,
            
            # 止损比例 - 核心回测参数
            'stop_loss_ratio': stop_loss_ratio,
            
            # 权重配置 (总和必须为100) - 选股策略核心
            'weights_config': weights_config,
            
            # 子权重配置 (每个主指标的子权重总和必须为100) - 选股策略细节
            'sub_weights_config': self._generate_sub_weights_combinations(test_mode, max_combinations=max_sub_combinations, use_advanced_mode=use_advanced_weights)
        }
    
    def _generate_custom_weights_combinations(self, indicators: List[str], total: int, step: int, focus_indicators: List[str] = None, focus_weight_factor: float = 1.5) -> List[Dict[str, int]]:
        """
        生成自定义权重组合，支持重点指标加权
        
        Args:
            indicators: 指标列表
            total: 总权重
            step: 步长
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            
        Returns:
            List[Dict[str, int]]: 自定义权重组合列表
        """
        # 先生成基础组合
        base_combinations = self._generate_weights_combinations(indicators, total, step)
        
        if not focus_indicators or not base_combinations:
            return base_combinations
        
        custom_combinations = []
        focus_indicators = [ind for ind in focus_indicators if ind in indicators]
        
        if not focus_indicators:
            return base_combinations
        
        # 策略1: 基础重点指标加权
        for base_weights in base_combinations:
            # 生成重点指标加权的组合
            focus_weighted = base_weights.copy()
            non_focus_total = sum(weight for ind, weight in focus_weighted.items() if ind not in focus_indicators)
            focus_total = sum(weight for ind, weight in focus_weighted.items() if ind in focus_indicators)
            
            # 如果有重点指标和非重点指标
            if focus_total > 0 and non_focus_total > 0:
                # 调整权重，放大重点指标
                new_non_focus_total = max(1, int(non_focus_total / focus_weight_factor))
                new_focus_total = total - new_non_focus_total
                
                if new_non_focus_total > 0:
                    # 缩放非重点指标
                    for ind in focus_weighted:
                        if ind not in focus_indicators and focus_weighted[ind] > 0:
                            ratio = new_non_focus_total / non_focus_total
                            focus_weighted[ind] = max(1, int(focus_weighted[ind] * ratio))
                    
                    # 重新计算非重点指标总权重
                    non_focus_total = sum(focus_weighted[ind] for ind in focus_weighted if ind not in focus_indicators)
                    
                    # 分配剩余权重给重点指标
                    remaining = total - non_focus_total
                    if remaining > 0:
                        # 按比例分配给重点指标
                        if focus_total > 0:
                            for ind in focus_weighted:
                                if ind in focus_indicators:
                                    ratio = focus_weighted[ind] / focus_total
                                    focus_weighted[ind] = int(remaining * ratio)
                        else:
                            # 如果原重点指标总权重为0，平均分配
                            num_focus = len(focus_indicators)
                            avg = remaining // num_focus
                            remainder = remaining % num_focus
                            for i, ind in enumerate(focus_indicators):
                                focus_weighted[ind] = avg + (1 if i < remainder else 0)
                    
                    # 确保总权重为100
                    current_total = sum(focus_weighted.values())
                    if current_total < total:
                        # 分配剩余权重
                        for ind in focus_indicators:
                            focus_weighted[ind] += 1
                            current_total += 1
                            if current_total == total:
                                break
                    elif current_total > total:
                        # 减少权重
                        for ind in focus_weighted:
                            if ind not in focus_indicators and focus_weighted[ind] > 1:
                                focus_weighted[ind] -= 1
                                current_total -= 1
                                if current_total == total:
                                    break
                    
                    custom_combinations.append(focus_weighted)
        
        # 策略2: 直接为重点指标分配固定比例权重
        fixed_focus_combinations = []
        for base_weights in base_combinations[:10]:  # 仅使用前10个基础组合
            for focus_ratio in [0.6, 0.7, 0.8]:  # 重点指标总权重占比
                if focus_ratio * total < len(focus_indicators) * 5:  # 确保每个重点指标至少5分
                    continue
                
                fixed_weights = {ind: 5 for ind in indicators}  # 基础分5分
                remaining = total - len(indicators) * 5
                
                # 重点指标分配剩余权重的大部分
                focus_remaining = int(remaining * focus_ratio)
                non_focus_remaining = remaining - focus_remaining
                
                # 分配给重点指标
                for i, ind in enumerate(focus_indicators):
                    if i < len(focus_indicators) - 1:
                        fixed_weights[ind] += focus_remaining // len(focus_indicators)
                    else:
                        fixed_weights[ind] += focus_remaining // len(focus_indicators) + focus_remaining % len(focus_indicators)
                
                # 分配给非重点指标
                non_focus_indicators = [ind for ind in indicators if ind not in focus_indicators]
                if non_focus_indicators:
                    for i, ind in enumerate(non_focus_indicators):
                        if i < len(non_focus_indicators) - 1:
                            fixed_weights[ind] += non_focus_remaining // len(non_focus_indicators)
                        else:
                            fixed_weights[ind] += non_focus_remaining // len(non_focus_indicators) + non_focus_remaining % len(non_focus_indicators)
                
                # 确保总权重正确
                current_total = sum(fixed_weights.values())
                if current_total != total:
                    diff = total - current_total
                    for ind in focus_indicators:
                        fixed_weights[ind] += diff
                        break
                
                fixed_focus_combinations.append(fixed_weights)
        
        # 策略3: 组合不同的重点指标
        multi_focus_combinations = []
        if len(focus_indicators) >= 2:
            # 为每个重点指标单独生成极端组合
            for focus_ind in focus_indicators:
                single_focus = {ind: 5 for ind in indicators}
                single_focus[focus_ind] = total - (len(indicators) - 1) * 5
                if single_focus[focus_ind] <= 90:  # 限制最大权重
                    multi_focus_combinations.append(single_focus)
            
            # 为两两重点指标组合生成极端组合
            for i in range(len(focus_indicators) - 1):
                for j in range(i + 1, len(focus_indicators)):
                    pair_focus = {ind: 5 for ind in indicators}
                    pair_total = total - (len(indicators) - 2) * 5
                    pair_focus[focus_indicators[i]] = pair_total // 2
                    pair_focus[focus_indicators[j]] = pair_total - pair_focus[focus_indicators[i]]
                    if pair_focus[focus_indicators[i]] <= 80 and pair_focus[focus_indicators[j]] <= 80:
                        multi_focus_combinations.append(pair_focus)
        
        # 合并所有自定义组合
        all_custom = custom_combinations + fixed_focus_combinations + multi_focus_combinations
        
        # 去重
        seen = set()
        unique_custom = []
        for combo in all_custom:
            key = tuple(sorted(combo.items()))
            if key not in seen:
                seen.add(key)
                unique_custom.append(combo)
        
        # 合并基础组合和自定义组合，并再次去重
        all_combos = unique_custom + base_combinations
        final_seen = set()
        final_combinations = []
        
        for combo in all_combos:
            key = tuple(sorted(combo.items()))
            if key not in final_seen:
                final_seen.add(key)
                final_combinations.append(combo)
        
        return final_combinations
    
    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                       end_date: str = '2025-12-25', focus_indicators: List[str] = None, 
                                       focus_weight_factor: float = 1.5) -> List[Dict[str, Any]]:
        """
        生成所有参数组合

        Args:
            test_mode: 是否为测试模式（使用最小参数范围，仅生成第一个组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            end_date: 回测终点日期（格式：YYYY-MM-DD）
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            
        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        param_ranges = self.define_parameter_ranges(test_mode, max_sub_combinations, True, end_date, focus_indicators, focus_weight_factor)
        
        # 优化：参数空间剪枝 - 减少不必要的参数组合
        print(f"开始生成参数组合...")
        
        combinations = []
        current_count = 0
        
        # 生成所有可能的组合
        for backtest_days in param_ranges['backtest_days']:
            for end_date in param_ranges['end_date']:
                # 优化1：提前计算有效止盈止损组合
                valid_pairs = []
                for stop_profit_ratio in param_ranges['stop_profit_ratio']:
                    for stop_loss_ratio in param_ranges['stop_loss_ratio']:
                        if stop_profit_ratio > stop_loss_ratio:
                            valid_pairs.append((stop_profit_ratio, stop_loss_ratio))
                
                # 计算总组合数（用于进度显示）
                total_combinations = len(valid_pairs) * len(param_ranges['weights_config']) * len(param_ranges['sub_weights_config'])
                logger.info(f"预计总组合数: {total_combinations}")
                
                for stop_profit_ratio, stop_loss_ratio in valid_pairs:
                    for weights_config in param_ranges['weights_config']:
                        # 优化2：跳过不合理的权重配置
                        # 避免deepv权重过大
                        if weights_config.get('deepv', 0) > 50:
                            continue
                        
                        for sub_weights_config in param_ranges['sub_weights_config']:
                            # 将deepv权重设置为零
                            weights_config_with_zero_deepv = weights_config.copy()
                            weights_config_with_zero_deepv['deepv'] = 0
                            
                            param_comb = {
                                'backtest_days': backtest_days,
                                'end_date': end_date,
                                'stop_profit_ratio': stop_profit_ratio,
                                'stop_loss_ratio': stop_loss_ratio,
                                'weights_config': weights_config_with_zero_deepv,
                                'sub_weights_config': sub_weights_config,
                                'initial_capital': self.initial_capital
                            }
                            combinations.append(param_comb)
                            current_count += 1
                            
                            # 每生成1000个组合显示一次进度
                            if current_count % 1000 == 0:
                                logger.info(f"已生成 {current_count}/{total_combinations} 个参数组合")
                            
                            # 测试模式下仅生成第一个组合
                            if test_mode and current_count >= 1:
                                logger.info(f"[测试模式] 仅生成并返回第一个参数组合")
                                return combinations
        
        logger.info(f"总共生成 {len(combinations)} 个参数组合")
        return combinations
    
    def run_backtest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个参数组合的回测
        
        Args:
            params: 参数组合
            
        Returns:
            Dict[str, Any]: 回测结果
        """
        # 先检查缓存中是否已有结果
        cached_result = self._get_cached_result(params)
        if cached_result is not None:
            import os
            from utils.logger import logger
            pid = os.getpid()
            logger.info(f"\n📋 进程 {pid} 使用缓存结果")
            logger.debug(f"   参数组合: {params}")
            logger.info(f"✅ 进程 {pid} 回测完成（缓存命中）")
            return cached_result
        
        try:
            import sys
            import os
            import json
            from datetime import datetime, timedelta
            
            # 设置项目根目录到sys.path
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # 在子进程中重新导入日志系统
            from utils.logger import logger
            
            # 获取进程ID，用于显示并行执行情况
            pid = os.getpid()
            
            # 记录进程开始执行信息
            logger.info(f"\n📋 进程 {pid} 开始执行回测")
            logger.debug(f"   参数组合: {json.dumps(params, ensure_ascii=False, indent=2)}")
            
            # 创建策略ID
            strategy_id = f"optimization_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # 计算回测区间
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d')
            start_date = end_date - timedelta(days=params['backtest_days'])
            
            # 准备符合标准回测要求的配置结构
            # 测试模式下使用100只股票，非测试模式下使用1只股票
            is_test_mode = params.get('backtest_days', 90) == 10  # 检测是否为测试模式
            # 使用BaseOptimizer类的initial_capital属性，而不是params字典中的值
            frontend_config = {
                'backtest': {
                    'initial_capital': self.initial_capital,
                    'backtest_days': params['backtest_days'],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'max_stocks_to_backtest': 100 if is_test_mode else 1,
                    'strategy_id': strategy_id,
                    'commission_ratio': 0.0003
                },
                'strategy': {
                    'stop_profit_ratio': params['stop_profit_ratio'],
                    'stop_loss_ratio': params['stop_loss_ratio'],
                    'weights_config': params['weights_config'],
                    'sub_weights_config': params['sub_weights_config'],
                    'strategy_type': '参数优化策略'
                },
                # 不硬编码选股结果，让回测系统根据参数重新选股
                'selected_stocks': []
            }
            
            # 使用内存中的配置直接调用回测函数，避免配置文件的IO操作
            try:
                # 确保ulti-para-seeker目录在sys.path的最前面
                current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if current_dir in sys.path:
                    sys.path.remove(current_dir)
                sys.path.insert(0, current_dir)
                
                # 直接导入并调用backtest_runner的run_backtest函数，传入配置对象
                from backtest_runner import run_backtest as run_backtest_func
                run_backtest_func(config=frontend_config)
            except Exception as e:
                logger.error(f"调用回测函数失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 从文件中读取回测结果 - 等待固定名称的报告文件生成
            report = {}
            import time
            
            # 等待回测结果文件生成（给回测系统一些时间）
            max_wait = 10
            wait_count = 0
            report_file = os.path.join(project_root, 'backtest_report.json')
            
            # 添加短暂延迟，确保报告文件有足够时间生成
            time.sleep(0.5)
            
            while not os.path.exists(report_file) and wait_count < max_wait:
                time.sleep(0.5)  # 500ms延迟，减少等待时间
                wait_count += 1
            
            if os.path.exists(report_file):
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    logger.debug(f"成功读取报告文件: {report}")
                    
                    # 添加短暂延迟，确保其他进程有时间读取文件后再删除
                    time.sleep(0.1)
                    
                    # 删除结果文件，避免影响下一次回测
                    os.unlink(report_file)
                except Exception as e:
                    logger.error(f"读取报告文件失败: {e}")
                    report = {}
            else:
                logger.warning(f"报告文件未生成: {report_file}")
            
            # 从报告中提取需要的结果
            performance_metrics = report.get('performance_metrics', {})
            trade_statistics = report.get('trade_statistics', {})
            
            # 直接从report中提取数据，处理不同的报告格式
            if not performance_metrics:
                # 尝试直接从report中提取数据（兼容旧格式）
                performance_metrics = {
                    'total_return': report.get('total_return', 0.0),
                    'annual_return': report.get('annual_return', 0.0),
                    'max_drawdown': report.get('max_drawdown', 0.0),
                    'sharpe_ratio': report.get('sharpe_ratio', 0.0)
                }
            
            if not trade_statistics:
                # 尝试直接从report中提取数据（兼容旧格式）
                trade_statistics = {
                    'total_trades': report.get('trades_count', 0),
                    'win_rate': report.get('win_rate', 0.0)
                }
            
            # 记录调试信息，确保参数和结果正确关联
            logger.debug(f"[调试] 参数组合: {json.dumps(params, ensure_ascii=False, indent=2)}")
            logger.debug(f"[调试] 回测报告: {json.dumps(report, ensure_ascii=False, indent=2)}")
            logger.debug(f"[调试] 回测结果: {performance_metrics}, {trade_statistics}")
            
            # 返回结果，包含完整的回测指标和关键参数
            result = {
                **params,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'total_return': performance_metrics.get('total_return', 0.0),
                'annual_return': performance_metrics.get('annual_return', 0.0),
                'max_drawdown': performance_metrics.get('max_drawdown', 0.0),
                'sharpe_ratio': performance_metrics.get('sharpe_ratio', 0.0),
                'win_rate': trade_statistics.get('win_rate', 0.0),
                'trades_count': trade_statistics.get('total_trades', 0)
            }
            logger.debug(f"[调试] 准备返回的结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 将结果存入缓存
            self._cache_result(params, result)
            
            return result
            
        except Exception as e:
            logger.error(f"回测失败: {e}")
            result = {
                **params,
                'total_return': -100.0,  # 失败时返回极低收益率
                'annual_return': -100.0,
                'max_drawdown': -100.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'trades_count': 0
            }
            # 失败结果也存入缓存，避免重复计算
            self._cache_result(params, result)
            return result
        finally:
            # 记录进程完成信息
            logger.info(f"✅ 进程 {pid} 回测完成")
    
    def optimize(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                end_date: str = '2025-12-25', focus_indicators: List[str] = None, 
                focus_weight_factor: float = 1.5, blueprint_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        执行暴力优化

        Args:
            test_mode: 是否为测试模式（使用最小参数范围，仅生成第一个组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            end_date: 回测终点日期（格式：YYYY-MM-DD）
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            blueprint_file: 蓝图文件路径（用于断点续传）

        Returns:
            List[Dict[str, Any]]: 按收益率排序的结果列表
        """
        # 加载蓝图（如果提供）
        blueprint = None
        if blueprint_file:
            try:
                blueprint = self.load_blueprint(blueprint_file)
            except FileNotFoundError:
                print(f"蓝图文件 {blueprint_file} 不存在，将生成新的蓝图")
        
        # 如果没有蓝图或蓝图为空，生成新的参数组合
        if not blueprint or len(blueprint['combinations']) == 0:
            param_combinations = self.generate_parameter_combinations(test_mode, max_sub_combinations, end_date, focus_indicators, focus_weight_factor)
            
            # 如果提供了蓝图文件路径但文件不存在，生成新蓝图
            if blueprint_file:
                blueprint_path = self.generate_blueprint(test_mode, max_sub_combinations, end_date, blueprint_file)
                blueprint = self.load_blueprint(blueprint_file)
            else:
                # 没有蓝图文件路径，直接使用参数组合
                blueprint = {
                    'combinations': [
                        {
                            'id': i + 1,
                            'params': param,
                            'status': 'pending',
                            'result': None
                        }
                        for i, param in enumerate(param_combinations)
                    ],
                    'total_combinations': len(param_combinations)
                }
        else:
            # 从蓝图中提取待处理的参数组合
            param_combinations = [combo['params'] for combo in blueprint['combinations'] if combo['status'] in ['pending', 'failed']]
        
        # 执行优化
        results = self.run_parallel_optimization(param_combinations, blueprint=blueprint, blueprint_file=blueprint_file)
        
        return results
    
    def run_parallel_optimization(self, param_combinations: List[Dict[str, Any]], num_workers: int = None, batch_size: int = 50, save_interval: int = 1, blueprint: Optional[Dict[str, Any]] = None, blueprint_file: str = "parameter_blueprint.json") -> List[Dict[str, Any]]:
        """
        使用ProcessPoolExecutor并行运行参数优化（支持断点续传和结果更新）

        Args:
            param_combinations: 参数组合列表
            num_workers: 并行工作进程数，None表示使用CPU核心数
            batch_size: 每批处理的参数组合数（已废弃，保留参数兼容性）
            save_interval: 保存中间结果的批次间隔
            blueprint: 参数组合蓝图数据（用于断点续传）
            blueprint_file: 蓝图文件路径

        Returns:
            List[Dict[str, Any]]: 按收益率排序的结果列表
        """
        # 导入日志系统
        import os
        from utils.logger import logger
        
        total_combinations = len(param_combinations)
        self.start_time = datetime.now()
        all_results = []
        
        # 设置默认工作进程数
        if num_workers is None:
            num_workers = os.cpu_count() - 1 if os.cpu_count() > 1 else 1
        
        logger.info("\n=== 并行处理模式 ===")
        logger.info(f"开始并行优化，使用 {num_workers} 个进程")
        logger.info(f"总参数组合数: {total_combinations}")
        logger.info(f"每 {save_interval} 个组合更新一次Excel结果")
        logger.info(f"支持断点续传: {'是' if blueprint else '否'}")
        logger.info("=" * 50)
        
        # 准备要处理的组合列表，包括其在蓝图中的ID（如果有）
        combo_list = []
        for i, param in enumerate(param_combinations):
            combo_id = None
            if blueprint:
                for combo in blueprint['combinations']:
                    if combo['params'] == param:
                        combo_id = combo['id']
                        # 更新状态为running
                        combo['status'] = 'running'
                        combo['started_at'] = datetime.now().isoformat()
                        break
            combo_list.append((i, param, combo_id))
        
        # 保存更新后的蓝图（如果有）
        if blueprint:
            self.save_blueprint(blueprint, blueprint_file)
        
        # 使用ProcessPoolExecutor并行处理
        from concurrent.futures import ProcessPoolExecutor, as_completed
        import os
        import threading
        
        logger.info(f"\n🚀 开始提交并行任务，使用 {num_workers} 个进程")
        logger.info(f"📋 总任务数: {total_combinations}")
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            # 提交所有任务
            future_to_combo = {}
            for i, param, combo_id in combo_list:
                # 添加任务提交日志
                logger.info(f"📌 提交任务 {i + 1}/{total_combinations} 到进程池")
                future = executor.submit(self.run_backtest, param)
                future_to_combo[future] = (i, param, combo_id)
            
            # 处理结果
            processed = 0
            for future in as_completed(future_to_combo):
                i, param, combo_id = future_to_combo[future]
                try:
                    result = future.result()
                    all_results.append(result)
                    processed += 1
                    
                    # 计算进度
                    progress = (processed / total_combinations) * 100
                    
                    # 使用logger记录进度，不使用end="", 因为logger已经有自己的输出方式
                    logger.info(f"✅ 已完成 {processed}/{total_combinations} 个组合 ({progress:.1f}%)")
                    
                    # 更新蓝图中的组合状态为completed
                    if blueprint and combo_id is not None:
                        blueprint = self.update_combination_status(blueprint, combo_id, 'completed', result)
                    
                    # 按指定间隔更新Excel结果和蓝图
                    if processed % save_interval == 0 or processed == total_combinations:
                        # 保存更新后的蓝图（如果有）
                        if blueprint:
                            self.save_blueprint(blueprint, blueprint_file)
                        # 更新Excel结果
                        self._update_excel_results(all_results)
                except Exception as e:
                    logger.error(f"❌ 组合 {i + 1}/{total_combinations} 处理失败: {e}")
                    
                    # 更新蓝图中的组合状态为failed
                    if blueprint and combo_id is not None:
                        blueprint = self.update_combination_status(blueprint, combo_id, 'failed')
                        self.save_blueprint(blueprint, blueprint_file)
                    
                    # 添加失败结果
                    all_results.append({
                        **param,
                        'total_return': -100.0,
                        'annual_return': -100.0,
                        'max_drawdown': -100.0,
                        'trades_count': 0
                    })
                    processed += 1
        
        self.end_time = datetime.now()
        total_duration = self.end_time - self.start_time
        
        # 按总收益率降序排序
        if all_results:
            all_results.sort(key=lambda x: x['total_return'], reverse=True)
            logger.info(f"\n{'='*50}")
            logger.success(f"优化完成！总耗时: {total_duration.total_seconds():.2f} 秒")
            logger.info(f"总共处理 {len(all_results)} 个参数组合")
            logger.info(f"使用 {num_workers} 个进程并行处理")
        
        return all_results
    
    def _update_excel_results(self, results: List[Dict[str, Any]], fixed_file_name: str = "parameter_optimization_results.xlsx"):
        """
        更新固定Excel文件的结果（支持从已有文件读取并追加）
        
        Args:
            results: 回测结果列表
            fixed_file_name: 固定的Excel文件名
        """
        # 导入日志系统
        from utils.logger import logger
        
        logger.info(f"\n🔄 更新Excel结果文件: {fixed_file_name}")
        
        # 使用ResultProcessor类来处理结果，确保与export_to_excel方法保持一致
        from .result_processor import ResultProcessor
        processor = ResultProcessor()
        
        # 获取结果文件的完整路径 - 保存到项目根目录，与app.py保持一致
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(project_root, fixed_file_name)
        
        # 调用export_to_excel方法，确保字段完整和列顺序一致
        processor.export_to_excel(results, file_path)

# 测试代码
if __name__ == "__main__":
    optimizer = BruteForceOptimizer()
    
    # 测试模式
    print("=== 测试模式 ===")
    results = optimizer.optimize(test_mode=True, max_sub_combinations=1, end_date='2025-12-25')
    print(f"测试结果: {results}")
