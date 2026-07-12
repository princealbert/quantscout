#!/usr/bin/env python
# coding=utf-8
"""
QuantScout选股策略启动器 - 统一入口
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
        "gm",
        "openpyxl"  # Excel文件处理
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
    print("🚀 启动QuantScout量化选股系统...")
    print("=" * 60)
    print("🎯 QuantScout量化选股系统 (重构版)")
    print("=" * 60)
    print("🆕 重构特性:")
    print("• 模块化架构: UI/业务/展示/工具模块分离")
    print("• 单一职责原则: 每个模块专注特定功能")
    print("• 代码可维护性: 更清晰的代码组织结构")
    print("• 功能特色:")
    print("  • 策略支持: 多维综合策略")
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
        cmd = f'"{sys.executable}" -m streamlit run strategy_controller/main.py --server.port 8502 --server.headless true --server.address 127.0.0.1 --logger.level info --server.runOnSave false'
        
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


def start_parameter_optimizer():
    """启动参数优化器 - 在当前终端启动headless版本"""
    print("🚀 启动参数优化器...")
    print("=" * 60)
    print("🎯 参数优化器")
    print("=" * 60)
    print("功能特色:")
    print("• 参数组合生成与优化")
    print("• 支持暴力搜索和遗传算法")
    print("• 回测结果可视化")
    print("• 支持从Excel文件读取回测结果")
    print("=" * 60)
    
    try:
        # 设置环境变量强制使用UTF-8编码
        import os
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        # 构建启动命令
        app_path = os.path.join(os.path.dirname(__file__), "ulti-para-seeker", "app.py")
        cmd = f'"{sys.executable}" -m streamlit run "{app_path}" --server.port 8501 --server.headless true --server.address 127.0.0.1 --logger.level info --server.runOnSave false'
        
        print("🌐 在当前终端启动Streamlit服务器...")
        print("📱 请在浏览器中访问: http://localhost:8501")
        print("📊 服务器日志将显示在当前终端中")
        print("⏹️  按 Ctrl+C 停止服务器")
        print("=" * 60)
        
        # 等待2秒后打开浏览器
        import time
        time.sleep(2)
        webbrowser.open("http://localhost:8501")
        
        # 启动Streamlit服务器
        print("🚀 启动参数优化器服务器...")
        print("=" * 60)
        
        result = subprocess.run(cmd, shell=True, env=env)
        
        if result.returncode == 0:
            print("✅ 参数优化器服务器已正常停止")
        else:
            print(f"⚠️  参数优化器服务器异常退出，返回码: {result.returncode}")
        
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
        from strategies.multi_dim_strategy import run_multi_dim_strategy_screener
        
        print("测试多维综合策略...")
        
        # 使用正确的函数调用方式
        results = run_multi_dim_strategy_screener(
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


def start_all_applications():
    """同时启动策略控制器和参数优化器"""
    print("🚀 同时启动策略控制器和参数优化器...")
    print("=" * 60)
    print("🎯 多应用启动模式")
    print("=" * 60)
    print("• 策略控制器: http://localhost:8502")
    print("• 参数优化器: http://localhost:8501")
    print("• 两个应用将同时运行在不同端口")
    print("=" * 60)
    
    try:
        # 设置环境变量强制使用UTF-8编码
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        # 启动参数优化器 (端口8501) - 添加详细日志级别
        optimizer_path = os.path.join(os.path.dirname(__file__), "ulti-para-seeker", "app.py")
        optimizer_cmd = f'"{sys.executable}" -m streamlit run "{optimizer_path}" --server.port 8501 --server.headless true --server.address 127.0.0.1 --logger.level info'
        
        # 启动策略控制器 (端口8502) - 添加详细日志级别
        controller_cmd = f'"{sys.executable}" -m streamlit run strategy_controller/main.py --server.port 8502 --server.headless true --server.address 127.0.0.1 --logger.level info --server.runOnSave false'
        
        print("🌐 启动参数优化器服务器...")
        print(f"   命令: {optimizer_cmd}")
        # 直接输出到当前终端，不重定向
        optimizer_process = subprocess.Popen(optimizer_cmd, shell=True, env=env)
        
        print("🌐 启动策略控制器服务器...")
        print(f"   命令: {controller_cmd}")
        # 直接输出到当前终端，不重定向
        controller_process = subprocess.Popen(controller_cmd, shell=True, env=env)
        
        # 等待2秒后打开浏览器
        import time
        time.sleep(2)
        
        print("📱 打开浏览器窗口...")
        webbrowser.open("http://localhost:8501")  # 参数优化器
        webbrowser.open("http://localhost:8502")  # 策略控制器
        
        print("\n✅ 两个应用已成功启动！")
        print("📊 服务器日志将输出到后台")
        print("⏹️  按 Ctrl+C 停止所有服务器")
        print("=" * 60)
        
        # 等待用户中断
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 用户中断，正在停止所有服务器...")
            
            # 尝试优雅关闭
            optimizer_process.terminate()
            controller_process.terminate()
            
            # 等待进程结束
            optimizer_process.wait(timeout=5)
            controller_process.wait(timeout=5)
            
            print("✅ 所有服务器已停止")
            return True
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def display_help():
    """显示帮助信息"""
    print("\n📚 使用说明:")
    print("1. 策略控制器 - 完整的Web界面，支持权重配置和可视化")
    print("2. 参数优化器 - 参数组合生成与优化，回测结果可视化")
    print("3. 同时启动 - 一键启动策略控制器和参数优化器")
    print("4. 后端测试 - 测试选股策略功能")
    print("5. 帮助 - 显示使用说明")
    print("\n💡 推荐使用同时启动模式，提供完整的策略分析体验")


def main():
    """主函数"""
    print("🎯 QuantScout量化选股系统启动器")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖包检查失败，请手动安装所需包")
        return
    
    while True:
        print("\n📋 请选择操作:")
        print("1. 🚀 启动策略控制器")
        print("2. 🎯 启动参数优化器")
        print("3. 🤖 同时启动两个应用")
        print("4. 🔧 测试后端选股功能")
        print("5. 📚 显示帮助信息")
        print("6. 👋 退出")
        
        try:
            choice = input("\n请输入选择 (1-6): ").strip()
            
            if choice == "1":
                start_controller()
                break
            elif choice == "2":
                start_parameter_optimizer()
                break
            elif choice == "3":
                start_all_applications()
                break
            elif choice == "4":
                run_backend_test()
                break
            elif choice == "5":
                display_help()
            elif choice == "6":
                print("👋 再见！")
                break
            else:
                print("❌ 无效选择，请重新输入")
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break


if __name__ == "__main__":
    main()