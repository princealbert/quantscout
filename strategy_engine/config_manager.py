#!/usr/bin/env python
# coding=utf-8
"""
配置管理模块 - 负责策略参数的统一管理
与现有的strategy_params.py整合，提供更高级的配置管理功能
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime


class ConfigManager:
    """配置管理器 - 负责策略参数的统一管理"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为None（使用默认路径）
        """
        if config_path is None:
            # 使用项目根目录下的config目录
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, 'config', 'strategy_config.json')
        
        self.config_path = config_path
        self._ensure_config_file()
    
    def _ensure_config_file(self):
        """确保配置文件存在"""
        if not os.path.exists(self.config_path):
            # 创建默认配置
            default_config = self._get_default_config()
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            self._save_config(default_config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "backtest": {
                "initial_capital": 100000,
                "commission_ratio": 0.0003,
                "slippage_ratio": 0.0001,
                "backtest_days": 360,
                "max_stocks_to_backtest": 1,
                "stock_pool_limit": 50
            },
            "trading": {
                "stop_profit_ratio": 0.20,
                "stop_loss_ratio": -0.1,
                "max_position_ratio": 1.0,
                "min_trade_amount": 100
            },
            "strategy": {
                "strategy_id": "zge_strategy_v1",
                "strategy_type": "碗选股",
                "weights_config": {
                    "kdj": 25,
                    "macd": 20,
                    "rsi": 15,
                    "boll": 20,
                    "volume": 20
                },
                "sub_weights_config": {
                    "kdj": {"sub_weights": {"j_value": 60, "k_d_cross": 40}},
                    "macd": {"sub_weights": {"diff": 40, "dea": 30, "histogram": 30}},
                    "rsi": {"sub_weights": {"rsi6": 40, "rsi12": 30, "rsi24": 30}},
                    "boll": {"sub_weights": {"upper": 35, "middle": 30, "lower": 35}},
                    "volume": {"sub_weights": {"volume_ratio": 60, "volume_trend": 40}}
                }
            },
            "risk_management": {
                "max_drawdown_limit": -0.15,
                "max_position_concentration": 0.5,
                "volatility_limit": 0.1
            },
            "fallback": {
                "fallback_stocks": ["000001.SZ", "000002.SZ", "000858.SZ", "600036.SH", "601318.SH"]
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        try:
            config['last_modified'] = datetime.now().isoformat()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
    
    def get_backtest_params(self) -> Dict[str, Any]:
        """获取回测参数"""
        config = self.load_config()
        return config.get('backtest', {})
    
    def get_trading_params(self) -> Dict[str, Any]:
        """获取交易参数"""
        config = self.load_config()
        return config.get('trading', {})
    
    def get_strategy_params(self) -> Dict[str, Any]:
        """获取策略参数"""
        config = self.load_config()
        return config.get('strategy', {})
    
    def get_risk_params(self) -> Dict[str, Any]:
        """获取风控参数"""
        config = self.load_config()
        return config.get('risk_management', {})
    
    def update_backtest_params(self, new_params: Dict[str, Any]):
        """更新回测参数"""
        config = self.load_config()
        config['backtest'].update(new_params)
        self._save_config(config)
    
    def update_trading_params(self, new_params: Dict[str, Any]):
        """更新交易参数"""
        config = self.load_config()
        config['trading'].update(new_params)
        self._save_config(config)
    
    def update_strategy_params(self, new_params: Dict[str, Any]):
        """更新策略参数"""
        config = self.load_config()
        config['strategy'].update(new_params)
        self._save_config(config)
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置有效性"""
        config = self.load_config()
        issues = []
        
        # 验证回测参数
        backtest = config.get('backtest', {})
        if backtest.get('initial_capital', 0) <= 0:
            issues.append("初始资金必须大于0")
        if backtest.get('commission_ratio', 0) < 0:
            issues.append("佣金比例不能为负数")
        
        # 验证交易参数
        trading = config.get('trading', {})
        if trading.get('stop_profit_ratio', 0) <= trading.get('stop_loss_ratio', 0):
            issues.append("止盈比例必须大于止损比例")
        
        # 验证策略参数
        strategy = config.get('strategy', {})
        weights = strategy.get('weights_config', {})
        if sum(weights.values()) != 100:
            issues.append("权重配置总和必须等于100")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "config_summary": {
                "backtest_params": len(backtest),
                "trading_params": len(trading),
                "strategy_params": len(strategy)
            }
        }
    
    def export_config_template(self, export_path: str):
        """导出配置模板"""
        template = self._get_default_config()
        
        # 添加说明文档
        template['_description'] = """
z哥选股策略配置模板

配置说明:
1. backtest: 回测相关参数
2. trading: 交易相关参数  
3. strategy: 策略权重配置
4. risk_management: 风险控制参数
5. fallback: 备用参数

注意事项:
- 权重配置总和必须等于100
- 止盈比例必须大于止损比例
- 所有数值参数都需要合理设置
"""
        
        try:
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            print(f"✅ 配置模板已导出到: {export_path}")
        except Exception as e:
            print(f"❌ 导出配置模板失败: {e}")
    
    def create_custom_config(self, config_name: str, custom_params: Dict[str, Any]) -> bool:
        """创建自定义配置"""
        try:
            # 创建自定义配置目录
            custom_dir = os.path.join(os.path.dirname(self.config_path), 'custom')
            os.makedirs(custom_dir, exist_ok=True)
            
            # 基于默认配置创建自定义配置
            base_config = self._get_default_config()
            base_config.update(custom_params)
            base_config['config_name'] = config_name
            base_config['created_at'] = datetime.now().isoformat()
            
            # 保存自定义配置
            custom_path = os.path.join(custom_dir, f"{config_name}.json")
            with open(custom_path, 'w', encoding='utf-8') as f:
                json.dump(base_config, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 自定义配置 '{config_name}' 已创建: {custom_path}")
            return True
            
        except Exception as e:
            print(f"❌ 创建自定义配置失败: {e}")
            return False


class FrontendConfigLoader:
    """
    前端配置加载器 - 负责读取和处理前端生成的JSON配置文件
    """
    
    @staticmethod
    def get_fixed_config_path() -> str:
        """
        获取固定配置文件的路径
        
        Returns:
            str: 固定配置文件路径
        """
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, "config", "current_backtest_config.json")
    
    @staticmethod
    def load_fixed_config() -> Optional[Dict[str, Any]]:
        """
        加载固定配置文件（config/current_backtest_config.json）
        
        Returns:
            Dict[str, Any]: 配置数据，如果加载失败则返回None
        """
        fixed_config_path = FrontendConfigLoader.get_fixed_config_path()
        return FrontendConfigLoader.load_frontend_config(fixed_config_path)
    
    @staticmethod
    def load_frontend_config(config_path: str) -> Optional[Dict[str, Any]]:
        """
        加载前端生成的JSON配置文件
        
        Args:
            config_path: JSON配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据，如果加载失败则返回None
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载前端配置文件失败: {e}")
            return None
    
    @staticmethod
    def convert_to_strategy_params(frontend_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        将前端配置转换为StrategyParams兼容的格式
        
        Args:
            frontend_config: 前端生成的配置数据
            
        Returns:
            Dict[str, Any]: 转换后的配置数据
        """
        backtest = frontend_config.get('backtest', {})
        strategy = frontend_config.get('strategy', {})
        selected_stocks = frontend_config.get('selected_stocks', [])
        
        return {
            'initial_capital': backtest.get('initial_capital', 100000),
            'commission_ratio': 0.0003,  # 默认值
            'backtest_days': backtest.get('backtest_days', 90),
            'stop_profit_ratio': strategy.get('stop_profit_ratio', 0.03),
            'stop_loss_ratio': strategy.get('stop_loss_ratio', -0.02),
            'strategy_id': backtest.get('strategy_id', f"zge_strategy_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            'strategy_type': strategy.get('strategy_type', 'zge_strategy'),
            'max_stocks_to_backtest': backtest.get('max_stocks_to_backtest', len(selected_stocks)),
            'stock_pool_limit': None,  # 默认值
            'weights_config': strategy.get('weights_config', {}),
            'sub_weights_config': strategy.get('sub_weights_config', {}),
            'fallback_stocks': selected_stocks  # 使用前端选择的股票作为备选股票
        }
    
    @staticmethod
    def get_selected_stocks(frontend_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取前端选择的股票列表
        
        Args:
            frontend_config: 前端生成的配置数据
            
        Returns:
            List[Dict[str, Any]]: 选中的股票列表
        """
        return frontend_config.get('selected_stocks', [])
    
    @staticmethod
    def validate_frontend_config(frontend_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证前端配置的有效性
        
        Args:
            frontend_config: 前端生成的配置数据
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        issues = []
        
        # 验证基本结构
        if 'backtest' not in frontend_config:
            issues.append("缺少回测配置")
        if 'strategy' not in frontend_config:
            issues.append("缺少策略配置")
        if 'selected_stocks' not in frontend_config:
            issues.append("缺少选股结果")
        
        # 验证回测参数
        backtest = frontend_config.get('backtest', {})
        if backtest.get('initial_capital', 0) <= 0:
            issues.append("初始资金必须大于0")
        if backtest.get('backtest_days', 0) <= 0:
            issues.append("回测天数必须大于0")
        
        # 验证策略参数
        strategy = frontend_config.get('strategy', {})
        weights = strategy.get('weights_config', {})
        if weights and sum(weights.values()) != 100:
            issues.append("权重配置总和必须等于100")
        
        # 验证选股结果
        selected_stocks = frontend_config.get('selected_stocks', [])
        if not selected_stocks:
            issues.append("选股结果不能为空")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }


def get_current_config() -> Dict[str, Any]:
    """
    获取当前配置（快速函数）
    
    Returns:
        Dict[str, Any]: 当前配置
    """
    manager = ConfigManager()
    return manager.load_config()


def update_backtest_config(new_params: Dict[str, Any]) -> bool:
    """
    更新回测配置（快速函数）
    
    Args:
        new_params: 新参数
        
    Returns:
        bool: 是否成功
    """
    manager = ConfigManager()
    manager.update_backtest_params(new_params)
    return True


def validate_current_config() -> Dict[str, Any]:
    """
    验证当前配置（快速函数）
    
    Returns:
        Dict[str, Any]: 验证结果
    """
    manager = ConfigManager()
    return manager.validate_config()


# 与现有strategy_params.py的兼容性函数
def get_strategy_params_compatible() -> Dict[str, Any]:
    """
    获取策略参数（兼容现有代码）
    
    Returns:
        Dict[str, Any]: 策略参数
    """
    manager = ConfigManager()
    config = manager.load_config()
    
    # 转换为与StrategyParams类兼容的格式
    strategy_params = config.get('strategy', {})
    backtest_params = config.get('backtest', {})
    trading_params = config.get('trading', {})
    fallback_params = config.get('fallback', {})
    
    return {
        'initial_capital': backtest_params.get('initial_capital', 100000),
        'commission_ratio': backtest_params.get('commission_ratio', 0.0003),
        'backtest_days': backtest_params.get('backtest_days', 90),
        'stop_profit_ratio': trading_params.get('stop_profit_ratio', 0.03),
        'stop_loss_ratio': trading_params.get('stop_loss_ratio', -0.02),
        'strategy_id': strategy_params.get('strategy_id', 'zge_strategy_v1'),
        'strategy_type': strategy_params.get('strategy_type', '碗选股'),
        'max_stocks_to_backtest': backtest_params.get('max_stocks_to_backtest', 1),
        'stock_pool_limit': backtest_params.get('stock_pool_limit', 50),
        'weights_config': strategy_params.get('weights_config', {}),
        'sub_weights_config': strategy_params.get('sub_weights_config', {}),
        'fallback_stocks': fallback_params.get('fallback_stocks', [])
    }