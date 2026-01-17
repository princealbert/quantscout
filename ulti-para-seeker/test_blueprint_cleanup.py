#!/usr/bin/env python
# coding=utf-8
"""
蓝图清理功能测试脚本
"""

import os
import sys
import json
import shutil
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.blueprint_cleaner import BlueprintCleaner


def create_test_blueprint(num_combinations=1200):
    """
    创建测试蓝图文件

    Args:
        num_combinations: 组合数量

    Returns:
        Dict[str, Any]: 测试蓝图数据
    """
    print(f"\n=== 创建测试蓝图 ===")
    print(f"组合数量: {num_combinations}")

    combinations = []

    for i in range(num_combinations):
        # 模拟不同状态的组合
        status_ratio = i / num_combinations

        if status_ratio < 0.6:  # 前60%为已完成
            status = 'completed'
            # 模拟递减的收益率(越靠后越差)
            total_return = 100 - (i / num_combinations * 150)  # 从100%递减到-50%
            result = {
                'total_return': total_return,
                'annual_return': total_return * 365 / 90,
                'max_drawdown': -abs(total_return * 0.3),
                'sharpe_ratio': max(0, total_return / 10),
                'win_rate': 50 + total_return / 10,
                'trades_count': 100
            }
        elif status_ratio < 0.85:  # 60%-85%为失败
            status = 'failed'
            result = None
        elif status_ratio < 0.95:  # 85%-95%为待处理
            status = 'pending'
            result = None
        else:  # 最后5%为运行中
            status = 'running'
            result = None

        combo = {
            'id': i + 1,
            'params': {
                'backtest_days': 90,
                'end_date': '2025-01-16',
                'stop_profit_ratio': 5,
                'stop_loss_ratio': -4,
                'weights_config': {'trend': 50, 'risk_reward': 50},
                'sub_weights_config': {}
            },
            'status': status,
            'result': result,
            'started_at': datetime.now().isoformat() if status == 'running' else None,
            'completed_at': datetime.now().isoformat() if status in ['completed', 'failed'] else None
        }

        combinations.append(combo)

    blueprint = {
        'version': '1.0',
        'generated_at': datetime.now().isoformat(),
        'last_modified': datetime.now().isoformat(),
        'total_combinations': num_combinations,
        'test_mode': False,
        'max_sub_combinations': 90,
        'end_date': '2025-01-16',
        'algorithm': '测试算法',
        'completed_combinations': sum(1 for c in combinations if c['status'] == 'completed'),
        'failed_combinations': sum(1 for c in combinations if c['status'] == 'failed'),
        'pending_combinations': sum(1 for c in combinations if c['status'] == 'pending'),
        'running_combinations': sum(1 for c in combinations if c['status'] == 'running'),
        'combinations': combinations
    }

    print(f"- 已完成: {blueprint['completed_combinations']}")
    print(f"- 失败: {blueprint['failed_combinations']}")
    print(f"- 待处理: {blueprint['pending_combinations']}")
    print(f"- 运行中: {blueprint['running_combinations']}")

    return blueprint


def test_cleanup_recommendations():
    """测试获取清理建议"""
    print("\n" + "="*60)
    print("测试1: 获取清理建议")
    print("="*60)

    # 创建测试蓝图
    blueprint = create_test_blueprint(1200)

    # 创建清理器
    cleaner = BlueprintCleaner(max_total=1000, max_elite=500, keep_failed=False)

    # 获取清理建议
    recommendations = cleaner.get_cleanup_recommendations(blueprint)

    print("\n清理建议:")
    print(f"- 需要清理: {recommendations['needs_cleanup']}")
    print(f"- 当前大小: {recommendations['current_size']}")
    print(f"- 阈值: {recommendations['threshold']}")
    print(f"- 需删除: {recommendations['to_delete']} 个组合")

    print("\n当前分布:")
    for status, count in recommendations['current_breakdown'].items():
        print(f"  {status}: {count}")

    print("\n建议删除:")
    for status, count in recommendations['suggested_deletion'].items():
        print(f"  {status}: {count}")

    print(f"\n预计节省空间: {recommendations['estimated_space_saved']}")


