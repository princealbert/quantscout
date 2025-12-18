# coding=utf-8
"""
权重配置模块 - 定义策略参数和权重配置
相对固定的配置逻辑，便于维护和调整
"""

from typing import Dict, Any, List, Tuple


class WeightConfig:
    """权重配置类"""
    
    # 默认权重配置（百分制评分系统）
    DEFAULT_WEIGHTS = {
        'kdj_j': 25,       # KDJ J值权重（25分）
        'trend': 25,       # 趋势权重（25分）
        'deepv': 10,       # 深V信号权重（10分）
        'volume': 8,       # 成交量权重（8分）
        'fundamental': 8,  # 基本面权重（8分）
        'position': 4,     # 位置权重（4分）
        'risk_reward': 20  # 盈亏比权重（20分）
    }
    
    # 指标参数配置
    INDICATOR_PARAMS = {
        'kdj': {
            'period': 9,  # KDJ计算周期
        },
        'zhi_xing': {
            'white_line_span': 10,  # 白线EMA周期
            'yellow_line_periods': [14, 28, 57, 114],  # 黄线MA周期
            'bbi_periods': [3, 6, 12, 24]  # BBI线周期
        },
        'deepv': {
            'short_period': 3,   # 短期线周期
            'long_period': 21,   # 长期线周期
            'buy_signal_threshold': 20,  # 买入信号阈值
            'dual_zero_threshold': 6     # 双线归零阈值
        }
    }
    
    # 筛选条件配置
    SCREENING_CONDITIONS = {
        'j_threshold': 20,           # J值阈值
        'pe_max': 100,               # PE最大值
        'market_cap_min': 50 * 1e8,  # 最小流通市值（50亿）
        'volume_threshold': 8000 * 1e4  # 成交量阈值（8000万股）
    }
    
    @classmethod
    def get_normalized_weights(cls, custom_weights: Dict[str, int] = None) -> Dict[str, int]:
        """获取标准化权重配置"""
        if custom_weights:
            weights = cls.DEFAULT_WEIGHTS.copy()
            # 更新自定义权重
            for key, value in custom_weights.items():
                if key in weights:
                    weights[key] = value
            
            # 确保权重总和为100
            total_weight = sum(weights.values())
            if total_weight != 100:
                scale_factor = 100.0 / total_weight
                for key in weights:
                    weights[key] = int(weights[key] * scale_factor)
        else:
            weights = cls.DEFAULT_WEIGHTS.copy()
        
        return weights
    
    @classmethod
    def get_dynamic_j_weights(cls, kdj_j_total_weight: int, custom_sub_weights: Dict[str, int] = None) -> List[Tuple[float, float, int]]:
        """动态计算J值区间权重"""
        if custom_sub_weights and 'kdj_j' in custom_sub_weights:
            # 使用自定义子权重
            sub_weights = custom_sub_weights['kdj_j']['sub_weights']
            dynamic_weights = [
                (0, 20, sub_weights.get('j_0_20', 1)),
                (-10, 0, sub_weights.get('j_-10_0', 2)),
                (-20, -10, sub_weights.get('j_-20_-10', 3)),
                (-30, -20, sub_weights.get('j_-30_-20', 4)),
                (-999, -30, sub_weights.get('j_below_-30', 5))
            ]
        else:
            # 使用默认权重
            base_weights = [1, 2, 3, 4, 5]  # 基础权重：5个区间
            base_total = sum(base_weights)
            
            # 按比例调整权重
            scale_factor = kdj_j_total_weight / base_total
            dynamic_weights = [
                (0, 20, int(1 * scale_factor)),
                (-10, 0, int(2 * scale_factor)),
                (-20, -10, int(3 * scale_factor)),
                (-30, -20, int(4 * scale_factor)),
                (-999, -30, int(5 * scale_factor))
            ]
        
        return dynamic_weights
    
    @classmethod
    def get_dynamic_position_weights(cls, position_total_weight: int, custom_sub_weights: Dict[str, int] = None) -> Dict[str, int]:
        """动态计算位置权重"""
        if custom_sub_weights and 'position' in custom_sub_weights:
            # 使用自定义子权重
            sub_weights = custom_sub_weights['position']['sub_weights']
            dynamic_weights = {
                'above_white': sub_weights.get('above_white', 3),
                'between_lines': sub_weights.get('between_lines', 2),
                'below_yellow': sub_weights.get('below_yellow', 1)
            }
        else:
            # 使用默认权重
            base_weights = {'above_white': 3, 'between_lines': 2, 'below_yellow': 1}
            base_total = sum(base_weights.values())
            
            scale_factor = position_total_weight / base_total
            dynamic_weights = {}
            for key, value in base_weights.items():
                dynamic_weights[key] = int(value * scale_factor)
        
        return dynamic_weights
    
    @classmethod
    def get_dynamic_volume_weights(cls, volume_total_weight: int, custom_sub_weights: Dict[str, int] = None) -> Dict[str, int]:
        """动态计算成交量权重"""
        if custom_sub_weights and 'volume' in custom_sub_weights:
            # 使用自定义子权重
            sub_weights = custom_sub_weights['volume']['sub_weights']
            dynamic_weights = {
                'big_volume': sub_weights.get('big_volume', 2),
                'volume_anomaly': sub_weights.get('volume_anomaly', 2),
                'volume_breathing': sub_weights.get('volume_breathing', 1)
            }
        else:
            # 使用默认权重
            base_weights = {'big_volume': 2, 'volume_anomaly': 2, 'volume_breathing': 1}
            base_total = sum(base_weights.values())
            
            scale_factor = volume_total_weight / base_total
            dynamic_weights = {}
            for key, value in base_weights.items():
                dynamic_weights[key] = int(value * scale_factor)
        
        return dynamic_weights
    
    @classmethod
    def get_dynamic_fundamental_weights(cls, fundamental_total_weight: int, custom_sub_weights: Dict[str, int] = None) -> Dict[str, int]:
        """动态计算基本面权重"""
        if custom_sub_weights and 'fundamental' in custom_sub_weights:
            # 使用自定义子权重
            sub_weights = custom_sub_weights['fundamental']['sub_weights']
            dynamic_weights = {
                'pe_positive': sub_weights.get('pe_positive', 1),
                'pe_low': sub_weights.get('pe_low', 2),
                'market_cap': sub_weights.get('market_cap', 1),
                'volume_threshold': sub_weights.get('volume_threshold', 1)
            }
        else:
            # 使用默认权重
            base_weights = {'pe_positive': 1, 'pe_low': 2, 'market_cap': 1, 'volume_threshold': 1}
            base_total = sum(base_weights.values())
            
            scale_factor = fundamental_total_weight / base_total
            dynamic_weights = {}
            for key, value in base_weights.items():
                dynamic_weights[key] = int(value * scale_factor)
        
        return dynamic_weights
    
    @classmethod
    def get_dynamic_trend_weights(cls, trend_total_weight: int, custom_sub_weights: Dict[str, int] = None) -> Dict[str, int]:
        """动态计算趋势权重"""
        if custom_sub_weights and 'trend' in custom_sub_weights:
            # 使用自定义子权重
            sub_weights = custom_sub_weights['trend']['sub_weights']
            dynamic_weights = {
                'up_trend': sub_weights.get('up_trend', 2),
                'volume_price_rise': sub_weights.get('volume_price_rise', 1),
                'volume_contraction': sub_weights.get('volume_contraction', 1)
            }
        else:
            # 使用默认权重
            base_weights = {'up_trend': 2, 'volume_price_rise': 1, 'volume_contraction': 1}
            base_total = sum(base_weights.values())
            
            scale_factor = trend_total_weight / base_total
            dynamic_weights = {}
            for key, value in base_weights.items():
                dynamic_weights[key] = int(value * scale_factor)
        
        return dynamic_weights


# 全局配置实例
weight_config = WeightConfig()