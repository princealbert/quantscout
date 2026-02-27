#!/usr/bin/env python
# coding=utf-8
"""
遗传算法优化器 - 使用遗传算法进行参数优化
"""

import random
import copy
from typing import Dict, Any, List, Optional, Tuple
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


class GeneticOptimizer(BaseOptimizer):
    """
    遗传算法优化器 - 使用遗传算法进行参数优化
    """
    
    def __init__(self):
        """
        初始化遗传算法优化器
        """
        super().__init__()
        
        # 遗传算法参数
        self.population_size = 50  # 种群大小
        self.generations = 50  # 迭代代数
        self.crossover_rate = 0.8  # 交叉概率
        self.mutation_rate = 0.1  # 变异概率
        self.tournament_size = 5  # 锦标赛选择规模
        self.elitism = 5  # 精英保留数量
        self.early_stopping_generations = 10  # 早期停止代数
        self.min_improvement = 0.1  # 最小改进阈值（百分比）
    
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
        print("定义遗传算法参数边界...")
        print(f"- 回测天数: {backtest_days}天，终点日期为{end_date}")
        print(f"- 初始资金: {initial_capital}元")
        
        # 如果用户提供了参数边界，使用用户提供的值，否则使用默认值
        if test_mode:
            print("[测试模式] 使用最小参数范围")
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
            
            print(f"- 止盈比例: {actual_stop_profit_min}%-{actual_stop_profit_max}%，步长{actual_stop_profit_step}%")
            print(f"- 止损比例: {actual_stop_loss_min}%--{abs(actual_stop_loss_max)}%，步长{actual_stop_loss_step}%")
            print(f"- 最大持仓天数: {max_holding_days_min}-{max_holding_days_max}天，步长{max_holding_days_step}天")
            print(f"- 权重配置: 总和100，步长{actual_weight_step}%")
            
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
        生成初始种群

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
            List[Dict[str, Any]]: 初始种群（参数组合列表）
        """
        param_space = self.define_parameter_space(test_mode, max_sub_combinations, end_date, backtest_days,
                                               stop_profit_min, stop_profit_max, stop_profit_step,
                                               stop_loss_min, stop_loss_max, stop_loss_step,
                                               weight_step, initial_capital,
                                               max_holding_days_min, max_holding_days_max, max_holding_days_step)

        print(f"开始生成遗传算法初始种群...")
        print(f"- 种群大小: {self.population_size}")

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
            print(f"\n💡 提示: 未检测到现有蓝图文件，将使用纯随机生成的初始种群\n")

        # 计算种群中优势和随机部分的比例
        # 精英占30%，随机占70%
        elite_count = min(len(elite_combinations), int(self.population_size * 0.3))
        random_count = self.population_size - elite_count

        population = elite_combinations[:elite_count]


        if elite_count > 0:
            print(f"种群构成: 优势组合 {elite_count} 个 + 基于精英生成的 {random_count} 个")
        else:
            print(f"种群构成: 全部 {self.population_size} 个为随机生成组合")

        # 生成子权重配置
        from utils.weight_utils import generate_sub_weights_combinations
        sub_weights_configs = generate_sub_weights_combinations(
            test_mode, max_combinations=max_sub_combinations, use_advanced_mode=True
        )

        # 确保生成足够多的不重复组合
        generated_combs = set()
        attempts = 0
        max_attempts = self.population_size * 5  # 最多尝试5倍于种群数量的次数

        while len(population) < self.population_size and attempts < max_attempts:
            attempts += 1

            # 如果有优势组合，基于精英进行交叉变异；否则随机生成
            if elite_combinations and random.random() < 0.7:  # 70%的概率基于精英组合
                # 从精英组合中随机选择两个进行交叉
                parent1 = random.choice(elite_combinations)
                parent2 = random.choice(elite_combinations)

                # 交叉操作
                if random.random() < 0.5:
                    # 止盈交叉，止损交叉
                    stop_profit = parent1['stop_profit_ratio']
                    stop_loss = parent2['stop_loss_ratio']
                    max_holding_days = parent1.get('max_holding_days', 10)
                else:
                    # 止损交叉，止盈交叉
                    stop_profit = parent2['stop_profit_ratio']
                    stop_loss = parent1['stop_loss_ratio']
                    max_holding_days = parent2.get('max_holding_days', 10)

                # 变异操作
                if random.random() < self.mutation_rate:
                    # 止盈变异
                    param_space_min = param_space['stop_profit_ratio']['min']
                    param_space_max = param_space['stop_profit_ratio']['max']
                    param_space_step = param_space['stop_profit_ratio']['step']

                    # 在原有基础上进行小幅调整
                    mutation_direction = random.choice([-1, 1])
                    mutation_amount = mutation_direction * param_space_step * random.randint(1, 2)
                    stop_profit = max(param_space_min, min(param_space_max, stop_profit + mutation_amount))

                    # 确保值在步长网格上
                    offset = stop_profit % param_space_step
                    if offset != 0:
                        stop_profit = stop_profit - offset

                if random.random() < self.mutation_rate:
                    # 止损变异
                    param_space_min = param_space['stop_loss_ratio']['min']
                    param_space_max = param_space['stop_loss_ratio']['max']
                    param_space_step = param_space['stop_loss_ratio']['step']

                    # 在原有基础上进行小幅调整
                    mutation_direction = random.choice([-1, 1])
                    mutation_amount = mutation_direction * param_space_step * random.randint(1, 2)
                    stop_loss = max(param_space_min, min(param_space_max, stop_loss + mutation_amount))

                    # 确保值在步长网格上
                    offset = abs(stop_loss) % param_space_step
                    if offset != 0:
                        stop_loss = stop_loss - offset if stop_loss > 0 else stop_loss + offset

                if random.random() < self.mutation_rate:
                    # 最大持仓天数变异
                    param_space_min = param_space['max_holding_days']['min']
                    param_space_max = param_space['max_holding_days']['max']
                    param_space_step = param_space['max_holding_days']['step']

                    # 在原有基础上进行小幅调整
                    mutation_direction = random.choice([-1, 1])
                    mutation_amount = mutation_direction * param_space_step * random.randint(1, 2)
                    max_holding_days = max(param_space_min, min(param_space_max, max_holding_days + mutation_amount))

                # 权重配置：交叉操作 - 真正的交叉，不是简单继承
                parent1_weights = parent1.get('weights_config', {})
                parent2_weights = parent2.get('weights_config', {})

                # 合并两个父代的权重配置
                weights_config = {}
                for key in parent1_weights:
                    if key in parent2_weights:
                        # 均值交叉: 两个父代的权重平均值
                        weights_config[key] = (parent1_weights[key] + parent2_weights[key]) // 2
                    else:
                        weights_config[key] = parent1_weights[key]
                # 补充parent2独有的权重
                for key in parent2_weights:
                    if key not in weights_config:
                        weights_config[key] = parent2_weights[key]

                # 权重变异 - 提高变异概率
                if random.random() < self.mutation_rate * 2:  # 从0.5倍提高到2倍
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
                    population.append(param_comb)
                    generated_combs.add(comb_hash)

                    # 只在成功添加到population时打印日志
                    if elite_combinations and random.random() < 0.7:
                        # 显示完整的交叉变异信息，包括权重摘要
                        weights_summary = {}
                        if weights_config:
                            # 显示前3个最重要的权重
                            sorted_weights = sorted(weights_config.items(), key=lambda x: x[1], reverse=True)[:3]
                            weights_summary = {k: v for k, v in sorted_weights}
                        print(f"  基于精英交叉变异: 止盈={stop_profit}%, 止损={stop_loss}%, 最大持仓={max_holding_days}天, 权重={weights_summary}")

                    if len(population) >= self.population_size:
                        break

        
        # 如果生成的有效组合不足，补充不同的配置
        while len(population) < self.population_size:
            # 使用基类的通用方法生成随机参数组合
            param_comb = self._generate_random_params(param_space, backtest_days, end_date)

            # 验证参数组合
            if validate_parameter_combination(param_comb):
                # 检查是否重复
                from utils.parameter_utils import generate_param_hash
                comb_hash = generate_param_hash(param_comb)
                if comb_hash not in generated_combs:
                    population.append(param_comb)
                    generated_combs.add(comb_hash)

        print(f"已生成 {len(population)} 个初始参数组合（包含 {elite_count} 个优势组合）")
        return population

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
        执行遗传算法优化
        
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
        print("开始遗传算法优化...")
        print(f"- 种群大小: {self.population_size}")
        print(f"- 迭代代数: {self.generations}")
        print(f"- 交叉概率: {self.crossover_rate}")
        print(f"- 变异概率: {self.mutation_rate}")
        print(f"- 精英保留: {self.elitism}")
        print(f"- 早期停止: {self.early_stopping_generations} 代无改进")
        
        # 初始化种群，传递所有参数边界
        population = self.generate_initial_population(
            test_mode, max_sub_combinations, end_date, backtest_days,
            stop_profit_min, stop_profit_max, stop_profit_step,
            stop_loss_min, stop_loss_max, stop_loss_step,
            weight_step, initial_capital, max_holding_days_min,
            max_holding_days_max, max_holding_days_step, existing_blueprint
        )
        
        # 为每个参数组合添加初始资金
        for param in population:
            param['initial_capital'] = initial_capital
        
        # 评估初始种群
        population_with_fitness = self._evaluate_population(population)
        
        # 保存所有代的最佳结果
        all_results = []
        
        # 初始化早期停止相关变量
        best_fitness_history = []
        no_improvement_generations = 0
        
        # 进化过程
        for generation in range(self.generations):
            print(f"\n第 {generation + 1}/{self.generations} 代进化...")
            
            # 选择
            selected = self._selection(population_with_fitness)
            
            # 交叉
            offspring = self._crossover(selected)
            
            # 变异
            mutated = self._mutation(offspring)
            
            # 评估新种群
            mutated_with_fitness = self._evaluate_population(mutated)
            
            # 精英保留
            new_population = self._elitism_selection(population_with_fitness, mutated_with_fitness)
            
            # 更新种群
            population_with_fitness = new_population
            
            # 找出当前代最佳个体
            best_individual = max(population_with_fitness, key=lambda x: x['fitness'])
            current_best_fitness = best_individual['fitness']
            
            # 保存结果
            all_results.append(best_individual['params'])
            all_results[-1]['fitness'] = current_best_fitness
            all_results[-1]['generation'] = generation + 1
            
            # 打印当前代信息
            print(f"  当前代最佳适应度: {current_best_fitness:.4f}")
            print(f"  止盈比例: {best_individual['params']['stop_profit_ratio']:.3f}")
            print(f"  止损比例: {best_individual['params']['stop_loss_ratio']:.3f}")
            print(f"  权重配置: {best_individual['params']['weights_config']}")
            
            # 早期停止检查
            best_fitness_history.append(current_best_fitness)
            
            if len(best_fitness_history) > 1:
                prev_best = best_fitness_history[-2]
                improvement = (current_best_fitness - prev_best) / abs(prev_best) * 100 if prev_best != 0 else 0
                
                if improvement < self.min_improvement:
                    no_improvement_generations += 1
                    print(f"  连续无改进代数: {no_improvement_generations}/{self.early_stopping_generations}")
                    print(f"  改进幅度: {improvement:.2f}% < {self.min_improvement}%")
                else:
                    no_improvement_generations = 0
                    print(f"  改进幅度: {improvement:.2f}%")
                
                # 检查是否触发早期停止
                if no_improvement_generations >= self.early_stopping_generations:
                    print(f"\n✅ 触发早期停止：连续 {self.early_stopping_generations} 代没有明显改进")
                    print(f"  最佳适应度: {max(best_fitness_history):.4f}")
                    break
            
            # 测试模式下提前终止
            if test_mode and generation >= 2:
                break
        
        # 按适应度排序并返回最佳结果
        sorted_results = sorted(all_results, key=lambda x: x.get('fitness', 0), reverse=True)
        return sorted_results[:10]  # 返回前10个最佳结果
    

    
    def _evaluate_population(self, population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        评估种群适应度
        
        Args:
            population: 种群列表
        
        Returns:
            List[Dict[str, Any]]: 包含适应度的种群列表
        """
        population_with_fitness = []
        
        for params in population:
            try:
                # 运行回测
                result = self.run_backtest(params)
                
                # 计算适应度（使用总收益率作为适应度）
                fitness = self._calculate_fitness(result)
            except Exception as e:
                # 如果回测失败，使用较低的适应度
                fitness = -1000
            
            population_with_fitness.append({
                'params': params,
                'fitness': fitness
            })
        
        return population_with_fitness
    
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
    
    def _selection(self, population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        选择操作（锦标赛选择）
        
        Args:
            population: 种群列表
        
        Returns:
            List[Dict[str, Any]]: 选择后的种群
        """
        selected = []
        
        for _ in range(len(population)):
            # 随机选择锦标赛成员
            tournament = random.sample(population, self.tournament_size)
            
            # 选择适应度最高的个体
            winner = max(tournament, key=lambda x: x['fitness'])
            selected.append(winner)
        
        return selected
    
    def _crossover(self, population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        交叉操作
        
        Args:
            population: 种群列表
        
        Returns:
            List[Dict[str, Any]]: 交叉后的种群
        """
        offspring = []
        
        for i in range(0, len(population), 2):
            parent1 = population[i]['params']
            parent2 = population[min(i + 1, len(population) - 1)]['params']
            
            # 随机决定是否进行交叉
            if random.random() < self.crossover_rate:
                # 止盈止损交叉
                child1 = copy.deepcopy(parent1)
                child2 = copy.deepcopy(parent2)
                
                # 均匀交叉止盈止损
                if random.random() < 0.5:
                    child1['stop_profit_ratio'], child2['stop_profit_ratio'] = child2['stop_profit_ratio'], child1['stop_profit_ratio']
                
                if random.random() < 0.5:
                    child1['stop_loss_ratio'], child2['stop_loss_ratio'] = child2['stop_loss_ratio'], child1['stop_loss_ratio']
                
                # 交叉最大持仓天数
                if random.random() < 0.5:
                    child1['max_holding_days'] = parent1.get('max_holding_days', 10)
                    child2['max_holding_days'] = parent2.get('max_holding_days', 10)
                else:
                    child1['max_holding_days'] = parent2.get('max_holding_days', 10)
                    child2['max_holding_days'] = parent1.get('max_holding_days', 10)
                
                # 权重配置交叉（单点交叉）
                if random.random() < 0.5:
                    child1['weights_config'], child2['weights_config'] = self._crossover_weights(child1['weights_config'], child2['weights_config'])
                
                # 子权重配置交叉（随机选择父代的子权重）
                if random.random() < 0.5:
                    for main_ind in child1['sub_weights_config']:
                        if random.random() < 0.5:
                            child1['sub_weights_config'][main_ind] = child2['sub_weights_config'][main_ind]
                
                # 验证并添加到下一代
                if validate_parameter_combination(child1):
                    offspring.append(child1)
                else:
                    offspring.append(parent1)
                
                if validate_parameter_combination(child2):
                    offspring.append(child2)
                else:
                    offspring.append(parent2)
            else:
                # 不进行交叉，直接复制父代
                offspring.append(parent1)
                offspring.append(parent2)
        
        return offspring
    
    def _crossover_weights(self, weights1: Dict[str, int], weights2: Dict[str, int]) -> Tuple[Dict[str, int], Dict[str, int]]:
        """
        权重配置交叉
        
        Args:
            weights1: 父代1权重配置
            weights2: 父代2权重配置
        
        Returns:
            Tuple[Dict[str, int], Dict[str, int]]: 两个子代的权重配置
        """
        child1 = weights1.copy()
        child2 = weights2.copy()
        
        # 随机选择要交叉的指标
        indicators = list(weights1.keys())
        if len(indicators) >= 2:
            cross_indicators = random.sample(indicators, random.randint(1, len(indicators) - 1))
            
            for ind in cross_indicators:
                child1[ind] = weights2[ind]
                child2[ind] = weights1[ind]
            
            # 调整权重总和为100
            child1 = self._adjust_weights_total(child1)
            child2 = self._adjust_weights_total(child2)
        
        return child1, child2
    
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
    
    def _mutation(self, population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        变异操作
        
        Args:
            population: 种群列表
        
        Returns:
            List[Dict[str, Any]]: 变异后的种群
        """
        mutated = []
        
        for params in population:
            if random.random() < self.mutation_rate:
                mutated_params = copy.deepcopy(params)
                
                # 随机选择变异类型
                mutation_type = random.choice(['stop_profit', 'stop_loss', 'max_holding_days', 'weights', 'sub_weights'])
                
                if mutation_type == 'stop_profit':
                    # 止盈比例变异（百分位格式）
                    mutated_params['stop_profit_ratio'] = max(3, min(15, 
                        mutated_params['stop_profit_ratio'] + random.choice([-2, -1, 1, 2])))
                
                elif mutation_type == 'stop_loss':
                    # 止损比例变异（百分位格式）
                    mutated_params['stop_loss_ratio'] = max(-15, min(-1, 
                        mutated_params['stop_loss_ratio'] + random.choice([-1, 1])))
                
                elif mutation_type == 'max_holding_days':
                    # 最大持仓天数变异
                    current_days = mutated_params.get('max_holding_days', 10)
                    change = random.choice([-5, -1, 1, 5])
                    mutated_params['max_holding_days'] = max(1, min(365, current_days + change))
                
                elif mutation_type == 'weights':
                    # 权重配置变异
                    indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
                    if indicators:
                        ind_to_mutate = random.choice(indicators)
                        change = random.choice([-10, -5, 5, 10])
                        
                        current_weight = mutated_params['weights_config'].get(ind_to_mutate, 10)
                        new_weight = max(5, min(95, current_weight + change))
                        
                        # 调整其他权重以保持总和为100
                        diff = new_weight - current_weight
                        if diff != 0:
                            mutated_params['weights_config'][ind_to_mutate] = new_weight
                            
                            # 随机选择其他指标进行调整
                            other_indicators = [ind for ind in indicators if ind != ind_to_mutate]
                            if other_indicators:
                                while diff != 0 and other_indicators:
                                    adjust_ind = random.choice(other_indicators)
                                    adjust_weight = mutated_params['weights_config'].get(adjust_ind, 10)
                                    
                                    if diff > 0:
                                        # 需要减少其他指标权重
                                        adjust_change = min(diff, adjust_weight - 5)
                                        if adjust_change > 0:
                                            mutated_params['weights_config'][adjust_ind] -= adjust_change
                                            diff -= adjust_change
                                    else:
                                        # 需要增加其他指标权重
                                        adjust_change = max(diff, -(95 - adjust_weight))
                                        if adjust_change < 0:
                                            mutated_params['weights_config'][adjust_ind] -= adjust_change
                                            diff -= adjust_change
                
                elif mutation_type == 'sub_weights':
                    # 子权重配置变异
                    main_indicators = list(mutated_params['sub_weights_config'].keys())
                    if main_indicators:
                        main_ind = random.choice(main_indicators)
                        sub_weights = mutated_params['sub_weights_config'][main_ind]['sub_weights']
                        
                        # 随机选择两个子指标进行权重调整
                        sub_indicators = list(sub_weights.keys())
                        if len(sub_indicators) >= 2:
                            ind1, ind2 = random.sample(sub_indicators, 2)
                            change = random.choice([-5, 5])
                            
                            if sub_weights[ind1] + change >= 5 and sub_weights[ind1] + change <= 90:
                                sub_weights[ind1] += change
                                
                                if sub_weights[ind2] - change >= 5 and sub_weights[ind2] - change <= 90:
                                    sub_weights[ind2] -= change
                
                # 验证变异后的参数组合
                if validate_parameter_combination(mutated_params):
                    mutated.append(mutated_params)
                else:
                    mutated.append(params)
            else:
                mutated.append(params)
        
        return mutated
    
    def _elitism_selection(self, parent_population: List[Dict[str, Any]], 
                          offspring_population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        精英保留选择
        
        Args:
            parent_population: 父代种群
            offspring_population: 子代种群
        
        Returns:
            List[Dict[str, Any]]: 新一代种群
        """
        # 合并种群
        combined = parent_population + offspring_population
        
        # 按适应度排序
        sorted_combined = sorted(combined, key=lambda x: x['fitness'], reverse=True)
        
        # 保留精英和最优个体
        new_population = sorted_combined[:self.population_size]
        
        return new_population
