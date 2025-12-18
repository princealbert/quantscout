# coding=utf-8
"""
趋势指标计算模块 - 包含知行趋势线等指标
"""

import pandas as pd
from typing import Dict, Any
from emgm.config.weights_config import weight_config


class TrendIndicators:
    """趋势指标计算器"""
    
    def __init__(self):
        self.params = weight_config.INDICATOR_PARAMS['zhi_xing']
    
    def compute_zhi_xing_overlays(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算知行趋势线系列
        
        包含：
        - white_line: EMA(EMA(CLOSE,10),10) - 白线
        - yellow_line: 大哥线（黄线）
        - bbi_line: BBI线
        """
        try:
            if df.empty:
                return {}
            
            # 检查数据框是否有时间列，如果没有则按索引排序
            if 'bob' in df.columns:
                df = df.sort_values('bob').reset_index(drop=True)
            else:
                df = df.reset_index(drop=True)
            
            close = pd.to_numeric(df['close'], errors='coerce')
            
            # EMA(10) 两次 - 白线
            ema10 = close.ewm(span=self.params['white_line_span'], adjust=False).mean()
            white_line = ema10.ewm(span=self.params['white_line_span'], adjust=False).mean()
            
            # 大哥线（黄线）
            ma_values = []
            for period in self.params['yellow_line_periods']:
                ma_values.append(close.rolling(window=period, min_periods=1).mean())
            yellow_line = sum(ma_values) / len(ma_values)
            
            # BBI线
            bbi_values = []
            for period in self.params['bbi_periods']:
                bbi_values.append(close.rolling(window=period, min_periods=1).mean())
            bbi_line = sum(bbi_values) / len(bbi_values)
            
            # 计算斜率（最近5天的平均斜率）
            white_slope = self._calculate_slope(white_line)
            yellow_slope = self._calculate_slope(yellow_line)
            
            return {
                'white_line': float(white_line.iloc[-1]) if not pd.isna(white_line.iloc[-1]) else None,
                'yellow_line': float(yellow_line.iloc[-1]) if not pd.isna(yellow_line.iloc[-1]) else None,
                'bbi_line': float(bbi_line.iloc[-1]) if not pd.isna(bbi_line.iloc[-1]) else None,
                'white_slope': white_slope,
                'yellow_slope': yellow_slope,
                'close_price': float(close.iloc[-1]) if not pd.isna(close.iloc[-1]) else None
            }
            
        except Exception as e:
            return {}
    
    def _calculate_slope(self, series: pd.Series, window: int = 5) -> float:
        """计算斜率"""
        if len(series) < window:
            return 0
        
        try:
            recent = series.iloc[-window:].values
            x = list(range(window))
            y = [float(val) for val in recent if not pd.isna(val)]
            
            if len(y) < window:
                return 0
            
            slope = (window * sum(x[i]*y[i] for i in range(len(x))) - 
                    sum(x) * sum(y)) / (window * sum(xx*xx for xx in x) - sum(x)**2)
            return slope
            
        except Exception as e:
            return 0
    
    def analyze_volume_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析成交量趋势"""
        try:
            if df.empty:
                return {}
            
            volume = pd.to_numeric(df['volume'], errors='coerce')
            close = pd.to_numeric(df['close'], errors='coerce')
            
            analysis = {
                'big_volume': False,  # 是否放巨量
                'volume_anomaly': False,  # 成交量异动
                'volume_price_rise': False,  # 价随量升
                'volume_contraction': False  # 缩量下跌
            }
            
            if len(volume) >= 3:
                # 检查最近是否有放巨量（超过前20天平均量的3倍）
                recent_volume = volume.iloc[-1]
                avg_volume_20 = volume.iloc[-21:-1].mean() if len(volume) > 21 else recent_volume
                analysis['big_volume'] = recent_volume > avg_volume_20 * 3
                
                # 检查价随量升
                recent_volume_change = volume.iloc[-1] / volume.iloc[-2]
                recent_price_change = close.iloc[-1] / close.iloc[-2]
                analysis['volume_price_rise'] = recent_volume_change > 1.2 and recent_price_change > 1.01
            
            if len(volume) >= 5:
                # 检查缩量下跌
                volume_avg_5 = volume.iloc[-5:].mean()
                analysis['volume_contraction'] = (volume.iloc[-1] < volume_avg_5 * 0.7 and 
                                                close.iloc[-1] < close.iloc[-2])
            
            if len(volume) >= 60:
                # 成交量异动权重（近60日成交量标准差超过均值）
                recent_60_volume = volume.iloc[-60:]
                analysis['volume_anomaly'] = recent_60_volume.std() > recent_60_volume.mean() * 0.5
            
            return analysis
            
        except Exception as e:
            return {}