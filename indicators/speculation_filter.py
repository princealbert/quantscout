# coding=utf-8
"""
投机炒作筛选器 - 排除短期被爆炒过的股票
条件：
1. 30日内股价最高价比最低价 > 50%
2. 出现过一字涨停板（游资炒作特征）
"""

import pandas as pd
from typing import Dict, Any


class SpeculationFilter:
    """投机炒作筛选器 - 排除短期爆炒的股票"""
    
    def __init__(self, lookback_days: int = 30, volatility_threshold: float = 0.5):
        """
        初始化投机筛选器
        
        Args:
            lookback_days: 回溯天数（默认30天）
            volatility_threshold: 波动率阈值（默认50%，即0.5）
        """
        self.lookback_days = lookback_days
        self.volatility_threshold = volatility_threshold
    
    def check_high_volatility(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        检查是否为高波动股票
        
        Args:
            df: K线数据
            
        Returns:
            包含以下字段的字典：
            - is_high_volatility: 是否为高波动股票
            - volatility_ratio: 波动率（最高价/最低价 - 1）
            - high_price: 最高价
            - low_price: 最低价
            - high_date: 最高价日期
            - low_date: 最低价日期
        """
        try:
            if df is None or df.empty or len(df) < 5:
                return {
                    'is_high_volatility': False,
                    'volatility_ratio': 0,
                    'high_price': 0,
                    'low_price': 0,
                    'high_date': None,
                    'low_date': None,
                    'reason': '数据不足'
                }
            
            # 确保数据类型正确
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['open'] = pd.to_numeric(df.get('open', df['close']), errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            
            # 取最近lookback_days天的数据
            if len(df) > self.lookback_days:
                df_lookback = df.iloc[-self.lookback_days:].copy()
            else:
                df_lookback = df.copy()
            
            # 计算波动率：最高价/最低价 - 1
            max_high = df_lookback['high'].max()
            min_low = df_lookback['low'].min()
            
            # 防止除零错误
            if min_low <= 0:
                return {
                    'is_high_volatility': False,
                    'volatility_ratio': 0,
                    'high_price': max_high,
                    'low_price': min_low,
                    'high_date': None,
                    'low_date': None,
                    'reason': '最低价无效'
                }
            
            volatility_ratio = (max_high - min_low) / min_low
            
            # 获取最高价和最低价的日期
            max_high_idx = df_lookback['high'].idxmax()
            min_low_idx = df_lookback['low'].idxmin()
            
            high_date = df_lookback.loc[max_high_idx, 'bob'] if 'bob' in df_lookback.columns else max_high_idx
            low_date = df_lookback.loc[min_low_idx, 'bob'] if 'bob' in df_lookback.columns else min_low_idx
            
            # 判断是否超过阈值
            is_high_volatility = volatility_ratio > self.volatility_threshold
            
            return {
                'is_high_volatility': is_high_volatility,
                'volatility_ratio': volatility_ratio,
                'high_price': float(max_high) if pd.notna(max_high) else 0,
                'low_price': float(min_low) if pd.notna(min_low) else 0,
                'high_date': high_date,
                'low_date': low_date,
                'reason': '波动率过高' if is_high_volatility else '波动率正常'
            }
            
        except Exception as e:
            return {
                'is_high_volatility': False,
                'volatility_ratio': 0,
                'high_price': 0,
                'low_price': 0,
                'high_date': None,
                'low_date': None,
                'reason': f'计算异常: {str(e)}'
            }
    
    def check_limit_up_board(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        检查是否出现过一字涨停板

        一字板特征：
        - 开盘价 = 收盘价 = 最高价（价格无波动）
        - 涨幅 ≥ 9.5%（接近涨停10%）
        - 成交量异常小（或正常范围内，一字板也可能有成交）

        Args:
            df: K线数据

        Returns:
            包含以下字段的字典：
            - has_limit_up_board: 是否出现过一字板
            - limit_up_date: 一字板日期
            - limit_up_price: 一字板价格
            - limit_up_rate: 涨幅
            - limit_up_volume: 成交量
            - board_count: 一字板出现次数
        """
        try:
            if df is None or df.empty or len(df) < 5:
                return {
                    'has_limit_up_board': False,
                    'limit_up_date': None,
                    'limit_up_price': 0,
                    'limit_up_rate': 0,
                    'limit_up_volume': 0,
                    'board_count': 0,
                    'reason': '数据不足'
                }

            # 确保数据类型正确
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['open'] = pd.to_numeric(df.get('open', df['close']), errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

            # 取最近lookback_days天的数据
            if len(df) > self.lookback_days:
                df_lookback = df.iloc[-self.lookback_days:].copy()
            else:
                df_lookback = df.copy()

            # 重置索引，确保索引从0开始
            df_lookback = df_lookback.reset_index(drop=True)

            # 寻找一字涨停板
            limit_up_dates = []
            board_count = 0
            latest_limit_up = None

            for idx in range(len(df_lookback)):
                row = df_lookback.iloc[idx]
                open_price = row['open']
                close_price = row['close']
                high_price = row['high']
                low_price = row['low']
                volume = row['volume']

                # 计算涨幅（使用前一日的收盘价）
                if idx > 0:
                    prev_close = df_lookback.iloc[idx - 1]['close']
                    if prev_close > 0 and pd.notna(prev_close):
                        change_rate = (close_price - prev_close) / prev_close
                    else:
                        change_rate = 0
                else:
                    change_rate = 0

                # 判断是否为一字涨停板
                # 条件1：开盘价 = 收盘价 = 最高价（使用相对比例判断，而非绝对值）
                # 条件2：涨幅 ≥ 9.5%（接近涨停10%，预留一点误差）
                # 条件3：有成交量（一字板也可能有少量成交）

                if pd.notna(open_price) and pd.notna(close_price) and pd.notna(high_price) and open_price > 0:
                    # 相对差异：价格差异不超过0.1%
                    open_close_diff = abs(open_price - close_price) / open_price
                    close_high_diff = abs(close_price - high_price) / high_price if high_price > 0 else 1

                    is_limit_up = (
                        open_close_diff < 0.001 and  # 开盘与收盘差异<0.1%
                        close_high_diff < 0.001 and  # 收盘与最高差异<0.1%
                        change_rate >= 0.095 and  # 涨幅≥9.5%
                        pd.notna(volume) and volume > 0  # 有成交
                    )

                    if is_limit_up:
                        board_count += 1
                        limit_up_dates.append({
                            'date': row.get('bob', idx),
                            'price': close_price,
                            'rate': change_rate,
                            'volume': volume
                        })

                        # 记录最新的一次一字板
                        if latest_limit_up is None:
                            latest_limit_up = {
                                'date': row.get('bob', idx),
                                'price': close_price,
                                'rate': change_rate,
                                'volume': volume
                            }

            has_limit_up = board_count > 0

            if has_limit_up:
                return {
                    'has_limit_up_board': True,
                    'limit_up_date': latest_limit_up['date'],
                    'limit_up_price': latest_limit_up['price'],
                    'limit_up_rate': latest_limit_up['rate'],
                    'limit_up_volume': latest_limit_up['volume'],
                    'board_count': board_count,
                    'limit_up_details': limit_up_dates,
                    'reason': f'检测到{board_count}次一字涨停板'
                }
            else:
                return {
                    'has_limit_up_board': False,
                    'limit_up_date': None,
                    'limit_up_price': 0,
                    'limit_up_rate': 0,
                    'limit_up_volume': 0,
                    'board_count': 0,
                    'reason': '未检测到一字涨停板'
                }

        except Exception as e:
            return {
                'has_limit_up_board': False,
                'limit_up_date': None,
                'limit_up_price': 0,
                'limit_up_rate': 0,
                'limit_up_volume': 0,
                'board_count': 0,
                'reason': f'计算异常: {str(e)}'
            }
    
    def check_speculation_signal(self, df: pd.DataFrame, use_volatility: bool = False) -> Dict[str, Any]:
        """
        综合检查投机炒作信号

        满足以下条件即为投机股票（可配置）：
        1. 一字涨停板（主要条件）
        2. 波动率 > 50%（可选条件，默认不使用，避免误杀主升浪）

        Args:
            df: K线数据
            use_volatility: 是否使用波动率条件（默认False）

        Returns:
            包含以下字段的字典：
            - has_speculation_signal: 是否存在投机信号
            - reason: 详细原因
            - volatility_result: 波动率检查结果
            - limit_up_result: 一字板检查结果
        """
        try:
            # 检查一字板（主要条件）
            limit_up_result = self.check_limit_up_board(df)

            # 检查波动率（可选条件）
            volatility_result = self.check_high_volatility(df)

            # 综合判断：以一字板为主，波动率为辅
            has_speculation = limit_up_result.get('has_limit_up_board', False)

            # 如果启用了波动率条件，则也纳入判断
            if use_volatility:
                has_speculation = (
                    has_speculation or
                    volatility_result.get('is_high_volatility', False)
                )

            # 构建原因说明
            reasons = []
            if limit_up_result.get('has_limit_up_board'):
                reasons.append(f"出现{limit_up_result['board_count']}次一字板")
            if use_volatility and volatility_result.get('is_high_volatility'):
                reasons.append(f"波动率过高({volatility_result['volatility_ratio']*100:.1f}%)")

            reason = "、".join(reasons) if reasons else "未检测到投机信号"

            return {
                'has_speculation_signal': has_speculation,
                'reason': reason,
                'volatility_result': volatility_result,
                'limit_up_result': limit_up_result,
                'use_volatility': use_volatility
            }

        except Exception as e:
            return {
                'has_speculation_signal': False,
                'reason': f'计算异常: {str(e)}',
                'volatility_result': {},
                'limit_up_result': {},
                'use_volatility': use_volatility
            }
    
    def filter_stock(self, df: pd.DataFrame) -> tuple:
        """
        筛选股票：返回是否通过筛选（True表示通过，False表示需要排除）
        
        Args:
            df: K线数据
            
        Returns:
            (is_passed, details): is_passed=True表示通过筛选，details为详细信息
        """
        result = self.check_speculation_signal(df)
        
        # 如果存在投机信号，则不通过筛选
        is_passed = not result['has_speculation_signal']
        
        return is_passed, result


# 便捷函数
def check_speculation_filter(df: pd.DataFrame, lookback_days: int = 30, use_volatility: bool = False) -> bool:
    """
    便捷函数：快速检查股票是否通过投机筛选

    Args:
        df: K线数据
        lookback_days: 回溯天数
        use_volatility: 是否使用波动率条件（默认False，只使用一字板检测）

    Returns:
        True表示通过筛选（可以保留），False表示需要排除
    """
    filter_spec = SpeculationFilter(lookback_days)
    is_passed, _ = filter_spec.filter_stock(df)
    return is_passed
