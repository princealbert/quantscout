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
                               use_advanced_weights: bool = True, end_date: str = '2025-12-25') -> Dict[str, List[Any]]:
        """
        定义参数范围
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            use_advanced_weights: 是否使用高级权重配置模式
            end_date: 回测终点日期
            
        Returns:
            参数范围字典
        """
        pass
    
    @abstractmethod
    def generate_parameter_combinations(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                                       end_date: str = '2025-12-25') -> List[Dict[str, Any]]:
        """
        生成参数组合
        
        Args:
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
            
        Returns:
            参数组合列表
        """
        pass
    
    @abstractmethod
    def run_backtest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个参数组合的回测
        
        Args:
            params: 参数组合
            
        Returns:
            回测结果
        """
        pass
    
    @abstractmethod
    def optimize(self, test_mode: bool = False, max_sub_combinations: int = 10, 
                end_date: str = '2025-12-25', blueprint_file: Optional[str] = None) -> List[Dict[str, Any]]:
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
        import itertools
        
        combinations = []
        n = len(indicators)
        
        if n == 0:
            return []
        
        # 方法1: 笛卡尔积生成 - 基础方法
        ranges = [range(min_weight, max_weight + 1, step) for _ in range(n)]
        
        for weights in itertools.product(*ranges):
            if sum(weights) == total and all(w >= min_weight and w <= max_weight for w in weights):
                combinations.append(dict(zip(indicators, weights)))
        
        # 方法2: 如果笛卡尔积没有生成足够的组合，使用递归生成更灵活的组合
        if len(combinations) < 5 and n > 1:
            def recursive_generate(start_idx, remaining, current):
                if start_idx == n - 1:
                    if remaining >= min_weight and remaining <= max_weight:
                        current[indicators[start_idx]] = remaining
                        combinations.append(dict(current))
                    return
                
                min_val = min_weight
                max_val = min(max_weight, remaining - (n - 1 - start_idx) * min_weight)
                
                for weight in range(min_val, max_val + 1, step):
                    current[indicators[start_idx]] = weight
                    recursive_generate(start_idx + 1, remaining - weight, current.copy())
            
            recursive_generate(0, total, {})
        
        # 方法3: 添加一些特殊组合
        if n > 0 and len(combinations) < 10:
            # 添加平均分配组合
            avg_weight = total // n
            remainder = total % n
            avg_weights = [avg_weight] * n
            for i in range(remainder):
                avg_weights[i] += 1
            
            # 验证平均分配组合
            if sum(avg_weights) == total and all(w >= min_weight for w in avg_weights):
                combinations.append(dict(zip(indicators, avg_weights)))
            
            # 添加极端权重组合（一个指标占大部分权重）
            for i in range(min(3, n)):  # 最多为前3个指标生成极端组合
                extreme_weights = [min_weight] * n
                extreme_weights[i] = total - (n - 1) * min_weight
                
                # 验证极端权重组合
                if sum(extreme_weights) == total and extreme_weights[i] <= max_weight and all(w >= min_weight for w in extreme_weights):
                    combinations.append(dict(zip(indicators, extreme_weights)))
            
            # 添加两两指标占主导的组合
            if n >= 2:
                for i in range(n - 1):
                    for j in range(i + 1, n):
                        if len(combinations) >= 15:  # 控制总数
                            break
                        pair_weights = [min_weight] * n
                        pair_weights[i] = (total - (n - 2) * min_weight) // 2
                        pair_weights[j] = total - (n - 2) * min_weight - pair_weights[i]
                        
                        # 验证两两主导组合
                        if sum(pair_weights) == total and pair_weights[i] <= max_weight and pair_weights[j] <= max_weight and all(w >= min_weight for w in pair_weights):
                            combinations.append(dict(zip(indicators, pair_weights)))
        
        # 去重
        seen = set()
        unique_combinations = []
        for combo in combinations:
            # 再次验证组合的有效性
            if sum(combo.values()) == total and all(w >= min_weight and w <= max_weight for w in combo.values()):
                key = tuple(sorted(combo.items()))
                if key not in seen:
                    seen.add(key)
                    unique_combinations.append(combo)
        
        return unique_combinations
    
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
        import itertools
        import random

        # 定义每个主指标的子指标
        sub_indicators = {
            'kdj_j': ['j_0_20', 'j_-10_0', 'j_-20_-10', 'j_-30_-20', 'j_below_-30'],
            'position': ['above_white', 'between_lines', 'below_yellow'],
            'volume': ['big_volume', 'volume_anomaly', 'volume_breathing'],
            'fundamental': ['pe_positive', 'pe_low', 'market_cap', 'volume_threshold'],
            'trend': ['up_trend', 'volume_price_rise', 'volume_contraction']
        }

        # 测试模式：只生成一个简单的子权重组合
        if test_mode:
            simple_sub_weights = {}
            for main_indicator, subs in sub_indicators.items():
                num_subs = len(subs)
                # 计算每个子指标的权重（相等分配）
                weight_per_sub = 100 // num_subs
                remainder = 100 % num_subs

                weights = [weight_per_sub] * num_subs
                for i in range(remainder):
                    weights[i] += 1

                simple_sub_weights[main_indicator] = {'sub_weights': dict(zip(subs, weights))}

            return [simple_sub_weights]

        # 正式模式：生成可控数量的子权重组合

        # 为每个主指标生成子权重组合
        sub_weights_combinations = {}
        for main_indicator, subs in sub_indicators.items():
            # 根据子指标数量选择合适的步长
            num_subs = len(subs)
            if use_advanced_mode:
                # 高级模式：使用更小的步长
                if num_subs == 3:
                    step = 5
                elif num_subs == 4:
                    step = 5
                else:  # num_subs == 5
                    step = 5
            else:
                # 普通模式：使用较大步长
                if num_subs == 3:
                    step = 10
                elif num_subs == 4:
                    step = 10
                else:  # num_subs == 5
                    step = 10

            # 生成子权重组合，限制子权重范围为5%-90%
            sub_weights = self._generate_weights_combinations(subs, 100, step, min_weight=5, max_weight=90)

            # 提前筛选有效的子权重组合
            valid_sub_weights = []
            for sw in sub_weights:
                if sum(sw.values()) == 100 and all(5 <= w <= 90 for w in sw.values()):
                    valid_sub_weights.append(sw)

            sub_weights_combinations[main_indicator] = valid_sub_weights

        # 生成所有主指标的子权重组合的笛卡尔积
        main_indicators = list(sub_weights_combinations.keys())
        sub_weights_lists = [sub_weights_combinations[ind] for ind in main_indicators]

        # 计算总笛卡尔积数量
        total_cartesian = 1
        for sub_list in sub_weights_lists:
            total_cartesian *= len(sub_list)

        # 生成笛卡尔积，但限制数量
        combinations = []

        # 高级模式：使用多种策略生成组合
        if use_advanced_mode and total_cartesian > max_combinations:
            # 策略1: 分层随机采样
            stratified_samples = []

            # 为每个主指标选择固定数量的子权重组合
            samples_per_indicator = 3  # 每个主指标至少采样3个组合

            # 为每个主指标创建子权重组合池
            indicator_pools = {}
            for main_ind, sub_weights_list in sub_weights_combinations.items():
                # 为每个主指标随机选择samples_per_indicator个组合
                if len(sub_weights_list) > samples_per_indicator:
                    indicator_pools[main_ind] = random.sample(sub_weights_list, samples_per_indicator)
                else:
                    indicator_pools[main_ind] = sub_weights_list.copy()

            # 生成这些组合的笛卡尔积
            stratified_cartesian = list(itertools.product(*[indicator_pools[ind] for ind in main_indicators]))

            # 如果生成的组合过多，再次随机采样
            if len(stratified_cartesian) > max_combinations:
                stratified_samples = random.sample(stratified_cartesian, max_combinations)
            else:
                stratified_samples = stratified_cartesian

            # 将采样结果转换为标准格式
            stratified_combinations = []
            for combo in stratified_samples:
                sub_weights_config = {}
                for i, main_indicator in enumerate(main_indicators):
                    sub_weights_config[main_indicator] = {'sub_weights': combo[i]}
                stratified_combinations.append(sub_weights_config)

            combinations.extend(stratified_combinations)

            # 策略2: 变异策略
            if len(combinations) < max_combinations and len(combinations) > 0:
                mutation_count = min(5, max_combinations - len(combinations))

                for _ in range(mutation_count):
                    # 随机选择一个基础组合
                    base_combo = random.choice(combinations)
                    mutated_combo = base_combo.copy()

                    # 随机选择一个主指标进行变异
                    mutate_indicator = random.choice(main_indicators)
                    mutate_subs = sub_indicators[mutate_indicator]
                    num_subs = len(mutate_subs)

                    # 获取当前子权重
                    current_weights = base_combo[mutate_indicator]['sub_weights']

                    # 随机选择两个子指标进行权重交换或调整
                    if num_subs >= 2:
                        i, j = random.sample(range(num_subs), 2)
                        sub_i = mutate_subs[i]
                        sub_j = mutate_subs[j]

                        # 随机调整权重（±5%范围内）
                        adjust_amount = random.randint(1, 10)
                        if random.random() > 0.5:
                            # 增加i，减少j
                            if current_weights[sub_i] + adjust_amount <= 90 and current_weights[sub_j] - adjust_amount >= 5:
                                current_weights[sub_i] += adjust_amount
                                current_weights[sub_j] -= adjust_amount
                        else:
                            # 增加j，减少i
                            if current_weights[sub_j] + adjust_amount <= 90 and current_weights[sub_i] - adjust_amount >= 5:
                                current_weights[sub_j] += adjust_amount
                                current_weights[sub_i] -= adjust_amount

                    # 验证变异后的组合是否有效
                    if sum(current_weights.values()) == 100 and all(w > 0 for w in current_weights.values()):
                        # 更新变异后的组合
                        mutated_combo[mutate_indicator]['sub_weights'] = current_weights.copy()
                        combinations.append(mutated_combo)
        else:
            # 普通模式：遍历笛卡尔积
            current = 0
            for combination in itertools.product(*sub_weights_lists):
                sub_weights_config = {}
                for i, main_indicator in enumerate(main_indicators):
                    sub_weights_config[main_indicator] = {'sub_weights': combination[i]}
                combinations.append(sub_weights_config)

                current += 1
                if current >= max_combinations:
                    break

        # 去重
        seen = set()
        unique_combinations = []
        for combo in combinations:
            key = tuple(sorted((k, tuple(sorted(v['sub_weights'].items()))) for k, v in combo.items()))
            if key not in seen:
                seen.add(key)
                unique_combinations.append(combo)

        return unique_combinations[:max_combinations]
    
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