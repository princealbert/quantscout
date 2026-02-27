#!/usr/bin/env python
# coding=utf-8
"""
优化器管理器 - 协调不同的优化算法，管理优化流程和蓝图
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# 项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入日志系统
from utils.logger import logger

# 导入优化算法
from algorithms.brute_force import BruteForceOptimizer
from algorithms.genetic import GeneticOptimizer
from algorithms.particle_swarm import ParticleSwarmOptimizer

# 导入结果处理器
from core.result_processor import ResultProcessor

# 导入参数工具
from utils.parameter_utils import generate_param_hash, remove_duplicate_combinations


class OptimizerManager:
    """
    优化器管理器 - 用于协调不同的优化算法，管理优化流程
    """
    
    def __init__(self):
        """初始化优化器管理器"""
        self.results = []
        self.start_time = None
        self.end_time = None
        self.result_processor = ResultProcessor()

        # 使用当前工作目录 + ulti-para-seeker 来确定蓝图文件所在目录
        # 这样无论从哪里运行，都能正确找到蓝图文件
        cwd = os.getcwd()
        # 检查当前工作目录是否已经是 ulti-para-seeker 目录
        if cwd.endswith('ulti-para-seeker'):
            self.current_dir = cwd
        else:
            # 如果在项目根目录，拼接 ulti-para-seeker
            self.current_dir = os.path.join(cwd, 'ulti-para-seeker')

        # 初始化蓝图管理器,使用相对路径
        from utils.blueprint_manager import BlueprintManager
        blueprint_file = os.path.join(self.current_dir, "parameter_blueprint.json")
        self.blueprint_manager = BlueprintManager(blueprint_file)

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
                                      backtest_days: int = 90, existing_blueprint: Optional[Dict[str, Any]] = None,
                                      max_holding_days_min: int = 1, max_holding_days_max: int = 30,
                                      max_holding_days_step: int = 1) -> List[Dict[str, Any]]:
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
            existing_blueprint: 现有蓝图数据（用于提取优势组合）
            max_holding_days_min: 最大持仓天数最小值
            max_holding_days_max: 最大持仓天数最大值
            max_holding_days_step: 最大持仓天数步长
        
        Returns:
            List[Dict[str, Any]]: 所有可能的参数组合列表
        """
        # 根据算法选择优化器
        if algorithm not in self.optimizers:
            logger.error(f"未知优化算法: {algorithm}")
            raise ValueError(f"未知优化算法: {algorithm}")
        
        optimizer = self.optimizers[algorithm]
        
        # 将用户设置的参数传递给优化器
        return optimizer.generate_parameter_combinations(
            test_mode=test_mode,
            max_sub_combinations=max_sub_combinations,
            end_date=end_date,
            stop_profit_min=stop_profit_min,
            stop_profit_max=stop_profit_max,
            stop_profit_step=stop_profit_step,
            stop_loss_min=stop_loss_min,
            stop_loss_max=stop_loss_max,
            stop_loss_step=stop_loss_step,
            weight_step=weight_step,
            focus_indicators=focus_indicators,
            focus_weight_factor=focus_weight_factor,
            initial_capital=initial_capital,
            backtest_days=backtest_days,
            max_holding_days_min=max_holding_days_min,
            max_holding_days_max=max_holding_days_max,
            max_holding_days_step=max_holding_days_step,
            existing_blueprint=existing_blueprint  # 传递现有蓝图
        )
    
    def run_optimization(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                        end_date: str = '2025-12-25', algorithm: str = "暴力搜索", 
                        blueprint_file: str = None, max_workers: int = None, 
                        stop_profit_min: int = None, stop_profit_max: int = None, 
                        stop_profit_step: int = None, stop_loss_min: int = None, 
                        stop_loss_max: int = None, stop_loss_step: int = None, 
                        weight_step: int = None, use_advanced_weights: bool = True,
                        focus_indicators: List[str] = None, focus_weight_factor: float = None, initial_capital: int = 60000, 
                        use_parallel: bool = False, auto_clean_blueprint: bool = True,
                        blueprint_max_total: int = 1000, blueprint_max_elite: int = 500, 
                        max_holding_days_min: int = 1, max_holding_days_max: int = 30, 
                        max_holding_days_step: int = 1) -> List[Dict[str, Any]]:
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
            use_parallel: 是否使用并行模式，默认False（串行执行）
            auto_clean_blueprint: 是否自动清理蓝图文件
            blueprint_max_total: 蓝图保留的最大总组合数
            blueprint_max_elite: 保留的最优组合数
            max_holding_days_min: 最大持仓天数最小值
            max_holding_days_max: 最大持仓天数最大值
            max_holding_days_step: 最大持仓天数步长

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
        
        # 执行回测，根据use_parallel参数选择并行或串行模式
        if blueprint_file:
            logger.info(f"从蓝图文件加载参数组合: {blueprint_file}")
            blueprint = self.load_blueprint(blueprint_file, load_all=True)
            # 过滤出待处理的组合
            pending_combinations = [combo['params'] for combo in blueprint['combinations'] if combo['status'] == 'pending']
            
            if use_parallel:
                # 使用并行回测
                logger.info(f"使用并行模式执行回测，线程数: {max_workers or 'CPU核心数-1'}")
                results = self.run_parallel_optimization(pending_combinations, blueprint=blueprint, blueprint_file=blueprint_file, num_workers=max_workers)
            else:
                # 使用串行回测
                logger.info(f"使用串行模式执行回测")
                results = self.run_serial_optimization(pending_combinations, blueprint=blueprint, blueprint_file=blueprint_file, optimizer=optimizer)
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
                    focus_weight_factor=focus_weight_factor,
                    max_holding_days_min=max_holding_days_min,
                    max_holding_days_max=max_holding_days_max,
                    max_holding_days_step=max_holding_days_step
                )
                # 为每个参数组合添加初始资金
                for param in param_combinations:
                    param['initial_capital'] = initial_capital
                
                if use_parallel:
                    # 使用并行回测
                    logger.info(f"使用并行模式执行回测，线程数: {max_workers or 'CPU核心数-1'}")
                    results = self.run_parallel_optimization(param_combinations, num_workers=max_workers, optimizer=optimizer)
                else:
                    # 使用串行回测
                    logger.info(f"使用串行模式执行回测")
                    results = self.run_serial_optimization(param_combinations, optimizer=optimizer)
            else:
                # 加载现有蓝图
                existing_blueprint = None
                if os.path.exists(os.path.join(self.current_dir, "parameter_blueprint.json")):
                    existing_blueprint = self._load_blueprint(os.path.join(self.current_dir, "parameter_blueprint.json"))

                # 遗传算法和粒子群算法自身包含参数生成和优化逻辑
                # 这里需要确保optimize方法能处理initial_capital参数
                results = optimizer.optimize(
                    test_mode=test_mode,
                    max_sub_combinations=max_sub_combinations,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    backtest_days=90,  # 默认使用90天回测
                    existing_blueprint=existing_blueprint,  # 传递现有蓝图
                    max_holding_days_min=max_holding_days_min,
                    max_holding_days_max=max_holding_days_max,
                    max_holding_days_step=max_holding_days_step
                )

        # 优化完成后,自动清理蓝图文件
        if auto_clean_blueprint and blueprint_file:
            self._auto_clean_blueprint(blueprint_file, blueprint_max_total, blueprint_max_elite)

        return results
    
    def generate_blueprint(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                          end_date: str = '2025-12-25', blueprint_file: str = "parameter_blueprint.json",
                          algorithm: str = "暴力搜索", stop_profit_min: int = None, stop_profit_max: int = None,
                          stop_profit_step: int = None, stop_loss_min: int = None, stop_loss_max: int = None,
                          stop_loss_step: int = None, weight_step: int = None, use_advanced_weights: bool = True,
                          focus_indicators: List[str] = None, focus_weight_factor: float = None, initial_capital: int = 60000,
                          backtest_days: int = 90, force_new_blueprint: bool = False,
                          max_holding_days_min: int = 1, max_holding_days_max: int = 30,
                          max_holding_days_step: int = 1) -> str:
        """
        生成参数组合蓝图文件
        
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
            force_new_blueprint: 是否强制生成新蓝图，忽略现有文件
            max_holding_days_min: 最大持仓天数最小值
            max_holding_days_max: 最大持仓天数最大值
            max_holding_days_step: 最大持仓天数步长
            
        Returns:
            蓝图文件路径
        """
        # 保存蓝图文件到当前目录
        blueprint_path = os.path.join(self.current_dir, blueprint_file)
        
        # 检查是否已有蓝图文件，如果有则增量更新
        existing_blueprint = None
        try:
            if os.path.exists(blueprint_path) and not force_new_blueprint:
                existing_blueprint = self._load_blueprint(blueprint_path)
                logger.info(f"检测到现有蓝图文件，将进行增量更新")
            elif force_new_blueprint:
                logger.info(f"强制生成新蓝图，忽略现有文件")
                # 如果强制生成新蓝图，删除现有文件
                if os.path.exists(blueprint_path):
                    os.remove(blueprint_path)
                    existing_blueprint = None
        except Exception as e:
            logger.warning(f"加载现有蓝图失败，将创建新蓝图: {e}")
        
        # 对于所有算法，都生成新的参数组合
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
            backtest_days=backtest_days,
            existing_blueprint=existing_blueprint,  # 传递现有蓝图
            max_holding_days_min=max_holding_days_min,
            max_holding_days_max=max_holding_days_max,
            max_holding_days_step=max_holding_days_step
        )
        
        # 为每个参数组合添加初始资金
        for param in param_combinations:
            param['initial_capital'] = initial_capital
        
        # 生成蓝图
        blueprint = self._generate_blueprint(
            param_combinations=param_combinations,
            test_mode=test_mode,
            max_sub_combinations=max_sub_combinations,
            end_date=end_date,
            algorithm=algorithm,
            existing_blueprint=existing_blueprint
        )
        
        # 保存蓝图
        self._save_blueprint(blueprint, blueprint_path)
        
        if existing_blueprint:
            new_combinations_count = len(blueprint["combinations"]) - len(existing_blueprint["combinations"])
            logger.info(f"蓝图已增量更新，新增 {new_combinations_count} 个参数组合，总组合数: {len(blueprint['combinations'])}")
        else:
            logger.info(f"蓝图已生成，包含 {len(blueprint['combinations'])} 个参数组合")
        
        return blueprint_path
    
    def load_blueprint(self, blueprint_file: str = "parameter_blueprint.json", load_all: bool = True) -> Dict[str, Any]:
        """
        加载参数组合蓝图文件
        
        Args:
            blueprint_file: 蓝图文件路径
            load_all: 是否加载所有组合
            
        Returns:
            蓝图数据
        """
        blueprint_path = os.path.join(self.current_dir, blueprint_file)
        return self._load_blueprint(blueprint_path)
    
    def list_blueprints(self) -> List[Dict[str, Any]]:
        """
        列出所有蓝图文件
        
        Returns:
            List[Dict[str, Any]]: 蓝图文件列表
        """
        blueprints = []
        
        # 遍历目录下的蓝图文件
        for filename in os.listdir(self.current_dir):
            if filename.startswith('parameter_blueprint') and filename.endswith('.json'):
                file_path = os.path.join(self.current_dir, filename)
                try:
                    # 获取文件大小
                    size = os.path.getsize(file_path)
                    size_kb = round(size / 1024, 2)
                    
                    # 读取文件内容，获取蓝图信息
                    with open(file_path, 'r', encoding='utf-8') as f:
                        blueprint_data = json.load(f)
                    
                    # 提取必要信息
                    total_combinations = blueprint_data.get('total_combinations', 0)
                    algorithm = blueprint_data.get('algorithm', '未知')
                    version = blueprint_data.get('version', '1.0')
                    generated_at = blueprint_data.get('generated_at', '')
                    
                    blueprints.append({
                        'filename': filename,
                        'size_kb': size_kb,
                        'total_combinations': total_combinations,
                        'algorithm': algorithm,
                        'version': version,
                        'generated_at': generated_at,
                        'created_at': generated_at,  # 兼容app.py中的created_at字段
                        'modified_at': generated_at,  # 兼容app.py中的modified_at字段
                        'is_index': 'files' in blueprint_data,  # 检查是否为分拆的蓝图索引文件
                        'file_path': file_path
                    })
                except Exception as e:
                    logger.warning(f"读取蓝图文件失败: {filename}, 错误: {e}")
        
        # 按生成时间降序排序
        blueprints.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
        
        return blueprints
    
    def clear_blueprints(self) -> int:
        """
        清除所有蓝图文件
        
        Returns:
            int: 删除的文件数量
        """
        deleted_count = 0
        
        # 遍历目录下的蓝图文件
        for filename in os.listdir(self.current_dir):
            if filename.startswith('parameter_blueprint') and filename.endswith('.json'):
                file_path = os.path.join(self.current_dir, filename)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"已删除蓝图文件: {filename}")
                except Exception as e:
                    logger.error(f"删除蓝图文件失败: {filename}, 错误: {e}")
        
        return deleted_count
        
    def delete_blueprint(self, filename: str) -> bool:
        """
        删除特定的蓝图文件
        
        Args:
            filename: 要删除的蓝图文件名
            
        Returns:
            bool: 删除是否成功
        """
        # 检查文件名格式是否合法
        if not (filename.startswith('parameter_blueprint') and filename.endswith('.json')):
            logger.error(f"无效的蓝图文件名: {filename}")
            return False
        
        file_path = os.path.join(self.current_dir, filename)
        
        try:
            # 检查文件是否存在
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"已删除蓝图文件: {filename}")
                return True
            else:
                logger.warning(f"蓝图文件不存在: {filename}")
                return False
        except Exception as e:
            logger.error(f"删除蓝图文件失败: {filename}, 错误: {e}")
            return False
    
    def run_parallel_optimization(self, param_combinations: List[Dict[str, Any]], num_workers: int = None, 
                                 batch_size: int = 50, save_interval: int = 1, blueprint: Optional[Dict[str, Any]] = None, 
                                 blueprint_file: str = "parameter_blueprint.json", optimizer=None) -> List[Dict[str, Any]]:
        """
        使用ProcessPoolExecutor并行运行参数优化
        
        Args:
            param_combinations: 参数组合列表
            num_workers: 并行工作进程数
            batch_size: 每批处理的参数组合数
            save_interval: 保存中间结果的批次间隔
            blueprint: 参数组合蓝图数据
            blueprint_file: 蓝图文件路径
            optimizer: 具体的优化器实例
            
        Returns:
            List[Dict[str, Any]]: 按收益率排序的结果列表
        """
        import os
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
            self._save_blueprint(blueprint, os.path.join(self.current_dir, blueprint_file))
        
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
                    
                    logger.info(f"✅ 已完成 {processed}/{total_combinations} 个组合 ({progress:.1f}%)")
                    
                    # 更新蓝图中的组合状态为completed
                    if blueprint and combo_id is not None:
                        blueprint = self.update_combination_status(blueprint, combo_id, 'completed', result)
                    
                    # 按指定间隔更新蓝图
                    if processed % save_interval == 0 or processed == total_combinations:
                        # 保存更新后的蓝图（如果有）
                        if blueprint:
                            self._save_blueprint(blueprint, os.path.join(self.current_dir, blueprint_file))
                except Exception as e:
                    logger.error(f"❌ 组合 {i + 1}/{total_combinations} 处理失败: {e}")
                    
                    # 更新蓝图中的组合状态为failed
                    if blueprint and combo_id is not None:
                        blueprint = self.update_combination_status(blueprint, combo_id, 'failed', None)
                        self._save_blueprint(blueprint, os.path.join(self.current_dir, blueprint_file))
                    
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

    def run_serial_optimization(self, param_combinations: List[Dict[str, Any]], blueprint: Optional[Dict[str, Any]] = None, 
                               blueprint_file: str = "parameter_blueprint.json", optimizer=None) -> List[Dict[str, Any]]:
        """
        串行运行参数优化
        
        Args:
            param_combinations: 参数组合列表
            blueprint: 参数组合蓝图数据
            blueprint_file: 蓝图文件路径
            optimizer: 具体的优化器实例
            
        Returns:
            List[Dict[str, Any]]: 按收益率排序的结果列表
        """
        import os
        from datetime import datetime
        
        total_combinations = len(param_combinations)
        self.start_time = datetime.now()
        all_results = []
        
        logger.info(f"\n=== 串行处理模式 ===")
        logger.info(f"开始串行优化")
        logger.info(f"总参数组合数: {total_combinations}")
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
            self._save_blueprint(blueprint, os.path.join(self.current_dir, blueprint_file))
        
        logger.info(f"\n🚀 开始串行执行任务")
        logger.info(f"📋 总任务数: {total_combinations}")
        
        # 串行执行所有任务
        processed = 0
        for i, param, combo_id in combo_list:
            logger.info(f"📌 开始执行任务 {i + 1}/{total_combinations}")
            
            # 使用指定的优化器运行回测，默认使用暴力搜索优化器
            if optimizer is None:
                optimizer = self.optimizers["暴力搜索"]
            
            try:
                # 直接调用回测函数
                result = optimizer.run_backtest(param)
                all_results.append(result)
                processed += 1
                
                # 计算进度
                progress = (processed / total_combinations) * 100
                
                logger.info(f"✅ 已完成 {processed}/{total_combinations} 个组合 ({progress:.1f}%)")
                
                # 更新蓝图中的组合状态为completed
                if blueprint and combo_id is not None:
                    blueprint = self.update_combination_status(blueprint, combo_id, 'completed', result)
                    # 保存更新后的蓝图
                    self._save_blueprint(blueprint, os.path.join(self.current_dir, blueprint_file))
            except Exception as e:
                logger.error(f"❌ 组合 {i + 1}/{total_combinations} 处理失败: {e}")
                
                # 更新蓝图中的组合状态为failed
                if blueprint and combo_id is not None:
                    blueprint = self.update_combination_status(blueprint, combo_id, 'failed', None)
                    self._save_blueprint(blueprint, os.path.join(self.current_dir, blueprint_file))
                
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
        
        return all_results
    
    def export_to_excel(self, results: List[Dict[str, Any]], file_path: str = "parameter_optimization_results.xlsx"):
        """
        导出结果到Excel
        
        Args:
            results: 回测结果列表
            file_path: Excel文件路径
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
    
    # 蓝图管理功能
    def _generate_blueprint(self, param_combinations: List[Dict[str, Any]], 
                          test_mode: bool = False, 
                          max_sub_combinations: int = 10, 
                          end_date: str = '2025-12-25',
                          algorithm: str = "暴力搜索",
                          existing_blueprint: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成参数组合蓝图
        
        Args:
            param_combinations: 参数组合列表
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            algorithm: 优化算法类型
            existing_blueprint: 现有蓝图（可选），用于增量生成
        
        Returns:
            Dict[str, Any]: 蓝图数据结构
        """
        # 1. 去重新生成的参数组合
        unique_new_combinations = remove_duplicate_combinations(param_combinations)
        
        # 2. 提取现有蓝图信息
        existing_hashes = set()
        existing_combinations = []
        next_id = 1
        
        if existing_blueprint:
            # 提取现有蓝图中的组合哈希
            for combo in existing_blueprint["combinations"]:
                existing_hashes.add(generate_param_hash(combo["params"]))
                existing_combinations.append(combo)
                next_id = max(next_id, combo["id"] + 1)
        
        # 3. 移除与现有蓝图重复的新组合，保留所有不重复的组合
        all_new_unique_combinations = []
        for combo in unique_new_combinations:
            combo_hash = generate_param_hash(combo)
            if combo_hash not in existing_hashes:
                all_new_unique_combinations.append(combo)
        
        # 4. 对于所有算法，都应该添加新的组合，而不是受限于max_sub_combinations
        final_combinations = []
        
        if algorithm in ["遗传算法", "粒子群算法"]:
            # 对于遗传算法和粒子群算法，我们总是添加新的组合
            import random
            
            # 从新生成的组合中选择max_sub_combinations个新组合
            if len(all_new_unique_combinations) >= max_sub_combinations:
                # 如果有足够的新组合，随机选择max_sub_combinations个
                random.shuffle(all_new_unique_combinations)
                final_combinations = all_new_unique_combinations[:max_sub_combinations]
            else:
                # 如果新组合不够，使用所有新组合
                final_combinations = all_new_unique_combinations.copy()
        else:
            # 暴力搜索算法使用所有新生成的组合
            final_combinations = all_new_unique_combinations.copy()
        
        # 5. 创建蓝图数据结构
        if existing_blueprint:
            # 增量更新现有蓝图
            blueprint = existing_blueprint.copy()
            blueprint["last_modified"] = datetime.now().isoformat()
            # 保留algorithm字段为字符串类型，使用逗号分隔多个算法
            current_algorithm = blueprint.get("algorithm", "")
            if current_algorithm:
                # 如果当前算法已经包含了多个算法，转换为集合去重
                algorithms = set(current_algorithm.split(", "))
                algorithms.add(algorithm)
                blueprint["algorithm"] = ", ".join(algorithms)
            else:
                # 否则，直接设置为当前算法
                blueprint["algorithm"] = algorithm
            # 更新max_sub_combinations为总组合数
            blueprint["max_sub_combinations"] = len(blueprint["combinations"]) + len(final_combinations)
        else:
            # 创建新蓝图
            blueprint = {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "total_combinations": len(final_combinations),
                "test_mode": test_mode,
                "max_sub_combinations": max_sub_combinations,
                "end_date": end_date,
                "algorithm": algorithm,
                "completed_combinations": 0,
                "failed_combinations": 0,
                "pending_combinations": len(final_combinations),
                "running_combinations": 0,
                "combinations": []
            }
        
        # 6. 添加现有组合到新蓝图中（如果有）
        if existing_blueprint:
            blueprint["combinations"] = existing_combinations.copy()
        
        # 7. 为新组合分配唯一ID并添加到蓝图
        for param in final_combinations:
            combination = {
                "id": next_id,
                "params": param,
                "status": "pending",  # pending, running, completed, failed
                "result": None,
                "started_at": None,
                "completed_at": None
            }
            blueprint["combinations"].append(combination)
            next_id += 1
        
        # 8. 更新蓝图统计信息
        self._update_blueprint_stats(blueprint)
        
        return blueprint
    
    def _update_blueprint_stats(self, blueprint: Dict[str, Any]):
        """
        更新蓝图的统计信息
        
        Args:
            blueprint: 蓝图数据结构
        """
        if not blueprint:
            raise ValueError("蓝图数据为空")
        
        total = len(blueprint['combinations'])
        completed = 0
        failed = 0
        running = 0
        
        for combo in blueprint['combinations']:
            if combo['status'] == 'completed':
                completed += 1
            elif combo['status'] == 'failed':
                failed += 1
            elif combo['status'] == 'running':
                running += 1
        
        pending = total - completed - failed - running
        
        blueprint['total_combinations'] = total
        blueprint['completed_combinations'] = completed
        blueprint['failed_combinations'] = failed
        blueprint['pending_combinations'] = pending
        blueprint['running_combinations'] = running
    
    def _save_blueprint(self, blueprint: Dict[str, Any], blueprint_file: str) -> str:
        """
        保存蓝图文件
        
        Args:
            blueprint: 蓝图数据结构
            blueprint_file: 保存路径
        
        Returns:
            str: 保存后的蓝图文件路径
        """
        # 更新最后修改时间
        blueprint['last_modified'] = datetime.now().isoformat()

        # 更新统计信息
        self._update_blueprint_stats(blueprint)

        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(blueprint_file)), exist_ok=True)

        # 使用原子写入：先写临时文件，再重命名
        # 这样可以防止写入过程中断电/中断导致文件损坏
        temp_file = blueprint_file + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, ensure_ascii=False, indent=2)

            # 在 Windows 上需要先删除目标文件（如果存在）
            if os.path.exists(blueprint_file):
                os.remove(blueprint_file)

            # 重命名临时文件为目标文件（原子操作）
            os.rename(temp_file, blueprint_file)
        except Exception:
            # 如果出错，清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise

        return blueprint_file
    
    def save_blueprint(self, blueprint: Dict[str, Any], blueprint_file: str = "parameter_blueprint.json") -> str:
        """
        保存蓝图文件（公共方法）
        
        Args:
            blueprint: 蓝图数据结构
            blueprint_file: 蓝图文件路径
        
        Returns:
            str: 保存后的蓝图文件路径
        """
        blueprint_path = os.path.join(self.current_dir, blueprint_file)
        return self._save_blueprint(blueprint, blueprint_path)
    
    def run_backtest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个参数组合的回测
        
        Args:
            params: 参数组合
            
        Returns:
            Dict[str, Any]: 回测结果
        """
        # 调用BacktestAdapter的run_backtest方法
        from backtest.backtest_adapter import BacktestAdapter
        return BacktestAdapter.run_backtest(params)
    
    def _load_blueprint(self, blueprint_file: str) -> Dict[str, Any]:
        """
        加载参数组合蓝图
        
        Args:
            blueprint_file: 蓝图文件路径
        
        Returns:
            Dict[str, Any]: 蓝图数据结构
            
        Raises:
            FileNotFoundError: 蓝图文件不存在
        """
        if not os.path.exists(blueprint_file):
            raise FileNotFoundError(f"蓝图文件不存在: {blueprint_file}")
        
        with open(blueprint_file, 'r', encoding='utf-8') as f:
            blueprint = json.load(f)
        
        return blueprint
    
    def get_next_combination(self, blueprint: Dict[str, Any]) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """
        获取下一个待处理的参数组合
        
        Args:
            blueprint: 蓝图数据结构
        
        Returns:
            Tuple[Optional[int], Optional[Dict[str, Any]]]: (组合ID, 参数组合)
        """
        if not blueprint:
            raise ValueError("蓝图数据为空")
        
        for combo in blueprint['combinations']:
            if combo['status'] == 'pending':
                return combo['id'], combo['params']
        
        return None, None
    
    def update_combination_status(self, blueprint: Dict[str, Any], combo_id: int, status: str, 
                                 result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        更新参数组合的状态和结果
        
        Args:
            blueprint: 蓝图数据结构
            combo_id: 组合ID
            status: 新状态 (pending, running, completed, failed)
            result: 回测结果（可选）
        
        Returns:
            Dict[str, Any]: 更新后的蓝图数据
        """
        if not blueprint:
            raise ValueError("蓝图数据为空")
        
        valid_statuses = ['pending', 'running', 'completed', 'failed']
        if status not in valid_statuses:
            raise ValueError(f"无效的状态值: {status}，有效状态: {', '.join(valid_statuses)}")
        
        # 查找并更新组合状态
        for combo in blueprint['combinations']:
            if combo['id'] == combo_id:
                combo['status'] = status
                
                if status == 'running':
                    combo['started_at'] = datetime.now().isoformat()
                
                if status == 'completed' or status == 'failed':
                    combo['completed_at'] = datetime.now().isoformat()
                    combo['result'] = result
                
                break
        
        # 更新蓝图统计信息
        self._update_blueprint_stats(blueprint)
        
        return blueprint
    
    def get_blueprint_stats(self, blueprint: Dict[str, Any]) -> Dict[str, int]:
        """
        获取蓝图统计信息
        
        Args:
            blueprint: 蓝图数据结构
        
        Returns:
            Dict[str, int]: 统计信息字典
        """
        if not blueprint:
            raise ValueError("蓝图数据为空")
        
        # 确保统计信息是最新的
        self._update_blueprint_stats(blueprint)
        
        return {
            "total": blueprint.get("total_combinations", 0),
            "pending": blueprint.get("pending_combinations", 0),
            "running": blueprint.get("running_combinations", 0),
            "completed": blueprint.get("completed_combinations", 0),
            "failed": blueprint.get("failed_combinations", 0)
        }
    
    def reset_blueprint(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        重置蓝图，将所有组合状态设为pending
        
        Args:
            blueprint: 蓝图数据结构
        
        Returns:
            Dict[str, Any]: 重置后的蓝图数据
        """
        if not blueprint:
            raise ValueError("蓝图数据为空")
        
        for combo in blueprint['combinations']:
            combo['status'] = 'pending'
            combo['result'] = None
            combo['started_at'] = None
            combo['completed_at'] = None
        
        # 更新统计信息
        self._update_blueprint_stats(blueprint)
        
        return blueprint
    
    def get_completed_results(self, blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取所有已完成组合的结果
        
        Args:
            blueprint: 蓝图数据结构
        
        Returns:
            List[Dict[str, Any]]: 已完成组合的结果列表
        """
        if not blueprint:
            raise ValueError("蓝图数据为空")
        
        results = []
        for combo in blueprint['combinations']:
            if combo['status'] == 'completed' and combo['result']:
                result = combo['result'].copy()
                result['combination_id'] = combo['id']
                result['started_at'] = combo['started_at']
                result['completed_at'] = combo['completed_at']
                result['params'] = combo['params']
                results.append(result)
        
        return results
    
    def count_completed_combinations(self, blueprint: Dict[str, Any]) -> int:
        """
        统计已完成的组合数
        
        Args:
            blueprint: 蓝图数据
        
        Returns:
            int: 已完成的组合数
        """
        if not blueprint:
            raise ValueError("蓝图数据为空")
        
        if blueprint.get('files'):
            # 分拆的蓝图文件
            completed = 0
            for sub_file_info in blueprint['files']:
                sub_file_path = os.path.join(os.path.dirname(self.blueprint_file), sub_file_info['file']) if hasattr(self, 'blueprint_file') else sub_file_info['file']
                if os.path.exists(sub_file_path):
                    with open(sub_file_path, 'r', encoding='utf-8') as f:
                        sub_blueprint = json.load(f)
                    completed += sum(1 for c in sub_blueprint['combinations'] if c['status'] == 'completed')
            return completed
        else:
            # 非分拆的蓝图文件
            return sum(1 for c in blueprint['combinations'] if c['status'] == 'completed')
    
    # 参数处理逻辑
    def _generate_weights_combinations(self, indicators: List[str], total: int, step: int, min_weight: int = 0, max_weight: int = 100) -> List[Dict[str, int]]:
        """
        生成权重组合
        
        Args:
            indicators: 指标列表
            total: 总权重
            step: 步长
            min_weight: 单个指标最小权重
            max_weight: 单个指标最大权重
            
        Returns:
            权重组合列表
        """
        from utils.weight_utils import generate_weights_combinations
        return generate_weights_combinations(indicators, total, step, min_weight, max_weight)
    
    def _generate_custom_weights_combinations(self, indicators: List[str], total: int, step: int, 
                                             focus_indicators: List[str] = None, focus_weight_factor: float = 1.5) -> List[Dict[str, int]]:
        """
        生成自定义权重组合
        
        Args:
            indicators: 指标列表
            total: 总权重
            step: 步长
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            
        Returns:
            自定义权重组合列表
        """
        from utils.weight_utils import generate_custom_weights_combinations
        return generate_custom_weights_combinations(indicators, total, step, focus_indicators, focus_weight_factor)
    
    def _generate_sub_weights_combinations(self, test_mode: bool = False, max_combinations: int = 10, 
                                          use_advanced_mode: bool = True) -> List[Dict[str, Dict[str, int]]]:
        """
        生成子权重组合
        
        Args:
            test_mode: 是否为测试模式
            max_combinations: 最大子权重组合数
            use_advanced_mode: 是否使用高级模式
            
        Returns:
            子权重组合列表
        """
        from utils.weight_utils import generate_sub_weights_combinations
        return generate_sub_weights_combinations(test_mode, max_combinations, use_advanced_mode)

    def _auto_clean_blueprint(self, blueprint_file: str,
                              max_total: int = 1000,
                              max_elite: int = 500):
        """
        自动清理蓝图文件,保持文件大小在合理范围

        Args:
            blueprint_file: 蓝图文件路径
            max_total: 蓝图保留的最大总组合数
            max_elite: 保留的最优组合数
        """
        try:
            # 加载蓝图
            blueprint = self._load_blueprint(blueprint_file)
            total = len(blueprint.get('combinations', []))

            # 如果未超过阈值,不处理
            if total <= max_total:
                return

            logger.info(f"\n=== 自动清理蓝图 ===")
            logger.info(f"当前组合数: {total}, 阈值: {max_total}")

            # 创建清理器并执行清理
            from utils.blueprint_cleaner import BlueprintCleaner
            cleaner = BlueprintCleaner(max_total=max_total, max_elite=max_elite, keep_failed=False)

            cleaned_blueprint, archive_data = cleaner.clean_blueprint(
                blueprint,
                blueprint_file=blueprint_file,
                auto_archive=True
            )

            # 保存清理后的蓝图
            self._save_blueprint(cleaned_blueprint, blueprint_file)

            logger.success(f"蓝图清理完成,保留 {len(cleaned_blueprint['combinations'])} 个组合")

        except Exception as e:
            logger.error(f"清理蓝图失败: {e}")

    def get_blueprint_cleanup_status(self, blueprint_file: str = "parameter_blueprint.json",
                                     max_total: int = 1000,
                                     max_elite: int = 500) -> Dict[str, Any]:
        """
        获取蓝图清理状态和建议

        Args:
            blueprint_file: 蓝图文件路径
            max_total: 蓝图保留的最大总组合数
            max_elite: 保留的最优组合数

        Returns:
            Dict[str, Any]: 清理状态和建议
        """
        try:
            blueprint = self._load_blueprint(os.path.join(self.current_dir, blueprint_file))

            from utils.blueprint_cleaner import BlueprintCleaner
            cleaner = BlueprintCleaner(max_total=max_total, max_elite=max_elite, keep_failed=False)

            recommendations = cleaner.get_cleanup_recommendations(blueprint)

            # 获取归档列表
            archives = cleaner.list_archives(self.current_dir)

            return {
                "blueprint_file": blueprint_file,
                "current_size": len(blueprint.get('combinations', [])),
                "threshold": max_total,
                "needs_cleanup": recommendations.get('needs_cleanup', False),
                "recommendations": recommendations,
                "archives_count": len(archives),
                "archives": archives[:10]  # 只返回最近10个归档
            }

        except Exception as e:
            logger.error(f"获取蓝图清理状态失败: {e}")
            return {
                "error": str(e)
            }