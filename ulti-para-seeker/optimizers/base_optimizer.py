#!/usr/bin/env python
# coding=utf-8
"""
基础优化器接口 - 所有优化器的基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

class BaseOptimizer(ABC):
    """
    基础优化器抽象类
    """
    
    def __init__(self):
        """初始化优化器"""
        self.initial_capital = 60000  # 固定初始资金
        self.results = []
        self.start_time = None
        self.end_time = None
        # 回测结果缓存 - 使用字典存储，键为参数组合的哈希值，值为回测结果
        self.backtest_cache = {}
    
    @abstractmethod
    def define_parameter_ranges(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                               use_advanced_weights: bool = True, end_date: str = '2025-12-25',
                               focus_indicators: List[str] = None, focus_weight_factor: float = 1.5, initial_capital: int = 60000,
                               backtest_days: int = 90) -> Dict[str, List[Any]]:
        """
        定义参数范围
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            use_advanced_weights: 是否使用高级权重配置模式
            end_date: 回测终点日期
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            initial_capital: 初始资金
            backtest_days: 回测天数
            
        Returns:
            参数范围字典
        """
        pass
    
    @abstractmethod
    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                       end_date: str = '2025-12-25', focus_indicators: List[str] = None, 
                                       focus_weight_factor: float = 1.5, backtest_days: int = 90) -> List[Dict[str, Any]]:
        """
        生成参数组合
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            focus_indicators: 需要重点关注的指标列表
            focus_weight_factor: 重点指标的权重放大倍数
            backtest_days: 回测天数
            
        Returns:
            参数组合列表
        """
        pass
    
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
            # 使用参数组合中的initial_capital，如果不存在则使用默认值
            initial_capital = params.get('initial_capital', self.initial_capital)
            frontend_config = {
                'backtest': {
                    'initial_capital': initial_capital,
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
                
                # 直接导入并调用backtest_modified的run_optimizer_backtest函数，传入配置对象
                from backtest_modified import run_optimizer_backtest as run_backtest_func
                # 直接获取回测结果，而不是依赖文件
                report = run_backtest_func(config=frontend_config)
                logger.info(f"直接从回测函数获取到结果: {'成功' if report else '空结果'}")
            except Exception as e:
                logger.error(f"调用回测函数失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 检查是否已经从回测函数获取到结果
            if not report or isinstance(report, bool):
                logger.warning("从回测函数获取的结果为空或无效，尝试从文件读取")
                
                # 等待回测结果文件生成（给回测系统一些时间）
                max_wait = 10
                wait_count = 0
                
                # 检查多个可能的报告文件位置和名称
                possible_report_files = [
                    os.path.join(project_root, 'backtest_report.json'),
                    os.path.join(os.path.dirname(project_root), 'backtest_report.json'),
                    os.path.join(os.path.dirname(os.path.dirname(project_root)), 'backtest_report.json')
                ]
                
                # 检查是否有报告文件生成
                report_file = None
                for possible_file in possible_report_files:
                    if os.path.exists(possible_file):
                        report_file = possible_file
                        logger.info(f"找到回测报告文件: {report_file}")
                        break
                
                # 如果没有立即找到，等待一段时间
                if not report_file:
                    logger.info("等待回测报告文件生成...")
                    wait_count = 0
                    while wait_count < max_wait:
                        import time
                        time.sleep(0.5)  # 500ms延迟
                        wait_count += 1
                        for possible_file in possible_report_files:
                            if os.path.exists(possible_file):
                                report_file = possible_file
                                logger.info(f"找到回测报告文件: {report_file}")
                                break
                        if report_file:
                            break
                
                if report_file and os.path.exists(report_file):
                    try:
                        with open(report_file, 'r', encoding='utf-8') as f:
                            report = json.load(f)
                        logger.info(f"成功读取回测报告，包含 {len(report)} 个键值对")
                        logger.debug(f"报告内容: {json.dumps(report, ensure_ascii=False, indent=2)}")
                        
                        # 添加短暂延迟，确保其他进程有时间读取文件后再删除
                        import time
                        time.sleep(0.1)
                        
                        # 删除结果文件，避免影响下一次回测
                        os.unlink(report_file)
                        logger.info(f"已删除回测报告文件: {report_file}")
                    except Exception as e:
                        logger.error(f"读取报告文件失败: {e}")
                        report = {}
                else:
                    logger.warning(f"未找到回测报告文件，检查了位置: {possible_report_files}")
                    report = {}
            
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
            from utils.logger import logger
            import os
            pid = os.getpid()
            logger.info(f"✅ 进程 {pid} 回测完成")
    
    @abstractmethod
    def optimize(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                end_date: str = '2025-12-25', blueprint_file: Optional[str] = None, initial_capital: int = 60000) -> List[Dict[str, Any]]:
        """
        执行优化
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            algorithm: 优化算法
            end_date: 回测终点日期
            stop_profit_min: 止盈最小值
            stop_profit_max: 止盈最大值
            stop_profit_step: 止盈步长
            stop_loss_min: 止损最小值
            stop_loss_max: 止损最大值
            stop_loss_step: 止损步长
            weight_step: 权重步长
            use_advanced_weights: 是否使用高级权重配置
            focus_indicators: 重点指标列表
            focus_weight_factor: 重点指标权重因子
            blueprint_file: 蓝图文件路径（用于断点续传）
            initial_capital: 初始资金
            
        Returns:
            优化结果列表
        """
        pass
    
    def _validate_parameter_combination(self, params: Dict[str, Any]) -> bool:
        """
        验证参数组合的有效性
        
        Args:
            params: 参数组合
            
        Returns:
            参数组合是否有效
        """
        try:
            # 1. 验证止盈止损逻辑
            stop_profit = params.get('stop_profit_ratio', 0)
            stop_loss = params.get('stop_loss_ratio', 0)
            
            if stop_profit <= stop_loss:
                return False
            
            if not (0 < stop_profit <= 1):
                return False
            
            if not (-1 <= stop_loss < 0):
                return False
            
            # 2. 验证权重配置
            weights = params.get('weights_config', {})
            total_weight = sum(weights.values())
            
            if total_weight != 100:
                return False
            
            # 核心指标权重必须为正数，deepv权重可以为零
            core_indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
            for ind in core_indicators:
                if weights.get(ind, 0) <= 0:
                    return False
            
            # 3. 验证子权重配置
            sub_weights = params.get('sub_weights_config', {})
            for main_indicator, sub_config in sub_weights.items():
                if 'sub_weights' not in sub_config:
                    return False
                
                sub_weights_dict = sub_config['sub_weights']
                if sum(sub_weights_dict.values()) != 100 or any(w <= 0 for w in sub_weights_dict.values()):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _filter_parameter_combinations(self, combinations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        筛选有效的参数组合
        
        Args:
            combinations: 参数组合列表
            
        Returns:
            有效参数组合列表
        """
        valid_combinations = []
        for params in combinations:
            if self._validate_parameter_combination(params):
                valid_combinations.append(params)
        return valid_combinations
    
    # 蓝图管理相关方法
    def generate_blueprint(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                          algorithm: str = "暴力搜索", end_date: str = '2025-12-25', 
                          stop_profit_min: int = 3, stop_profit_max: int = 15, stop_profit_step: int = 2,
                          stop_loss_min: int = 1, stop_loss_max: int = 5, stop_loss_step: int = 1,
                          weight_step: int = 10, use_advanced_weights: bool = True,
                          focus_indicators: List[str] = None, focus_weight_factor: float = 1.5,
                          blueprint_file: str = "parameter_blueprint.json") -> str:
        """
        生成参数组合蓝图文件
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            blueprint_file: 蓝图文件路径
            
        Returns:
            蓝图文件路径
        """
        import os
        import json
        
        # 生成所有参数组合
        param_combinations = self.generate_parameter_combinations(test_mode, max_sub_combinations, end_date)
        
        # 创建蓝图数据结构
        blueprint = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "total_combinations": len(param_combinations),
            "test_mode": test_mode,
            "max_sub_combinations": max_sub_combinations,
            "end_date": end_date,
            "combinations": []
        }
        
        # 为每个组合分配唯一ID并添加到蓝图
        for i, param in enumerate(param_combinations):
            combination = {
                "id": i + 1,
                "params": param,
                "status": "pending",  # pending, running, completed, failed
                "result": None
            }
            blueprint["combinations"].append(combination)
        
        # 保存蓝图文件
        # 使用当前文件的父目录作为项目根目录，避免依赖不存在的path_utils模块
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        blueprint_path = os.path.join(project_root, blueprint_file)
        with open(blueprint_path, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, ensure_ascii=False, indent=2)
        
        return blueprint_path
    
    def load_blueprint(self, blueprint_file: str = "parameter_blueprint.json") -> Dict[str, Any]:
        """
        加载参数组合蓝图文件
        
        Args:
            blueprint_file: 蓝图文件路径
            
        Returns:
            蓝图数据
        """
        import os
        import json
        
        # 使用当前文件的父目录作为项目根目录，避免依赖不存在的path_utils模块
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        blueprint_path = os.path.join(project_root, blueprint_file)
        
        if not os.path.exists(blueprint_path):
            raise FileNotFoundError(f"蓝图文件不存在: {blueprint_path}")
        
        with open(blueprint_path, 'r', encoding='utf-8') as f:
            blueprint = json.load(f)
        
        return blueprint
    
    def get_next_combination(self, blueprint: Dict[str, Any]) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """
        获取下一个待处理的参数组合
        
        Args:
            blueprint: 蓝图数据
            
        Returns:
            (组合ID, 参数组合)
        """
        for combo in blueprint['combinations']:
            if combo['status'] == 'pending':
                return combo['id'], combo['params']
        return None, None
    
    def update_combination_status(self, blueprint: Dict[str, Any], combo_id: int, status: str, 
                                 result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        更新参数组合的状态和结果
        
        Args:
            blueprint: 蓝图数据
            combo_id: 组合ID
            status: 新状态
            result: 回测结果
            
        Returns:
            更新后的蓝图数据
        """
        for combo in blueprint['combinations']:
            if combo['id'] == combo_id:
                combo['status'] = status
                combo['result'] = result
                if result is not None:
                    combo['completed_at'] = datetime.now().isoformat()
                break
        return blueprint
    
    def save_blueprint(self, blueprint: Dict[str, Any], blueprint_file: str = "parameter_blueprint.json") -> str:
        """
        保存蓝图文件
        
        Args:
            blueprint: 蓝图数据
            blueprint_file: 蓝图文件路径
            
        Returns:
            保存后的蓝图文件路径
        """
        import os
        import json
        
        # 使用当前文件的父目录作为项目根目录，避免依赖不存在的path_utils模块
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        blueprint_path = os.path.join(project_root, blueprint_file)
        
        # 更新最后修改时间
        blueprint['last_modified'] = datetime.now().isoformat()
        
        with open(blueprint_path, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, ensure_ascii=False, indent=2)
        
        return blueprint_path
    
    def _generate_weights_combinations(self, indicators: List[str], total: int, step: int, 
                                      min_weight: int = 0, max_weight: int = 100) -> List[Dict[str, int]]:
        """
        生成权重组合（使用weight_utils模块）
        
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
    
    def _generate_sub_weights_combinations(self, test_mode: bool = False, max_combinations: int = 10, 
                                          use_advanced_mode: bool = True) -> List[Dict[str, Dict[str, int]]]:
        """
        生成子权重组合（使用weight_utils模块）

        Args:
            test_mode: 是否为测试模式
            max_combinations: 最大子权重组合数
            use_advanced_mode: 是否使用高级模式

        Returns:
            子权重组合列表
        """
        from utils.weight_utils import generate_sub_weights_combinations
        return generate_sub_weights_combinations(test_mode, max_combinations, use_advanced_mode)
    
    def _get_cache_key(self, params: Dict[str, Any]) -> str:
        """
        生成回测结果缓存的唯一键
        
        Args:
            params: 参数组合
            
        Returns:
            唯一的缓存键字符串
        """
        # 对参数进行排序并生成稳定的字符串表示
        def _sort_dict(d):
            if isinstance(d, dict):
                return tuple(sorted((k, _sort_dict(v)) for k, v in d.items()))
            elif isinstance(d, list):
                return tuple(_sort_dict(item) for item in d)
            else:
                return d
        
        # 排序后的参数元组
        sorted_params = _sort_dict(params)
        # 使用哈希值作为缓存键
        return str(hash(sorted_params))
    
    def _get_cached_result(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从缓存中获取回测结果
        
        Args:
            params: 参数组合
            
        Returns:
            缓存的回测结果，如果不存在则返回None
        """
        cache_key = self._get_cache_key(params)
        return self.backtest_cache.get(cache_key, None)
    
    def _cache_result(self, params: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        将回测结果存入缓存
        
        Args:
            params: 参数组合
            result: 回测结果
        """
        cache_key = self._get_cache_key(params)
        self.backtest_cache[cache_key] = result
    
    def clear_cache(self) -> None:
        """
        清空回测结果缓存
        """
        self.backtest_cache.clear()