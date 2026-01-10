# coding=utf-8
"""
S1筛选器测试脚本 - 使用模拟数据
功能：创建模拟的K线数据，验证S1筛选逻辑
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from indicators.s1_filter import S1Filter


def create_test_data_scenario_1():
    """
    场景1：典型的S1信号
    - 第20天出现最高价（假设100元）
    - 第18天（高点前2天）出现放量绿柱，成交量500万，超过前日红柱300万
    - 这个500万是30日内的最大成交量
    """
    dates = [(datetime(2025, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(40)]
    
    # 创建价格数据：第20天出现最高价100
    prices = [80 + i*0.8 for i in range(20)] + [100] + [90, 85] + [80, 75, 70] + [65 + i*0.5 for i in range(15)]
    
    # 创建成交量：第18天放量绿柱500万（30日最大），第17天红柱300万
    volumes = [1000000] * 40
    volumes[17] = 3000000  # 第18天前一日（索引17）
    volumes[18] = 5000000  # 第18天（索引18）- 绿柱
    
    # 收盘价：第18天要低于第17天（形成绿柱）
    closes = prices.copy()
    closes[18] = closes[17] - 2  # 第18天收盘价低于第17天
    
    data = {
        'bob': dates,
        'close': closes,
        'high': [p + 2 for p in prices],
        'low': [p - 2 for p in prices],
        'volume': volumes
    }
    
    df = pd.DataFrame(data)
    return df, "场景1：典型S1信号 - 应该被过滤"


def create_test_data_scenario_2():
    """
    场景2：无S1信号（不符合条件）
    - 第20天出现最高价
    - 虽然有绿柱，但成交量不大，不是30日最大
    """
    dates = [(datetime(2025, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(40)]
    
    prices = [80 + i*0.8 for i in range(20)] + [100] + [90, 85] + [80, 75, 70] + [65 + i*0.5 for i in range(15)]
    volumes = [1000000] * 40
    volumes[20] = 8000000  # 第21天放量（30日最大）
    volumes[18] = 2000000  # 第18天绿柱，但不是最大
    
    closes = prices.copy()
    closes[18] = closes[17] - 2  # 绿柱
    
    data = {
        'bob': dates,
        'close': closes,
        'high': [p + 2 for p in prices],
        'low': [p - 2 for p in prices],
        'volume': volumes
    }
    
    df = pd.DataFrame(data)
    return df, "场景2：有绿柱但不是最大量 - 应该通过"


def create_test_data_scenario_3():
    """
    场景3：绿柱成交量未超过前日红柱
    - 第20天出现最高价
    - 第18天绿柱200万，第17天红柱300万，绿柱未超过红柱
    """
    dates = [(datetime(2025, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(40)]
    
    prices = [80 + i*0.8 for i in range(20)] + [100] + [90, 85] + [80, 75, 70] + [65 + i*0.5 for i in range(15)]
    volumes = [1000000] * 40
    volumes[18] = 2000000  # 绿柱
    volumes[17] = 3000000  # 红柱，比绿柱大
    
    closes = prices.copy()
    closes[18] = closes[17] - 2  # 绿柱
    
    data = {
        'bob': dates,
        'close': closes,
        'high': [p + 2 for p in prices],
        'low': [p - 2 for p in prices],
        'volume': volumes
    }
    
    df = pd.DataFrame(data)
    return df, "场景3：绿柱量小于红柱 - 应该通过"


def create_test_data_scenario_4():
    """
    场景4：高点范围内无绿柱
    - 第20天出现最高价
    - 高点前后2天都是红柱
    """
    dates = [(datetime(2025, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(40)]
    
    prices = [80 + i*0.8 for i in range(20)] + [100] + [95, 90] + [85, 80, 75] + [70 + i*0.5 for i in range(15)]
    volumes = [1000000] * 40
    
    # 高点前后都是红柱（收盘价持续上涨）
    closes = prices.copy()
    closes[18] = closes[17] + 2  # 红柱
    closes[19] = closes[18] + 2  # 红柱
    closes[20] = closes[19] + 2  # 红柱
    
    data = {
        'bob': dates,
        'close': closes,
        'high': [p + 2 for p in prices],
        'low': [p - 2 for p in prices],
        'volume': volumes
    }
    
    df = pd.DataFrame(data)
    return df, "场景4：高点范围内无绿柱 - 应该通过"


def create_test_data_scenario_5():
    """
    场景5：绿柱在范围外
    - 第20天出现最高价
    - 第15天出现放量绿柱，但距离高点超过2天
    """
    dates = [(datetime(2025, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(40)]
    
    prices = [80 + i*0.8 for i in range(20)] + [100] + [90, 85] + [80, 75, 70] + [65 + i*0.5 for i in range(15)]
    volumes = [1000000] * 40
    volumes[15] = 5000000  # 第16天放量绿柱（30日最大）
    volumes[14] = 3000000  # 前一日红柱
    
    closes = prices.copy()
    closes[15] = closes[14] - 2  # 绿柱
    
    data = {
        'bob': dates,
        'close': closes,
        'high': [p + 2 for p in prices],
        'low': [p - 2 for p in prices],
        'volume': volumes
    }
    
    df = pd.DataFrame(data)
    return df, "场景5：放量绿柱在范围外 - 应该通过"


def print_data_summary(df, scenario_name):
    """打印数据摘要"""
    print(f"\n{'='*80}")
    print(f"测试场景：{scenario_name}")
    print(f"{'='*80}")
    
    # 找出最高价
    max_high_idx = df['high'].idxmax()
    max_high = df.loc[max_high_idx, 'high']
    max_date = df.loc[max_high_idx, 'bob']
    
    print(f"30日内最高价：{max_high:.2f}（第{max_high_idx}天，{max_date}）")
    
    # 显示高点前后范围
    context_days = 2
    start_idx = max(0, max_high_idx - context_days)
    end_idx = min(len(df) - 1, max_high_idx + context_days)
    
    print(f"\n高点前后{context_days}天数据：")
    print("-" * 80)
    print(f"{'日期':<12} {'收盘':>8} {'最高':>8} {'最低':>8} {'成交量':>12} {'涨跌':>8}")
    print("-" * 80)
    
    for i in range(start_idx, end_idx + 1):
        row = df.loc[i]
        close = row['close']
        volume = row['volume']
        change = ''
        if i > 0:
            prev_close = df.loc[i-1, 'close']
            change_pct = (close - prev_close) / prev_close * 100
            change = f"{change_pct:+.2f}%" if change_pct != 0 else "0.00%"
        
        color = "🟢红柱" if change and change.startswith('+') else "🔴绿柱" if change and change.startswith('-') else "-"
        
        print(f"{row['bob']:<12} {close:>8.2f} {row['high']:>8.2f} {row['low']:>8.2f} {volume:>12,.0f} {change:>8} {color}")
    
    # 显示30日最大成交量
    max_volume_30 = df['volume'].max()
    max_volume_idx = df['volume'].idxmax()
    print(f"\n30日最大成交量：{max_volume_30:,.0f}（第{max_volume_idx}天）")


def test_scenario(df, scenario_name, expected_result):
    """测试单个场景"""
    print_data_summary(df, scenario_name)
    
    s1_filter = S1Filter(lookback_days=30, context_days=2)
    is_passed, result = s1_filter.filter_stock(df)
    
    print(f"\n{'-'*80}")
    print(f"S1筛选结果：{'通过 ✅' if is_passed else '未通过 ❌（被过滤）'}")
    print(f"预期结果：  {'通过 ✅' if expected_result else '未通过 ❌（被过滤）'}")
    print(f"测试结果：  {'✅ 符合预期' if is_passed == expected_result else '❌ 不符合预期'}")
    
    if result.get('has_s1_signal'):
        print(f"\nS1信号详情：")
        print(f"  - 原因：{result['s1_reason']}")
        print(f"  - 高点价格：{result['s1_high_price']:.2f}")
        print(f"  - 绿柱成交量：{result['s1_green_volume']:,.0f}")
        print(f"  - 前日红柱：{result['s1_prev_red_volume']:,.0f}")
        print(f"  - 量比：{result['s1_volume_ratio']:.2f}")
        print(f"  - 30日最大量：{result['s1_max_volume_30days']:,.0f}")
    else:
        print(f"\n未发现S1信号：{result.get('s1_reason', '')}")
    
    return is_passed == expected_result


def main():
    """主函数"""
    print("=" * 80)
    print("S1筛选器逻辑测试 - 使用模拟数据")
    print("=" * 80)
    print("\n测试目的：验证S1筛选逻辑是否正确识别主力获利了结信号")
    print("S1信号定义：30日内高点前后2天范围内，出现放量绿柱超过前日红柱，")
    print("            且该绿柱成交量为30日最大")
    print("=" * 80)
    
    # 测试场景配置：(df, 场景描述, 预期是否通过)
    scenarios = [
        (create_test_data_scenario_1(), True),   # 应该被过滤
        (create_test_data_scenario_2(), False),  # 应该通过
        (create_test_data_scenario_3(), False),  # 应该通过
        (create_test_data_scenario_4(), False),  # 应该通过
        (create_test_data_scenario_5(), False),  # 应该通过
    ]
    
    results = []
    for (df, desc), expected in scenarios:
        result = test_scenario(df, desc, expected)
        results.append((desc, result))
        print("\n")
    
    # 总结
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for desc, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {desc}")
    
    print(f"\n总计：{passed}/{total} 个场景符合预期")
    
    if passed == total:
        print("\n🎉 所有测试场景均符合预期！S1筛选逻辑正确！")
    else:
        print(f"\n⚠️  有 {total - passed} 个场景不符合预期，需要调整逻辑")


if __name__ == '__main__':
    main()
