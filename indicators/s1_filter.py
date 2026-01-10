# coding=utf-8
"""
S1筛选器 - 排除前期高点出现放量绿柱的股票
逻辑：30个交易日内股价高点及前后2天范围内，出现绿色成交量大于前一个交易日的红色成交量，
      而且是30日内最大成交量的，需要过滤掉
"""

import pandas as pd
from typing import Dict, Any, Tuple


class S1Filter:
    """S1筛选器 - 排除主力获利了结信号"""
    
    def __init__(self, lookback_days: int = 30, context_days: int = 2):
        """
        初始化S1筛选器
        
        Args:
            lookback_days: 回溯天数（默认30天）
            context_days: 高点前后的天数范围（默认2天）
        """
        self.lookback_days = lookback_days
        self.context_days = context_days
    
    def check_s1_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        检查是否存在S1信号（主力获利了结）
        
        Args:
            df: K线数据，必须包含 close, volume, high, low 列
            
        Returns:
            包含以下字段的字典：
            - has_s1_signal: 是否存在S1信号（True表示需要排除）
            - s1_signal_date: S1信号出现的日期
            - s1_high_price: S1信号对应的高点价格
            - s1_green_volume: 绿柱成交量
            - s1_prev_red_volume: 前一日红柱成交量
            - s1_volume_ratio: 绿柱/红柱成交量比率
            - s1_reason: 详细原因说明
        """
        try:
            # 数据验证
            if df is None or df.empty or len(df) < (self.lookback_days + 5):
                return {
                    'has_s1_signal': False,
                    's1_reason': '数据不足'
                }
            
            # 必需列检查
            required_columns = ['close', 'volume', 'high', 'low']
            if not all(col in df.columns for col in required_columns):
                return {
                    'has_s1_signal': False,
                    's1_reason': '缺少必需列'
                }
            
            # 按日期排序（确保数据按时间顺序）
            if 'bob' in df.columns:
                df_sorted = df.sort_values('bob').reset_index(drop=True)
            else:
                df_sorted = df.reset_index(drop=True)
            
            # 取最近lookback_days天的数据
            if len(df_sorted) > self.lookback_days:
                df_lookback = df_sorted.iloc[-self.lookback_days:].copy()
            else:
                df_lookback = df_sorted.copy()
            
            # 确保数据类型正确
            df_lookback['close'] = pd.to_numeric(df_lookback['close'], errors='coerce')
            df_lookback['volume'] = pd.to_numeric(df_lookback['volume'], errors='coerce')
            df_lookback['high'] = pd.to_numeric(df_lookback['high'], errors='coerce')
            df_lookback['low'] = pd.to_numeric(df_lookback['low'], errors='coerce')
            
            # 步骤1：找出30日内的最高价
            max_high_idx = df_lookback['high'].idxmax()
            max_high_date = df_lookback.loc[max_high_idx, 'bob'] if 'bob' in df_lookback.columns else max_high_idx
            max_high_price = df_lookback.loc[max_high_idx, 'high']
            
            # 步骤2：确定高点前后context_days天的范围
            start_idx = max(0, max_high_idx - self.context_days)
            end_idx = min(len(df_lookback) - 1, max_high_idx + self.context_days)
            
            # 步骤3：在这个范围内寻找绿柱（阴线）成交量最大的交易日
            max_green_volume = 0
            green_volume_idx = None
            
            for idx in range(start_idx, end_idx + 1):
                if idx >= len(df_lookback):
                    continue
                
                current_close = df_lookback.loc[idx, 'close']
                current_volume = df_lookback.loc[idx, 'volume']
                
                # 判断是否为绿柱（阴线）：收盘价 < 开盘价 或 收盘价 < 前一日收盘价
                is_green = False
                if idx > 0:
                    prev_close = df_lookback.loc[idx - 1, 'close']
                    if current_close < prev_close:
                        is_green = True
                
                # 如果是绿柱且成交量更大，记录下来
                if is_green and pd.notna(current_volume) and current_volume > max_green_volume:
                    max_green_volume = current_volume
                    green_volume_idx = idx
            
            # 如果没有找到绿柱，返回无信号
            if green_volume_idx is None:
                return {
                    'has_s1_signal': False,
                    's1_reason': '高点范围内未发现绿柱'
                }
            
            # 步骤4：检查绿柱前一日的红柱成交量
            if green_volume_idx == 0:
                return {
                    'has_s1_signal': False,
                    's1_reason': '绿柱为第一日，无前一日数据'
                }
            
            prev_red_idx = green_volume_idx - 1
            prev_red_close = df_lookback.loc[prev_red_idx, 'close']
            prev_close_for_red = df_lookback.loc[prev_red_idx - 1, 'close'] if prev_red_idx > 0 else prev_red_close
            prev_red_volume = df_lookback.loc[prev_red_idx, 'volume']
            
            # 判断前一日是否为红柱（阳线）
            if prev_red_idx > 0:
                is_red = prev_red_close > prev_close_for_red
            else:
                is_red = True  # 如果是第一日，默认认为没有明确信号
            
            # 步骤5：比较绿柱和前一日红柱的成交量
            if is_red and pd.notna(prev_red_volume) and prev_red_volume > 0:
                volume_ratio = max_green_volume / prev_red_volume
                
                # 步骤6：检查是否为30日内最大成交量
                max_volume_30days = df_lookback['volume'].max()
                
                # 判断条件：绿柱成交量 > 前一日红柱成交量 且 绿柱成交量是30日内最大
                if max_green_volume > prev_red_volume and max_green_volume >= max_volume_30days * 0.95:
                    # 找到S1信号，需要排除
                    return {
                        'has_s1_signal': True,
                        's1_signal_date': df_lookback.loc[green_volume_idx, 'bob'] if 'bob' in df_lookback.columns else green_volume_idx,
                        's1_high_date': max_high_date,
                        's1_high_price': max_high_price,
                        's1_green_volume': max_green_volume,
                        's1_prev_red_volume': prev_red_volume,
                        's1_volume_ratio': volume_ratio,
                        's1_max_volume_30days': max_volume_30days,
                        's1_reason': f'高点{max_high_price:.2f}前后出现放量绿柱({max_green_volume:.0f})超过前日红柱({prev_red_volume:.0f})，且为30日最大成交量'
                    }
            
            return {
                'has_s1_signal': False,
                's1_reason': '不符合S1信号条件'
            }
            
        except Exception as e:
            return {
                'has_s1_signal': False,
                's1_reason': f'计算异常: {str(e)}'
            }
    
    def filter_stock(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        筛选股票：返回是否通过筛选（True表示通过，False表示需要排除）
        
        Args:
            df: K线数据
            
        Returns:
            (is_passed, details): is_passed=True表示通过筛选，details为详细信息
        """
        result = self.check_s1_signal(df)
        
        # 如果存在S1信号，则不通过筛选
        is_passed = not result['has_s1_signal']
        
        return is_passed, result


# 便捷函数
def check_s1_filter(df: pd.DataFrame, lookback_days: int = 30, context_days: int = 2) -> bool:
    """
    便捷函数：快速检查股票是否通过S1筛选
    
    Args:
        df: K线数据
        lookback_days: 回溯天数
        context_days: 高点前后天数
        
    Returns:
        True表示通过筛选（可以保留），False表示需要排除
    """
    filter_s1 = S1Filter(lookback_days, context_days)
    is_passed, _ = filter_s1.filter_stock(df)
    return is_passed
