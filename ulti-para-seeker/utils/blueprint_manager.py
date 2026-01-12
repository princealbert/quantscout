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
            blueprint_file: 蓝图文件路径（可以是绝对路径或相对路径）
        """
        # 如果传入的是相对路径，将其转换为绝对路径
        # 使用当前工作目录作为基准
        if not os.path.isabs(blueprint_file):
            self.blueprint_file = os.path.join(os.getcwd(), blueprint_file)
        else:
            self.blueprint_file = blueprint_file
        self.blueprint = None
    
    def generate_blueprint(self, param_combinations: List[Dict[str, Any]], 
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
        from .parameter_utils import generate_param_hash, remove_duplicate_combinations
        
        # 1. 去重新生成的参数组合
        unique_new_combinations = remove_duplicate_combinations(param_combinations)
        
        # 2. 根据算法类型选择最终使用的参数组合
        final_combinations = unique_new_combinations.copy()
        
        if algorithm in ["遗传算法", "粒子群算法"] and len(final_combinations) > max_sub_combinations:
            # 遗传算法和粒子群算法只使用固定数量的组合
            import random
            random.shuffle(final_combinations)
            final_combinations = final_combinations[:max_sub_combinations]
        
        # 3. 如果有现有蓝图，移除与现有蓝图中重复的组合
        existing_hashes = set()
        existing_combinations = []
        next_id = 1
        
        if existing_blueprint:
            # 提取现有蓝图中的组合哈希
            for combo in existing_blueprint["combinations"]:
                existing_hashes.add(generate_param_hash(combo["params"]))
                existing_combinations.append(combo)
                next_id = max(next_id, combo["id"] + 1)
        
        # 4. 移除与现有蓝图重复的新组合
        new_unique_combinations = []
        for combo in final_combinations:
            combo_hash = generate_param_hash(combo)
            if combo_hash not in existing_hashes:
                new_unique_combinations.append(combo)
        
        # 5. 创建蓝图数据结构
        if existing_blueprint:
            # 增量更新现有蓝图
            blueprint = existing_blueprint.copy()
            blueprint["last_modified"] = datetime.now().isoformat()
            blueprint["algorithm"] = algorithm
        else:
            # 创建新蓝图
            blueprint = {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "total_combinations": len(new_unique_combinations),
                "test_mode": test_mode,
                "max_sub_combinations": max_sub_combinations,
                "end_date": end_date,
                "algorithm": algorithm,
                "completed_combinations": 0,
                "failed_combinations": 0,
                "pending_combinations": len(new_unique_combinations),
                "running_combinations": 0,
                "combinations": []
            }
        
        # 6. 为新组合分配唯一ID并添加到蓝图
        for param in new_unique_combinations:
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
        
        # 7. 更新蓝图统计信息
        if existing_blueprint:
            # 重新计算统计信息
            self._update_blueprint_stats(blueprint)
        
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
            # 如果传入的是相对路径，将其转换为绝对路径
            if not os.path.isabs(blueprint_file):
                self.blueprint_file = os.path.join(os.getcwd(), blueprint_file)
            else:
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
            # 如果传入的是相对路径，将其转换为绝对路径
            if not os.path.isabs(blueprint_file):
                self.blueprint_file = os.path.join(os.getcwd(), blueprint_file)
            else:
                self.blueprint_file = blueprint_file

        if not self.blueprint:
            raise ValueError("蓝图数据为空，无法保存")

        # 更新最后修改时间
        self.blueprint['last_modified'] = datetime.now().isoformat()

        # 更新统计信息
        self._update_blueprint_stats()

        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(self.blueprint_file)), exist_ok=True)

        # 使用原子写入：先写临时文件，再重命名
        # 这样可以防止写入过程中断电/中断导致文件损坏
        temp_file = self.blueprint_file + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.blueprint, f, ensure_ascii=False, indent=2)

            # 在 Windows 上需要先删除目标文件（如果存在）
            if os.path.exists(self.blueprint_file):
                os.remove(self.blueprint_file)

            # 重命名临时文件为目标文件（原子操作）
            os.rename(temp_file, self.blueprint_file)
        except Exception:
            # 如果出错，清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise

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

    def reset_and_save_blueprint(self, blueprint: Optional[Dict[str, Any]] = None,
                                blueprint_file: Optional[str] = None) -> str:
        """
        重置蓝图并保存到文件

        Args:
            blueprint: 蓝图数据结构（可选，默认使用当前蓝图）
            blueprint_file: 保存路径（可选，默认使用当前文件路径）

        Returns:
            str: 保存后的蓝图文件路径
        """
        # 重置蓝图
        reset_blueprint = self.reset_blueprint(blueprint)

        # 保存到文件
        return self.save_blueprint(reset_blueprint, blueprint_file)
    
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
    
    def list_blueprints(self, directory: str = None) -> List[Dict[str, Any]]:
        """
        列出所有蓝图文件

        Args:
            directory: 蓝图文件所在目录，默认为当前工作目录

        Returns:
            List[Dict[str, Any]]: 蓝图文件列表，每个文件包含filename、size_kb、total_combinations、algorithm等信息
        """
        blueprints = []

        # 使用指定目录或当前工作目录
        search_dir = directory or os.getcwd()

        # 遍历目录下的蓝图文件
        for filename in os.listdir(search_dir):
            if filename.startswith('parameter_blueprint') and filename.endswith('.json'):
                file_path = os.path.join(search_dir, filename)
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
                    print(f"读取蓝图文件失败: {filename}, 错误: {e}")

        # 按生成时间降序排序
        blueprints.sort(key=lambda x: x.get('generated_at', ''), reverse=True)

        return blueprints
    
    def clear_blueprints(self, directory: str = None) -> int:
        """
        清除所有蓝图文件

        Args:
            directory: 蓝图文件所在目录，默认为当前工作目录

        Returns:
            int: 删除的文件数量
        """
        deleted_count = 0

        # 使用指定目录或当前工作目录
        search_dir = directory or os.getcwd()

        # 遍历目录下的蓝图文件
        for filename in os.listdir(search_dir):
            if filename.startswith('parameter_blueprint') and filename.endswith('.json'):
                file_path = os.path.join(search_dir, filename)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"已删除蓝图文件: {filename}")
                except Exception as e:
                    print(f"删除蓝图文件失败: {filename}, 错误: {e}")

        return deleted_count
        
    def delete_blueprint(self, filename: str, directory: str = None) -> bool:
        """
        删除特定的蓝图文件

        Args:
            filename: 要删除的蓝图文件名
            directory: 蓝图文件所在目录，默认为当前工作目录

        Returns:
            bool: 删除是否成功
        """
        # 检查文件名格式是否合法
        if not (filename.startswith('parameter_blueprint') and filename.endswith('.json')):
            print(f"无效的蓝图文件名: {filename}")
            return False

        # 使用指定目录或当前工作目录
        search_dir = directory or os.getcwd()
        file_path = os.path.join(search_dir, filename)
        
        try:
            # 检查文件是否存在
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"已删除蓝图文件: {filename}")
                return True
            else:
                print(f"蓝图文件不存在: {filename}")
                return False
        except Exception as e:
            print(f"删除蓝图文件失败: {filename}, 错误: {e}")
            return False
    
    def count_completed_combinations(self, blueprint: Dict[str, Any] = None) -> int:
        """
        统计已完成的组合数
        
        Args:
            blueprint: 蓝图数据
            
        Returns:
            int: 已完成的组合数
        """
        if not blueprint:
            blueprint = self.blueprint
        
        if not blueprint:
            raise ValueError("蓝图数据为空")
        
        if blueprint.get('files'):
            # 分拆的蓝图文件
            completed = 0
            for sub_file_info in blueprint['files']:
                sub_file_path = os.path.join(os.path.dirname(self.blueprint_file), sub_file_info['file'])
                if os.path.exists(sub_file_path):
                    with open(sub_file_path, 'r', encoding='utf-8') as f:
                        sub_blueprint = json.load(f)
                    completed += sum(1 for c in sub_blueprint['combinations'] if c['status'] == 'completed')
            return completed
        else:
            # 非分拆的蓝图文件
            return sum(1 for c in blueprint['combinations'] if c['status'] == 'completed')
    

