#!/usr/bin/env python
# coding=utf-8
"""
参数暴力求解器 - 寻找回测收益率最高的参数组合
"""

import os
import sys
import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# 项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 支持直接运行和作为模块导入两种方式
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入日志系统
from utils.logger import logger

# 导入现有优化器和结果处理器
from optimizers.brute_force_optimizer import BruteForceOptimizer
from optimizers.result_processor import ResultProcessor

# 导入蓝图管理器
from utils.blueprint_manager import BlueprintManager


class ParameterOptimizer(BruteForceOptimizer):
    """
    参数优化器 - 用于暴力求解最佳参数组合
    继承自BruteForceOptimizer，保持原有接口兼容
    """
    
    def __init__(self):
        """初始化参数优化器"""
        super().__init__()
        self.results = []
        self.start_time = None
        self.end_time = None
        self.result_processor = ResultProcessor(current_dir)
        # 初始化蓝图管理器
        self.blueprint_manager = BlueprintManager()
        # 保存当前目录，用于文件操作
        self.current_dir = current_dir
    
    def define_parameter_ranges(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                               use_advanced_weights: bool = True, end_date: str = '2025-12-25', 
                               stop_profit_min: int = None, stop_profit_max: int = None, 
                               stop_profit_step: int = None, stop_loss_min: int = None, 
                               stop_loss_max: int = None, stop_loss_step: int = None, 
                               weight_step: int = None, focus_indicators: List[str] = None, 
                               focus_weight_factor: float = None) -> Dict[str, List[Any]]:
        """
        定义参数范围

        Args:
            test_mode: 是否为测试模式（只生成一个简单子权重组合）
            max_sub_combinations: 最大子权重组合数（仅在非测试模式下生效）
            use_advanced_weights: 是否使用高级权重配置模式
            end_date: 回测终点日期（格式：YYYY-MM-DD）
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            focus_indicators: 重点关注的指标列表
            focus_weight_factor: 重点指标权重因子

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
            # 使用用户传递的参数范围，如果没有传递则使用默认值
            if stop_profit_min is None:
                stop_profit_min = 3
            if stop_profit_max is None:
                stop_profit_max = 15
            if stop_profit_step is None:
                stop_profit_step = 2
            if stop_loss_min is None:
                stop_loss_min = 1
            if stop_loss_max is None:
                stop_loss_max = 5
            if stop_loss_step is None:
                stop_loss_step = 1
            if weight_step is None:
                if use_advanced_weights:
                    weight_step = 10
                else:
                    weight_step = 20
            
            logger.info(f"- 止盈比例: {stop_profit_min}%-{stop_profit_max}%，步长{stop_profit_step}%")
            logger.info(f"- 止损比例: {-stop_loss_max}%--{-stop_loss_min}%，步长{stop_loss_step}%")
            logger.info(f"- 权重配置: 总和100，步长{weight_step}%")
            
            # 使用用户指定的范围生成参数
            stop_profit_ratio = [x/100 for x in range(stop_profit_min, stop_profit_max + 1, stop_profit_step)]
            stop_loss_ratio = [-x/100 for x in range(stop_loss_min, stop_loss_max + 1, stop_loss_step)]
        
        logger.info("- 子权重配置: 每个主指标子权重总和100")
        
        # 选股策略核心指标（权重配置）
        # 移除deepv指标，将其权重设为零以减少组合数量
        core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
        
        # 生成权重配置
        if test_mode:
            # 测试模式：直接生成一个简单的权重组合
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
            
            # 使用传入的重点指标和权重因子，或使用默认值
            actual_focus_indicators = focus_indicators if focus_indicators else ['kdj_j', 'trend']
            actual_focus_weight_factor = focus_weight_factor if focus_weight_factor else 1.5
            
            logger.info(f"  - 重点指标: {', '.join(actual_focus_indicators)}")
            logger.info(f"  - 权重因子: {actual_focus_weight_factor:.1f}")
            
            # 基础权重组合 - 限制主权重范围为5%-95%，避免极端值
            base_weights = self._generate_weights_combinations(core_indicators, 100, weight_step, min_weight=5, max_weight=95)
            logger.info(f"  - 基础权重组合数: {len(base_weights)}")
            
            # 生成重点指标加权组合
            kdj_trend_weights = self._generate_custom_weights_combinations(
                core_indicators, 100, weight_step, 
                focus_indicators=actual_focus_indicators, 
                focus_weight_factor=actual_focus_weight_factor
            )
            logger.info(f"  - 重点指标加权组合数: {len(kdj_trend_weights)}")
            
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
            logger.info(f"  - 去重后权重组合总数: {len(weights_config)}")
        else:
            # 普通模式：仅生成基础权重组合 - 限制主权重范围为5%-95%，避免极端值
            weights_config = self._generate_weights_combinations(core_indicators, 100, weight_step, min_weight=5, max_weight=95)
            logger.info(f"[普通模式] 权重组合数: {len(weights_config)}")
        
        return {
            # 回测天数 - 测试模式下使用10天，非测试模式下使用90天（适合超跌反弹策略）
            'backtest_days': [10] if test_mode else [90],
            
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
    
    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                      end_date: str = '2025-12-25', algorithm: str = "暴力搜索", 
                                      stop_profit_min: int = None, stop_profit_max: int = None, 
                                      stop_profit_step: int = None, stop_loss_min: int = None, 
                                      stop_loss_max: int = None, stop_loss_step: int = None, 
                                      weight_step: int = None, use_advanced_weights: bool = True,
                                      focus_indicators: List[str] = None, focus_weight_factor: float = None) -> List[Dict[str, Any]]:
        """
        生成所有可能的参数组合

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            algorithm: 优化算法选择
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            use_advanced_weights: 是否使用高级权重配置模式
            focus_indicators: 重点关注的指标列表
            focus_weight_factor: 重点指标权重因子

        Returns:
            List[Dict[str, Any]]: 所有可能的参数组合列表
        """
        # 使用当前类的define_parameter_ranges方法，确保前端传入的参数范围生效
        param_ranges = self.define_parameter_ranges(
            test_mode=test_mode,
            max_sub_combinations=max_sub_combinations,
            use_advanced_weights=use_advanced_weights,
            end_date=end_date,
            stop_profit_min=stop_profit_min,
            stop_profit_max=stop_profit_max,
            stop_profit_step=stop_profit_step,
            stop_loss_min=stop_loss_min,
            stop_loss_max=stop_loss_max,
            stop_loss_step=stop_loss_step,
            weight_step=weight_step,
            focus_indicators=focus_indicators,
            focus_weight_factor=focus_weight_factor
        )
        
        # 计算总组合数（用于进度显示）
        total_combinations = (len(param_ranges['backtest_days']) * 
                            len(param_ranges['end_date']) * 
                            len(param_ranges['stop_profit_ratio']) * 
                            len(param_ranges['stop_loss_ratio']) * 
                            len(param_ranges['weights_config']) * 
                            len(param_ranges['sub_weights_config']))
        
        logger.info(f"开始生成参数组合...")
        logger.info(f"预计总组合数: {total_combinations}")
        
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
                                    
                                    # 创建参数组合
                                    combination = {
                                        'backtest_days': backtest_days,
                                        'end_date': end_date,
                                        'stop_profit_ratio': stop_profit_ratio,
                                        'stop_loss_ratio': stop_loss_ratio,
                                        'weights_config': weights_config_with_zero_deepv,
                                        'sub_weights_config': sub_weights_config
                                    }
                                    
                                    combinations.append(combination)
                                    current_count += 1
                                    
                                    # 每生成1000个组合显示一次进度，使用行内刷新
                                    if current_count % 1000 == 0:
                                        print(f"已生成 {current_count}/{total_combinations} 个参数组合", end="\r", flush=True)
                                    
                                    # 测试模式下仅生成第一个组合
                                    if test_mode and len(combinations) >= 1:
                                        logger.info("[测试模式] 仅生成并返回第一个参数组合")
                                        return combinations
        
        # 注意：generate_parameter_combinations方法始终返回所有生成的组合
        # 遗传算法的组合选择将在后续的run_optimization或蓝图生成过程中进行
        logger.info(f"完成参数组合生成，共生成 {len(combinations)} 个组合")
        
        return combinations
    
    def run_optimization(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                        end_date: str = '2025-12-25', algorithm: str = "暴力搜索", 
                        blueprint_file: str = None, max_workers: int = None, 
                        stop_profit_min: int = None, stop_profit_max: int = None, 
                        stop_profit_step: int = None, stop_loss_min: int = None, 
                        stop_loss_max: int = None, stop_loss_step: int = None, 
                        weight_step: int = None, use_advanced_weights: bool = True,
                        focus_indicators: List[str] = None, focus_weight_factor: float = None) -> List[Dict[str, Any]]:
        """
        执行参数优化

        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            algorithm: 优化算法
            blueprint_file: 蓝图文件路径
            max_workers: 最大工作线程数
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            use_advanced_weights: 是否使用高级权重配置模式
            focus_indicators: 重点关注的指标列表
            focus_weight_factor: 重点指标权重因子

        Returns:
            List[Dict[str, Any]]: 回测结果列表
        """
        logger.info("\n=== 执行参数优化 ===")
        logger.info(f"优化算法: {algorithm}")
        logger.info(f"测试模式: {test_mode}")
        logger.info(f"最大子权重组合数: {max_sub_combinations}")
        
        # 根据算法选择优化器
        if algorithm == "暴力搜索":
            logger.info("使用暴力搜索优化器")
            # 使用当前类的暴力搜索实现
            # 如果提供了蓝图文件，从蓝图文件加载参数组合
            if blueprint_file:
                logger.info(f"从蓝图文件加载参数组合: {blueprint_file}")
                blueprint = self.load_blueprint(blueprint_file, load_all=True)
                # 过滤出待处理的组合
                pending_combinations = [combo['params'] for combo in blueprint['combinations'] if combo['status'] == 'pending']
                param_combinations = pending_combinations
            else:
                # 生成参数组合
                param_combinations = self.generate_parameter_combinations(
                    test_mode=test_mode,
                    max_sub_combinations=max_sub_combinations,
                    end_date=end_date,
                    algorithm=algorithm,
                    stop_profit_min=stop_profit_min,
                    stop_profit_max=stop_profit_max,
                    stop_profit_step=stop_profit_step,
                    stop_loss_min=stop_loss_min,
                    stop_loss_max=stop_loss_max,
                    stop_loss_step=stop_loss_step,
                    weight_step=weight_step,
                    use_advanced_weights=use_advanced_weights,
                    focus_indicators=focus_indicators,
                    focus_weight_factor=focus_weight_factor
                )
            
            # 执行回测（使用父类的run_parallel_optimization方法）
            results = self.run_parallel_optimization(param_combinations)
        elif algorithm == "遗传算法":
            logger.info("使用遗传算法优化器")
            # 导入遗传算法优化器
            from optimizers.genetic_optimizer import GeneticOptimizer
            optimizer = GeneticOptimizer()
            # 执行遗传算法优化
            results = optimizer.optimize(
                test_mode=test_mode,
                max_sub_combinations=max_sub_combinations,
                end_date=end_date
            )
        elif algorithm == "粒子群算法":
            logger.info("使用粒子群算法优化器")
            # 导入粒子群算法优化器
            from optimizers.particle_swarm_optimizer import ParticleSwarmOptimizer
            optimizer = ParticleSwarmOptimizer()
            # 执行粒子群算法优化
            results = optimizer.optimize(
                test_mode=test_mode,
                max_sub_combinations=max_sub_combinations,
                end_date=end_date
            )
        else:
            logger.error(f"未知优化算法: {algorithm}")
            raise ValueError(f"未知优化算法: {algorithm}")
        
        return results
    
    def run_parallel_backtests(self, param_combinations: List[Dict[str, Any]], max_workers: int = None) -> List[Dict[str, Any]]:
        """
        并行执行回测

        Args:
            param_combinations: 参数组合列表
            max_workers: 最大工作线程数

        Returns:
            List[Dict[str, Any]]: 回测结果列表
        """
        # 兼容原有接口，调用父类的run_parallel_optimization方法
        return self.run_parallel_optimization(param_combinations)
    
    def export_to_excel(self, results: List[Dict[str, Any]], file_path: str = "parameter_optimization_results.xlsx"):
        """
        导出结果到Excel
        
        Args:
            results: 回测结果列表
            file_path: Excel文件路径（默认使用固定文件名）
        """
        self.result_processor.export_to_excel(results, file_path)
    
    def save_results(self, results: List[Dict[str, Any]], output_file: str = "parameter_optimization_results.json"):
        """
        保存结果到JSON文件
        
        Args:
            results: 回测结果列表
            output_file: 输出文件名
        """
        self.result_processor.save_results(results, output_file)
    
    def visualize_yield_distribution(self, results: List[Dict[str, Any]], output_file: str = "yield_distribution.html") -> None:
        """
        可视化收益率分布
        
        Args:
            results: 回测结果列表
            output_file: 输出HTML文件名
        """
        self.result_processor.visualize_yield_distribution(results, output_file)
    
    def get_best_result(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取最佳结果
        
        Args:
            results: 回测结果列表
            
        Returns:
            Dict[str, Any]: 最佳结果
        """
        return self.result_processor.get_best_result(results)
    
    def generate_blueprint(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                          end_date: str = '2025-12-25', blueprint_file: str = "parameter_blueprint.json",
                          algorithm: str = "暴力搜索", stop_profit_min: int = None, stop_profit_max: int = None,
                          stop_profit_step: int = None, stop_loss_min: int = None, stop_loss_max: int = None,
                          stop_loss_step: int = None, weight_step: int = None, use_advanced_weights: bool = True,
                          focus_indicators: List[str] = None, focus_weight_factor: float = None) -> str:
        """
        生成参数组合蓝图文件，使用蓝图管理器实现
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            blueprint_file: 蓝图文件路径
            algorithm: 优化算法
            stop_profit_min: 止盈最小值（%）
            stop_profit_max: 止盈最大值（%）
            stop_profit_step: 止盈步长（%）
            stop_loss_min: 止损最小值（%）
            stop_loss_max: 止损最大值（%）
            stop_loss_step: 止损步长（%）
            weight_step: 权重步长（%）
            use_advanced_weights: 是否使用高级权重配置模式
            focus_indicators: 重点关注的指标列表
            focus_weight_factor: 重点指标权重因子
            
        Returns:
            蓝图文件路径
        """
        # 生成参数组合，使用重写后的方法，确保前端传入的参数范围生效
        param_combinations = self.generate_parameter_combinations(
            test_mode=test_mode,
            max_sub_combinations=max_sub_combinations,
            end_date=end_date,
            algorithm=algorithm,
            stop_profit_min=stop_profit_min,
            stop_profit_max=stop_profit_max,
            stop_profit_step=stop_profit_step,
            stop_loss_min=stop_loss_min,
            stop_loss_max=stop_loss_max,
            stop_loss_step=stop_loss_step,
            weight_step=weight_step,
            use_advanced_weights=use_advanced_weights,
            focus_indicators=focus_indicators,
            focus_weight_factor=focus_weight_factor
        )
        
        # 使用蓝图管理器生成蓝图
        blueprint = self.blueprint_manager.generate_blueprint(
            param_combinations=param_combinations,
            test_mode=test_mode,
            max_sub_combinations=max_sub_combinations,
            end_date=end_date,
            algorithm=algorithm
        )
        
        # 保存蓝图文件到当前目录
        blueprint_path = os.path.join(self.current_dir, blueprint_file)
        
        # 检查是否已有蓝图文件，如果有则增量更新
        existing_blueprint = None
        try:
            if os.path.exists(blueprint_path):
                existing_blueprint = self.blueprint_manager.load_blueprint(blueprint_path)
                logger.info(f"检测到现有蓝图文件，将进行增量更新")
        except Exception as e:
            logger.warning(f"加载现有蓝图失败，将创建新蓝图: {e}")
        
        # 如果有现有蓝图，先加载，然后增量更新
        if existing_blueprint:
            # 增量更新现有蓝图
            updated_blueprint = self.blueprint_manager.generate_blueprint(
                param_combinations=param_combinations,
                test_mode=test_mode,
                max_sub_combinations=max_sub_combinations,
                end_date=end_date,
                algorithm=algorithm,
                existing_blueprint=existing_blueprint
            )
            self.blueprint_manager.save_blueprint(updated_blueprint, blueprint_path)
            new_combinations_count = len(updated_blueprint["combinations"]) - len(existing_blueprint["combinations"])
            logger.info(f"蓝图已增量更新，新增 {new_combinations_count} 个参数组合，总组合数: {len(updated_blueprint['combinations'])}")
        else:
            # 保存新蓝图
            self.blueprint_manager.save_blueprint(blueprint, blueprint_path)
            logger.info(f"蓝图已生成，包含 {len(param_combinations)} 个参数组合")
        
        return blueprint_path
    
    def list_blueprints(self) -> List[Dict[str, Any]]:
        """
        列出所有蓝图文件
        
        Returns:
            List[Dict[str, Any]]: 蓝图文件列表，每个文件包含filename、size_kb、total_combinations、algorithm等信息
        """
        return self.blueprint_manager.list_blueprints(self.current_dir)
    
    def clear_blueprints(self) -> int:
        """
        清除所有蓝图文件
        
        Returns:
            int: 删除的文件数量
        """
        return self.blueprint_manager.clear_blueprints(self.current_dir)
        
    def delete_blueprint(self, filename: str) -> bool:
        """
        删除特定的蓝图文件
        
        Args:
            filename: 要删除的蓝图文件名
            
        Returns:
            bool: 删除是否成功
        """
        return self.blueprint_manager.delete_blueprint(filename, self.current_dir)
    
    def load_blueprint(self, blueprint_file: str = "parameter_blueprint.json", load_all: bool = True) -> Dict[str, Any]:
        """
        加载参数组合蓝图文件，使用蓝图管理器实现
        
        Args:
            blueprint_file: 蓝图文件路径
            load_all: 是否加载所有组合（暂不使用，保持接口兼容）
            
        Returns:
            蓝图数据
        """
        blueprint_path = os.path.join(self.current_dir, blueprint_file)
        return self.blueprint_manager.load_blueprint(blueprint_path)
    
    def _count_completed_combinations(self, blueprint: Dict[str, Any]) -> int:
        """
        统计已完成的组合数
        
        Args:
            blueprint: 蓝图数据
            
        Returns:
            已完成的组合数
        """
        return self.blueprint_manager.count_completed_combinations(blueprint)


