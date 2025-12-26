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

class BruteForceOptimizer(BaseOptimizer):
    """
    暴力优化器类 - 使用暴力枚举方法进行参数优化
    """
    
    def __init__(self):
        """初始化暴力优化器"""
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
    
    def define_parameter_ranges(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                               use_advanced_weights: bool = True, end_date: str = '2025-12-25') -> Dict[str, List[Any]]:
        """
        定义参数范围

        Args:
            test_mode: 是否为测试模式（只生成一个简单子权重组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            use_advanced_weights: 是否使用高级权重配置模式
            end_date: 回测终点日期（格式：YYYY-MM-DD）

        Returns:
            Dict[str, List[Any]]: 参数范围字典
        """
        print("定义参数范围...")
        print(f"- 回测天数固定为90天，终点日期为{end_date}")
        
        # 根据模式调整参数范围
        if test_mode:
            print("[测试模式] 使用最小参数范围")
            stop_profit_ratio = [0.02]  # 仅测试2%止盈
            stop_loss_ratio = [-0.01]  # 仅测试1%止损
            weight_step = 10  # 使用合理步长以生成有效组合
        else:
            print("- 止盈比例: 3%-15%，步长2%")
            print("- 止损比例: -5%--1%，步长1%")
            if use_advanced_weights:
                print("- 权重配置: 总和100，步长10%")
                weight_step = 10
            else:
                print("- 权重配置: 总和100，步长20%")
                weight_step = 20
            
            # 缩小止盈止损范围以减少组合数量（量化专家建议范围）
            stop_profit_ratio = [x/100 for x in range(3, 16, 2)]  # 3%-15%，步长2%
            stop_loss_ratio = [-x/100 for x in range(1, 6, 1)]  # -5%--1%，步长1%
        
        print("- 子权重配置: 每个主指标子权重总和100")
        
        # 选股策略核心指标（权重配置）
        # 移除deepv指标，将其权重设为零以减少组合数量
        core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
        
        # 生成权重配置
        if test_mode:
            print("[测试模式] 直接生成简单权重组合")
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
            print("[高级模式] 使用重点指标加权的权重配置")
            
            # 基础权重组合 - 限制主权重范围为5%-95%，避免极端值
            base_weights = self._generate_weights_combinations(core_indicators, 100, weight_step, min_weight=5, max_weight=95)
            
            # 仅保留KDJ J值和趋势作为重点指标的组合（减少组合数）
            kdj_trend_weights = self._generate_custom_weights_combinations(
                core_indicators, 100, weight_step, 
                focus_indicators=['kdj_j', 'trend'], 
                focus_weight_factor=1.5
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
            'sub_weights_config': self._generate_sub_weights_combinations(test_mode, max_sub_combinations, use_advanced_mode=use_advanced_weights)
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
                                       end_date: str = '2025-12-25') -> List[Dict[str, Any]]:
        """
        生成所有参数组合

        Args:
            test_mode: 是否为测试模式（使用最小参数范围，仅生成第一个组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            end_date: 回测终点日期（格式：YYYY-MM-DD）
            
        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        param_ranges = self.define_parameter_ranges(test_mode, max_sub_combinations, end_date=end_date)
        
        # 计算总组合数（用于进度显示）
        total_combinations = (len(param_ranges['backtest_days']) * 
                            len(param_ranges['end_date']) * 
                            len(param_ranges['stop_profit_ratio']) * 
                            len(param_ranges['stop_loss_ratio']) * 
                            len(param_ranges['weights_config']) * 
                            len(param_ranges['sub_weights_config']))
        
        print(f"开始生成参数组合...")
        print(f"预计总组合数: {total_combinations}")
        
        combinations = []
        current_count = 0
        
        # 生成所有可能的组合
        for backtest_days in param_ranges['backtest_days']:
            for end_date in param_ranges['end_date']:
                for stop_profit_ratio in param_ranges['stop_profit_ratio']:
                    for stop_loss_ratio in param_ranges['stop_loss_ratio']:
                        for weights_config in param_ranges['weights_config']:
                            for sub_weights_config in param_ranges['sub_weights_config']:
                                # 确保止盈大于止损
                                if stop_profit_ratio > stop_loss_ratio:
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
                                        print(f"已生成 {current_count}/{total_combinations} 个参数组合")
                                    
                                    # 测试模式下仅生成第一个组合
                                    if test_mode and current_count >= 1:
                                        print(f"[测试模式] 仅生成并返回第一个参数组合")
                                        return combinations
        
        print(f"总共生成 {len(combinations)} 个参数组合")
        return combinations
    
    def run_backtest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个参数组合的回测
        
        Args:
            params: 参数组合
            
        Returns:
            Dict[str, Any]: 回测结果
        """
        try:
            import sys
            import os
            import json
            import tempfile
            from datetime import datetime, timedelta
            
            # 设置项目根目录到sys.path
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # 创建策略ID
            strategy_id = f"optimization_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # 计算回测区间
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d')
            start_date = end_date - timedelta(days=params['backtest_days'])
            
            # 准备符合标准回测要求的配置结构
            frontend_config = {
                'backtest': {
                    'initial_capital': params['initial_capital'],
                    'backtest_days': params['backtest_days'],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'max_stocks_to_backtest': 1,
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
                # 添加默认的选股结果（至少包含一个股票）
                'selected_stocks': [
                    {
                        'symbol': '600000.SH',
                        'sec_name': '浦发银行',
                        'industry': '银行',
                        'market_value': 300000000000,
                        'score': 100
                    }
                ]
            }
            
            # 将配置文件保存到求解器目录的config文件夹
            config_dir = os.path.join(self.current_dir, 'config')
            os.makedirs(config_dir, exist_ok=True)
            config_file_path = os.path.join(config_dir, 'current_backtest_config.json')
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(frontend_config, f, ensure_ascii=False, indent=2)
            print(f"✅ 参数配置已更新: {config_file_path}")
            temp_config_file = config_file_path
            
            # 保存原始的sys.argv，避免与gm.api.run()的命令行参数解析冲突
            original_argv = sys.argv.copy()
            sys.argv = [os.path.join(project_root, 'ulti-para-seeker', 'main.py')]
            
            try:
                # 使用标准回测函数运行回测
                try:
                    import backtest_runner
                    backtest_runner.run_backtest(config_path=temp_config_file)
                except ImportError:
                    from .backtest_runner import run_backtest
                    run_backtest(config_path=temp_config_file)
            finally:
                # 恢复原始的sys.argv
                sys.argv = original_argv
            
            # 从文件中读取回测结果
            report_file = 'backtest_report.json'  # 使用与report_generator.py一致的路径
            report = {}
            
            if os.path.exists(report_file):
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    # 删除结果文件，避免影响下一次回测
                    os.unlink(report_file)
                except Exception as e:
                    print(f"读取报告文件失败: {e}")
                    report = {}
            
            # 从报告中提取需要的结果
            performance_metrics = report.get('performance_metrics', {})
            trade_statistics = report.get('trade_statistics', {})
            
            # 返回结果
            return {
                **params,
                'total_return': performance_metrics.get('total_return', 0.0),
                'annual_return': performance_metrics.get('annual_return', 0.0),
                'max_drawdown': performance_metrics.get('max_drawdown', 0.0),
                'trades_count': trade_statistics.get('total_trades', 0)
            }
            
        except Exception as e:
            print(f"回测失败: {e}")
            return {
                **params,
                'total_return': -100.0,  # 失败时返回极低收益率
                'annual_return': -100.0,
                'max_drawdown': -100.0,
                'trades_count': 0
            }
        finally:
            # 不再删除配置文件，因为它是持久化的参数配置文件
            print(f"✅ 参数组合配置已保留: {temp_config_file}")
    
    def optimize(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                end_date: str = '2025-12-25', blueprint_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        执行暴力优化

        Args:
            test_mode: 是否为测试模式（使用最小参数范围，仅生成第一个组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            end_date: 回测终点日期（格式：YYYY-MM-DD）
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
            param_combinations = self.generate_parameter_combinations(test_mode, max_sub_combinations, end_date)
            
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
    
    def run_parallel_optimization(self, param_combinations: List[Dict[str, Any]], num_workers: int = 4, batch_size: int = 50, save_interval: int = 1, blueprint: Optional[Dict[str, Any]] = None, blueprint_file: str = "parameter_blueprint.json") -> List[Dict[str, Any]]:
        """
        排队运行参数优化（支持每10个组合更新一次Excel结果和断点续传）

        Args:
            param_combinations: 参数组合列表
            num_workers: 并行工作进程数（已废弃，保留参数兼容性）
            batch_size: 每批处理的参数组合数（已废弃，保留参数兼容性）
            save_interval: 保存中间结果的批次间隔（已废弃，保留参数兼容性）
            blueprint: 参数组合蓝图数据（用于断点续传）
            blueprint_file: 蓝图文件路径

        Returns:
            List[Dict[str, Any]]: 按收益率排序的结果列表
        """
        total_combinations = len(param_combinations)
        self.start_time = datetime.now()
        all_results = []
        
        print(f"\n=== 排队处理模式 ===")
        print(f"开始排队优化，一个组合一个组合处理")
        print(f"总参数组合数: {total_combinations}")
        print(f"每个组合更新一次Excel结果")
        print(f"支持断点续传: {'是' if blueprint else '否'}")
        print("=" * 50)
        
        # 单个组合逐个处理
        for i, param in enumerate(param_combinations):
            try:
                # 查找当前参数组合在蓝图中的ID
                combo_id = None
                if blueprint:
                    for combo in blueprint['combinations']:
                        if combo['params'] == param:
                            combo_id = combo['id']
                            # 更新状态为running
                            combo['status'] = 'running'
                            combo['started_at'] = datetime.now().isoformat()
                            # 保存更新后的蓝图
                            self.save_blueprint(blueprint, blueprint_file)
                            break
                
                # 处理当前组合
                start_time = datetime.now()
                result = self.run_backtest(param)
                all_results.append(result)
                duration = datetime.now() - start_time
                
                # 计算进度
                processed = i + 1
                progress = (processed / total_combinations) * 100
                
                print(f"\n✅ 组合 {processed}/{total_combinations} 处理完成")
                print(f"   耗时: {duration.total_seconds():.2f} 秒")
                print(f"   累计处理: {processed}/{total_combinations} ({progress:.1f}%)")
                print(f"   已处理组合数: {len(all_results)}")
                print(f"   当前组合总收益率: {result['total_return']:.2f}%")
                
                # 更新蓝图中的组合状态为completed
                if blueprint and combo_id is not None:
                    blueprint = self.update_combination_status(blueprint, combo_id, 'completed', result)
                    self.save_blueprint(blueprint, blueprint_file)
                    print(f"   蓝图已更新: 组合 {combo_id} 状态变更为 'completed'")
                
                # 每1个组合更新一次Excel结果
                if processed % 1 == 0 or processed == total_combinations:
                    self._update_excel_results(all_results)
                
                # 计算剩余时间估计
                if processed > 0:
                    avg_time = (datetime.now() - self.start_time).total_seconds() / processed
                    remaining_time = avg_time * (total_combinations - processed)
                    print(f"   预计剩余时间: {remaining_time:.2f} 秒")
                    
            except Exception as e:
                print(f"\n❌ 组合 {i + 1}/{total_combinations} 处理失败: {e}")
                print("   继续处理下一个组合...")
                
                # 更新蓝图中的组合状态为failed
                if blueprint:
                    combo_id = None
                    for combo in blueprint['combinations']:
                        if combo['params'] == param:
                            combo_id = combo['id']
                            break
                    if combo_id is not None:
                        blueprint = self.update_combination_status(blueprint, combo_id, 'failed')
                        self.save_blueprint(blueprint, blueprint_file)
                        print(f"   蓝图已更新: 组合 {combo_id} 状态变更为 'failed'")
                
                # 添加失败结果
                all_results.append({
                    **param,
                    'total_return': -100.0,
                    'annual_return': -100.0,
                    'max_drawdown': -100.0,
                    'trades_count': 0
                })
        
        self.end_time = datetime.now()
        total_duration = self.end_time - self.start_time
        
        # 按总收益率降序排序
        if all_results:
            all_results.sort(key=lambda x: x['total_return'], reverse=True)
            print(f"\n{'='*50}")
            print(f"优化完成！总耗时: {total_duration.total_seconds():.2f} 秒")
            print(f"总共处理 {len(all_results)} 个参数组合")
        
        return all_results
    
    def _update_excel_results(self, results: List[Dict[str, Any]], fixed_file_name: str = "parameter_optimization_results.xlsx"):
        """
        更新固定Excel文件的结果（支持从已有文件读取并追加）
        
        Args:
            results: 回测结果列表
            fixed_file_name: 固定的Excel文件名
        """
        print(f"\n🔄 更新Excel结果文件: {fixed_file_name}")
        
        # 获取结果文件的完整路径
        file_path = os.path.join(self.current_dir, fixed_file_name)
        
        # 转换新结果为DataFrame
        new_df_list = []
        
        for i, result in enumerate(results):
            # 提取参数
            row = {
                '序号': i + 1,
                '回测天数': result['backtest_days'],
                '止盈比例(%)': result['stop_profit_ratio'] * 100,
                '止损比例(%)': result['stop_loss_ratio'] * 100,
                '总收益率(%)': result['total_return'],
                '年化收益率(%)': result['annual_return'],
                '最大回撤(%)': result['max_drawdown'],
                '交易次数': result['trades_count']
            }
            
            # 添加权重配置
            for indicator, weight in result['weights_config'].items():
                row[f'权重_{indicator}'] = weight
            
            # 添加子权重配置
            for main_indicator, sub_config in result['sub_weights_config'].items():
                for sub_indicator, weight in sub_config['sub_weights'].items():
                    row[f'子权重_{main_indicator}_{sub_indicator}'] = weight
            
            new_df_list.append(row)
        
        new_df = pd.DataFrame(new_df_list)
        
        # 检查文件是否存在
        if os.path.exists(file_path):
            # 读取已有文件内容
            try:
                existing_df = pd.read_excel(file_path)
                
                # 合并数据
                # 注意：这里简单处理，替换已有数据
                # 在实际应用中，可能需要更复杂的合并逻辑
                combined_df = new_df
            except Exception as e:
                print(f"读取已有文件失败: {e}，将创建新文件")
                combined_df = new_df
        else:
            # 文件不存在，使用新数据
            combined_df = new_df
        
        # 保存结果到Excel文件
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                combined_df.to_excel(writer, index=False)
            print(f"✅ Excel结果文件已更新: {file_path}")
        except Exception as e:
            print(f"保存Excel文件失败: {e}")

# 测试代码
if __name__ == "__main__":
    optimizer = BruteForceOptimizer()
    
    # 测试模式
    print("=== 测试模式 ===")
    results = optimizer.optimize(test_mode=True, max_sub_combinations=1, end_date='2025-12-25')
    print(f"测试结果: {results}")
