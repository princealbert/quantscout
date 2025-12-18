#!/usr/bin/env python
# coding=utf-8
"""
短期策略优化器 - 针对短期交易特点优化的参数配置
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


class ShortTermOptimizer:
    """短期策略优化器"""
    
    def __init__(self):
        """初始化优化器"""
        self.optimization_configs = self._load_optimization_configs()
    
    def _load_optimization_configs(self) -> Dict[str, Dict[str, Any]]:
        """加载优化配置"""
        
        configs = {
            "aggressive_short_term": {
                "name": "激进短期策略",
                "description": "高风险高回报的短期交易策略",
                "weights": {
                    "kdj_j": 15,   # 降低KDJ权重，短期波动大
                    "trend": 35,   # 提高趋势权重，捕捉短期趋势
                    "deepv": 5,    # 降低深V信号权重
                    "volume": 20,  # 提高成交量权重
                    "fundamental": 5,  # 降低基本面权重
                    "position": 10,    # 保持位置权重
                    "risk_reward": 10  # 降低盈亏比权重
                },
                "sub_weights": {
                    "kdj_j": {
                        "total_weight": 15,
                        "sub_weights": {
                            "j_0_20": 1,
                            "j_-10_0": 2,
                            "j_-20_-10": 3,
                            "j_-30_-20": 4,
                            "j_below_-30": 5
                        }
                    },
                    "trend": {
                        "total_weight": 35,
                        "sub_weights": {
                            "up_trend": 20,  # 强调上升趋势
                            "volume_price_rise": 8,
                            "volume_contraction": 7
                        }
                    },
                    "volume": {
                        "total_weight": 20,
                        "sub_weights": {
                            "big_volume": 8,  # 强调放量
                            "volume_anomaly": 6,
                            "volume_breathing": 6
                        }
                    }
                },
                "screening_params": {
                    "max_results": 10,
                    "skip_st": True,
                    "test_mode": False,
                    "batch_size": 500,  # 小批量处理，提高速度
                    "max_workers": 4,   # 减少线程数
                    "stock_pool_type": "沪深300"  # 聚焦流动性好的股票
                },
                "backtest_params": {
                    "backtest_days": 30,  # 短期回测
                    "initial_capital": 50000,
                    "max_stocks": 3
                }
            },
            "conservative_short_term": {
                "name": "稳健短期策略",
                "description": "风险可控的短期策略",
                "weights": {
                    "kdj_j": 20,
                    "trend": 25,
                    "deepv": 10,
                    "volume": 15,
                    "fundamental": 10,
                    "position": 10,
                    "risk_reward": 10
                },
                "sub_weights": {
                    "kdj_j": {
                        "total_weight": 20,
                        "sub_weights": {
                            "j_0_20": 2,
                            "j_-10_0": 3,
                            "j_-20_-10": 4,
                            "j_-30_-20": 5,
                            "j_below_-30": 6
                        }
                    },
                    "trend": {
                        "total_weight": 25,
                        "sub_weights": {
                            "up_trend": 12,
                            "volume_price_rise": 7,
                            "volume_contraction": 6
                        }
                    }
                },
                "screening_params": {
                    "max_results": 15,
                    "skip_st": True,
                    "test_mode": False,
                    "batch_size": 1000,
                    "max_workers": 6,
                    "stock_pool_type": "全量A股"
                },
                "backtest_params": {
                    "backtest_days": 60,
                    "initial_capital": 100000,
                    "max_stocks": 5
                }
            },
            "momentum_short_term": {
                "name": "动量短期策略",
                "description": "捕捉短期动量效应的策略",
                "weights": {
                    "kdj_j": 10,   # 最低KDJ权重
                    "trend": 40,   # 最高趋势权重
                    "deepv": 0,    # 忽略深V信号
                    "volume": 25,  # 高成交量权重
                    "fundamental": 0,  # 忽略基本面
                    "position": 15,    # 中等位置权重
                    "risk_reward": 10
                },
                "sub_weights": {
                    "trend": {
                        "total_weight": 40,
                        "sub_weights": {
                            "up_trend": 25,  # 极度强调上升趋势
                            "volume_price_rise": 10,
                            "volume_contraction": 5
                        }
                    },
                    "volume": {
                        "total_weight": 25,
                        "sub_weights": {
                            "big_volume": 12,  # 强调放量
                            "volume_anomaly": 8,
                            "volume_breathing": 5
                        }
                    }
                },
                "screening_params": {
                    "max_results": 8,
                    "skip_st": True,
                    "test_mode": False,
                    "batch_size": 300,
                    "max_workers": 3,
                    "stock_pool_type": "创业板"  # 聚焦高波动性股票
                },
                "backtest_params": {
                    "backtest_days": 20,  # 超短期回测
                    "initial_capital": 30000,
                    "max_stocks": 2
                }
            }
        }
        
        return configs
    
    def get_optimization_configs(self) -> List[Dict[str, Any]]:
        """获取所有优化配置"""
        
        configs_list = []
        for config_id, config_data in self.optimization_configs.items():
            config_info = {
                "id": config_id,
                "name": config_data["name"],
                "description": config_data["description"],
                "risk_level": self._assess_risk_level(config_data),
                "recommended_for": self._get_recommendation(config_data)
            }
            configs_list.append(config_info)
        
        return configs_list
    
    def get_recommended_configs(self) -> List[Dict[str, Any]]:
        """获取推荐配置列表 - 兼容测试用的方法"""
        return self.get_optimization_configs()
    
    def generate_optimized_params(self, strategy_type: str) -> Dict[str, Any]:
        """
        生成优化后的参数配置
        
        Args:
            strategy_type: 策略类型 (aggressive, conservative, momentum)
            
        Returns:
            Dict[str, Any]: 优化后的参数配置
        """
        
        config_id_map = {
            "aggressive": "aggressive_short_term",
            "conservative": "conservative_short_term", 
            "momentum": "momentum_short_term"
        }
        
        config_id = config_id_map.get(strategy_type, "conservative_short_term")
        return self.get_optimization_config(config_id)
    
    def get_optimization_config(self, config_id: str) -> Dict[str, Any]:
        """获取特定优化配置"""
        
        if config_id in self.optimization_configs:
            return self.optimization_configs[config_id]
        else:
            # 返回默认配置
            return self.optimization_configs["conservative_short_term"]
    
    def _assess_risk_level(self, config_data: Dict[str, Any]) -> str:
        """评估风险等级"""
        
        # 基于权重配置评估风险
        weights = config_data["weights"]
        
        # 高风险指标：低KDJ权重、高趋势权重、低基本面权重
        risk_score = (
            (100 - weights.get("kdj_j", 0)) * 0.3 +  # KDJ权重越低风险越高
            weights.get("trend", 0) * 0.4 +          # 趋势权重越高风险越高
            (100 - weights.get("fundamental", 0)) * 0.3  # 基本面权重越低风险越高
        ) / 100
        
        if risk_score > 0.7:
            return "高"
        elif risk_score > 0.4:
            return "中"
        else:
            return "低"
    
    def _get_recommendation(self, config_data: Dict[str, Any]) -> str:
        """获取推荐说明"""
        
        risk_level = self._assess_risk_level(config_data)
        
        if risk_level == "高":
            return "适合经验丰富的交易者，追求高回报"
        elif risk_level == "中":
            return "适合大多数投资者，平衡风险与收益"
        else:
            return "适合保守型投资者，注重资金安全"
    
    def optimize_for_market_condition(self, market_condition: str) -> Dict[str, Any]:
        """根据市场状况优化配置"""
        
        market_conditions = {
            "bull": "牛市",
            "bear": "熊市", 
            "volatile": "震荡市",
            "stable": "平稳市"
        }
        
        # 根据市场状况选择不同的优化配置
        if market_condition == "bull":
            # 牛市：激进策略
            return self.optimization_configs["aggressive_short_term"]
        elif market_condition == "bear":
            # 熊市：保守策略
            return self.optimization_configs["conservative_short_term"]
        elif market_condition == "volatile":
            # 震荡市：动量策略
            return self.optimization_configs["momentum_short_term"]
        else:
            # 平稳市：默认保守策略
            return self.optimization_configs["conservative_short_term"]
    
    def generate_optimization_report(self, config_id: str) -> str:
        """生成优化报告"""
        
        config = self.get_optimization_config(config_id)
        
        report = f"""
