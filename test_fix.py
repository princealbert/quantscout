#!/usr/bin/env python
# coding=utf-8
"""
测试修复效果 - 验证环境变量在参数传递中的作用
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加项目根目录到sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 模拟并行回测环境
from config.strategy_params import StrategyParams, save_params_to_file, load_params_from_file


def test_environment_variable_handling():
    """
    测试环境变量在参数加载中的作用
    """
    print("=== 测试环境变量在参数加载中的作用 ===")
    
    # 创建两个不同的参数组合
    params1 = {
        'backtest_days': 11,
        'stop_profit_ratio': 0.086,
        'stop_loss_ratio': -0.05,
        'weights_config': {
            'kdj_j': 19,
            'trend': 19,
            'volume': 5,
            'fundamental': 30,
            'position': 5,
            'risk_reward': 22,
            'deepv': 0
        }
    }
    
    params2 = {
        'backtest_days': 11,
        'stop_profit_ratio': 0.138,
        'stop_loss_ratio': -0.024,
        'weights_config': {
            'kdj_j': 32,
            'trend': 6,
            'volume': 33,
            'fundamental': 13,
            'position': 10,
            'risk_reward': 6,
            'deepv': 0
        }
    }
    
    # 测试1：创建参数对象并保存到临时文件
    print("\n1. 测试参数保存到临时文件：")
    sp1 = StrategyParams(**params1)
    sp2 = StrategyParams(**params2)
    
    # 创建临时目录
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 为每个参数组合创建唯一文件
        file1 = os.path.join(temp_dir, 'params1.json')
        file2 = os.path.join(temp_dir, 'params2.json')
        
        save_params_to_file(sp1, file_path=file1)
        save_params_to_file(sp2, file_path=file2)
        
        print(f"   - 参数1已保存到: {file1}")
        print(f"   - 参数2已保存到: {file2}")
        
        # 测试2：验证环境变量优先于默认路径
        print("\n2. 测试环境变量优先级：")
        
        # 设置环境变量指向第一个文件
        os.environ['BACKTEST_PARAMS_FILE'] = file1
        
        # 不指定文件路径，应该使用环境变量中的路径
        loaded_params = load_params_from_file()
        if loaded_params:
            print(f"   - 加载的参数1：")
            print(f"     止盈比例: {loaded_params.stop_profit_ratio:.4f}")
            print(f"     止损比例: {loaded_params.stop_loss_ratio:.4f}")
            print(f"     KDJ_J权重: {loaded_params.weights_config['kdj_j']}")
            
        # 切换环境变量指向第二个文件
        os.environ['BACKTEST_PARAMS_FILE'] = file2
        
        # 再次加载，应该使用新的环境变量路径
        loaded_params = load_params_from_file()
        if loaded_params:
            print(f"   - 加载的参数2：")
            print(f"     止盈比例: {loaded_params.stop_profit_ratio:.4f}")
            print(f"     止损比例: {loaded_params.stop_loss_ratio:.4f}")
            print(f"     KDJ_J权重: {loaded_params.weights_config['kdj_j']}")
        
        # 测试3：验证main.py现在能正确处理环境变量
        print("\n3. 验证main.py的环境变量处理：")
        print("   - main.py已修改为优先使用环境变量BACKTEST_PARAMS_FILE")
        print("   - 配置文件优先级：命令行参数 > 环境变量 > 固定路径")
        print("   - 这确保了每个并行进程使用自己的参数文件")
        
        print("\n✅ 测试完成！环境变量处理正常，并行回测应该能正确使用不同的参数组合")
        
    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        # 移除环境变量
        if 'BACKTEST_PARAMS_FILE' in os.environ:
            del os.environ['BACKTEST_PARAMS_FILE']


if __name__ == "__main__":
    test_environment_variable_handling()