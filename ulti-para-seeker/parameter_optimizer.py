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
from optimizers.genetic_optimizer import GeneticOptimizer
from optimizers.particle_swarm_optimizer import ParticleSwarmOptimizer
from optimizers.result_processor import ResultProcessor

# 导入蓝图管理器
from utils.blueprint_manager import BlueprintManager


class ParameterOptimizer:
    """
    参数优化器 - 用于协调不同的优化算法，寻找回测收益率最高的参数组合
    直接使用BlueprintManager管理参数组合和回测流程
    """
    
    def __init__(self):
        """初始化参数优化器"""
        self.results = []
        self.start_time = None
        self.end_time = None
        self.result_processor = ResultProcessor(current_dir)
        # 初始化蓝图管理器
        self.blueprint_manager = BlueprintManager()
        # 保存当前目录，用于文件操作
        self.current_dir = current_dir
        # 初始化优化器实例
        self.optimizers = {
            "暴力搜索": BruteForceOptimizer(),
            "遗传算法": GeneticOptimizer(),
            "粒子群算法": ParticleSwarmOptimizer()
        }
    
    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                      end_date: str = '2025-12-25', algorithm: str = "暴力搜索", 
                                      stop_profit_min: int = None, stop_profit_max: int = None, 
                                      stop_profit_step: int = None, stop_loss_min: int = None, 
                                      stop_loss_max: int = None, stop_loss_step: int = None, 
                                      weight_step: int = None, use_advanced_weights: bool = True,
                                      focus_indicators: List[str] = None, focus_weight_factor: float = None, initial_capital: int = 60000,
                                      backtest_days: int = 90) -> List[Dict[str, Any]]:
        """
        根据选择的算法生成参数组合

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
            initial_capital: 初始资金
            backtest_days: 回测天数

        Returns:
            List[Dict[str, Any]]: 所有可能的参数组合列表
        """
        # 根据算法选择优化器
        if algorithm not in self.optimizers:
            logger.error(f"未知优化算法: {algorithm}")
            raise ValueError(f"未知优化算法: {algorithm}")
        
        optimizer = self.optimizers[algorithm]
        
        # 根据不同算法调用相应的参数组合生成方法
        if algorithm == "暴力搜索":
            # 暴力搜索算法需要完整的参数
            return optimizer.generate_parameter_combinations(
                test_mode=test_mode,
                max_sub_combinations=max_sub_combinations,
                end_date=end_date,
                focus_indicators=focus_indicators,
                focus_weight_factor=focus_weight_factor,
                backtest_days=backtest_days
            )
        elif algorithm == "遗传算法" or algorithm == "粒子群算法":
            # 遗传算法和粒子群算法使用简化参数
            return optimizer.generate_parameter_combinations(
                test_mode=test_mode,
                max_sub_combinations=max_sub_combinations,
                end_date=end_date,
                backtest_days=backtest_days
            )
        else:
            # 默认使用暴力搜索算法
            return self.optimizers["暴力搜索"].generate_parameter_combinations(
                test_mode=test_mode,
                max_sub_combinations=max_sub_combinations,
                end_date=end_date,
                backtest_days=backtest_days
            )
    
    def run_optimization(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                        end_date: str = '2025-12-25', algorithm: str = "暴力搜索", 
                        blueprint_file: str = None, max_workers: int = None, 
                        stop_profit_min: int = None, stop_profit_max: int = None, 
                        stop_profit_step: int = None, stop_loss_min: int = None, 
                        stop_loss_max: int = None, stop_loss_step: int = None, 
                        weight_step: int = None, use_advanced_weights: bool = True,
                        focus_indicators: List[str] = None, focus_weight_factor: float = None, initial_capital: int = 60000) -> List[Dict[str, Any]]:
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
            initial_capital: 初始资金

        Returns:
            List[Dict[str, Any]]: 回测结果列表
        """
        logger.info("\n=== 执行参数优化 ===")
        logger.info(f"优化算法: {algorithm}")
        logger.info(f"测试模式: {test_mode}")
        logger.info(f"最大子权重组合数: {max_sub_combinations}")
        
        # 根据算法选择优化器
        if algorithm not in self.optimizers:
            logger.error(f"未知优化算法: {algorithm}")
            raise ValueError(f"未知优化算法: {algorithm}")
        
        optimizer = self.optimizers[algorithm]
        
        # 使用蓝图文件或生成新的参数组合
        if blueprint_file:
            logger.info(f"从蓝图文件加载参数组合: {blueprint_file}")
            blueprint = self.load_blueprint(blueprint_file, load_all=True)
            # 过滤出待处理的组合
            pending_combinations = [combo['params'] for combo in blueprint['combinations'] if combo['status'] == 'pending']
            
            # 执行回测（使用ParameterOptimizer自己的并行回测功能，因为它支持蓝图管理）
            results = self.run_parallel_optimization(pending_combinations, blueprint=blueprint, blueprint_file=blueprint_file)
        else:
            # 直接调用对应算法的优化方法
            if algorithm == "暴力搜索":
                # 暴力搜索算法需要生成参数组合
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
                # 为每个参数组合添加初始资金
                for param in param_combinations:
                    param['initial_capital'] = initial_capital
                results = optimizer.run_parallel_optimization(param_combinations)
            else:
                # 遗传算法和粒子群算法自身包含参数生成和优化逻辑
                # 这里需要确保optimize方法能处理initial_capital参数
                results = optimizer.optimize(
                    test_mode=test_mode,
                    max_sub_combinations=max_sub_combinations,
                    end_date=end_date,
                    initial_capital=initial_capital
                )
        
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
        # 兼容原有接口，调用暴力搜索优化器的run_parallel_optimization方法
        return self.optimizers["暴力搜索"].run_parallel_optimization(param_combinations)
    
    def run_backtest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个参数组合的回测

        Args:
            params: 参数组合

        Returns:
            Dict[str, Any]: 回测结果
        """
        # 调用暴力搜索优化器的run_backtest方法
        return self.optimizers["暴力搜索"].run_backtest(params)
    
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
                          focus_indicators: List[str] = None, focus_weight_factor: float = None, initial_capital: int = 60000,
                          backtest_days: int = 90) -> str:
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
            initial_capital: 初始资金
            backtest_days: 回测天数
            
        Returns:
            蓝图文件路径
        """
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
            focus_weight_factor=focus_weight_factor,
            backtest_days=backtest_days
        )
        
        # 为每个参数组合添加初始资金，这是回测执行时需要的全局参数
        for param in param_combinations:
            param['initial_capital'] = initial_capital
        
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
            List[Dict[str, Any]]: 蓝图文件列表，每个文件包含filename、size_kb、total_combinations等信息
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
    
    def _generate_weights_combinations(self, indicators: List[str], total: int, step: int, min_weight: int = 0, max_weight: int = 100) -> List[Dict[str, int]]:
        """
        生成权重组合（委托给暴力搜索优化器）
        
        Args:
            indicators: 指标列表
            total: 总权重
            step: 步长
            min_weight: 单个指标最小权重
            max_weight: 单个指标最大权重
            
        Returns:
            权重组合列表
        """
        return self.optimizers["暴力搜索"]._generate_weights_combinations(indicators, total, step, min_weight, max_weight)
    
    def _generate_custom_weights_combinations(self, indicators: List[str], total: int, step: int, focus_indicators: List[str] = None, focus_weight_factor: float = 1.5) -> List[Dict[str, int]]:
        """
        生成自定义权重组合（委托给暴力搜索优化器）
        
        Args:
            indicators: 指标列表
            total: 总权重
            step: 步长
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            
        Returns:
            自定义权重组合列表
        """
        return self.optimizers["暴力搜索"]._generate_custom_weights_combinations(indicators, total, step, focus_indicators, focus_weight_factor)
    
    def _generate_sub_weights_combinations(self, test_mode: bool = False, max_combinations: int = 10, use_advanced_mode: bool = True) -> List[Dict[str, Dict[str, int]]]:
        """
        生成子权重组合（委托给暴力搜索优化器）
        
        Args:
            test_mode: 是否为测试模式
            max_combinations: 最大子权重组合数
            use_advanced_mode: 是否使用高级模式
            
        Returns:
            子权重组合列表
        """
        return self.optimizers["暴力搜索"]._generate_sub_weights_combinations(test_mode, max_combinations, use_advanced_mode)
    
    def update_combination_status(self, blueprint: Dict[str, Any], combo_id: int, status: str, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        更新参数组合的状态和结果（委托给蓝图管理器）
        
        Args:
            blueprint: 蓝图数据
            combo_id: 组合ID
            status: 新状态
            result: 回测结果
            
        Returns:
            更新后的蓝图数据
        """
        return self.blueprint_manager.update_combination_status(combo_id, status, result, blueprint)
    
    def save_blueprint(self, blueprint: Dict[str, Any], blueprint_file: str = "parameter_blueprint.json") -> str:
        """
        保存蓝图文件（委托给蓝图管理器）
        
        Args:
            blueprint: 蓝图数据
            blueprint_file: 蓝图文件路径
            
        Returns:
            保存后的蓝图文件路径
        """
        blueprint_path = os.path.join(self.current_dir, blueprint_file)
        return self.blueprint_manager.save_blueprint(blueprint, blueprint_path)
    
    def run_parallel_optimization(self, param_combinations: List[Dict[str, Any]], num_workers: int = None, batch_size: int = 50, save_interval: int = 1, blueprint: Optional[Dict[str, Any]] = None, blueprint_file: str = "parameter_blueprint.json", optimizer=None) -> List[Dict[str, Any]]:
        """
        使用ProcessPoolExecutor并行运行参数优化（支持断点续传和结果更新）
        
        Args:
            param_combinations: 参数组合列表
            num_workers: 并行工作进程数，None表示使用CPU核心数
            batch_size: 每批处理的参数组合数（已废弃，保留参数兼容性）
            save_interval: 保存中间结果的批次间隔
            blueprint: 参数组合蓝图数据（用于断点续传）
            blueprint_file: 蓝图文件路径
            optimizer: 具体的优化器实例，用于运行回测
            
        Returns:
            List[Dict[str, Any]]: 按收益率排序的结果列表
        """
        import os
        from utils.logger import logger
        from datetime import datetime
        from concurrent.futures import ProcessPoolExecutor, as_completed
        
        total_combinations = len(param_combinations)
        self.start_time = datetime.now()
        all_results = []
        
        # 设置默认工作进程数
        if num_workers is None:
            num_workers = os.cpu_count() - 1 if os.cpu_count() > 1 else 1
        
        logger.info("\n=== 并行处理模式 ===")
        logger.info(f"开始并行优化，使用 {num_workers} 个进程")
        logger.info(f"总参数组合数: {total_combinations}")
        logger.info(f"每 {save_interval} 个组合更新一次蓝图")
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
            self.blueprint_manager.save_blueprint(blueprint, os.path.join(self.current_dir, blueprint_file))
        
        logger.info(f"\n🚀 开始提交并行任务，使用 {num_workers} 个进程")
        logger.info(f"📋 总任务数: {total_combinations}")
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            # 提交所有任务
            future_to_combo = {}
            for i, param, combo_id in combo_list:
                # 添加任务提交日志
                logger.info(f"📌 提交任务 {i + 1}/{total_combinations} 到进程池")
                # 使用指定的优化器运行回测，默认使用暴力搜索优化器
                if optimizer is None:
                    optimizer = self.optimizers["暴力搜索"]
                future = executor.submit(optimizer.run_backtest, param)
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
                        blueprint = self.blueprint_manager.update_combination_status(blueprint, combo_id, 'completed', result)
                    
                    # 按指定间隔更新蓝图
                    if processed % save_interval == 0 or processed == total_combinations:
                        # 保存更新后的蓝图（如果有）
                        if blueprint:
                            self.blueprint_manager.save_blueprint(blueprint, os.path.join(self.current_dir, blueprint_file))
                except Exception as e:
                    logger.error(f"❌ 组合 {i + 1}/{total_combinations} 处理失败: {e}")
                    
                    # 更新蓝图中的组合状态为failed
                    if blueprint and combo_id is not None:
                        blueprint = self.blueprint_manager.update_combination_status(blueprint, combo_id, 'failed')
                        self.blueprint_manager.save_blueprint(blueprint, os.path.join(self.current_dir, blueprint_file))
                    
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
    
    # 保存结果到Excel和生成可视化
    if results:
        # 导出结果到Excel
        output_file = "parameter_optimization_results.xlsx"
        optimizer.export_to_excel(results, output_file)
    
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