# coding=utf-8
"""
测试龙洲股份的一字板检测
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.stock_data_provider import StockDataProvider
from indicators.speculation_filter import SpeculationFilter

def test_stock(symbol, trade_date=None):
    """测试单只股票"""
    if trade_date is None:
        trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"测试股票: {symbol}")
    print(f"测试日期: {trade_date}")
    print("=" * 80)

    # 获取数据
    data_provider = StockDataProvider()
    df = data_provider.get_stock_kline_data(symbol, trade_date, days=60)

    if df.empty:
        print("❌ 无法获取K线数据")
        return

    # 获取基础信息
    basic_info = data_provider.get_stock_basic_info(symbol, trade_date)
    if basic_info:
        print(f"股票名称: {basic_info.get('sec_name', '未知')}")
        print(f"当前价格: {df['close'].iloc[-1]:.2f}")
        print(f"PE: {basic_info.get('pe', 0):.1f}")
        print(f"市值: {basic_info.get('a_mv', 0)/1e8:.1f}亿")

    print(f"\nK线数据概览（最近30天）：")
    print("-" * 80)
    print(f"{'日期':<12} {'开盘':>8} {'收盘':>8} {'最高':>8} {'最低':>8} {'成交量':>12} {'涨幅%':>8}")
    print("-" * 80)

    # 显示最近30天数据
    df_30 = df.tail(30).reset_index(drop=True)
    for idx in range(len(df_30)):
        row = df_30.iloc[idx]
        open_p = row['open']
        close_p = row['close']
        high_p = row['high']
        low_p = row['low']
        vol = row['volume']
        date = row.get('bob', idx)

        # 计算涨幅（使用前一日的收盘价）
        if idx > 0:
            prev_close = df_30.iloc[idx - 1]['close']
            if prev_close > 0:
                change_rate = (close_p - prev_close) / prev_close * 100
            else:
                change_rate = 0
        else:
            change_rate = 0

        # 检测是否一字板特征
        if open_p > 0 and high_p > 0:
            open_close_diff = abs(open_p - close_p) / open_p
            close_high_diff = abs(close_p - high_p) / high_p
            is_yi_zi = open_close_diff < 0.001 and close_high_diff < 0.001 and change_rate >= 9.5
            marker = "🚨一字板" if is_yi_zi else ""
        else:
            marker = ""

        print(f"{date:<12} {open_p:>8.2f} {close_p:>8.2f} {high_p:>8.2f} {low_p:>8.2f} {vol:>12,.0f} {change_rate:>7.2f}% {marker}")

    print("\n" + "=" * 80)
    print("投机炒作筛选器检测结果")
    print("=" * 80)

    # 使用筛选器检测
    filter_spec = SpeculationFilter(lookback_days=30)
    is_passed, result = filter_spec.filter_stock(df)

    if result.get('has_speculation_signal'):
        print(f"❌ 检测到投机炒作信号！")
        print(f"原因: {result['reason']}")

        if result['limit_up_result'].get('has_limit_up_board'):
            print(f"\n一字板详情:")
            print(f"  出现次数: {result['limit_up_result']['board_count']} 次")
            print(f"  最近日期: {result['limit_up_result']['limit_up_date']}")
            print(f"  价格: {result['limit_up_result']['limit_up_price']:.2f}")
            print(f"  涨幅: {result['limit_up_result']['limit_up_rate']*100:.2f}%")
            print(f"  成交量: {result['limit_up_result']['limit_up_volume']:,.0f}")

            if 'limit_up_details' in result['limit_up_result']:
                print(f"\n所有一字板记录:")
                for i, detail in enumerate(result['limit_up_result']['limit_up_details'], 1):
                    print(f"  [{i}] {detail['date']}, 价格: {detail['price']:.2f}, 涨幅: {detail['rate']*100:.2f}%, 成交量: {detail['volume']:,.0f}")
    else:
        print(f"✅ 未检测到投机炒作信号")
        print(f"原因: {result['reason']}")

    print("=" * 80)


if __name__ == '__main__':
    # 测试龙洲股份
    test_stock('SZSE.002682')  # 龙洲股份
