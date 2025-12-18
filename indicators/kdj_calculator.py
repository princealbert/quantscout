# coding=utf-8
"""
KDJ指标计算模块
"""

import pandas as pd
from typing import Dict, List
from config.weights_config import weight_config


class KDJCalculator:
    """KDJ指标计算器"""
    
    def __init__(self):
        self.params = weight_config.INDICATOR_PARAMS['kdj']
    
    def calculate_kdj(self, closes: List[float], highs: List[float], lows: List[float]) -> Dict[str, float]:
        """计算KDJ指标（与东方财富一致）"""
        if len(closes) < self.params['period']:
            return {'kdj_k': 50, 'kdj_d': 50, 'kdj_j': 50}
        
        try:
            n = self.params['period']
            k = 50
            d = 50
            
            for i in range(n-1, len(closes)):
                high_n = max(highs[i-n+1:i+1])
                low_n = min(lows[i-n+1:i+1])
                
                if high_n == low_n:
                    rsv = 50
                else:
                    rsv = (closes[i] - low_n) / (high_n - low_n) * 100
                
                k = (2/3) * k + (1/3) * rsv
                d = (2/3) * d + (1/3) * k
            
            j = 3 * k - 2 * d
            return {'kdj_k': round(k, 2), 'kdj_d': round(d, 2), 'kdj_j': round(j, 2)}
            
        except Exception as e:
            return {'kdj_k': 50, 'kdj_d': 50, 'kdj_j': 50}