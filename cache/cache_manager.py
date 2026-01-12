#!/usr/bin/env python
# coding=utf-8
"""
缓存管理器 - 提供缓存统计、清理、优化、预热和健康度检查功能
"""

import argparse
import sys
from typing import List
from cache.data_cache import StockDataCache


def main():
    """缓存管理主函数"""
    parser = argparse.ArgumentParser(description='股票数据缓存管理器')
    subparsers = parser.add_subparsers(dest='action', help='操作类型')
    
    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='显示缓存统计信息')
    
    # 清理命令
    clean_parser = subparsers.add_parser('clean', help='清理过期缓存')
    clean_parser.add_argument('--days', type=int, default=7, 
                            help='清理时指定过期天数 (默认: 7天)')
    
    # 优化命令
    optimize_parser = subparsers.add_parser('optimize', help='优化数据库性能')
    
    # 预热命令
    prewarm_parser = subparsers.add_parser('prewarm', help='缓存预热')
    prewarm_parser.add_argument('--symbols', type=str, default='',
                               help='股票代码列表，逗号分隔')
    prewarm_parser.add_argument('--date', type=str, default='2025-12-08',
                               help='交易日期 (默认: 2025-12-08)')
    prewarm_parser.add_argument('--days', type=int, default=180,
                               help='数据天数 (默认: 180天)')
    prewarm_parser.add_argument('--batch-size', type=int, default=100,
                               help='批次大小 (默认: 100)')
    prewarm_parser.add_argument('--workers', type=int, default=8,
                               help='工作线程数 (默认: 8)')
    
    # 健康度检查命令
    health_parser = subparsers.add_parser('health', help='查看缓存健康度报告')
    
    # 智能清理命令
    smart_parser = subparsers.add_parser('smart', help='智能缓存清理')
    smart_parser.add_argument('--strategy', type=str, default='回测',
                             choices=['回测', '实时', '默认'],
                             help='策略类型 (默认: 回测)')
    smart_parser.add_argument('--max-size', type=int, default=100,
                             help='最大缓存大小(MB) (默认: 100MB)')
    
    args = parser.parse_args()
    
    # 创建缓存实例
    cache = StockDataCache()
    
    if not args.action:
        parser.print_help()
        return
    
    if args.action == 'stats':
        show_cache_stats(cache)
    elif args.action == 'clean':
        clean_cache(cache, args.days)
    elif args.action == 'optimize':
        optimize_cache(cache)
    elif args.action == 'prewarm':
        pre_warm_cache(cache, args)
    elif args.action == 'health':
        show_health_report(cache)
    elif args.action == 'smart':
        smart_cache_cleanup(cache, args.strategy, args.max_size)


def show_cache_stats(cache):
    """显示缓存统计信息"""
    print("📊 缓存统计信息")
    print("=" * 50)
    
    stats = cache.get_cache_stats()
    
    if not stats:
        print("❌ 无法获取缓存统计信息")
        return
    
    # K线数据统计
    kline_data = stats['kline_data']
    print("📈 K线数据缓存:")
    print(f"   • 总记录数: {kline_data['total_count']:,} 条")
    print(f"   • 唯一股票数: {kline_data['unique_symbols']:,} 只")
    print(f"   • 最早访问: {kline_data['earliest_access'] or '无'}")
    print(f"   • 最近访问: {kline_data['latest_access'] or '无'}")
    print()
    
    # 基础信息统计
    basic_info = stats['basic_info']
    print("📋 基础信息缓存:")
    print(f"   • 总记录数: {basic_info['total_count']:,} 条")
    print(f"   • 唯一股票数: {basic_info['unique_symbols']:,} 只")
    print(f"   • 最早访问: {basic_info['earliest_access'] or '无'}")
    print(f"   • 最近访问: {basic_info['latest_access'] or '无'}")
    print()
    
    # 文件大小
    total_size = stats['total_size_kb']
    print(f"💾 缓存文件大小: {total_size:.1f} KB ({total_size/1024:.2f} MB)")
    
    # 性能评估
    if kline_data['total_count'] > 0:
        avg_records_per_stock = kline_data['total_count'] / kline_data['unique_symbols']
        print(f"📊 平均每只股票缓存记录: {avg_records_per_stock:.1f} 条")
    
    print("=" * 50)


def clean_cache(cache, days):
    """清理过期缓存"""
    print(f"🧹 开始清理 {days} 天前的缓存数据...")
    print("-" * 50)
    
    # 清理前统计
    stats_before = cache.get_cache_stats()
    if stats_before:
        print("清理前:")
        print(f"   • K线数据: {stats_before['kline_data']['total_count']:,} 条")
        print(f"   • 基础信息: {stats_before['basic_info']['total_count']:,} 条")
        print()
    
    # 执行清理
    cache.clear_old_cache(days)
    print()
    
    # 清理后统计
    stats_after = cache.get_cache_stats()
    if stats_after:
        print("清理后:")
        print(f"   • K线数据: {stats_after['kline_data']['total_count']:,} 条")
        print(f"   • 基础信息: {stats_after['basic_info']['total_count']:,} 条")
        
        if stats_before:
            kline_reduction = stats_before['kline_data']['total_count'] - stats_after['kline_data']['total_count']
            basic_reduction = stats_before['basic_info']['total_count'] - stats_after['basic_info']['total_count']
            total_reduction = kline_reduction + basic_reduction
            
            print(f"\n🎯 清理结果:")
            print(f"   • 共清理 {total_reduction:,} 条记录")
            print(f"   • K线数据减少: {kline_reduction:,} 条")
            print(f"   • 基础信息减少: {basic_reduction:,} 条")
    
    print("-" * 50)


