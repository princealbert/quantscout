# coding=utf-8
"""
深V信号指标计算模块
"""

import pandas as pd
from typing import Dict, Any
from config.weights_config import weight_config


class DeepVCalculator:
    """深V信号计算器"""
    
    def __init__(self):
        self.params = weight_config.INDICATOR_PARAMS['deepv']
    
    def compute_deep_v(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算深V信号指标
        
        返回：
        - dv_short: 短期线（黑色）
        - dv_long: 主力线（红色）
        - deepv_signal: 深V补票信号（True/False）
        """
        try:
            if df.empty or len(df) < 3:
                return {'deepv_signal': False}
            
            # 检查数据框是否有时间列，如果没有则按索引排序
            if 'bob' in df.columns:
                df = df.sort_values('bob').reset_index(drop=True)
            else:
                df = df.reset_index(drop=True)
            
            close = pd.to_numeric(df['close'], errors='coerce')
            low = pd.to_numeric(df['low'], errors='coerce')
            
            def rolling_hhv(series: pd.Series, n: int) -> pd.Series:
                return series.rolling(window=n, min_periods=1).max()
            
            def rolling_llv(series: pd.Series, n: int) -> pd.Series:
                return series.rolling(window=n, min_periods=1).min()
            
            # 短期与长期核心线
            hhv_short = rolling_hhv(close, self.params['short_period'])
            llv_short = rolling_llv(low, self.params['short_period'])
            
            # 避免除零错误
            denom_short = (hhv_short - llv_short)
            denom_short = denom_short.replace(0, 1)
            dv_short = 100 * (close - llv_short) / denom_short
            
            hhv_long = rolling_hhv(close, self.params['long_period'])
            llv_long = rolling_llv(low, self.params['long_period'])
            denom_long = (hhv_long - llv_long)
            denom_long = denom_long.replace(0, 1)
            dv_long = 100 * (close - llv_long) / denom_long
            
            # 清洗与截断到[0,100]
            dv_short = dv_short.clip(lower=0, upper=100).fillna(50)
            dv_long = dv_long.clip(lower=0, upper=100).fillna(50)
            
            # 检查深V补票序列（T-2, T-1, T）
            deepv_signal = False
            if len(dv_short) >= 3 and len(dv_long) >= 3:
                t_2_short = dv_short.iloc[-3] if not pd.isna(dv_short.iloc[-3]) else 0
                t_2_long = dv_long.iloc[-3] if not pd.isna(dv_long.iloc[-3]) else 0
                
                t_1_short = dv_short.iloc[-2] if not pd.isna(dv_short.iloc[-2]) else 0
                t_1_long = dv_long.iloc[-2] if not pd.isna(dv_long.iloc[-2]) else 0
                
                t_short = dv_short.iloc[-1] if not pd.isna(dv_short.iloc[-1]) else 0
                t_long = dv_long.iloc[-1] if not pd.isna(dv_long.iloc[-1]) else 0
                
                # 深V补票条件
                deepv_signal = (
                    t_2_short >= 80 and t_2_long >= 80 and  # T-2
                    t_1_short <= self.params['buy_signal_threshold'] and 
                    t_1_long >= 80 and  # T-1
                    t_short >= 80 and t_long >= 80           # T
                )
            
            return {
                'dv_short': float(dv_short.iloc[-1]) if not pd.isna(dv_short.iloc[-1]) else None,
                'dv_long': float(dv_long.iloc[-1]) if not pd.isna(dv_long.iloc[-1]) else None,
                'deepv_signal': deepv_signal
            }
            
        except Exception as e:
            return {'deepv_signal': False}