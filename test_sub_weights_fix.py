#!/usr/bin/env python
# coding=utf-8
"""
测试子权重配置保存功能是否正常工作
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入配置管理器
from strategy_controller.utils.config_manager import ConfigManager

def test_sub_weights_saving():
    """测试子权重配置是否能正确保存"""
    print("开始测试子权重保存功能...")
    
    # 创建配置管理器实例
    config_manager = ConfigManager()
    
    # 准备测试数据
    test_weights = {
        'kdj_j': 20,
        'trend': 30,
        'deepv': 0,
        'volume': 20,
        'fundamental': 10,
        'position': 10,
        'risk_reward': 10
    }
    
    test_sub_weights = {
        'kdj_j': {
            'total_weight': 20,
            'sub_weights': {
                'j_0_20': 0,
                'j_-10_0': 5,
                'j_-20_-10': 5,
                'j_-30_-20': 5,
                'j_below_-30': 5
            }
        },
        'trend': {
            'total_weight': 30,
            'sub_weights': {
                'up_trend': 15,
                'volume_price_rise': 10,
                'volume_contraction': 5
            }
        }
    }
    
    config_name = f"测试配置_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\n测试配置名称: {config_name}")
    print(f"主权重: {test_weights}")
    print(f"子权重: {test_sub_weights}")
    
    # 保存配置
    try:
        config_id = config_manager.save_config(
            name=config_name,
            weights=test_weights,
            sub_weights=test_sub_weights,
            description="测试子权重保存功能"
        )
        print(f"\n✓ 配置保存成功，配置ID: {config_id}")
        
        # 重新加载配置
        loaded_config = config_manager.get_config(config_id)
        if loaded_config:
            print(f"✓ 配置重新加载成功")
            
            # 检查子权重是否正确保存
            loaded_sub_weights = loaded_config.get('sub_weights', {})
            if loaded_sub_weights:
                print(f"✓ 子权重已正确保存到配置中")
                print(f"  加载的子权重: {loaded_sub_weights}")
                
                # 验证内容是否一致
                if loaded_sub_weights == test_sub_weights:
                    print("\n🎉 测试通过！子权重配置保存和加载功能正常工作。")
                    return True
                else:
                    print("\n❌ 测试失败！保存的子权重与原始数据不一致。")
                    print(f"  原始数据: {test_sub_weights}")
                    print(f"  保存后: {loaded_sub_weights}")
                    return False
            else:
                print("\n❌ 测试失败！加载的配置中没有子权重数据。")
                return False
        else:
            print("\n❌ 测试失败！无法重新加载保存的配置。")
            return False
    except Exception as e:
        print(f"\n❌ 测试失败！保存配置时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sub_weights_saving()
    sys.exit(0 if success else 1)
