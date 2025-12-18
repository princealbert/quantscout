# coding=utf-8
"""
权重评分模块 - 负责计算各维度的评分权重
"""

from typing import Dict, Any, Tuple, List
from config.weights_config import weight_config


class WeightScorer:
    """权重评分计算器"""
    
    def __init__(self, custom_weights: Dict[str, int] = None, sub_weights_config: Dict[str, Any] = None):
        self.score_weights = weight_config.get_normalized_weights(custom_weights)
        self.sub_weights_config = sub_weights_config
        
        # 初始化动态权重（支持子指标权重）
        self.kdj_j_weights = weight_config.get_dynamic_j_weights(self.score_weights['kdj_j'], self.sub_weights_config)
        self.position_weights = weight_config.get_dynamic_position_weights(self.score_weights['position'], self.sub_weights_config)
        self.volume_weights = weight_config.get_dynamic_volume_weights(self.score_weights['volume'], self.sub_weights_config)
        self.fundamental_weights = weight_config.get_dynamic_fundamental_weights(self.score_weights['fundamental'], self.sub_weights_config)
        self.trend_weights = weight_config.get_dynamic_trend_weights(self.score_weights['trend'], self.sub_weights_config)
    
    def calculate_kdj_j_weight(self, j_value: float) -> float:
        """根据J值计算权重"""
        for min_val, max_val, weight in self.kdj_j_weights:
            if min_val > max_val:  # 处理负数区间（如-20到-999）
                if j_value <= min_val and j_value > max_val:
                    return weight
            else:  # 处理正数区间
                if min_val <= j_value < max_val:
                    return weight
        return 0
    
    def calculate_position_weight(self, close_price: float, white_line: float, yellow_line: float) -> Tuple[float, str]:
        """计算股价相对黄白线位置的权重"""
        if white_line is None or yellow_line is None:
            return 0, "未知"
        
        if close_price >= white_line:
            return self.position_weights['above_white'], "白线上方"
        elif close_price >= yellow_line:
            return self.position_weights['between_lines'], "碗里"
        else:
            return self.position_weights['below_yellow'], "黄线下方"
    
    def calculate_volume_weight(self, volume_analysis: Dict[str, Any]) -> float:
        """计算成交量权重"""
        volume_weight = 0
        
        # 放巨量权重
        if volume_analysis.get('big_volume', False):
            volume_weight += self.volume_weights['big_volume']
        
        # 成交量异动权重
        if volume_analysis.get('volume_anomaly', False):
            volume_weight += self.volume_weights['volume_anomaly']
        
        # 成交量呼吸节奏权重
        volume_breathing = (volume_analysis.get('volume_price_rise', False) or 
                          volume_analysis.get('volume_contraction', False))
        if volume_breathing:
            volume_weight += self.volume_weights['volume_breathing']
        
        return volume_weight
    
    def calculate_trend_score(self, trend_data: Dict[str, Any]) -> float:
        """计算趋势评分"""
        trend_score = 0
        
        # 白线在黄线上方且斜率向上
        white_line = trend_data.get('white_line')
        yellow_line = trend_data.get('yellow_line')
        white_slope = trend_data.get('white_slope', 0)
        
        if (white_line and yellow_line and 
            float(white_line) >= float(yellow_line) and 
            float(white_slope) > 0):
            trend_score += self.trend_weights['up_trend']
        
        # 价随量升
        if trend_data.get('volume_price_rise', False):
            trend_score += self.trend_weights['volume_price_rise']
        
        # 缩量下跌
        if trend_data.get('volume_contraction', False):
            trend_score += self.trend_weights['volume_contraction']
        
        return trend_score
    
    def calculate_fundamental_score(self, fundamental_data: Dict[str, Any]) -> float:
        """计算基本面评分"""
        fundamental_score = 0
        
        pe = fundamental_data.get('pe', 100)
        a_mv = fundamental_data.get('a_mv', 0)
        
        # PE为正
        if pe > 0:
            fundamental_score += self.fundamental_weights['pe_positive']
        
        # PE小于60
        if 0 < pe < 60:
            fundamental_score += self.fundamental_weights['pe_low']
        
        # 流通市值大于100亿
        if a_mv > 100 * 1e8:
            fundamental_score += self.fundamental_weights['market_cap']
        
        # 日均成交量大于8000万股
        if fundamental_data.get('volume_threshold', False):
            fundamental_score += self.fundamental_weights['volume_threshold']
        
        return fundamental_score