#!/usr/bin/env python
# coding=utf-8
"""
粒子群算法优化器 - 使用粒子群算法进行参数优化
"""

import random
import copy
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .base_optimizer import BaseOptimizer
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
        
        # 速度限制
        self.max_velocity = {
            'stop_profit_ratio': 0.02,
            'stop_loss_ratio': 0.01,
            'weight_change': 10
        }
    
    def define_parameter_ranges(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                               use_advanced_weights: bool = True, end_date: str = '2025-12-25') -> Dict[str, Any]:
        """
        定义参数范围
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            use_advanced_weights: 是否使用高级权重配置模式
            end_date: 回测终点日期
        
        Returns:
            Dict[str, Any]: 参数范围字典
        """
        from utils.logger import logger
        logger.info("定义粒子群算法参数边界...")
        logger.info(f"- 回测天数固定为90天，终点日期为{end_date}")
        
        if test_mode:
            logger.info("[测试模式] 使用最小参数范围")
            # 测试模式下使用简化参数范围
            param_ranges = {
                'stop_profit_ratio': {'min': 0.02, 'max': 0.05, 'step': 0.01},
                'stop_loss_ratio': {'min': -0.03, 'max': -0.01, 'step': 0.01},
                'weights_step': 50,
                'test_mode': True,
                'end_date': end_date
            }
        else:
            logger.info("- 止盈比例: 3%-15%，步长2%")
            logger.info("- 止损比例: -5%--1%，步长1%")
            if use_advanced_weights:
                logger.info("- 权重配置: 总和100，步长10%")
                weight_step = 10
            else:
                logger.info("- 权重配置: 总和100，步长20%")
                weight_step = 20
            
            param_ranges = {
                'stop_profit_ratio': {'min': 0.03, 'max': 0.15, 'step': 0.02},
                'stop_loss_ratio': {'min': -0.05, 'max': -0.01, 'step': 0.01},
                'weights_step': weight_step,
                'test_mode': False,
                'end_date': end_date
            }
        
        return param_ranges
    
    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                       end_date: str = '2025-12-25') -> List[Dict[str, Any]]:
        """
        生成参数组合（粒子群初始化）
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
        
        Returns:
            List[Dict[str, Any]]: 参数组合列表（初始化粒子群）
        """
        from utils.logger import logger
        param_ranges = self.define_parameter_ranges(test_mode, max_sub_combinations, end_date=end_date)
        
        logger.info(f"开始生成粒子群初始种群...")
        logger.info(f"- 粒子数量: {self.population_size}")
        
        # 生成初始粒子群
        particles = []
        
        for _ in range(self.population_size):
            # 随机生成止盈止损比例
            stop_profit = random.uniform(
                param_ranges['stop_profit_ratio']['min'],
                param_ranges['stop_profit_ratio']['max']
            )
            stop_profit = round(stop_profit, 3)  # 保留3位小数
            
            stop_loss = random.uniform(
                param_ranges['stop_loss_ratio']['min'],
                param_ranges['stop_loss_ratio']['max']
            )
            stop_loss = round(stop_loss, 3)  # 保留3位小数
            
            # 确保止盈大于止损
            if stop_profit <= stop_loss:
                continue
            
            # 生成权重配置
            weights_config = self._generate_random_weights_config(param_ranges['weights_step'])
            
            # 生成子权重配置
            sub_weights_config = self._generate_sub_weights_combinations(test_mode, max_combinations=max_sub_combinations, use_advanced_mode=True)
            
            # 如果没有生成子权重配置，使用默认配置
            if not sub_weights_config:
                sub_weights_config = [self._generate_default_sub_weights()]
            
            # 随机选择一个子权重配置
            sub_weights = random.choice(sub_weights_config)
            
            # 创建参数组合
            param_comb = {
                'backtest_days': 90,
                'end_date': end_date,
                'stop_profit_ratio': stop_profit,
                'stop_loss_ratio': stop_loss,
                'weights_config': weights_config,
                'sub_weights_config': sub_weights,
                'initial_capital': self.initial_capital
            }
            
            # 验证参数组合
            if validate_parameter_combination(param_comb):
                particles.append(param_comb)
                
                if len(particles) >= self.population_size:
                    break
        
        # 如果生成的有效组合不足，补充默认配置
        while len(particles) < self.population_size:
            default_comb = format_parameter_combination({
                'backtest_days': 90,
                'end_date': end_date,
                'initial_capital': self.initial_capital
            })
            particles.append(default_comb)
        
        logger.info(f"已生成 {len(particles)} 个初始粒子")
        return particles
    
    def optimize(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                end_date: str = '2025-12-25', blueprint_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        执行粒子群算法优化
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            blueprint_file: 蓝图文件路径（粒子群算法通常不需要蓝图）
        
        Returns:
            List[Dict[str, Any]]: 优化结果列表
        """
        from utils.logger import logger
        logger.info("开始粒子群算法优化...")
        logger.info(f"- 粒子数量: {self.population_size}")
        logger.info(f"- 迭代代数: {self.generations}")
        logger.info(f"- 认知因子(c1): {self.c1}")
        logger.info(f"- 社会因子(c2): {self.c2}")
        logger.info(f"- 惯性权重(w): {self.w}")
        logger.info(f"- 早期停止: {self.early_stopping_generations} 代无改进")
        
        # 初始化粒子群
        particles = self.generate_parameter_combinations(test_mode, max_sub_combinations, end_date)
        
        # 初始化粒子的速度和历史最优位置
        swarm = []
        global_best = None
        global_best_fitness = -float('inf')
        
        for particle in particles:
            # 初始化速度
            velocity = {
                'stop_profit_ratio': 0,
                'stop_loss_ratio': 0,
                'weights_velocity': {}
            }
            
            # 初始化粒子的历史最优位置
            swarm.append({
                'position': particle,
                'velocity': velocity,
                'best_position': particle.copy(),
                'best_fitness': -float('inf')
            })
        
        # 评估初始粒子群
        swarm = self._evaluate_swarm(swarm)
        
        # 初始化全局最优
        for particle in swarm:
            if particle['best_fitness'] > global_best_fitness:
                global_best_fitness = particle['best_fitness']
                global_best = particle['best_position'].copy()
        
        # 保存所有代的最佳结果
        all_results = []
        
        # 初始化早期停止相关变量
        best_fitness_history = []
        no_improvement_generations = 0
        
        # 进化过程
        for generation in range(self.generations):
            logger.info(f"\n第 {generation + 1}/{self.generations} 代进化...")
            
            # 动态调整惯性权重
            w = self.w_max - (self.w_max - self.w_min) * (generation / self.generations)
            
            for i, particle in enumerate(swarm):
                # 更新粒子速度
                self._update_velocity(particle, w, global_best)
                
                # 更新粒子位置
                self._update_position(particle)
            
            # 评估新的粒子群
            swarm = self._evaluate_swarm(swarm)
            
            # 更新全局最优
            for particle in swarm:
                if particle['best_fitness'] > global_best_fitness:
                    global_best_fitness = particle['best_fitness']
                    global_best = particle['best_position'].copy()
            
            # 保存结果
            result = global_best.copy()
            result['fitness'] = global_best_fitness
            result['generation'] = generation + 1
            all_results.append(result)
            
            # 打印当前代信息
            logger.info(f"  当前代最佳适应度: {global_best_fitness:.4f}")
            logger.info(f"  止盈比例: {global_best['stop_profit_ratio']:.3f}")
            logger.info(f"  止损比例: {global_best['stop_loss_ratio']:.3f}")
            logger.info(f"  权重配置: {global_best['weights_config']}")
            
            # 早期停止检查
            best_fitness_history.append(global_best_fitness)
            
            if len(best_fitness_history) > 1:
                prev_best = best_fitness_history[-2]
                improvement = (global_best_fitness - prev_best) / abs(prev_best) * 100 if prev_best != 0 else 0
                
                if improvement < self.min_improvement:
                    no_improvement_generations += 1
                    logger.info(f"  连续无改进代数: {no_improvement_generations}/{self.early_stopping_generations}")
                    logger.info(f"  改进幅度: {improvement:.2f}% < {self.min_improvement}%")
                else:
                    no_improvement_generations = 0
                    logger.info(f"  改进幅度: {improvement:.2f}%")
                
                # 检查是否触发早期停止
                if no_improvement_generations >= self.early_stopping_generations:
                    logger.info(f"\n✅ 触发早期停止：连续 {self.early_stopping_generations} 代没有明显改进")
                    logger.info(f"  最佳适应度: {max(best_fitness_history):.4f}")
                    break
            
            # 测试模式下提前终止
            if test_mode and generation >= 2:
                break
        
        # 按适应度排序并返回最佳结果
        sorted_results = sorted(all_results, key=lambda x: x.get('fitness', 0), reverse=True)
        return sorted_results[:10]  # 返回前10个最佳结果
    
    def run_backtest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个参数组合的回测（与暴力优化器相同）
        
        Args:
            params: 参数组合
        
        Returns:
            Dict[str, Any]: 回测结果
        """
        # 复用暴力优化器的回测方法，确保使用缓存机制
        from .brute_force_optimizer import BruteForceOptimizer
        brute_optimizer = BruteForceOptimizer()
        return brute_optimizer.run_backtest(params)
    
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
                result = self.run_backtest(particle['position'])
                
                # 计算适应度（使用总收益率作为适应度）
                fitness = self._calculate_fitness(result)
            except Exception as e:
                # 如果回测失败，使用较低的适应度
                fitness = -1000
            
            # 更新粒子的历史最优位置
            if fitness > particle['best_fitness']:
                particle['best_fitness'] = fitness
                particle['best_position'] = particle['position'].copy()
        
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
        if global_best is None:
            return
        
        # 更新止盈比例速度
        cognitive_velocity_profit = self.c1 * random.random() * (
            particle['best_position']['stop_profit_ratio'] - particle['position']['stop_profit_ratio']
        )
        social_velocity_profit = self.c2 * random.random() * (
            global_best['stop_profit_ratio'] - particle['position']['stop_profit_ratio']
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
            particle['best_position']['stop_loss_ratio'] - particle['position']['stop_loss_ratio']
        )
        social_velocity_loss = self.c2 * random.random() * (
            global_best['stop_loss_ratio'] - particle['position']['stop_loss_ratio']
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
    
    def _update_position(self, particle: Dict[str, Any]):
        """
        更新粒子位置
        
        Args:
            particle: 粒子
        """
        # 更新止盈比例
        particle['position']['stop_profit_ratio'] += particle['velocity']['stop_profit_ratio']
        # 限制在参数范围内
        particle['position']['stop_profit_ratio'] = max(0.03, min(0.15, particle['position']['stop_profit_ratio']))
        particle['position']['stop_profit_ratio'] = round(particle['position']['stop_profit_ratio'], 3)
        
        # 更新止损比例
        particle['position']['stop_loss_ratio'] += particle['velocity']['stop_loss_ratio']
        # 限制在参数范围内
        particle['position']['stop_loss_ratio'] = max(-0.05, min(-0.01, particle['position']['stop_loss_ratio']))
        particle['position']['stop_loss_ratio'] = round(particle['position']['stop_loss_ratio'], 3)
        
        # 确保止盈大于止损
        if particle['position']['stop_profit_ratio'] <= particle['position']['stop_loss_ratio']:
            # 调整止盈比例略大于止损比例
            particle['position']['stop_profit_ratio'] = particle['position']['stop_loss_ratio'] + 0.01
            particle['position']['stop_profit_ratio'] = round(particle['position']['stop_profit_ratio'], 3)
    

