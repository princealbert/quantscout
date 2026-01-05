# coding=utf-8
"""
综合评分模块 - 负责计算最终的综合评分
"""

from typing import Dict, Any
from config.weights_config import weight_config
from scoring.weight_scorer import WeightScorer


class ComprehensiveScorer:
    """综合评分计算器"""
    
    def __init__(self, custom_weights: Dict[str, int] = None, sub_weights_config: Dict[str, Any] = None):
        self.weight_scorer = WeightScorer(custom_weights, sub_weights_config)
        self.score_weights = self.weight_scorer.score_weights
    
    def calculate_comprehensive_score(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算综合评分（百分制）"""
        try:
            score_details = {}
            
            # 调试信息：显示当前使用的权重配置已被注释
            
            # 1. KDJ J值权重
            j_value = float(stock_data.get('kdj_j', 50))
            kdj_final_score = float(self.weight_scorer.calculate_kdj_j_weight(j_value))
            score_details['kdj_score'] = kdj_final_score
            
            # 调试KDJ评分计算
            # print(f"[DEBUG] KDJ J值: {j_value}, KDJ总分: {kdj_final_score}")
            
            # 2. 趋势权重
            trend_score = self.weight_scorer.calculate_trend_score(stock_data)
            score_details['trend_score'] = trend_score
            # print(f"[DEBUG] 趋势总分: {trend_score}")
            
            # 3. 深V信号权重
            deepv_data = stock_data.get('deepv', {})
            deepv_signal = deepv_data.get('deepv_signal', False)
            deepv_score = 1 if deepv_signal else 0
            score_details['deepv_score'] = round(deepv_score * self.score_weights['deepv'], 1)
            # print(f"[DEBUG] 深V信号: {deepv_signal}, 深V总分: {score_details['deepv_score']}")
            
            # 4. 成交量权重
            volume_analysis = stock_data.get('volume_analysis', {})
            volume_score = self.weight_scorer.calculate_volume_weight(volume_analysis)
            score_details['volume_score'] = volume_score
            # print(f"[DEBUG] 成交量总分: {volume_score}")
            
            # 5. 基本面权重
            fundamental_data = {
                'pe': stock_data.get('pe', 100),
                'a_mv': stock_data.get('a_mv', 0),
                'volume_threshold': stock_data.get('volume_threshold', False)
            }
            fundamental_score = self.weight_scorer.calculate_fundamental_score(fundamental_data)
            score_details['fundamental_score'] = fundamental_score
            # print(f"[DEBUG] 基本面总分: {fundamental_score}")
            
            # 6. 位置权重
            close_price = float(stock_data.get('close', 0))
            zhi_xing_data = stock_data.get('zhi_xing', {})
            white_line = zhi_xing_data.get('white_line')
            yellow_line = zhi_xing_data.get('yellow_line')
            position_score, position_desc = self.weight_scorer.calculate_position_weight(
                close_price, white_line, yellow_line
            )
            score_details['position_score'] = float(position_score)
            score_details['position_desc'] = position_desc
            # print(f"[DEBUG] 位置: {position_desc}, 位置总分: {position_score}")
            
            # 7. 盈亏比权重
            risk_reward_data = self._calculate_risk_reward_ratio(stock_data)
            risk_reward_score = risk_reward_data.get('risk_reward_score', 0)
            score_details['risk_reward_score'] = round(risk_reward_score * self.score_weights['risk_reward'], 1)
            # print(f"[DEBUG] 盈亏比: {risk_reward_data.get('risk_reward_ratio', 0)}, 盈亏比总分: {score_details['risk_reward_score']}")
            
            # 将盈亏比数据添加到股票数据中
            stock_data['risk_reward_data'] = risk_reward_data
            
            # 总分（百分制）
            total_score = sum([float(v) for v in score_details.values() if isinstance(v, (int, float))])
            score_details['total_score'] = round(min(total_score, 100), 1)  # 限制最高100分并保留1位小数
            
            return score_details
            
        except Exception as e:
            return {'total_score': 0}
    
    def _calculate_risk_reward_ratio(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算盈亏比权重"""
        try:
            df = stock_data.get('df', None)
            close_price = float(stock_data.get('close', 0))
            zhi_xing_data = stock_data.get('zhi_xing', {})
            
            if df is None or len(df) < 31:
                return {'risk_reward_ratio': 0, 'risk_reward_score': 0, 'stop_loss_price': 0, 'target_price': 0}
            
            # 计算目标价：近30个交易日的最高价
            high_prices = df['high'] if hasattr(df['high'], 'iloc') else df['high']
            target_price = float(high_prices.iloc[-30:].max()) if len(high_prices) >= 30 else close_price * 1.1
            
            # 根据位置计算止损价
            white_line = zhi_xing_data.get('white_line')
            yellow_line = zhi_xing_data.get('yellow_line')
            
            # 获取前一日最低价
            low_prices = df['low'] if hasattr(df['low'], 'iloc') else df['low']
            prev_low = float(low_prices.iloc[-2]) if len(low_prices) >= 2 else close_price * 0.95
            
            # 根据位置确定止损价
            if white_line is not None and yellow_line is not None:
                if close_price >= white_line:  # 白线上方
                    stop_loss_price = white_line
                elif close_price >= yellow_line:  # 碗里（黄白线之间）
                    stop_loss_price = yellow_line
                else:  # 黄线下方
                    stop_loss_price = prev_low
            else:
                stop_loss_price = prev_low
            
            # 计算盈亏比
            potential_profit = target_price - close_price
            potential_loss = close_price - stop_loss_price
            
            # 避免除零错误
            if potential_loss <= 0:
                risk_reward_ratio = 0
            else:
                risk_reward_ratio = potential_profit / potential_loss
            
            # 计算盈亏比权重分
            if risk_reward_ratio >= 3.0:
                risk_reward_score = min(risk_reward_ratio / 10.0, 1.0)  # 归一化到0-1
            else:
                risk_reward_score = (risk_reward_ratio - 3.0) / 3.0  # 低于3:1给负分
            
            return {
                'risk_reward_ratio': risk_reward_ratio,
                'risk_reward_score': max(risk_reward_score, -1.0),  # 限制最低分
                'stop_loss_price': stop_loss_price,
                'target_price': target_price
            }
            
        except Exception as e:
            return {'risk_reward_ratio': 0, 'risk_reward_score': 0, 'stop_loss_price': 0, 'target_price': 0}