def optimize_cache(cache):
    """优化缓存数据库"""
    print("🔧 开始优化缓存数据库...")
    print("-" * 50)
    
    # 优化前文件大小
    stats_before = cache.get_cache_stats()
    size_before = stats_before.get('total_size_kb', 0) if stats_before else 0
    
    print(f"优化前文件大小: {size_before:.1f} KB")
    print("正在执行数据库优化 (VACUUM + ANALYZE)...")
    
    # 执行优化
    cache.optimize_database()
    
    # 优化后文件大小
    stats_after = cache.get_cache_stats()
    size_after = stats_after.get('total_size_kb', 0) if stats_after else 0
    
    print(f"优化后文件大小: {size_after:.1f} KB")
    
    if size_before > 0:
        size_change = size_after - size_before
        change_percent = (size_change / size_before) * 100
        
        if size_change < 0:
            print(f"✅ 文件大小减少: {abs(size_change):.1f} KB ({abs(change_percent):.1f}%)")
        else:
            print(f"ℹ️  文件大小变化: {size_change:.1f} KB ({change_percent:.1f}%)")
    
    print("-" * 50)


def pre_warm_cache(cache, args):
    """缓存预热"""
    print("🔥 开始缓存预热...")
    print("-" * 50)
    
    # 解析股票代码
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        # 默认使用沪深300成分股示例
        symbols = [
            "SHSE.600519", "SHSE.601318", "SZSE.000001", "SHSE.600036", "SHSE.600276",
            "SHSE.600887", "SHSE.601166", "SHSE.600030", "SHSE.601888", "SHSE.600900"
        ]
    
    print(f"预热参数:")
    print(f"   • 股票数量: {len(symbols)} 只")
    print(f"   • 交易日期: {args.date}")
    print(f"   • 数据天数: {args.days} 天")
    print(f"   • 批次大小: {args.batch_size}")
    print(f"   • 工作线程: {args.workers}")
    print()
    
    # 执行预热
    stats = cache.pre_warm_cache(
        symbols=symbols,
        trade_date=args.date,
        days=args.days,
        batch_size=args.batch_size,
        max_workers=args.workers
    )
    
    if stats:
        print("\n✅ 缓存预热完成!")
    else:
        print("\n❌ 缓存预热失败")
    
    print("-" * 50)


def show_health_report(cache):
    """显示缓存健康度报告"""
    print("🏥 缓存健康度报告")
    print("=" * 50)
    
    health_report = cache.get_cache_health_report()
    
    if not health_report:
        print("❌ 无法获取健康度报告")
        return
    
    # 基本信息
    print(f"💾 缓存大小: {health_report['cache_size']:.2f} MB")
    print(f"🏥 健康度评分: {health_report['health_score']:.1f}/100")
    
    # 健康度评估
    score = health_report['health_score']
    if score >= 90:
        status = "✅ 优秀"
    elif score >= 80:
        status = "🟢 良好"
    elif score >= 60:
        status = "🟡 一般"
    else:
        status = "🔴 需要关注"
    
    print(f"📊 健康状态: {status}")
    print()
    
    # K线数据新鲜度
    kline_freshness = health_report['kline_data']['freshness']
    total_kline = health_report['kline_data']['total_count']
    
    print("📈 K线数据新鲜度:")
    print(f"   • 今日访问: {kline_freshness['today']:,} 条 ({kline_freshness['today']/total_kline*100:.1f}%)")
    print(f"   • 本周访问: {kline_freshness['week']:,} 条 ({kline_freshness['week']/total_kline*100:.1f}%)")
    print(f"   • 陈旧数据: {kline_freshness['old']:,} 条 ({kline_freshness['old']/total_kline*100:.1f}%)")
    print()
    
    # 基础信息新鲜度
    basic_freshness = health_report['basic_info']['freshness']
    total_basic = health_report['basic_info']['total_count']
    
    print("📋 基础信息新鲜度:")
    print(f"   • 今日访问: {basic_freshness['today']:,} 条 ({basic_freshness['today']/total_basic*100:.1f}%)")
    print(f"   • 本周访问: {basic_freshness['week']:,} 条 ({basic_freshness['week']/total_basic*100:.1f}%)")
    print(f"   • 陈旧数据: {basic_freshness['old']:,} 条 ({basic_freshness['old']/total_basic*100:.1f}%)")
    print()
    
    # 优化建议
    print("💡 优化建议:")
    if score >= 90:
        print("   • 继续保持当前状态")
    elif score >= 80:
        print("   • 可考虑定期清理过期数据")
    elif score >= 60:
        print("   • 建议执行缓存预热")
        print("   • 考虑清理陈旧数据")
    else:
        print("   • 强烈建议执行缓存预热")
        print("   • 立即清理陈旧数据")
        print("   • 考虑增加缓存大小限制")
    
    print("=" * 50)


def smart_cache_cleanup(cache, strategy_type, max_size_mb):
    """智能缓存清理"""
    print(f"🧠 智能缓存清理 - 策略: {strategy_type}")
    print("-" * 50)
    
    print(f"清理参数:")
    print(f"   • 策略类型: {strategy_type}")
    print(f"   • 最大缓存大小: {max_size_mb} MB")
    print()
    
    # 执行智能清理
    stats = cache.smart_cache_cleanup(strategy_type, max_size_mb=max_size_mb)
    
    if stats:
        print("\n✅ 智能缓存清理完成!")
    else:
        print("\n❌ 智能缓存清理失败")
    
    print("-" * 50)


if __name__ == "__main__":
    main()