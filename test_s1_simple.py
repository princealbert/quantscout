# coding=utf-8
"""
S1筛选器简单测试
"""

import pandas as pd

# 测试场景1：典型的S1信号
print("场景1：典型S1信号（应该被过滤）")
print("=" * 80)

# 创建数据
dates = list(range(40))
prices = [80 + i*0.8 for i in range(20)] + [100] + [90, 85] + [80, 75, 70] + [65 + i*0.5 for i in range(15)]
volumes = [1000000] * 40
volumes[17] = 3000000  # 第18天前一日红柱
volumes[18] = 5000000  # 第18天绿柱（30日最大）

closes = prices.copy()
closes[18] = closes[17] - 2  # 绿柱：第18天收盘价低于第17天

df = pd.DataFrame({
    'bob': dates,
    'close': closes,
    'high': [p + 2 for p in prices],
    'low': [p - 2 for p in prices],
    'volume': volumes
})

print(f"最高价：{df['high'].max():.2f}（第{df['high'].idxmax()}天）")
print(f"30日最大成交量：{df['volume'].max():,.0f}")
print(f"第17天收盘：{closes[17]:.2f}，成交量：{volumes[17]:,.0f}")
print(f"第18天收盘：{closes[18]:.2f}，成交量：{volumes[18]:,.0f}")
print(f"第18天跌幅：{(closes[18] - closes[17]) / closes[17] * 100:.2f}%")

# 测试S1筛选
from indicators.s1_filter import S1Filter
s1_filter = S1Filter(lookback_days=30, context_days=2)
is_passed, result = s1_filter.filter_stock(df)

print(f"\n筛选结果：{'通过 ✅' if is_passed else '未通过 ❌'}")
if result.get('has_s1_signal'):
    print(f"S1信号：{result['s1_reason']}")
    print(f"高点价格：{result['s1_high_price']}")
    print(f"绿柱量：{result['s1_green_volume']}")
    print(f"前日红柱：{result['s1_prev_red_volume']}")
else:
    print(f"无S1信号：{result.get('s1_reason')}")

print("\n" + "=" * 80)
print("测试完成！")
