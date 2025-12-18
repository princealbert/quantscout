#!/usr/bin/env python
# coding=utf-8
"""
z哥选股策略启动器 - 统一入口
整合所有功能，提供完整的用户体验
"""

import os
import sys
import subprocess
import webbrowser
from datetime import datetime


def check_dependencies():
    """检查依赖包"""
    print("📦 检查依赖包...")
    
    required_packages = [
        "streamlit",
        "plotly", 
        "pandas",
        "numpy",
        "gm"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"{package} 已安装")
        except ImportError:
            print(f"{package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def start_controller():
    """启动策略控制器 - 在当前终端启动headless版本"""
    print("🚀 启动重构版z哥选股策略控制器...")
    print("=" * 60)
    print("🎯 z哥选股策略控制器 (重构版)")
    print("=" * 60)
    print("🆕 重构特性:")
    print("• 模块化架构: UI/业务/展示/工具模块分离")
    print("• 单一职责原则: 每个模块专注特定功能")
    print("• 代码可维护性: 更清晰的代码组织结构")
    print("• 功能特色:")
    print("  • 策略支持: z哥综合策略")
    print("  • 实时权重调整: 支持7个维度的权重配置")
    print("  • 可视化分析: 图表分析、数据表格、详细视图")
    print("  • 批量处理: 支持全量A股分批处理")
    print("  • 报告生成: HTML/CSV格式报告")
    print("=" * 60)
    
    try:
        # 设置环境变量强制使用UTF-8编码
        import os
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        # 直接在当前终端启动Streamlit headless版本
        cmd = f'"{sys.executable}" -m streamlit run emgm/strategy_controller/main.py --server.port 8502 --server.headless true --server.address 127.0.0.1 --logger.level info'
        
        print("🌐 在当前终端启动Streamlit服务器...")
        print("📱 请在浏览器中访问: http://localhost:8502")
        print("📊 服务器日志将显示在当前终端中")
        print("⏹️  按 Ctrl+C 停止服务器")
        print("=" * 60)
        
        # 等待2秒后打开浏览器
        import time
        time.sleep(2)
        webbrowser.open("http://localhost:8502")
        
        # 在当前终端中启动Streamlit（这会阻塞当前进程）
        print("🚀 启动Streamlit服务器...")
        print("=" * 60)
        
        # 使用subprocess.run()而不是Popen，这样会在当前终端运行
        result = subprocess.run(cmd, shell=True, env=env)
        
        if result.returncode == 0:
            print("✅ Streamlit服务器已正常停止")
        else:
            print(f"⚠️  Streamlit服务器异常退出，返回码: {result.returncode}")
        
        return True
            
    except KeyboardInterrupt:
        print("\n👋 用户中断，服务器已停止")
        return True
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_backend_test():
    """运行后端测试 - 增强错误处理和用户体验"""
    print("🔧 测试后端选股功能...")
    
    try:
        from emgm.strategies.zge_strategy import run_zge_strategy_screener
        
        print("测试z哥综合策略...")
        
        # 使用正确的函数调用方式
        results = run_zge_strategy_screener(
            test_mode=True,    # 测试模式：仅处理前100只股票
            max_results=10,    # 最大结果数
            skip_st=True       # 跳过ST股
        )
        
        if results:
            print(f"✅ 后端测试成功！找到 {len(results)} 只符合条件的股票")
            
            # 显示结果摘要
            print("\n📊 选股结果摘要:")
            print("-" * 80)
            print(f"{'排名':<4} {'股票代码':<12} {'股票名称':<10} {'收盘价':<8} {'J值':<8} {'综合评分':<8}")
            print("-" * 80)
            
            for i, stock in enumerate(results):
                print(f"{i+1:<4} {stock['symbol']:<12} {stock.get('sec_name', 'N/A')[:8]:<10} "
                      f"{stock['close']:<8.2f} {stock['kdj_j']:<8.2f} {stock.get('total_score', 0):<8.2f}")
            
            print("-" * 80)
            
            # 提供更多统计信息
            print("\n📈 性能统计:")
            print(f"• 总耗时: 约 1-3 分钟")
            print(f"• 处理股票数: 100 只（测试模式）")
            print(f"• 筛选通过率: {len(results)/100*100:.1f}%")
            
            return True
        else:
            print("✅ 后端测试完成，但未找到符合条件的股票")
            print("💡 提示：这可能是因为当前市场条件或筛选条件较严格")
            return True
            
    except Exception as e:
        print(f"❌ 后端测试失败: {e}")
        print("\n🛠️  故障排除建议:")
        print("• 检查网络连接")
        print("• 确认API token有效")
        print("• 检查数据源是否可访问")
        return False


def display_help():
    """显示帮助信息"""
    print("\n📚 使用说明:")
    print("1. 策略控制器 - 完整的Web界面，支持权重配置和可视化")
    print("2. 后端测试 - 测试选股策略功能")
    print("3. 帮助 - 显示使用说明")
    print("\n💡 推荐使用策略控制器，提供最佳用户体验")


def main():
    """主函数"""
    print("🎯 z哥选股策略系统启动器")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖包检查失败，请手动安装所需包")
        return
    
    while True:
        print("\n📋 请选择操作:")
        print("1. 🚀 启动策略控制器 (推荐)")
        print("2. 🔧 测试后端选股功能")
        print("3. 📚 显示帮助信息")
        print("4. 👋 退出")
        
        try:
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == "1":
                start_controller()
                break
            elif choice == "2":
                run_backend_test()
                break
            elif choice == "3":
                display_help()
            elif choice == "4":
                print("👋 再见！")
                break
            else:
                print("❌ 无效选择，请重新输入")
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break


if __name__ == "__main__":
    main()