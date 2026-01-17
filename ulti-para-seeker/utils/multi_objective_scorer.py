#!/usr/bin/env python
# coding=utf-8
"""
多目标评价函数 - 综合评估参数组合的综合表现
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MultiObjectiveScorer:
    """
    多目标评价函数，综合评估策略表现

    考虑因素：
    1. 总收益率 (total_return)
    2. 夏普比率 (sharpe_ratio)
    3. 胜率 (win_rate)
    4. 最大回撤 (max_drawdown)
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化评价函数

        Args:
            weights: 各指标的权重配置，格式如下：
                {
                    'total_return': 0.35,      # 收益率权重
                    'sharpe_ratio': 0.35,      # 夏普比率权重
                    'win_rate': 0.15,           # 胜率权重
                    'max_drawdown': 0.15        # 回撤权重（回撤越小越好，所以会用负值评分）
                }
                如果为None，使用默认权重
        """
        # 默认权重配置（基于数据分析）
        self.weights = weights or {
            'total_return': 0.35,      # 收益率是核心指标
            'sharpe_ratio': 0.35,      # 夏普比率体现风险调整后收益
            'win_rate': 0.15,           # 胜率影响稳定性
            'max_drawdown': 0.15        # 回撤控制风险
        }

        # 各指标的参考范围（用于归一化）
        self.reference_ranges = {
            'total_return': (-40, 70),      # 收益率范围：-40% 到 70%
            'sharpe_ratio': (-3, 20),       # 夏普比率范围：-3 到 20
            'win_rate': (0, 100),           # 胜率范围：0% 到 100%
            'max_drawdown': (-40, 0)        # 回撤范围：-40% 到 0%
        }

        logger.info(f"多目标评价函数初始化完成，权重配置: {self.weights}")

    def calculate_score(self, result: Dict[str, Any]) -> float:
        """
        计算综合评分

        Args:
            result: 回测结果字典，必须包含：
                - total_return: 总收益率（百分比，如59.8）
                - sharpe_ratio: 夏普比率
                - win_rate: 胜率（百分比，如75）
                - max_drawdown: 最大回撤（百分比，如-6.21）

        Returns:
            float: 综合评分（0-100之间）
        """
        try:
            # 提取指标
            total_return = result.get('total_return', 0)
            sharpe_ratio = result.get('sharpe_ratio', 0)
            win_rate = result.get('win_rate', 0)
            max_drawdown = result.get('max_drawdown', 0)

            # 归一化各项指标到[0, 1]区间
            normalized_return = self._normalize_value(total_return, 'total_return')
            normalized_sharpe = self._normalize_value(sharpe_ratio, 'sharpe_ratio')
            normalized_win_rate = self._normalize_value(win_rate, 'win_rate')

            # 回撤需要特殊处理：回撤越大（越负），分数越低
            # 转换为正值：回撤-10% -> 评分0.75，回撤-30% -> 评分0.25
            drawdown_range = self.reference_ranges['max_drawdown']
            normalized_drawdown = 1 - self._normalize_value(max_drawdown, 'max_drawdown')

            # 计算加权综合评分
            score = (
                normalized_return * self.weights['total_return'] +
                normalized_sharpe * self.weights['sharpe_ratio'] +
                normalized_win_rate * self.weights['win_rate'] +
                normalized_drawdown * self.weights['max_drawdown']
            )

            # 转换到0-100分制
            final_score = score * 100

            return final_score

        except Exception as e:
            logger.error(f"计算综合评分失败: {e}")
            return 0.0

    def _normalize_value(self, value: float, metric_name: str) -> float:
        """
        将值归一化到[0, 1]区间

        Args:
            value: 原始值
            metric_name: 指标名称

        Returns:
            float: 归一化后的值（0-1之间）
        """
        min_val, max_val = self.reference_ranges[metric_name]

        # 限制在参考范围内
        value = max(min_val, min(max_val, value))

        # 归一化
        normalized = (value - min_val) / (max_val - min_val)
        return max(0, min(1, normalized))

    def compare(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> int:
        """
        比较两个回测结果

        Args:
            result1: 第一个回测结果
            result2: 第二个回测结果

        Returns:
            int: 1表示result1更好，-1表示result2更好，0表示相当
        """
        score1 = self.calculate_score(result1)
        score2 = self.calculate_score(result2)

        if abs(score1 - score2) < 0.5:  # 差异小于0.5分视为相当
            return 0
        elif score1 > score2:
            return 1
        else:
            return -1

    def rank_combinations(self, combinations: list, top_n: int = None) -> list:
        """
        对参数组合进行排名

        Args:
            combinations: 参数组合列表，每个组合必须包含result字典
            top_n: 返回前N个组合，如果为None返回全部

        Returns:
            list: 排序后的组合列表
        """
        # 计算每个组合的评分
        scored_combinations = []
        for combo in combinations:
            result = combo.get('result', {})
            if not result:
                continue

            score = self.calculate_score(result)
            scored_combinations.append({
                'combination': combo,
                'score': score
            })

        # 按评分降序排序
        scored_combinations.sort(key=lambda x: x['score'], reverse=True)

        # 返回组合列表
        sorted_combinations = [item['combination'] for item in scored_combinations]

        if top_n:
            return sorted_combinations[:top_n]
        return sorted_combinations


# 全局实例
_scorer = None


def get_scorer(weights: Optional[Dict[str, float]] = None) -> MultiObjectiveScorer:
    """
    获取全局评价函数实例

    Args:
        weights: 权重配置

    Returns:
        MultiObjectiveScorer: 评价函数实例
    """
    global _scorer
    if _scorer is None:
        _scorer = MultiObjectiveScorer(weights)
    elif weights is not None:
        _scorer = MultiObjectiveScorer(weights)
    return _scorer
