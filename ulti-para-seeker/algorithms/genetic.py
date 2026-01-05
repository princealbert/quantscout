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
                             end_date: str = '2025-12-25', backtest_days: int = 90) -> Dict[str, Any]:
        """
        定义参数空间
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            backtest_days: 回测天数
        
        Returns:
            Dict[str, Any]: 参数空间字典
        """
        print("定义遗传算法参数边界...")
        print(f"- 回测天数: {backtest_days}天，终点日期为{end_date}")
        
        if test_mode:
            print("[测试模式] 使用最小参数范围")
            # 测试模式下使用简化参数范围
            param_space = {
                'stop_profit_ratio': {'min': 0.02, 'max': 0.05, 'step': 0.01},
                'stop_loss_ratio': {'min': -0.03, 'max': -0.01, 'step': 0.01},
                'weights_step': 50,
                'test_mode': True,
                'end_date': end_date,
                'backtest_days': backtest_days
            }
        else:
            print("- 止盈比例: 3%-15%，步长2%")
            print("- 止损比例: -5%--1%，步长1%")
            print("- 权重配置: 总和100，步长10%")
            
            param_space = {
                'stop_profit_ratio': {'min': 0.03, 'max': 0.15, 'step': 0.02},
                'stop_loss_ratio': {'min': -0.05, 'max': -0.01, 'step': 0.01},
                'weights_step': 10,
                'test_mode': False,
                'end_date': end_date,
                'backtest_days': backtest_days
            }
        
        return param_space
    
    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                      end_date: str = '2025-12-25', focus_indicators: List[str] = None, 
                                      focus_weight_factor: float = 1.5, backtest_days: int = 90) -> List[Dict[str, Any]]:
        """
        兼容旧接口的参数组合生成方法
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            backtest_days: 回测天数
            
        Returns:
            List[Dict[str, Any]]: 参数组合列表
        """
        return self.generate_initial_population(test_mode, max_sub_combinations, end_date, backtest_days)
    
    def generate_initial_population(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                  end_date: str = '2025-12-25', backtest_days: int = 90) -> List[Dict[str, Any]]:
        """
        生成初始种群
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            backtest_days: 回测天数
        
        Returns:
            List[Dict[str, Any]]: 初始种群（参数组合列表）
        """
        param_space = self.define_parameter_space(test_mode, max_sub_combinations, end_date, backtest_days)
        
        print(f"开始生成遗传算法初始种群...")
        print(f"- 种群大小: {self.population_size}")
        
        # 生成初始种群
        population = []
        
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
            
            # 随机生成止盈止损比例
            stop_profit = random.uniform(
                param_space['stop_profit_ratio']['min'],
                param_space['stop_profit_ratio']['max']
            )
            stop_profit = round(stop_profit, 3)  # 保留3位小数
            
            stop_loss = random.uniform(
                param_space['stop_loss_ratio']['min'],
                param_space['stop_loss_ratio']['max']
            )
            stop_loss = round(stop_loss, 3)  # 保留3位小数
            
            # 确保止盈大于止损
            if stop_profit <= stop_loss:
                continue
            
            # 生成权重配置
            weights_config = self._generate_random_weights_config(param_space['weights_step'])
            
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
                    
                    if len(population) >= self.population_size:
                        break
        
        # 如果生成的有效组合不足，补充不同的默认配置
        while len(population) < self.population_size:
            # 生成不同的默认配置，通过添加随机扰动确保不重复
            default_comb = format_parameter_combination({
                'backtest_days': backtest_days,
                'end_date': end_date
            })
            
            # 添加随机扰动，确保不重复
            default_comb['stop_profit_ratio'] += random.uniform(-0.01, 0.01)
            default_comb['stop_loss_ratio'] += random.uniform(-0.01, 0.01)
            default_comb['stop_profit_ratio'] = round(default_comb['stop_profit_ratio'], 3)
            default_comb['stop_loss_ratio'] = round(default_comb['stop_loss_ratio'], 3)
            
            # 确保止盈大于止损
            if default_comb['stop_profit_ratio'] <= default_comb['stop_loss_ratio']:
                default_comb['stop_profit_ratio'] = default_comb['stop_loss_ratio'] + 0.01
            
            # 再次检查不重复
            from utils.parameter_utils import generate_param_hash
            comb_hash = generate_param_hash(default_comb)
            if comb_hash not in generated_combs:
                population.append(default_comb)
                generated_combs.add(comb_hash)
        
        print(f"已生成 {len(population)} 个初始参数组合")
        return population
    
    def optimize(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                end_date: str = '2025-12-25', initial_capital: int = 60000) -> List[Dict[str, Any]]:
        """
        执行遗传算法优化
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            initial_capital: 初始资金
        
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
        
        # 初始化种群
        population = self.generate_initial_population(
            test_mode, max_sub_combinations, end_date, backtest_days=90
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
    
    def _generate_random_weights_config(self, step: int) -> Dict[str, int]:
        """
        生成随机权重配置
        
        Args:
            step: 权重步长
        
        Returns:
            Dict[str, int]: 权重配置字典
        """
        core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
        num_indicators = len(core_indicators)
        
        # 生成随机权重（确保在5%-95%之间）
        weights = []
        for _ in range(num_indicators):
            weight = random.randrange(5, 96, step)
            weights.append(weight)
        
        # 调整权重总和为100
        total = sum(weights)
        if total != 100:
            # 按比例调整
            scale = 100.0 / total
            weights = [max(5, min(95, int(round(w * scale)))) for w in weights]
            
            # 再次调整总和
            total = sum(weights)
            diff = 100 - total
            if diff > 0:
                # 增加权重最大的指标
                max_index = weights.index(max(weights))
                weights[max_index] = min(95, weights[max_index] + diff)
            elif diff < 0:
                # 减少权重最大的指标
                max_index = weights.index(max(weights))
                weights[max_index] = max(5, weights[max_index] + diff)
        
        # 创建权重配置字典
        weights_config = dict(zip(core_indicators, weights))
        weights_config['deepv'] = 0  # deepv权重设为0
        
        return weights_config
    
    def _generate_default_sub_weights(self) -> Dict[str, Dict[str, int]]:
        """
        生成默认子权重配置
        
        Returns:
            Dict[str, Dict[str, int]]: 默认子权重配置
        """
        default_sub_weights = {
            'kdj_j': {'sub_weights': {'j_0_20': 20, 'j_-10_0': 20, 'j_-20_-10': 20, 'j_-30_-20': 20, 'j_below_-30': 20}},
            'position': {'sub_weights': {'above_white': 33, 'between_lines': 34, 'below_yellow': 33}},
            'volume': {'sub_weights': {'big_volume': 33, 'volume_anomaly': 34, 'volume_breathing': 33}},
            'fundamental': {'sub_weights': {'pe_positive': 25, 'pe_low': 25, 'market_cap': 25, 'volume_threshold': 25}},
            'trend': {'sub_weights': {'up_trend': 34, 'volume_price_rise': 33, 'volume_contraction': 33}}
        }
        return default_sub_weights
    
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
                mutation_type = random.choice(['stop_profit', 'stop_loss', 'weights', 'sub_weights'])
                
                if mutation_type == 'stop_profit':
                    # 止盈比例变异
                    mutated_params['stop_profit_ratio'] = max(0.03, min(0.15, 
                        mutated_params['stop_profit_ratio'] + random.uniform(-0.02, 0.02)))
                    mutated_params['stop_profit_ratio'] = round(mutated_params['stop_profit_ratio'], 3)
                
                elif mutation_type == 'stop_loss':
                    # 止损比例变异
                    mutated_params['stop_loss_ratio'] = max(-0.05, min(-0.01, 
                        mutated_params['stop_loss_ratio'] + random.uniform(-0.01, 0.01)))
                    mutated_params['stop_loss_ratio'] = round(mutated_params['stop_loss_ratio'], 3)
                
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
