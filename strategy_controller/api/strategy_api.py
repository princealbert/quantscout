#!/usr/bin/env python
# coding=utf-8
"""
策略参数API接口 - 提供前端与回测系统之间的参数传递接口
"""

import json
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Any


class StrategyAPI:
    """策略参数API类"""
    
    def __init__(self, api_base_path: str = None):
        """
        初始化API
        
        Args:
            api_base_path: API文件存储的基础路径
        """
        if api_base_path is None:
            # 使用临时目录作为默认路径
            api_base_path = os.path.join(tempfile.gettempdir(), "multi_dim_strategy_api")
        
        self.api_base_path = api_base_path
        os.makedirs(self.api_base_path, exist_ok=True)
    
    def save_strategy_config(self, 
                           strategy_results: List[Dict[str, Any]],
                           strategy_type: str,
                           weights_config: Dict[str, int],
                           sub_weights_config: Dict[str, Any] = None,
                           backtest_params: Dict[str, Any] = None) -> str:
        """
        保存策略配置到API文件
        
        Args:
            strategy_results: 选股结果
            strategy_type: 策略类型
            weights_config: 权重配置
            sub_weights_config: 子权重配置
            backtest_params: 回测参数
            
        Returns:
            str: 配置文件的路径
        """
        
        # 生成配置ID
        config_id = f"strategy_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        config_path = os.path.join(self.api_base_path, f"{config_id}.json")
        
        # 构建配置数据
        config_data = {
            "config_id": config_id,
            "created_at": datetime.now().isoformat(),
            "strategy_info": {
                "strategy_type": strategy_type,
                "selected_stocks_count": len(strategy_results)
            },
            "strategy_config": {
                "weights": weights_config,
                "sub_weights": sub_weights_config or {}
            },
            "backtest_params": backtest_params or {
                "backtest_days": 90,
                "initial_capital": 100000,
                "selected_stocks_count": 1
            },
            "selected_stocks": [
                {
                    "symbol": stock.get("symbol", stock.get("code", "000000")),
                    "sec_name": stock.get("sec_name", stock.get("name", "未知股票")),
                    "total_score": stock.get("total_score", stock.get("score", 0)),
                    "close_price": stock.get("close", 0),
                    "kdj_j": stock.get("kdj_j", 0),
                    "position_desc": stock.get("position_desc", "未知"),
                    "risk_reward_ratio": stock.get("risk_reward_data", {}).get("risk_reward_ratio", 0),
                    "target_price": stock.get("risk_reward_data", {}).get("target_price", 0),
                    "stop_loss_price": stock.get("risk_reward_data", {}).get("stop_loss_price", 0)
                }
                for stock in strategy_results
            ]
        }
        
        # 保存到文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 策略配置已保存: {config_path}")
        return config_path
    
    def load_strategy_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载策略配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            print(f"✅ 策略配置已加载: {config_path}")
            return config_data
            
        except Exception as e:
            print(f"❌ 加载策略配置失败: {e}")
            return {}
    
    def generate_backtest_script(self, config_data: Dict[str, Any]) -> str:
        """
        生成回测脚本
        
        Args:
            config_data: 策略配置数据
            
        Returns:
            str: 回测脚本路径
        """
        
        # 创建回测脚本
        script_content = self._build_backtest_script(config_data)
        
        # 保存脚本文件
        script_filename = f"backtest_{config_data['config_id']}.py"
        script_path = os.path.join(self.api_base_path, script_filename)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ 回测脚本已生成: {script_path}")
        return script_path
    
    def _build_backtest_script(self, config_data: Dict[str, Any]) -> str:
        """构建回测脚本内容"""
        
        strategy_type = config_data["strategy_info"]["strategy_type"]
        backtest_params = config_data["backtest_params"]
        selected_stocks = config_data["selected_stocks"]
        
        script_content = f'''#!/usr/bin/env python
# coding=utf-8
"""
QuantScout选股策略回测脚本 - 通过API自动生成
策略类型: {strategy_type}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
import os
import json
from datetime import datetime, timedelta

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gm.api import *


def load_strategy_config():
    """加载策略配置"""
    config_path = os.path.join(os.path.dirname(__file__), "{config_data['config_id']}.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载策略配置失败: {{e}}")
        return None


def main():
    """主回测函数"""
    
    # 加载策略配置
    config_data = load_strategy_config()
    if not config_data:
        print("❌ 无法加载策略配置，回测终止")
        return
    
    # 打印策略信息
    strategy_type = config_data["strategy_info"]["strategy_type"]
    selected_stocks = config_data["selected_stocks"]
    backtest_params = config_data["backtest_params"]
    
    print("=" * 60)
    print("🎯 QuantScout选股策略回测系统")
    print("=" * 60)
    print(f"策略类型: {{strategy_type}}")
    print(f"回测股票: {{len(selected_stocks)}}只")
    print(f"初始资金: {{backtest_params.get('initial_capital', 100000):,}}元")
    print(f"回测天数: {{backtest_params.get('backtest_days', 90)}}天")
    
    # 显示选股结果
    print("\\n📊 选股结果:")
    for i, stock in enumerate(selected_stocks, 1):
        print(f"  {{i}}. {{stock['symbol']}} ({{stock['sec_name']}})")
        print(f"     评分: {{stock.get('total_score', 0):.2f}}, J值: {{stock.get('kdj_j', 0):.2f}}")
        print(f"     位置: {{stock.get('position_desc', '未知')}}, 盈亏比: {{stock.get('risk_reward_ratio', 0):.2f}}")
    
    # 导入参数化配置系统（使用相对路径）
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    from config.strategy_params import StrategyParams
    
    # 创建基于用户配置的参数化配置
    strategy_params = StrategyParams(
        initial_capital=backtest_params.get('initial_capital', 100000),
        backtest_days=backtest_params.get('backtest_days', 90),
        strategy_type=strategy_type,
        max_stocks_to_backtest=len(selected_stocks)
    )
    
    # 使用参数化配置系统获取回测参数
    backtest_days = strategy_params.backtest_days
    initial_capital = strategy_params.initial_capital
    selected_stocks_count = strategy_params.max_stocks_to_backtest
    
    # 获取回测期间（基于参数化配置）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=backtest_days)
    
    strategy_id = f"multi_dim_strategy_{{config_data['config_id']}}"
    
    print(f"\\n🚀 准备启动回测...")
    print(f"回测期间: {{start_date.strftime('%Y-%m-%d')}} 到 {{end_date.strftime('%Y-%m-%d')}}")
    print(f"回测天数: {{backtest_days}}天")
    print(f"初始资金: {{initial_capital:,}}元")
    print(f"股票数量: {{selected_stocks_count}}只")
    print(f"策略ID: {{strategy_id}}")
    print(f"使用参数化配置系统 - 无硬编码参数")
    
    # 重要提示
    print("\\n⚠️  重要提示:")
    print("1. 请确保已安装东财掘金Python SDK")
    print("2. 请在下方替换YOUR_TOKEN_HERE为你的实际API token")
    print("3. 回测需要有效的网络连接")
    
    # 这里是实际回测代码（需要用户提供token）
    print("\\n📋 回测代码示例（需要配置token）:")
    print("```python")
    print(f"# 运行回测（取消注释并配置token后执行）")
    print(f"# run(")
    print(f"#     strategy_id=strategy_id,")
    print(f"#     filename=__file__,")
    print(f"#     mode=MODE_BACKTEST,")
    print(f"#     token='YOUR_TOKEN_HERE',  # 请替换为实际token")
    print(f"#     backtest_start_time=start_date.strftime('%Y-%m-%d 09:30:00'),")
    print(f"#     backtest_end_time=end_date.strftime('%Y-%m-%d 15:00:00'),")
    print(f"#     backtest_adjust=ADJUST_PREV,")
    print(f"#     backtest_initial_cash=initial_capital,")
    print(f"#     backtest_commission_ratio=0.0003,")
    print(f"#     backtest_slippage_ratio=0.0001")
    print(f"# )")
    print("```")
    
    print("\\n✅ 回测脚本生成完成！")
    print("请按照上述说明配置token并运行回测。")


if __name__ == '__main__':
    main()
'''
        
        return script_content
    
    def get_api_status(self) -> Dict[str, Any]:
        """获取API状态信息"""
        
        status = {
            "api_base_path": self.api_base_path,
            "config_files_count": len([f for f in os.listdir(self.api_base_path) 
                                     if f.endswith('.json')]),
            "script_files_count": len([f for f in os.listdir(self.api_base_path) 
                                      if f.endswith('.py')]),
            "last_updated": datetime.now().isoformat(),
            "status": "active"
        }
        
        return status


