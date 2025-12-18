"""
EMGM共享指标库适配器
使emgm项目能够使用共享指标库，同时保持独立性
"""

import sys
import os
import pandas as pd
from typing import Dict, Any, List, Optional

# 添加共享库路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
shared_path = os.path.join(project_root, "shared")
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

try:
    from shared.indicators.unified_service import UnifiedIndicatorService, StockData
    from shared.indicators.indicator_registry import IndicatorRegistry
    SHARED_AVAILABLE = True
except ImportError:
    SHARED_AVAILABLE = False
    print("⚠️ 共享指标库不可用，将使用本地实现")


class EMGMIndicatorAdapter:
    """EMGM指标适配器"""
    
    def __init__(self, use_shared: bool = True):
        """初始化适配器"""
        self.use_shared = use_shared and SHARED_AVAILABLE
        
        if self.use_shared:
            # 使用共享指标库
            self.unified_service = UnifiedIndicatorService()
            print("✅ 使用共享指标库")
        else:
            # 使用本地实现（后备方案）
            from .kdj_calculator import KDJCalculator
            from .deepv_calculator import DeepVCalculator
            from .trend_indicators import TrendIndicators
            
            self.kdj_calculator = KDJCalculator()
            self.deepv_calculator = DeepVCalculator()
            self.trend_indicators = TrendIndicators()
            print("⚠️ 使用本地指标实现")
    
    def compute_kdj(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算KDJ指标"""
        if self.use_shared:
            # 使用共享库
            stock_data = self._df_to_stock_data(df)
            result = self.unified_service.calculate_single('kdj', stock_data)
            return self._convert_kdj_result(result)
        else:
            # 使用本地实现
            return self.kdj_calculator.calculate_kdj(
                df['close'].tolist(),
                df['high'].tolist(),
                df['low'].tolist()
            )
    
    def compute_deepv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算深V信号"""
        if self.use_shared:
            stock_data = self._df_to_stock_data(df)
            result = self.unified_service.calculate_single('deepv', stock_data)
            return self._convert_deepv_result(result)
        else:
            return self.deepv_calculator.compute_deep_v(df)
    
    def compute_trend_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算趋势指标"""
        if self.use_shared:
            stock_data = self._df_to_stock_data(df)
            result = self.unified_service.calculate_single('trend', stock_data)
            return self._convert_trend_result(result)
        else:
            return self.trend_indicators.compute_zhi_xing_overlays(df)
    
    def compute_all_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算所有指标"""
        if self.use_shared:
            stock_data = self._df_to_stock_data(df)
            result = self.unified_service.calculate_all(stock_data)
            return self._convert_comprehensive_result(result, df)
        else:
            # 使用本地实现组合
            kdj_result = self.compute_kdj(df)
            deepv_result = self.compute_deepv(df)
            trend_result = self.compute_trend_indicators(df)
            
            return {
                'kdj': kdj_result,
                'deepv': deepv_result,
                'trend': trend_result,
                'total_score': self._calculate_total_score(kdj_result, deepv_result, trend_result),
                'current_price': df['close'].iloc[-1] if not df.empty else 0,
                'timestamp': pd.Timestamp.now().isoformat()
            }
    
    def _df_to_stock_data(self, df: pd.DataFrame) -> StockData:
        """将DataFrame转换为StockData"""
        closes = df['close'].tolist() if 'close' in df.columns else df.iloc[:, 0].tolist()
        highs = df['high'].tolist() if 'high' in df.columns else closes
        lows = df['low'].tolist() if 'low' in df.columns else closes
        volumes = df['volume'].tolist() if 'volume' in df.columns else [1.0] * len(closes)
        
        # 处理时间戳
        timestamps = None
        if 'timestamp' in df.columns:
            timestamps = df['timestamp'].tolist()
        elif 'bob' in df.columns:
            timestamps = df['bob'].tolist()
        
        return StockData(closes, highs, lows, volumes, timestamps)
    
    def _convert_kdj_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换KDJ结果格式"""
        if not result.get('success'):
            return {'kdj_k': 50, 'kdj_d': 50, 'kdj_j': 50}
        
        return {
            'kdj_k': result.get('kdj_k', 50),
            'kdj_d': result.get('kdj_d', 50),
            'kdj_j': result.get('kdj_j', 50)
        }
    
    def _convert_deepv_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换深V结果格式"""
        if not result.get('success'):
            return {'deepv_signal': False}
        
        return {
            'dv_short': result.get('dv_short'),
            'dv_long': result.get('dv_long'),
            'deepv_signal': result.get('deepv_signal', False)
        }
    
    def _convert_trend_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换趋势结果格式"""
        if not result.get('success'):
            return {}
        
        return {
            'white_line': result.get('white_line'),
            'yellow_line': result.get('yellow_line'),
            'bbi_line': result.get('bbi_line'),
            'white_slope': result.get('white_slope', 0),
            'yellow_slope': result.get('yellow_slope', 0)
        }
    
    def _convert_comprehensive_result(self, result: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """转换综合结果格式"""
        if not result.get('success'):
            return {'error': result.get('error', '计算失败')}
        
        comprehensive_result = {
            'total_score': result.get('total_score', 0),
            'current_price': df['close'].iloc[-1] if not df.empty else 0,
            'timestamp': result.get('timestamp', '')
        }
        
        # 提取各个指标结果
        results = result.get('results', {})
        
        for indicator_name, indicator_result in results.items():
            if indicator_result.get('success'):
                if indicator_name == 'kdj':
                    comprehensive_result['kdj'] = self._convert_kdj_result(indicator_result)
                elif indicator_name == 'deepv':
                    comprehensive_result['deepv'] = self._convert_deepv_result(indicator_result)
                elif indicator_name == 'trend':
                    comprehensive_result['trend'] = self._convert_trend_result(indicator_result)
        
        return comprehensive_result
    
    def _calculate_total_score(self, kdj_result: Dict, deepv_result: Dict, trend_result: Dict) -> int:
        """计算综合评分（本地实现）"""
        total_score = 0
        
        # KDJ评分 (0-40分)
        kdj_j = kdj_result.get('kdj_j', 50)
        if kdj_j < 20:
            total_score += 40  # 超卖，买入信号强
        elif kdj_j > 80:
            total_score += 10  # 超买，卖出信号
        else:
            total_score += 25  # 中性
        
        # 深V评分 (0-30分)
        if deepv_result.get('deepv_signal', False):
            total_score += 30
        
        # 趋势评分 (0-30分)
        white_slope = trend_result.get('white_slope', 0)
        yellow_slope = trend_result.get('yellow_slope', 0)
        if white_slope > 0 and yellow_slope > 0:
            total_score += 30  # 上升趋势
        elif white_slope < 0 and yellow_slope < 0:
            total_score += 10  # 下降趋势
        else:
            total_score += 20  # 震荡趋势
        
        return min(total_score, 100)
    
    def get_available_indicators(self) -> Dict[str, Any]:
        """获取可用指标列表"""
        if self.use_shared:
            return self.unified_service.get_available_indicators()
        else:
            return {
                'categories': ['oscillator', 'pattern', 'trend'],
                'indicators': {
                    'oscillator': {'kdj': 'KDJ随机指标'},
                    'pattern': {'deepv': '深V信号指标'},
                    'trend': {'trend': '趋势指标'}
                }
            }
    
    def is_shared_available(self) -> bool:
        """检查共享库是否可用"""
        return self.use_shared


# 全局适配器实例
emgm_adapter = EMGMIndicatorAdapter()