# 📊 短期策略优化报告

**策略名称**: {config['name']}  
**策略描述**: {config['description']}  
**风险等级**: {self._assess_risk_level(config)}  
**推荐对象**: {self._get_recommendation(config)}  

## 权重配置分析

"""
        
        # 添加权重分析
        weights = config["weights"]
        for key, value in weights.items():
            analysis = self._analyze_weight(key, value)
            report += f"- **{key}**: {value}分 - {analysis}\n"
        
        report += f"""

## 筛选参数
- 最大结果数: {config['screening_params']['max_results']}
- 股票池类型: {config['screening_params']['stock_pool_type']}
- 批次大小: {config['screening_params']['batch_size']}

## 回测建议
- 回测天数: {config['backtest_params']['backtest_days']}天
- 初始资金: {config['backtest_params']['initial_capital']:,}元
- 回测股票数: {config['backtest_params']['max_stocks']}只

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def _analyze_weight(self, weight_key: str, weight_value: int) -> str:
        """分析权重配置"""
        
        analysis_map = {
            "kdj_j": {
                "high": "过度依赖技术指标，可能错失基本面机会",
                "medium": "平衡技术分析与基本面",
                "low": "轻技术重趋势，适合短期交易"
            },
            "trend": {
                "high": "强调趋势跟踪，适合趋势市",
                "medium": "平衡趋势与反转信号",
                "low": "轻趋势重价值，适合价值投资"
            },
            "volume": {
                "high": "重视成交量，适合短线操作",
                "medium": "平衡量与价的关系",
                "low": "轻量重质，适合长线投资"
            }
        }
        
        if weight_key in analysis_map:
            if weight_value >= 25:
                level = "high"
            elif weight_value >= 15:
                level = "medium"
            else:
                level = "low"
            
            return analysis_map[weight_key].get(level, "")
        
        return ""


# 快速优化函数
def quick_optimize(strategy_type: str = "conservative") -> Dict[str, Any]:
    """
    快速优化函数
    
    Args:
        strategy_type: 策略类型 (aggressive, conservative, momentum)
        
    Returns:
        Dict[str, Any]: 优化后的配置
    """
    
    optimizer = ShortTermOptimizer()
    
    config_id_map = {
        "aggressive": "aggressive_short_term",
        "conservative": "conservative_short_term", 
        "momentum": "momentum_short_term"
    }
    
    config_id = config_id_map.get(strategy_type, "conservative_short_term")
    return optimizer.get_optimization_config(config_id)


def get_optimization_options() -> List[Dict[str, Any]]:
    """获取优化选项列表"""
    
    optimizer = ShortTermOptimizer()
    return optimizer.get_optimization_configs()