# 快速API函数
def create_backtest_package(strategy_results: List[Dict[str, Any]],
                          strategy_type: str,
                          weights_config: Dict[str, int],
                          sub_weights_config: Dict[str, Any] = None,
                          backtest_params: Dict[str, Any] = None) -> Dict[str, str]:
    """
    快速创建回测包
    
    Args:
        strategy_results: 选股结果
        strategy_type: 策略类型
        weights_config: 权重配置
        sub_weights_config: 子权重配置
        backtest_params: 回测参数
        
    Returns:
        Dict[str, str]: 包含配置文件和脚本文件路径的字典
    """
    
    api = StrategyAPI()
    
    # 保存配置
    config_path = api.save_strategy_config(
        strategy_results, strategy_type, weights_config, 
        sub_weights_config, backtest_params
    )
    
    # 加载配置
    config_data = api.load_strategy_config(config_path)
    
    # 生成脚本
    script_path = api.generate_backtest_script(config_data)
    
    return {
        "config_path": config_path,
        "script_path": script_path,
        "api_status": api.get_api_status()
    }


def get_backtest_recommendations() -> List[Dict[str, Any]]:
    """获取回测参数推荐"""
    
    recommendations = [
        {
            "name": "短期测试",
            "description": "快速验证策略有效性",
            "backtest_days": 30,
            "initial_capital": 50000,
            "max_stocks": 1,
            "risk_level": "低"
        },
        {
            "name": "中期验证",
            "description": "全面评估策略稳定性",
            "backtest_days": 90,
            "initial_capital": 100000,
            "max_stocks": 3,
            "risk_level": "中"
        },
        {
            "name": "长期评估",
            "description": "深度测试策略长期表现",
            "backtest_days": 180,
            "initial_capital": 200000,
            "max_stocks": 5,
            "risk_level": "高"
        }
    ]
    
    return recommendations