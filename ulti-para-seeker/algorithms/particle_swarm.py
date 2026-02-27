#!/usr/bin/env python
# coding=utf-8
"""
粒子群算法优化器 - 使用粒子群算法进行参数优化
"""

import random
import copy
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import BaseOptimizer
import sys
import os

# 添加项目根目录到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 使用绝对导入
from utils.parameter_utils import validate_parameter_combination, format_parameter_combination


class ParticleSwarmOptimizer(BaseOptimizer):
    """
    粒子群算法优化器 - 使用粒子群算法进行参数优化
    """

    def __init__(self):
        """
        初始化粒子群算法优化器
        """
        super().__init__()

        # 粒子群算法参数
        self.population_size = 50  # 粒子数量
        self.generations = 50  # 迭代代数
        self.c1 = 2.0  # 认知因子（粒子自身经验）
        self.c2 = 2.0  # 社会因子（群体经验）
        self.w = 0.7  # 惯性权重
        self.w_min = 0.4  # 最小惯性权重
        self.w_max = 0.9  # 最大惯性权重
        self.early_stopping_generations = 10  # 早期停止代数
        self.min_improvement = 0.1  # 最小改进阈值（百分比）

        # 速度限制（百分位格式）
        self.max_velocity = {
            'stop_profit_ratio': 2,
            'stop_loss_ratio': 1,
            'max_holding_days': 5,
            'weight_change': 10
        }

    def define_parameter_space(self, test_mode: bool = False, max_sub_combinations: int = 10,
                             end_date: str = '2025-12-25', backtest_days: int = 90,
                             stop_profit_min: int = None, stop_profit_max: int = None,
                             stop_profit_step: int = None, stop_loss_min: int = None,
                             stop_loss_max: int = None, stop_loss_step: int = None,
                             weight_step: int = None, initial_capital: int = 60000,
                             max_holding_days_min: int = 1, max_holding_days_max: int = 30,
                             max_holding_days_step: int = 1) -> Dict[str, Any]:
        """
        定义参数空间

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            backtest_days: 回测天数
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            initial_capital: 初始资金
            max_holding_days_min: 最大持仓天数最小值
            max_holding_days_max: 最大持仓天数最大值
            max_holding_days_step: 最大持仓天数步长

        Returns:
            Dict[str, Any]: 参数空间字典
        """
        from utils.logger import logger
        logger.info("定义粒子群算法参数边界...")
        logger.info(f"- 回测天数: {backtest_days}天，终点日期为{end_date}")
        logger.info(f"- 初始资金: {initial_capital}元")

        # 如果用户提供了参数边界，使用用户提供的值，否则使用默认值
        if test_mode:
            logger.info("[测试模式] 使用最小参数范围")
            # 测试模式下使用简化参数范围
            param_space = {
                'stop_profit_ratio': {'min': stop_profit_min if stop_profit_min is not None else 2,
                                    'max': stop_profit_max if stop_profit_max is not None else 5,
                                    'step': stop_profit_step if stop_profit_step is not None else 1},
                'stop_loss_ratio': {'min': stop_loss_min if stop_loss_min is not None else -3,
                                  'max': stop_loss_max if stop_loss_max is not None else -1,
                                  'step': stop_loss_step if stop_loss_step is not None else 1},
                'max_holding_days': {'min': max_holding_days_min,
                                   'max': max_holding_days_min + 1,
                                   'step': max_holding_days_step},
                'weights_step': weight_step if weight_step is not None else 50,
                'test_mode': True,
                'end_date': end_date,
                'backtest_days': backtest_days
            }
        else:
            # 使用用户提供的参数边界或默认值
            actual_stop_profit_min = stop_profit_min if stop_profit_min is not None else 3
            actual_stop_profit_max = stop_profit_max if stop_profit_max is not None else 15
            actual_stop_profit_step = stop_profit_step if stop_profit_step is not None else 2

            actual_stop_loss_min = stop_loss_min if stop_loss_min is not None else -5
            actual_stop_loss_max = stop_loss_max if stop_loss_max is not None else -1
            actual_stop_loss_step = stop_loss_step if stop_loss_step is not None else 1

            actual_weight_step = weight_step if weight_step is not None else 10

            logger.info(f"- 止盈比例: {actual_stop_profit_min}%-{actual_stop_profit_max}%，步长{actual_stop_profit_step}%")
            logger.info(f"- 止损比例: {actual_stop_loss_min}%--{abs(actual_stop_loss_max)}%，步长{actual_stop_loss_step}%")
            logger.info(f"- 最大持仓天数: {max_holding_days_min}-{max_holding_days_max}天，步长{max_holding_days_step}天")
            logger.info(f"- 权重配置: 总和100，步长{actual_weight_step}%")

            param_space = {
                'stop_profit_ratio': {'min': actual_stop_profit_min,
                                    'max': actual_stop_profit_max,
                                    'step': actual_stop_profit_step},
                'stop_loss_ratio': {'min': actual_stop_loss_min,
                                  'max': actual_stop_loss_max,
                                  'step': actual_stop_loss_step},
                'max_holding_days': {'min': max_holding_days_min,
                                   'max': max_holding_days_max,
                                   'step': max_holding_days_step},
                'weights_step': actual_weight_step,
                'test_mode': False,
                'end_date': end_date,
                'backtest_days': backtest_days
            }

        return param_space

    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10,
                                      end_date: str = '2025-12-25', stop_profit_min: int = None,
                                      stop_profit_max: int = None, stop_profit_step: int = None,
                                      stop_loss_min: int = None, stop_loss_max: int = None,
                                      stop_loss_step: int = None, weight_step: int = None,
                                      focus_indicators: List[str] = None, focus_weight_factor: float = 1.5,
                                      initial_capital: int = 60000, backtest_days: int = 90,
                                      max_holding_days_min: int = 1, max_holding_days_max: int = 30,
                                      max_holding_days_step: int = 1,
                                      existing_blueprint: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        生成参数组合

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            initial_capital: 初始资金
            backtest_days: 回测天数
            max_holding_days_min: 最大持仓天数最小值
            max_holding_days_max: 最大持仓天数最大值
            max_holding_days_step: 最大持仓天数步长
            existing_blueprint: 现有蓝图数据

        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        return self.generate_initial_population(test_mode, max_sub_combinations, end_date, backtest_days,
                                              stop_profit_min, stop_profit_max, stop_profit_step,
                                              stop_loss_min, stop_loss_max, stop_loss_step,
                                              weight_step, initial_capital, max_holding_days_min,
                                              max_holding_days_max, max_holding_days_step, existing_blueprint)

    def generate_initial_population(self, test_mode: bool = False, max_sub_combinations: int = 10,
                                  end_date: str = '2025-12-25', backtest_days: int = 90,
                                  stop_profit_min: int = None, stop_profit_max: int = None,
                                  stop_profit_step: int = None, stop_loss_min: int = None,
                                  stop_loss_max: int = None, stop_loss_step: int = None,
                                  weight_step: int = None, initial_capital: int = 60000,
                                  max_holding_days_min: int = 1, max_holding_days_max: int = 30,
                                  max_holding_days_step: int = 1,
                                  existing_blueprint: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        生成初始粒子群

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            backtest_days: 回测天数
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            initial_capital: 初始资金
            max_holding_days_min: 最大持仓天数最小值
            max_holding_days_max: 最大持仓天数最大值
            max_holding_days_step: 最大持仓天数步长
            existing_blueprint: 现有蓝图，用于提取优势组合

        Returns:
            List[Dict[str, Any]]: 初始粒子群（参数组合列表）
        """
        from utils.logger import logger
        param_space = self.define_parameter_space(test_mode, max_sub_combinations, end_date, backtest_days,
                                               stop_profit_min, stop_profit_max, stop_profit_step,
                                               stop_loss_min, stop_loss_max, stop_loss_step,
                                               weight_step, initial_capital,
                                               max_holding_days_min, max_holding_days_max, max_holding_days_step)

        print(f"开始生成粒子群初始种群...")
        print(f"- 粒子数量: {self.population_size}")

        # 从现有蓝图中提取优势组合
        elite_combinations = []
        if existing_blueprint:
            print(f"\n{'='*60}")
            print(f"📊 处理现有蓝图数据")
            print(f"{'='*60}")
            print(f"- 蓝图总组合数: {len(existing_blueprint.get('combinations', []))}")

            # 统计各状态组合数
            completed_count = sum(1 for c in existing_blueprint.get('combinations', []) if c.get('status') == 'completed')
            failed_count = sum(1 for c in existing_blueprint.get('combinations', []) if c.get('status') == 'failed')
            pending_count = sum(1 for c in existing_blueprint.get('combinations', []) if c.get('status') == 'pending')
            running_count = sum(1 for c in existing_blueprint.get('combinations', []) if c.get('status') == 'running')

            print(f"  ├─ 已完成: {completed_count}")
            print(f"  ├─ 失败: {failed_count}")
            print(f"  ├─ 待处理: {pending_count}")
            print(f"  └─ 运行中: {running_count}")

            print(f"\n开始提取优势组合...")
            elite_combinations = self._extract_elite_combinations(existing_blueprint, param_space)

            if elite_combinations:
                print(f"\n✅ 成功提取了 {len(elite_combinations)} 个优势组合")
                # 显示前3个优势组合的信息
                for i, elite in enumerate(elite_combinations[:3], 1):
                    print(f"  [{i}] 止盈:{elite.get('stop_profit_ratio')}%, 止损:{elite.get('stop_loss_ratio')}%, 最大持仓:{elite.get('max_holding_days', 10)}天")
                if len(elite_combinations) > 3:
                    print(f"  ... 还有 {len(elite_combinations) - 3} 个优势组合")
            else:
                print(f"\n⚠️  警告: 未提取到符合条件的优势组合")
                print(f"  - 可能原因:")
                print(f"    1. 蓝图中没有已完成的组合")
                print(f"    2. 已完成组合的收益率超出有效范围 (-50% ~ 150%)")
                print(f"    3. 组合参数不在当前参数空间范围内")

            print(f"{'='*60}\n")
        else:
            print(f"\n💡 提示: 未检测到现有蓝图文件，将使用纯随机生成的初始粒子群\n")

        # 计算种群中优势和随机部分的比例
        # 精英占30%，随机占70%
        elite_count = min(len(elite_combinations), int(self.population_size * 0.3))
        random_count = self.population_size - elite_count

        if elite_count > 0:
            print(f"种群构成: 优势组合 {elite_count} 个 + 基于精英变异的 {random_count} 个")
        else:
            print(f"种群构成: 全部 {self.population_size} 个为随机生成组合")

        particles = elite_combinations[:elite_count]

        # 生成子权重配置
        from utils.weight_utils import generate_sub_weights_combinations
        sub_weights_configs = generate_sub_weights_combinations(
            test_mode, max_combinations=max_sub_combinations, use_advanced_mode=True
        )

        # 确保生成足够多的不重复组合
        generated_combs = set()
        attempts = 0
        max_attempts = self.population_size * 5  # 最多尝试5倍于粒子数量的次数

        while len(particles) < self.population_size and attempts < max_attempts:
            attempts += 1

            # 如果有精英组合,基于精英进行变异;否则随机生成
            if elite_combinations and random.random() < 0.7:
                # 从精英组合中选择一个作为基准
                base_particle = random.choice(elite_combinations)

                # 粒子群算法的变异：在精英组合周围进行搜索
                stop_profit = base_particle['stop_profit_ratio']
                stop_loss = base_particle['stop_loss_ratio']
                max_holding_days = base_particle.get('max_holding_days', 10)
                weights_config = base_particle.get('weights_config', {})

                # 在精英组合周围添加随机扰动
                # 止盈扰动
                profit_perturbation = random.randint(-1, 1) * param_space['stop_profit_ratio']['step']
                stop_profit = max(
                    param_space['stop_profit_ratio']['min'],
                    min(param_space['stop_profit_ratio']['max'], stop_profit + profit_perturbation)
                )

                # 止损扰动
                loss_perturbation = random.randint(-1, 1) * param_space['stop_loss_ratio']['step']
                stop_loss = max(
                    param_space['stop_loss_ratio']['min'],
                    min(param_space['stop_loss_ratio']['max'], stop_loss + loss_perturbation)
                )

                # 最大持仓天数扰动
                days_perturbation = random.randint(-1, 1) * param_space['max_holding_days']['step']
                max_holding_days = max(
                    param_space['max_holding_days']['min'],
                    min(param_space['max_holding_days']['max'], max_holding_days + days_perturbation)
                )

                # 权重扰动 - 提高变异概率
                if random.random() < 0.7:  # 从0.3提高到0.7
                    weights_config = self._mutate_weights(weights_config, param_space['weights_step'])
            else:
                # 完全随机生成
                stop_profit_min = param_space['stop_profit_ratio']['min']
                stop_profit_max = param_space['stop_profit_ratio']['max']
                stop_profit_step = param_space['stop_profit_ratio']['step']

                # 生成止盈选项列表
                stop_profit_options = list(range(
                    stop_profit_min,
                    stop_profit_max + 1,
                    stop_profit_step
                ))
                stop_profit = random.choice(stop_profit_options)

                # 处理止损比例，确保范围正确
                stop_loss_min = param_space['stop_loss_ratio']['min']
                stop_loss_max = param_space['stop_loss_ratio']['max']
                stop_loss_step = param_space['stop_loss_ratio']['step']

                # 确保止损最小值小于最大值
                if stop_loss_min > stop_loss_max:
                    stop_loss_min, stop_loss_max = stop_loss_max, stop_loss_min

                # 生成止损选项列表
                stop_loss_options = list(range(
                    stop_loss_min,
                    stop_loss_max + 1,
                    stop_loss_step
                ))

                # 确保生成了有效的止损选项
                if not stop_loss_options:
                    # 如果没有生成有效的止损选项，使用默认值
                    stop_loss_options = [-3, -2, -1]

                stop_loss = random.choice(stop_loss_options)

                # 生成最大持仓天数选项列表
                max_holding_days_min = param_space['max_holding_days']['min']
                max_holding_days_max = param_space['max_holding_days']['max']
                max_holding_days_step = param_space['max_holding_days']['step']

                max_holding_days_options = list(range(
                    max_holding_days_min,
                    max_holding_days_max + 1,
                    max_holding_days_step
                ))
                max_holding_days = random.choice(max_holding_days_options)

                # 生成权重配置
                weights_config = self._generate_random_weights_config(param_space['weights_step'])

            # 确保止盈大于止损
            if stop_profit <= stop_loss:
                continue

            # 随机选择一个子权重配置
            if sub_weights_configs:
                sub_weights = random.choice(sub_weights_configs)
            else:
                sub_weights = self._generate_default_sub_weights()

            # 创建参数组合
            param_comb = {
                'backtest_days': backtest_days,
                'end_date': end_date,
                'stop_profit_ratio': stop_profit,
                'stop_loss_ratio': stop_loss,
                'max_holding_days': max_holding_days,
                'weights_config': weights_config,
                'sub_weights_config': sub_weights
            }

            # 生成组合哈希，用于去重
            from utils.parameter_utils import generate_param_hash
            comb_hash = generate_param_hash(param_comb)

            # 确保组合不重复
            if comb_hash not in generated_combs:
                # 验证参数组合
                if validate_parameter_combination(param_comb):
                    particles.append(param_comb)
                    generated_combs.add(comb_hash)

                    # 只在成功添加到particles时打印日志
                    if elite_combinations and random.random() < 0.7:
                        # 显示完整的变异信息，包括权重摘要
                        weights_summary = {}
                        if weights_config:
                            sorted_weights = sorted(weights_config.items(), key=lambda x: x[1], reverse=True)[:3]
                            weights_summary = {k: v for k, v in sorted_weights}
                        logger.info(f"  基于精英变异: 止盈={stop_profit}%, 止损={stop_loss}%, 最大持仓={max_holding_days}天, 权重={weights_summary}")

                    if len(particles) >= self.population_size:
                        break

        # 如果生成的有效组合不足，补充不同的配置
        while len(particles) < self.population_size:
            # 使用基类的通用方法生成随机参数组合
            param_comb = self._generate_random_params(param_space, backtest_days, end_date)

            # 验证参数组合
            if validate_parameter_combination(param_comb):
                # 检查是否重复
                from utils.parameter_utils import generate_param_hash
                comb_hash = generate_param_hash(param_comb)
                if comb_hash not in generated_combs:
                    particles.append(param_comb)
                    generated_combs.add(comb_hash)

        logger.info(f"已生成 {len(particles)} 个初始粒子（包含 {elite_count} 个优势组合）")
        return particles

    def _extract_elite_combinations(self, blueprint: Dict[str, Any],
                                    param_space: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从蓝图中提取优势组合(优化版 - 大数据量高效处理)

        Args:
            blueprint: 蓝图数据
            param_space: 参数空间边界

        Returns:
            List[Dict[str, Any]]: 优势组合列表
        """
        from utils.multi_objective_scorer import get_scorer

        scorer = get_scorer()

        # 获取所有已完成的组合
        completed_combinations = []
        total_combinations = len(blueprint.get('combinations', []))

        # 如果组合数很大(>2000),只处理前50%,提高效率
        scan_limit = min(total_combinations, 2000) if total_combinations > 2000 else total_combinations

        for i, combo in enumerate(blueprint.get('combinations', [])):
            if i >= scan_limit:
                break

            if combo.get('status') == 'completed' and combo.get('result'):
                # 快速过滤: 检查收益率是否在合理范围
                result = combo['result']
                total_return = result.get('total_return', 0)
                # 使用更严格的过滤,减少后续计算量
                if -50 <= total_return <= 150:  # 更严格的合理收益率范围
                    completed_combinations.append(combo)

        if not completed_combinations:
            return []

        # 使用多目标评价函数对组合进行排序
        ranked_combinations = scorer.rank_combinations(completed_combinations)

        # 获取前20%的精英组合,最多50个,避免过多
        elite_count = min(50, max(5, int(len(ranked_combinations) * 0.2)))
        elite_combinations = ranked_combinations[:elite_count]

        # 输出参数空间范围
        print(f"- 参数空间范围:")
        print(f"  止盈: {param_space['stop_profit_ratio']['min']}% ~ {param_space['stop_profit_ratio']['max']}%")
        print(f"  止损: {param_space['stop_loss_ratio']['min']}% ~ {param_space['stop_loss_ratio']['max']}%")

        # 转换为参数格式（提取params部分）
        converted_elite = []
        out_of_range_count = 0
        for combo in elite_combinations:
            params = combo.get('params', {}).copy()
            # 确保参数在当前参数空间边界内
            if self._is_within_param_space(params, param_space):
                converted_elite.append(params)
            else:
                out_of_range_count += 1
                if out_of_range_count <= 3:  # 只显示前3个超出范围的
                    print(f"  超出范围组合: 止盈={params.get('stop_profit_ratio')}%, 止损={params.get('stop_loss_ratio')}%")

        print(f"- 扫描了 {scan_limit}/{total_combinations} 个组合")
        print(f"- 筛选出 {len(completed_combinations)} 个有效组合")
        print(f"- 评估出 {len(elite_combinations)} 个优势组合")
        if out_of_range_count > 0:
            print(f"- 其中 {out_of_range_count} 个超出参数空间范围被过滤")
        print(f"- 最终保留 {len(converted_elite)} 个精英组合")

        return converted_elite

    def _is_within_param_space(self, params: Dict[str, Any], param_space: Dict[str, Any]) -> bool:
        """
        检查参数是否在指定空间内

        Args:
            params: 参数字典
            param_space: 参数空间边界

        Returns:
            bool: 是否在空间内
        """
        stop_profit = params.get('stop_profit_ratio', 0)
        stop_loss = params.get('stop_loss_ratio', 0)
        max_holding_days = params.get('max_holding_days', 10)

        # 检查止盈
        sp_min = param_space['stop_profit_ratio']['min']
        sp_max = param_space['stop_profit_ratio']['max']
        if not (sp_min <= stop_profit <= sp_max):
            return False

        # 检查止损
        sl_min = param_space['stop_loss_ratio']['min']
        sl_max = param_space['stop_loss_ratio']['max']
        if not (sl_min <= stop_loss <= sl_max):
            return False

        # 检查最大持仓天数
        mhd_min = param_space['max_holding_days']['min']
        mhd_max = param_space['max_holding_days']['max']
        if not (mhd_min <= max_holding_days <= mhd_max):
            return False

        return True

    def _mutate_weights(self, weights: Dict[str, int], weight_step: int = 10) -> Dict[str, int]:
        """
        权重配置变异操作

        Args:
            weights: 权重配置字典
            weight_step: 权重步长

        Returns:
            Dict[str, int]: 变异后的权重配置
        """
        mutated_weights = weights.copy()

        # 获取可变异的指标
        indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
        indicators_in_weights = [ind for ind in indicators if ind in mutated_weights]

        if not indicators_in_weights:
            return mutated_weights

        # 随机选择1-2个指标进行变异
        num_mutations = random.randint(1, min(2, len(indicators_in_weights)))
        indicators_to_mutate = random.sample(indicators_in_weights, num_mutations)

        for ind in indicators_to_mutate:
            current_weight = mutated_weights[ind]
            mutation_direction = random.choice([-1, 1])
            mutation_amount = mutation_direction * weight_step * random.randint(1, 2)
            new_weight = max(5, min(95, current_weight + mutation_amount))
            mutated_weights[ind] = new_weight

        # 调整权重总和为100
        mutated_weights = self._adjust_weights_total(mutated_weights)

        return mutated_weights

    def _adjust_weights_total(self, weights: Dict[str, int]) -> Dict[str, int]:
        """
        调整权重总和为100

        Args:
            weights: 权重配置字典

        Returns:
            Dict[str, int]: 调整后的权重配置
        """
        total = sum(weights.values())
        diff = 100 - total

        if diff == 0:
            return weights

        # 获取核心指标列表
        core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
        core_indicators_in_weights = [ind for ind in core_indicators if ind in weights]

        # 按权重从大到小排序
        sorted_indicators = sorted(core_indicators_in_weights, key=lambda x: weights[x], reverse=True)

        # 调整权重
        for ind in sorted_indicators:
            if diff > 0:
                # 增加权重
                if weights[ind] < 95:
                    add = min(diff, 95 - weights[ind])
                    weights[ind] += add
                    diff -= add
            else:
                # 减少权重
                if weights[ind] > 5:
                    subtract = max(diff, -(weights[ind] - 5))
                    weights[ind] += subtract
                    diff -= subtract

            if diff == 0:
                break

        # 最后确保总和为100
        total = sum(weights.values())
        if total != 100:
            diff = 100 - total
            if diff != 0:
                # 调整deepv权重
                weights['deepv'] = max(0, min(100, weights.get('deepv', 0) + diff))

        return weights

    def optimize(self, test_mode: bool = False, max_sub_combinations: int = 10,
                end_date: str = '2025-12-25', stop_profit_min: int = None,
                stop_profit_max: int = None, stop_profit_step: int = None,
                stop_loss_min: int = None, stop_loss_max: int = None,
                stop_loss_step: int = None, weight_step: int = None,
                initial_capital: int = 60000, backtest_days: int = 90,
                existing_blueprint: Optional[Dict[str, Any]] = None,
                max_holding_days_min: int = 1, max_holding_days_max: int = 30,
                max_holding_days_step: int = 1) -> List[Dict[str, Any]]:
        """
        执行粒子群算法优化

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            initial_capital: 初始资金
            backtest_days: 回测天数
            existing_blueprint: 现有蓝图数据
            max_holding_days_min: 最大持仓天数最小值
            max_holding_days_max: 最大持仓天数最大值
            max_holding_days_step: 最大持仓天数步长

        Returns:
            List[Dict[str, Any]]: 优化结果列表
        """
        print("开始粒子群算法优化...")
        print(f"- 粒子数量: {self.population_size}")
        print(f"- 迭代代数: {self.generations}")
        print(f"- 认知因子: {self.c1}")
        print(f"- 社会因子: {self.c2}")
        print(f"- 惯性权重: {self.w_min} ~ {self.w_max}")
        print(f"- 早期停止: {self.early_stopping_generations} 代无改进")

        # 初始化种群，传递所有参数边界
        swarm = self.generate_initial_population(
            test_mode, max_sub_combinations, end_date, backtest_days,
            stop_profit_min, stop_profit_max, stop_profit_step,
            stop_loss_min, stop_loss_max, stop_loss_step,
            weight_step, initial_capital, max_holding_days_min,
            max_holding_days_max, max_holding_days_step, existing_blueprint
        )

        # 为每个参数组合添加初始资金
        for param in swarm:
            param['initial_capital'] = initial_capital

        # 初始化粒子群数据结构
        swarm_with_fitness = []
        for particle in swarm:
            swarm_with_fitness.append({
                'params': particle,
                'fitness': -float('inf'),
                'best_position': particle.copy(),
                'best_fitness': -float('inf'),
                'velocity': {
                    'stop_profit_ratio': 0,
                    'stop_loss_ratio': 0,
                    'max_holding_days': 0,
                }
            })

        # 评估初始粒子群
        swarm_with_fitness = self._evaluate_swarm(swarm_with_fitness)

        # 找出全局最优解
        global_best = max(swarm_with_fitness, key=lambda x: x['best_fitness'])

        # 保存所有代的结果
        all_results = [global_best.copy()]

        # 初始化早期停止相关变量
        best_fitness_history = []
        no_improvement_generations = 0

        # 粒子群优化过程
        for generation in range(self.generations):
            print(f"\n第 {generation + 1}/{self.generations} 代进化...")

            # 计算当前代的惯性权重（线性递减）
            w = self.w_max - (self.w_max - self.w_min) * generation / self.generations

            # 更新粒子的速度和位置
            for particle in swarm_with_fitness:
                self._update_velocity(particle, w, global_best)
                self._update_position(particle)

            # 评估更新后的种群
            swarm_with_fitness = self._evaluate_swarm(swarm_with_fitness)

            # 找出当前代的最优解
            current_best = max(swarm_with_fitness, key=lambda x: x['fitness'])

            # 更新全局最优解
            if current_best['fitness'] > global_best['fitness']:
                global_best = current_best.copy()
                print(f"  发现新的全局最优解! 适应度: {global_best['fitness']:.4f}")

            # 记录最佳适应度历史
            best_fitness_history.append(global_best['fitness'])

            # 早期停止检查
            if len(best_fitness_history) >= self.early_stopping_generations:
                recent_improvement = best_fitness_history[-1] - best_fitness_history[-self.early_stopping_generations]
                if recent_improvement < self.min_improvement:
                    no_improvement_generations += 1
                    print(f"  连续 {no_improvement_generations} 代无显著改进 (改进: {recent_improvement:.4f})")
                    if no_improvement_generations >= 3:
                        print(f"\n早期停止: 已连续 {self.early_stopping_generations * 3} 代无显著改进")
                        break
                else:
                    no_improvement_generations = 0

            # 保存当前代的结果
            all_results.extend([item.copy() for item in swarm_with_fitness])

            print(f"  当前代最佳适应度: {current_best['fitness']:.4f}")
            print(f"  全局最佳适应度: {global_best['fitness']:.4f}")
            print(f"  全局最优参数: 止盈={global_best['params']['stop_profit_ratio']}%, 止损={global_best['params']['stop_loss_ratio']}%")

        print("\n粒子群算法优化完成!")
        print(f"最优解的参数:")
        print(f"  止盈: {global_best['params']['stop_profit_ratio']}%")
        print(f"  止损: {global_best['params']['stop_loss_ratio']}%")
        print(f"  适应度: {global_best['fitness']:.4f}")

        # 按适应度排序并返回最佳结果
        sorted_results = sorted(all_results, key=lambda x: x.get('fitness', 0), reverse=True)
        return sorted_results[:10]  # 返回前10个最佳结果

    def _evaluate_swarm(self, swarm: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        评估粒子群适应度

        Args:
            swarm: 粒子群列表

        Returns:
            List[Dict[str, Any]]: 包含适应度的粒子群列表
        """
        for particle in swarm:
            try:
                # 运行回测
                result = self.run_backtest(particle['params'])

                # 计算适应度（使用总收益率作为适应度）
                fitness = self._calculate_fitness(result)
            except Exception as e:
                # 如果回测失败，使用较低的适应度
                fitness = -1000

            # 更新粒子的历史最优位置
            if fitness > particle['best_fitness']:
                particle['best_fitness'] = fitness
                particle['best_position'] = particle['params'].copy()

            particle['fitness'] = fitness

        return swarm

    def _calculate_fitness(self, result: Dict[str, Any]) -> float:
        """
        计算适应度

        Args:
            result: 回测结果

        Returns:
            float: 适应度值
        """
        try:
            # 使用总收益率作为主要适应度指标
            total_return = result.get('total_return', 0)

            # 使用夏普比率作为辅助指标
            sharpe_ratio = result.get('sharpe_ratio', 0)

            # 使用最大回撤作为风险惩罚
            max_drawdown = result.get('max_drawdown', 0)

            # 计算综合适应度
            fitness = total_return * 100 + sharpe_ratio * 10 - max_drawdown * 50

            return fitness
        except Exception:
            return -1000

    def _update_velocity(self, particle: Dict[str, Any], w: float, global_best: Dict[str, Any]):
        """
        更新粒子速度

        Args:
            particle: 粒子
            w: 惯性权重
            global_best: 全局最优位置
        """
        # 更新止盈比例速度
        cognitive_velocity_profit = self.c1 * random.random() * (
            particle['best_position']['stop_profit_ratio'] - particle['params']['stop_profit_ratio']
        )
        social_velocity_profit = self.c2 * random.random() * (
            global_best['params']['stop_profit_ratio'] - particle['params']['stop_profit_ratio']
        )
        particle['velocity']['stop_profit_ratio'] = (
            w * particle['velocity']['stop_profit_ratio'] +
            cognitive_velocity_profit +
            social_velocity_profit
        )

        # 限制速度
        particle['velocity']['stop_profit_ratio'] = max(
            -self.max_velocity['stop_profit_ratio'],
            min(self.max_velocity['stop_profit_ratio'], particle['velocity']['stop_profit_ratio'])
        )

        # 更新止损比例速度
        cognitive_velocity_loss = self.c1 * random.random() * (
            particle['best_position']['stop_loss_ratio'] - particle['params']['stop_loss_ratio']
        )
        social_velocity_loss = self.c2 * random.random() * (
            global_best['params']['stop_loss_ratio'] - particle['params']['stop_loss_ratio']
        )
        particle['velocity']['stop_loss_ratio'] = (
            w * particle['velocity']['stop_loss_ratio'] +
            cognitive_velocity_loss +
            social_velocity_loss
        )

        # 限制速度
        particle['velocity']['stop_loss_ratio'] = max(
            -self.max_velocity['stop_loss_ratio'],
            min(self.max_velocity['stop_loss_ratio'], particle['velocity']['stop_loss_ratio'])
        )

        # 更新最大持仓天数速度
        cognitive_velocity_days = self.c1 * random.random() * (
            particle['best_position'].get('max_holding_days', 10) - particle['params'].get('max_holding_days', 10)
        )
        social_velocity_days = self.c2 * random.random() * (
            global_best['params'].get('max_holding_days', 10) - particle['params'].get('max_holding_days', 10)
        )
        particle['velocity']['max_holding_days'] = (
            w * particle['velocity']['max_holding_days'] +
            cognitive_velocity_days +
            social_velocity_days
        )

        # 限制速度
        particle['velocity']['max_holding_days'] = max(
            -self.max_velocity['max_holding_days'],
            min(self.max_velocity['max_holding_days'], particle['velocity']['max_holding_days'])
        )

    def _update_position(self, particle: Dict[str, Any]):
        """
        更新粒子位置

        Args:
            particle: 粒子
        """
        # 更新止盈比例
        particle['params']['stop_profit_ratio'] += particle['velocity']['stop_profit_ratio']
        # 限制在参数范围内（百分位格式）
        particle['params']['stop_profit_ratio'] = max(3, min(15, particle['params']['stop_profit_ratio']))
        particle['params']['stop_profit_ratio'] = int(particle['params']['stop_profit_ratio'])

        # 更新止损比例
        particle['params']['stop_loss_ratio'] += particle['velocity']['stop_loss_ratio']
        # 限制在参数范围内（百分位格式）
        particle['params']['stop_loss_ratio'] = max(-15, min(-1, particle['params']['stop_loss_ratio']))
        particle['params']['stop_loss_ratio'] = int(particle['params']['stop_loss_ratio'])

        # 更新最大持仓天数
        particle['params']['max_holding_days'] = particle['params'].get('max_holding_days', 10) + particle['velocity']['max_holding_days']
        # 限制在参数范围内
        particle['params']['max_holding_days'] = max(1, min(365, particle['params']['max_holding_days']))
        particle['params']['max_holding_days'] = int(particle['params']['max_holding_days'])

        # 确保止盈大于止损
        if particle['params']['stop_profit_ratio'] <= particle['params']['stop_loss_ratio']:
            # 调整止盈比例略大于止损比例
            particle['params']['stop_profit_ratio'] = particle['params']['stop_loss_ratio'] + 1
            particle['params']['stop_profit_ratio'] = int(particle['params']['stop_profit_ratio'])