def test_clean_blueprint():
    """测试清理蓝图"""
    print("\n" + "="*60)
    print("测试2: 清理蓝图")
    print("="*60)

    # 创建测试目录
    test_dir = "test_blueprint_data"
    os.makedirs(test_dir, exist_ok=True)

    try:
        # 创建测试蓝图
        blueprint = create_test_blueprint(1200)
        blueprint_file = os.path.join(test_dir, "parameter_blueprint.json")

        # 保存测试蓝图
        with open(blueprint_file, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, ensure_ascii=False, indent=2)

        print(f"\n已保存测试蓝图: {blueprint_file}")
        file_size = os.path.getsize(blueprint_file) / 1024
        print(f"文件大小: {file_size:.2f} KB")

        # 创建清理器
        cleaner = BlueprintCleaner(max_total=1000, max_elite=500, keep_failed=False)

        # 执行清理
        print(f"\n开始清理...")
        cleaned_blueprint, archive_data = cleaner.clean_blueprint(
            blueprint=blueprint,
            blueprint_file=blueprint_file,
            auto_archive=True
        )

        # 保存清理后的蓝图
        cleaned_file = os.path.join(test_dir, "parameter_blueprint_cleaned.json")
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_blueprint, f, ensure_ascii=False, indent=2)

        print(f"\n已保存清理后的蓝图: {cleaned_file}")
        cleaned_size = os.path.getsize(cleaned_file) / 1024
        print(f"文件大小: {cleaned_size:.2f} KB")

        # 检查归档文件
        archive_dir = os.path.join(test_dir, "blueprint_archives")
        if os.path.exists(archive_dir):
            archives = os.listdir(archive_dir)
            print(f"\n归档文件数: {len(archives)}")
            for archive in archives:
                archive_path = os.path.join(archive_dir, archive)
                archive_size = os.path.getsize(archive_path) / 1024
                print(f"- {archive}: {archive_size:.2f} KB")

        print(f"\n空间节省: {((file_size - cleaned_size) / file_size * 100):.1f}%")

        # 保存归档数据到单独文件(方便查看)
        archive_file = os.path.join(test_dir, "archived_data.json")
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, ensure_ascii=False, indent=2)
        print(f"\n归档数据已保存: {archive_file}")

    finally:
        # 清理测试目录
        # shutil.rmtree(test_dir)
        # print(f"\n已清理测试目录: {test_dir}")
        pass


def test_large_blueprint():
    """测试大蓝图文件的处理"""
    print("\n" + "="*60)
    print("测试3: 大蓝图文件处理")
    print("="*60)

    # 创建超大蓝图
    print("\n创建3000个组合的蓝图...")
    blueprint = create_test_blueprint(3000)

    cleaner = BlueprintCleaner(max_total=1500, max_elite=750)

    # 获取清理建议
    recommendations = cleaner.get_cleanup_recommendations(blueprint)

    print(f"\n当前组合数: {recommendations['current_size']}")
    print(f"需要删除: {recommendations['to_delete']} 个组合")
    print(f"预计节省: {recommendations['estimated_space_saved']}")


def test_list_archives():
    """测试列出归档文件"""
    print("\n" + "="*60)
    print("测试4: 列出归档文件")
    print("="*60)

    test_dir = "test_blueprint_data"
    cleaner = BlueprintCleaner()

    if os.path.exists(test_dir):
        archives = cleaner.list_archives(test_dir)

        if archives:
            print(f"\n找到 {len(archives)} 个归档文件:")
            for archive in archives:
                print(f"- {archive['filename']}")
                print(f"  归档时间: {archive['archived_at']}")
                print(f"  组合数: {archive['archived_count']}")
                print(f"  文件大小: {archive['size_kb']} KB")
                print(f"  归档原因: {archive['archive_reason']}")
        else:
            print("\n未找到归档文件")
    else:
        print("\n测试目录不存在,请先运行测试2")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("蓝图清理功能测试")
    print("="*60)

    try:
        # 运行测试
        test_cleanup_recommendations()
        test_clean_blueprint()
        test_large_blueprint()
        test_list_archives()

        print("\n" + "="*60)
        print("所有测试完成!")
        print("="*60)

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
