#!/usr/bin/env python
# coding=utf-8
"""
蓝图管理模块 - 提供参数组合蓝图的生成、加载、保存等功能
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class BlueprintManager:
    """
    蓝图管理器类 - 管理参数组合蓝图的生成、加载、保存和更新
    """
    
    def __init__(self, blueprint_file: str = "parameter_blueprint.json"):
        """
        初始化蓝图管理器
        
        Args:
            blueprint_file: 蓝图文件路径
        """
        self.blueprint_file = blueprint_file
        self.blueprint = None
    
    def generate_blueprint(self, param_combinations: List[Dict[str, Any]], 
                          test_mode: bool = False, 
                          max_sub_combinations: int = 10, 
                          end_date: str = '2025-12-25') -> Dict[str, Any]:
        """
        生成参数组合蓝图
        
        Args:
            param_combinations: 参数组合列表
            test_mode: 是否为测试模式
            max_sub_combinations: 最大子权重组合数
            end_date: 回测终点日期
        
        Returns:
            Dict[str, Any]: 蓝图数据结构
        """
        # 创建蓝图数据结构
        blueprint = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "total_combinations": len(param_combinations),
            "test_mode": test_mode,
            "max_sub_combinations": max_sub_combinations,
            "end_date": end_date,
            "completed_combinations": 0,
            "failed_combinations": 0,
            "pending_combinations": len(param_combinations),
            "running_combinations": 0,
            "combinations": []
        }
        
        # 为每个组合分配唯一ID并添加到蓝图
        for i, param in enumerate(param_combinations):
            combination = {
                "id": i + 1,
                "params": param,
                "status": "pending",  # pending, running, completed, failed
                "result": None,
                "started_at": None,
                "completed_at": None
            }
            blueprint["combinations"].append(combination)
        
        self.blueprint = blueprint
        return blueprint
    
    def load_blueprint(self, blueprint_file: Optional[str] = None) -> Dict[str, Any]:
        """
        加载参数组合蓝图
        
        Args:
            blueprint_file: 蓝图文件路径（可选，默认使用初始化时的文件）
        
        Returns:
            Dict[str, Any]: 蓝图数据结构
            
        Raises:
            FileNotFoundError: 蓝图文件不存在
        """
        if blueprint_file:
            self.blueprint_file = blueprint_file
        
        if not os.path.exists(self.blueprint_file):
            raise FileNotFoundError(f"蓝图文件不存在: {self.blueprint_file}")
        
        with open(self.blueprint_file, 'r', encoding='utf-8') as f:
            self.blueprint = json.load(f)
        
        return self.blueprint
    
    def save_blueprint(self, blueprint: Optional[Dict[str, Any]] = None, 
                      blueprint_file: Optional[str] = None) -> str:
        """
        保存蓝图文件
        
        Args:
            blueprint: 蓝图数据结构（可选，默认使用当前蓝图）
            blueprint_file: 保存路径（可选，默认使用当前文件路径）
        
        Returns:
            str: 保存后的蓝图文件路径
        """
        if blueprint:
            self.blueprint = blueprint
        
        if blueprint_file:
            self.blueprint_file = blueprint_file
        
        if not self.blueprint:
            raise ValueError("蓝图数据为空，无法保存")
        
        # 更新最后修改时间
        self.blueprint['last_modified'] = datetime.now().isoformat()
        
        # 更新统计信息
        self._update_blueprint_stats()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(self.blueprint_file)), exist_ok=True)
        
        with open(self.blueprint_file, 'w', encoding='utf-8') as f:
            json.dump(self.blueprint, f, ensure_ascii=False, indent=2)
        
        return self.blueprint_file
    
    def get_next_combination(self, blueprint: Optional[Dict[str, Any]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """
        获取下一个待处理的参数组合
        
        Args:
            blueprint: 蓝图数据结构（可选，默认使用当前蓝图）
        
        Returns:
            Tuple[Optional[int], Optional[Dict[str, Any]]]: (组合ID, 参数组合)
        """
        if not blueprint:
            blueprint = self.blueprint
        
        if not blueprint:
            raise ValueError("蓝图数据为空")
        
        for combo in blueprint['combinations']:
            if combo['status'] == 'pending':
                return combo['id'], combo['params']
        
        return None, None
    
    def update_combination_status(self, combo_id: int, status: str, 
                                 result: Optional[Dict[str, Any]] = None,
                                 blueprint: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        更新参数组合的状态和结果
        
        Args:
            combo_id: 组合ID
            status: 新状态 (pending, running, completed, failed)
            result: 回测结果（可选）
            blueprint: 蓝图数据结构（可选，默认使用当前蓝图）
        
        Returns:
            Dict[str, Any]: 更新后的蓝图数据
        """
        if not blueprint:
            blueprint = self.blueprint
        
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
    
    def get_blueprint_stats(self, blueprint: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        获取蓝图统计信息
        
        Args:
            blueprint: 蓝图数据结构（可选，默认使用当前蓝图）
        
        Returns:
            Dict[str, int]: 统计信息字典
        """
        if not blueprint:
            blueprint = self.blueprint
        
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
    
    def get_completed_results(self, blueprint: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        获取所有已完成组合的结果
        
        Args:
            blueprint: 蓝图数据结构（可选，默认使用当前蓝图）
        
        Returns:
            List[Dict[str, Any]]: 已完成组合的结果列表
        """
        if not blueprint:
            blueprint = self.blueprint
        
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
    
    def get_failed_combinations(self, blueprint: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        获取所有失败组合的信息
        
        Args:
            blueprint: 蓝图数据结构（可选，默认使用当前蓝图）
        
        Returns:
            List[Dict[str, Any]]: 失败组合的列表
        """
        if not blueprint:
            blueprint = self.blueprint
        
        if not blueprint:
            raise ValueError("蓝图数据为空")
        
        failed = []
        for combo in blueprint['combinations']:
            if combo['status'] == 'failed':
                failed.append(combo)
        
        return failed
    
    def reset_blueprint(self, blueprint: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        重置蓝图，将所有组合状态设为pending
        
        Args:
            blueprint: 蓝图数据结构（可选，默认使用当前蓝图）
        
        Returns:
            Dict[str, Any]: 重置后的蓝图数据
        """
        if not blueprint:
            blueprint = self.blueprint
        
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
    
    def _update_blueprint_stats(self, blueprint: Optional[Dict[str, Any]] = None):
        """
        更新蓝图的统计信息
        
        Args:
            blueprint: 蓝图数据结构（可选，默认使用当前蓝图）
        """
        if not blueprint:
            blueprint = self.blueprint
        
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