def main():
    """
    主函数
    """
    logger.info("=" * 60)
    logger.info("参数暴力求解器")
    logger.info("=" * 60)
    
    import argparse
    
    parser = argparse.ArgumentParser(description="参数暴力求解器 - 寻找回测收益率最高的参数组合")
    parser.add_argument('--test', action='store_true', help='测试模式，仅生成少量组合')
    parser.add_argument('--max-sub-combinations', type=int, default=10, help='最大子权重组合数')
    parser.add_argument('--algorithm', type=str, default='暴力搜索', choices=['暴力搜索', '遗传算法', '粒子群算法'], help='优化算法')
    parser.add_argument('--blueprint', type=str, help='从蓝图文件加载参数组合')
    parser.add_argument('--max-workers', type=int, help='最大工作线程数')
    parser.add_argument('--end-date', type=str, default='2025-12-25', help='回测终点日期（格式：YYYY-MM-DD）')
    parser.add_argument('--stop-profit-min', type=int, help='止盈最小值（%）')
    parser.add_argument('--stop-profit-max', type=int, help='止盈最大值（%）')
    parser.add_argument('--stop-profit-step', type=int, help='止盈步长（%）')
    parser.add_argument('--stop-loss-min', type=int, help='止损最小值（%）')
    parser.add_argument('--stop-loss-max', type=int, help='止损最大值（%）')
    parser.add_argument('--stop-loss-step', type=int, help='止损步长（%）')
    parser.add_argument('--weight-step', type=int, help='权重步长（%）')
    parser.add_argument('--dry-run', action='store_true', help='仅生成参数组合，不执行回测')
    parser.add_argument('--generate-blueprint', action='store_true', help='生成参数组合蓝图文件')
    
    args = parser.parse_args()
    
    # 创建优化器实例
    optimizer = ParameterOptimizer()
    
    if args.dry_run:
        # 仅生成参数组合，不执行回测
        logger.info("\n=== 仅生成参数组合（dry-run模式）===")
        param_combinations = optimizer.generate_parameter_combinations(
            test_mode=args.test,
            max_sub_combinations=args.max_sub_combinations,
            end_date=args.end_date,
            algorithm=args.algorithm,
            stop_profit_min=args.stop_profit_min,
            stop_profit_max=args.stop_profit_max,
            stop_profit_step=args.stop_profit_step,
            stop_loss_min=args.stop_loss_min,
            stop_loss_max=args.stop_loss_max,
            stop_loss_step=args.stop_loss_step,
            weight_step=args.weight_step
        )
        logger.info(f"\n✅ 成功生成 {len(param_combinations)} 个参数组合")
        if param_combinations:
            logger.info("\n示例参数组合:")
            logger.info(f"  - 回测天数: {param_combinations[0]['backtest_days']}")
            logger.info(f"  - 止盈比例: {param_combinations[0]['stop_profit_ratio']*100:.1f}%")
            logger.info(f"  - 止损比例: {param_combinations[0]['stop_loss_ratio']*100:.1f}%")
            logger.info(f"  - 权重配置: {param_combinations[0]['weights_config']}")
            logger.info(f"  - 子权重配置: {param_combinations[0]['sub_weights_config'].keys()}")
        logger.info("\n=== dry-run模式完成 ===")
        return
    
    if args.generate_blueprint:
        # 生成参数组合蓝图
        logger.info("\n=== 生成参数组合蓝图 ===")
        blueprint_path = optimizer.generate_blueprint(
            test_mode=args.test,
            max_sub_combinations=args.max_sub_combinations,
            end_date=args.end_date,
            algorithm=args.algorithm,
            stop_profit_min=args.stop_profit_min,
            stop_profit_max=args.stop_profit_max,
            stop_profit_step=args.stop_profit_step,
            stop_loss_min=args.stop_loss_min,
            stop_loss_max=args.stop_loss_max,
            stop_loss_step=args.stop_loss_step,
            weight_step=args.weight_step
        )
        logger.info(f"\n✅ 蓝图已成功生成: {blueprint_path}")
        logger.info(f"\n=== 蓝图生成完成 ===")
        return
    
    # 执行优化
    results = optimizer.run_optimization(
        test_mode=args.test,
        max_sub_combinations=args.max_sub_combinations,
        algorithm=args.algorithm,
        blueprint_file=args.blueprint,
        max_workers=args.max_workers,
        end_date=args.end_date,
        stop_profit_min=args.stop_profit_min,
        stop_profit_max=args.stop_profit_max,
        stop_profit_step=args.stop_profit_step,
        stop_loss_min=args.stop_loss_min,
        stop_loss_max=args.stop_loss_max,
        stop_loss_step=args.stop_loss_step,
        weight_step=args.weight_step
    )
    
    # 导出最终结果到固定Excel文件
    output_file = "parameter_optimization_results.xlsx"
    optimizer.export_to_excel(results, output_file)
    
    # 生成收益率分布可视化
    optimizer.visualize_yield_distribution(results)
    
    logger.info("=" * 60)
    logger.info("优化完成！")
    if results:
        best_result = results[0]
        # 检查结果是否包含回测指标（暴力搜索）或仅包含参数（PSO/GA）
        if 'total_return' in best_result:
            # 完整回测结果格式（暴力搜索）
            logger.info(f"最佳组合总收益率: {best_result['total_return']:.2f}%")
            logger.info(f"最佳组合年化收益率: {best_result['annual_return']:.2f}%")
        else:
            # 参数组合格式（PSO/GA）
            logger.info(f"最佳组合适应度: {best_result.get('fitness', -1000):.4f}")
        logger.info("最佳组合参数:")
        logger.info(f"  - 回测天数: {best_result['backtest_days']}")
        logger.info(f"  - 止盈比例: {best_result['stop_profit_ratio']*100:.1f}%")
        logger.info(f"  - 止损比例: {best_result['stop_loss_ratio']*100:.1f}%")
        logger.info(f"  - 权重配置: {best_result['weights_config']}")
        logger.info(f"  - 子权重配置: {best_result['sub_weights_config']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
