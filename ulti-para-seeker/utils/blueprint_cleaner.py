#!/usr/bin/env python
# coding=utf-8
"""
蓝图清理和优化模块 - 自动清理低价值组合,保持蓝图文件在合理大小
"""

import json
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path


class BlueprintCleaner:
    """
    蓝图清理器 - 用于清理和优化蓝图文件
    """

    def __init__(self, max_total: int = 1000, max_elite: int = 500,
                 keep_failed: bool = False, archive_dir: str = "blueprint_archives"):
        """
        初始化蓝图清理器

        Args:
            max_total: 蓝图保留的最大总组合数
            max_elite: 保留的最优组合数
            keep_failed: 是否保留失败组合
            archive_dir: 归档目录名称
        """
        self.max_total = max_total
        self.max_elite = max_elite
        self.keep_failed = keep_failed
        self.archive_dir = archive_dir

    def clean_blueprint(self, blueprint: Dict[str, Any],
                        blueprint_file: str = None,
                        auto_archive: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        清理蓝图文件,保留最有价值的组合

        Args:
            blueprint: 蓝图数据
            blueprint_file: 蓝图文件路径(用于归档)
            auto_archive: 是否自动归档被删除的组合

        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (清理后的蓝图, 归档数据)
        """
        if not blueprint or 'combinations' not in blueprint:
            raise ValueError("蓝图数据格式错误")

        combinations = blueprint['combinations']
        total = len(combinations)

        # 如果组合数未超过阈值,不处理
        if total <= self.max_total:
            return blueprint.copy(), {}

        print(f"\n=== 开始清理蓝图 ===")
        print(f"当前组合数: {total}")
        print(f"目标最大组合数: {self.max_total}")
        print(f"需删除: {total - self.max_total} 个组合")

        # 分类整理组合
        completed = []
        failed = []
        pending = []
        running = []

        for combo in combinations:
            status = combo.get('status', 'pending')
            if status == 'completed':
                completed.append(combo)
            elif status == 'failed':
                failed.append(combo)
            elif status == 'pending':
                pending.append(combo)
            elif status == 'running':
                running.append(combo)

        print(f"- 已完成: {len(completed)}")
        print(f"- 失败: {len(failed)}")
        print(f"- 待处理: {len(pending)}")
        print(f"- 运行中: {len(running)}")

        # 1. 筛选有价值的已完成组合
        if len(completed) > self.max_elite:
            from utils.multi_objective_scorer import get_scorer
            scorer = get_scorer()

            # 对已完成组合进行评分排序
            ranked = scorer.rank_combinations(completed)

            # 保留前N个最优组合
            kept_completed = ranked[:self.max_elite]
            archived_completed = ranked[self.max_elite:]

            print(f"- 已完成组合: 保留 {len(kept_completed)}, 归档 {len(archived_completed)}")
        else:
            kept_completed = completed
            archived_completed = []

        # 2. 处理失败组合(可选保留)
        if self.keep_failed:
            kept_failed = failed
            archived_failed = []
        else:
            kept_failed = []
            archived_failed = failed
            print(f"- 失败组合: 归档 {len(archived_failed)}")

        # 3. 处理待处理和运行中的组合
        # 如果总组合数仍然超过max_total,需要进一步删减
        current_total = len(kept_completed) + len(kept_failed) + len(pending) + len(running)

        if current_total > self.max_total:
            # 优先保留待处理的组合
            available_slots = self.max_total - len(kept_completed) - len(kept_failed) - len(running)

            if len(pending) > available_slots:
                kept_pending = pending[:available_slots]
                archived_pending = pending[available_slots:]
                print(f"- 待处理组合: 保留 {len(kept_pending)}, 归档 {len(archived_pending)}")
            else:
                kept_pending = pending
                archived_pending = []
        else:
            kept_pending = pending
            archived_pending = []

        # 运行中组合全部保留(可能是正在执行的任务)
        kept_running = running
        archived_running = []

        # 构建归档数据
        archived_combinations = archived_completed + archived_failed + archived_pending + archived_running

        archive_data = {
            "archived_at": datetime.now().isoformat(),
            "original_total": total,
            "archived_count": len(archived_combinations),
            "archive_reason": "blueprint_size_exceeded",
            "combinations": archived_combinations
        }

        # 构建清理后的蓝图
        cleaned_blueprint = blueprint.copy()
        cleaned_blueprint['combinations'] = kept_completed + kept_failed + kept_pending + kept_running
        cleaned_blueprint['last_cleaned'] = datetime.now().isoformat()
        cleaned_blueprint['archived_count'] = len(archived_combinations)

        # 更新统计信息
        self._update_blueprint_stats(cleaned_blueprint)

        print(f"=== 清理完成 ===")
        print(f"清理后组合数: {len(cleaned_blueprint['combinations'])}")
        print(f"归档组合数: {len(archived_combinations)}")
        print(f"压缩率: {100 * (total - len(cleaned_blueprint['combinations'])) / total:.1f}%")

        # 自动归档
        if auto_archive and blueprint_file and archived_combinations:
            self._archive_blueprint(archive_data, blueprint_file)

        return cleaned_blueprint, archive_data

    def _update_blueprint_stats(self, blueprint: Dict[str, Any]):
        """更新蓝图统计信息"""
        combinations = blueprint.get('combinations', [])
        total = len(combinations)

        completed = sum(1 for c in combinations if c.get('status') == 'completed')
        failed = sum(1 for c in combinations if c.get('status') == 'failed')
        running = sum(1 for c in combinations if c.get('status') == 'running')
        pending = total - completed - failed - running

        blueprint['total_combinations'] = total
        blueprint['completed_combinations'] = completed
        blueprint['failed_combinations'] = failed
        blueprint['pending_combinations'] = pending
        blueprint['running_combinations'] = running
        blueprint['last_modified'] = datetime.now().isoformat()

    def _archive_blueprint(self, archive_data: Dict[str, Any], blueprint_file: str):
        """
        将归档数据保存到归档文件

        Args:
            archive_data: 归档数据
            blueprint_file: 原蓝图文件路径
        """
        try:
            # 创建归档目录
            blueprint_dir = os.path.dirname(os.path.abspath(blueprint_file))
            archive_path = os.path.join(blueprint_dir, self.archive_dir)

            Path(archive_path).mkdir(parents=True, exist_ok=True)

            # 生成归档文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = os.path.join(archive_path, f"archive_{timestamp}.json")

            # 保存归档文件
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, ensure_ascii=False, indent=2)

            print(f"归档文件已保存: {archive_file}")

        except Exception as e:
            print(f"归档失败: {e}")

    def archive_old_failed_combinations(self, blueprint: Dict[str, Any],
                                        days_threshold: int = 30,
                                        blueprint_file: str = None) -> Dict[str, Any]:
        """
        归档旧的失败组合

        Args:
            blueprint: 蓝图数据
            days_threshold: 失败组合保留天数阈值
            blueprint_file: 蓝图文件路径(用于归档)

        Returns:
            Dict[str, Any]: 归档数据
        """
        now = datetime.now()
        threshold_date = (now - datetime.timedelta(days=days_threshold)).isoformat()

        kept_combinations = []
        failed_to_archive = []

        for combo in blueprint.get('combinations', []):
            if combo.get('status') == 'failed':
                completed_at = combo.get('completed_at', '')
                if completed_at and completed_at < threshold_date:
                    failed_to_archive.append(combo)
                else:
                    kept_combinations.append(combo)
            else:
                kept_combinations.append(combo)

        if failed_to_archive:
            archive_data = {
                "archived_at": now.isoformat(),
                "archive_reason": "old_failed_combinations",
                "days_threshold": days_threshold,
                "archived_count": len(failed_to_archive),
                "combinations": failed_to_archive
            }

            blueprint['combinations'] = kept_combinations
            self._update_blueprint_stats(blueprint)

            if blueprint_file:
                self._archive_blueprint(archive_data, blueprint_file)

            print(f"已归档 {len(failed_to_archive)} 个失败组合(超过{days_threshold}天)")

            return archive_data

        return {}

    def get_cleanup_recommendations(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取蓝图清理建议

        Args:
            blueprint: 蓝图数据

        Returns:
            Dict[str, Any]: 清理建议
        """
        combinations = blueprint.get('combinations', [])
        total = len(combinations)

        if total <= self.max_total:
            return {
                "needs_cleanup": False,
                "reason": "蓝图文大小未超过阈值",
                "current_size": total,
                "threshold": self.max_total
            }

        # 统计各类组合数量
        completed = sum(1 for c in combinations if c.get('status') == 'completed')
        failed = sum(1 for c in combinations if c.get('status') == 'failed')
        pending = sum(1 for c in combinations if c.get('status') == 'pending')
        running = sum(1 for c in combinations if c.get('status') == 'running')

        # 计算需要删除的数量
        to_delete = total - self.max_total

        # 估算各类组合的删除数量
        completed_to_delete = max(0, completed - self.max_elite)
        failed_to_delete = failed if not self.keep_failed else 0
        remaining_to_delete = max(0, to_delete - completed_to_delete - failed_to_delete)

        return {
            "needs_cleanup": True,
            "reason": "蓝图文大小超过阈值",
            "current_size": total,
            "threshold": self.max_total,
            "to_delete": to_delete,
            "current_breakdown": {
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "running": running
            },
            "suggested_deletion": {
                "completed": completed_to_delete,
                "failed": failed_to_delete,
                "pending": max(0, remaining_to_delete),
                "running": 0
            },
            "estimated_space_saved": f"{(to_delete / total * 100):.1f}%"
        }

    def list_archives(self, blueprint_dir: str) -> List[Dict[str, Any]]:
        """
        列出所有归档文件

        Args:
            blueprint_dir: 蓝图文件所在目录

        Returns:
            List[Dict[str, Any]]: 归档文件列表
        """
        archive_path = os.path.join(blueprint_dir, self.archive_dir)

        if not os.path.exists(archive_path):
            return []

        archives = []

        for filename in os.listdir(archive_path):
            if filename.startswith('archive_') and filename.endswith('.json'):
                file_path = os.path.join(archive_path, filename)
                try:
                    size = os.path.getsize(file_path)
                    size_kb = round(size / 1024, 2)

                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    archives.append({
                        "filename": filename,
                        "file_path": file_path,
                        "size_kb": size_kb,
                        "archived_at": data.get('archived_at', ''),
                        "archived_count": data.get('archived_count', 0),
                        "archive_reason": data.get('archive_reason', '')
                    })
                except Exception as e:
                    print(f"读取归档文件失败: {filename}, 错误: {e}")

        # 按归档时间排序
        archives.sort(key=lambda x: x.get('archived_at', ''), reverse=True)

        return archives

    def restore_from_archive(self, archive_file: str,
                             target_blueprint: Dict[str, Any],
                             max_restore: int = None) -> Dict[str, Any]:
        """
        从归档文件恢复组合到蓝图

        Args:
            archive_file: 归档文件路径
            target_blueprint: 目标蓝图
            max_restore: 最大恢复数量(可选)

        Returns:
            Dict[str, Any]: 更新后的蓝图
        """
        with open(archive_file, 'r', encoding='utf-8') as f:
            archive_data = json.load(f)

        archived_combinations = archive_data.get('combinations', [])

        if max_restore and len(archived_combinations) > max_restore:
            archived_combinations = archived_combinations[:max_restore]

        # 合并组合
        current_max_id = max((c.get('id', 0) for c in target_blueprint.get('combinations', [])), default=0)

        for combo in archived_combinations:
            current_max_id += 1
            combo['id'] = current_max_id

        target_blueprint['combinations'].extend(archived_combinations)
        self._update_blueprint_stats(target_blueprint)

        print(f"从归档文件恢复了 {len(archived_combinations)} 个组合")

        return target_blueprint
