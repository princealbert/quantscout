#!/usr/bin/env python
# coding=utf-8
"""
QuantScout量化选股系统 - 一键配置引导脚本
引导用户完成环境检测、依赖安装、Token配置等初始化工作

支持参数:
    --check-env     仅检测环境,不执行任何修改操作(Agent 友好)
    --auto-fix      自动修复可修复的问题(如自动创建 conda 环境)
    --diagnose      输出完整诊断报告,供 Agent 分析
    --create-shortcut  仅创建桌面快捷方式

设计原则:
    - 幂等:可反复调用,每次都打印清晰的 OK/FAIL
    - Agent 友好:每步输出结构化状态,Agent 可解析
    - 用户友好:图文提示 + 下载链接 + 教程引导
"""

import os
import sys
import subprocess
import time
import shutil
import platform


# ============================================================
# 通用工具函数
# ============================================================

def print_banner():
    """打印欢迎横幅"""
    print("=" * 70)
    print("QuantScout量化选股系统 - 配置向导")
    print("=" * 70)
    print("欢迎使用 QuantScout!本向导将帮助您完成系统配置。")
    print("完整流程:基础环境 → 依赖安装 → 掘金终端 → Token配置 → 桌面快捷方式")
    print("=" * 70)


def print_step(step_num, total_steps, title):
    """打印步骤标题

    参数:
        step_num: 当前步骤号
        total_steps: 总步骤数
        title: 步骤标题
    """
    print(f"\n[步骤 {step_num}/{total_steps}] {title}")
    print("-" * 70)


def print_ok(msg):
    """打印成功信息"""
    print(f"  [OK] {msg}")


def print_fail(msg):
    """打印失败信息"""
    print(f"  [FAIL] {msg}")


def print_warn(msg):
    """打印警告信息"""
    print(f"  [WARN] {msg}")


def print_info(msg):
    """打印提示信息"""
    print(f"  [INFO] {msg}")


def print_link(label, url):
    """打印链接"""
    print(f"  [LINK] {label}: {url}")


def get_project_root():
    """获取项目根目录"""
    return os.path.dirname(os.path.abspath(__file__))


def run_command(cmd, capture=True, timeout=60):
    """运行命令并返回结果

    参数:
        cmd: 命令列表或字符串
        capture: 是否捕获输出
        timeout: 超时秒数

    返回:
        (returncode, stdout, stderr) 元组
    """
    if isinstance(cmd, str):
        cmd_list = cmd.split()
    else:
        cmd_list = list(cmd)

    try:
        result = subprocess.run(
            cmd_list,
            capture_output=capture,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            shell=False
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except FileNotFoundError:
        return -2, "", f"命令不存在: {cmd_list[0]}"
    except Exception as e:
        return -3, "", str(e)


# ============================================================
# 步骤1: 基础环境检测 (Python / pip / conda / git)
# ============================================================

def check_python_version():
    """检测 Python 版本是否符合要求(>=3.8)

    返回:
        bool: 是否符合要求
    """
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print_info(f"Python 版本: {version_str} (路径: {sys.executable})")

    if version.major >= 3 and version.minor >= 8:
        print_ok(f"Python {version_str} 符合要求 (>=3.8)")
        return True
    else:
        print_fail(f"Python {version_str} 版本过低,需要 3.8 或更高版本")
        print_link("Python 下载", "https://www.python.org/downloads/")
        print_info("安装 Python 时请务必勾选 'Add Python to PATH'")
        return False


def check_pip():
    """检测 pip 是否可用

    返回:
        bool: pip 是否可用
    """
    returncode, stdout, _ = run_command([sys.executable, "-m", "pip", "--version"])

    if returncode == 0 and stdout.strip():
        # 解析 pip 版本
        first_line = stdout.strip().split("\n")[0]
        print_info(f"pip: {first_line}")
        print_ok("pip 可用")
        return True
    else:
        print_fail("pip 不可用")
        print_info("解决方案: 重新安装 Python,安装时勾选 'pip' 选项")
        print_link("Python 下载", "https://www.python.org/downloads/")
        return False


def check_conda():
    """检测 conda 是否可用

    返回:
        bool: conda 是否可用
    """
    # 优先使用 conda 命令
    returncode, stdout, _ = run_command(["conda", "--version"])

    if returncode == 0 and stdout.strip():
        print_info(f"conda: {stdout.strip()}")
        print_ok("conda 可用")
        return True

    # 尝试常见安装路径
    common_paths = [
        os.path.expanduser("~/anaconda3/Scripts/conda.exe"),
        os.path.expanduser("~/miniconda3/Scripts/conda.exe"),
        os.path.expanduser("~/AppData/Local/anaconda3/Scripts/conda.exe"),
        os.path.expanduser("~/AppData/Local/miniconda3/Scripts/conda.exe"),
        "C:\\ProgramData\\anaconda3\\Scripts\\conda.exe",
        "C:\\ProgramData\\miniconda3\\Scripts\\conda.exe",
    ]

    for conda_path in common_paths:
        if os.path.exists(conda_path):
            returncode, stdout, _ = run_command([conda_path, "--version"])
            if returncode == 0:
                print_info(f"conda: {stdout.strip()} (路径: {conda_path})")
                print_ok("conda 可用(在自定义路径找到)")
                # 提示用户可手动加入 PATH
                conda_dir = os.path.dirname(os.path.dirname(conda_path))
                print_warn(f"建议将以下路径加入系统 PATH: {conda_dir}\\Scripts")
                return True

    print_fail("conda 未安装")
    print_info("conda 不是必需,但强烈推荐用于管理 Python 虚拟环境")
    print_link("Anaconda 下载", "https://www.anaconda.com/download")
    print_link("Miniconda 下载(轻量)", "https://docs.conda.io/en/latest/miniconda.html")
    return False


def check_git():
    """检测 git 是否可用(可选依赖)

    返回:
        bool: git 是否可用
    """
    returncode, stdout, _ = run_command(["git", "--version"])

    if returncode == 0 and stdout.strip():
        print_info(f"git: {stdout.strip()}")
        print_ok("git 可用")
        return True
    else:
        print_warn("git 未安装(可选,仅克隆项目时需要)")
        print_link("Git 下载", "https://git-scm.com/download/win")
        return False


def check_in_conda_env():
    """检测当前是否在 conda 环境内

    返回:
        tuple: (是否在 conda 环境, 环境名)
    """
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "")
    if conda_env:
        return True, conda_env
    # 检查虚拟环境标识
    venv = os.environ.get("VIRTUAL_ENV", "")
    if venv:
        return True, os.path.basename(venv)
    return False, ""


def check_dcquant_env():
    """检测 dcquant conda 环境是否存在

    返回:
        bool: dcquant 环境是否存在
    """
    returncode, stdout, _ = run_command(["conda", "env", "list"])
    if returncode != 0:
        return False

    # 解析 conda env list 输出,查找 dcquant 环境
    for line in stdout.split("\n"):
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "dcquant":
            print_info(f"找到 dcquant 环境: {parts[1]}")
            return True
    return False


def create_dcquant_env():
    """创建 dcquant conda 环境

    返回:
        bool: 是否创建成功
    """
    print_info("正在创建 conda 环境 dcquant (Python 3.10)...")
    print_info("这可能需要几分钟时间,请耐心等待")

    cmd = ["conda", "create", "-n", "dcquant", "python=3.10", "-y"]
    returncode, stdout, stderr = run_command(cmd, timeout=600)

    if returncode == 0:
        print_ok("conda 环境 dcquant 创建成功")
        print_info("请在 dcquant 环境内重新运行本向导:")
        print("  conda activate dcquant")
        print("  python setup_wizard.py")
        return True
    else:
        print_fail("conda 环境 dcquant 创建失败")
        if stderr:
            print_info(f"错误信息: {stderr}")
        return False


def install_dependencies_in_conda(missing_packages):
    """在当前 conda 环境内安装缺失依赖

    参数:
        missing_packages: 缺失的依赖包列表

    返回:
        bool: 是否安装成功
    """
    if not missing_packages:
        print_ok("所有依赖包已安装")
        return True

    print_info(f"准备安装 {len(missing_packages)} 个缺失的依赖包...")
    print_info("使用清华源加速下载")

    # 使用国内镜像源加速安装
    pip_cmd = [sys.executable, "-m", "pip", "install",
               "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
    pip_cmd.extend(missing_packages)

    print_info(f"执行命令: {' '.join(pip_cmd)}")
    returncode, stdout, stderr = run_command(pip_cmd, timeout=600)

    if returncode == 0:
        print_ok("依赖包安装成功")
        return True
    else:
        print_fail("依赖包安装失败")
        if stderr:
            print_info(f"错误信息: {stderr}")
        print_info("可尝试手动安装: pip install -r requirements.txt")
        return False


def check_base_environment(auto_fix=False):
    """检测基础环境(Python/pip/conda/git)

    参数:
        auto_fix: 是否自动修复可修复的问题(如自动创建 conda 环境)

    返回:
        dict: 检测结果字典,包含各项状态
    """
    results = {
        "python_ok": False,
        "pip_ok": False,
        "conda_ok": False,
        "git_ok": False,
        "in_env": False,
        "env_name": "",
        "is_dcquant": False,
    }

    print("\n[阶段 1/5] 基础环境检测")
    print("=" * 70)
    print("检测 Python / pip / conda / git 是否就绪...\n")

    # 1. Python 版本
    results["python_ok"] = check_python_version()
    print()

    # 2. pip
    results["pip_ok"] = check_pip()
    print()

    # 3. conda
    results["conda_ok"] = check_conda()
    print()

    # 4. git (可选)
    results["git_ok"] = check_git()
    print()

    # 5. 当前是否在 conda 环境
    in_env, env_name = check_in_conda_env()
    results["in_env"] = in_env
    results["env_name"] = env_name
    if in_env:
        print_ok(f"当前在虚拟环境内: {env_name}")
        if env_name == "dcquant":
            results["is_dcquant"] = True
            print_ok("检测到目标环境 dcquant,符合规范")
    else:
        print_warn("未在虚拟环境内运行(使用系统 Python)")
        print_info("建议使用 conda 虚拟环境隔离依赖,避免污染系统 Python")
    print()

    # 6. 如果 conda 可用但不在 dcquant 环境,自动创建
    if results["conda_ok"] and not results["is_dcquant"] and auto_fix:
        if check_dcquant_env():
            print_ok("dcquant 环境已存在,请手动激活:")
            print("  conda activate dcquant")
            print("  python setup_wizard.py")
        else:
            print_warn("即将自动创建 dcquant 环境")
            create_dcquant_env()
    elif results["conda_ok"] and not results["is_dcquant"] and not auto_fix:
        if check_dcquant_env():
            print_info("dcquant 环境已存在,请激活后重新运行:")
            print("  conda activate dcquant")
            print("  python setup_wizard.py")
        else:
            print_info("检测到 conda 可用但 dcquant 环境未创建")
            print_info("可使用 --auto-fix 参数自动创建,或手动执行:")
            print("  conda create -n dcquant python=3.10 -y")
            print("  conda activate dcquant")
            print("  python setup_wizard.py")

    # 汇总
    print("-" * 70)
    required_ok = results["python_ok"] and results["pip_ok"]
    if required_ok:
        print_ok("基础环境核心检测通过 (Python + pip)")
    else:
        print_fail("基础环境核心检测未通过,请先安装 Python 3.8+")

    return results


# ============================================================
# 步骤2: 项目依赖检测与安装
# ============================================================

def check_dependencies():
    """检测所有依赖包是否已安装

    返回:
        list: 缺失的依赖包列表
    """
    print("\n[阶段 2/5] 项目依赖检测")
    print("=" * 70)
    print("检测项目所需的 Python 依赖包...\n")

    required_packages = [
        ("streamlit", "Streamlit Web框架"),
        ("plotly", "图表可视化库"),
        ("pandas", "数据分析库"),
        ("numpy", "数值计算库"),
        ("gm", "东财掘金SDK"),
        ("openpyxl", "Excel文件处理"),
        ("cryptography", "加密库"),
        ("requests", "HTTP请求库"),
    ]

    missing_packages = []

    for package, description in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print_ok(f"{package} ({description})")
        except ImportError:
            print_fail(f"{package} ({description}) - 未安装")
            missing_packages.append(package)

    return missing_packages


def install_dependencies(missing_packages):
    """安装缺失的依赖包

    参数:
        missing_packages: 缺失的依赖包列表

    返回:
        bool: 是否安装成功
    """
    if not missing_packages:
        print_ok("所有依赖包已安装")
        return True

    print_info(f"准备安装 {len(missing_packages)} 个缺失的依赖包...")
    print_info("使用清华源加速下载")

    try:
        pip_cmd = [sys.executable, "-m", "pip", "install",
                   "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
        pip_cmd.extend(missing_packages)

        print_info(f"执行命令: {' '.join(pip_cmd)}")
        returncode, stdout, stderr = run_command(pip_cmd, timeout=600)

        if returncode == 0:
            print_ok("依赖包安装成功")
            return True
        else:
            print_fail(f"依赖包安装失败: {stderr}")
            return False

    except Exception as e:
        print_fail(f"安装过程出错: {e}")
        return False


# ============================================================
# 步骤3: 掘金终端检测与引导
# ============================================================

def check_gm_terminal():
    """检测东财掘金终端是否运行,并测试 API 连通性

    返回:
        dict: 检测结果字典
    """
    print("\n[阶段 3/5] 东财掘金终端检测")
    print("=" * 70)
    print("检测掘金 SDK 是否可用,并测试 API 连通性...\n")

    results = {
        "gm_sdk_ok": False,
        "token_configured": False,
        "api_connected": False,
    }

    # 1. 检测 gm SDK 是否安装
    try:
        import gm
        print_ok(f"东财掘金 SDK 已安装 (版本: {getattr(gm, '__version__', '未知')})")
        results["gm_sdk_ok"] = True
    except ImportError:
        print_fail("东财掘金 SDK 未安装")
        print_info("请通过 pip 安装: pip install gm")
        return results
    print()

    # 2. 检测 Token 是否已配置
    try:
        # 临时将项目根目录加入 sys.path
        project_root = get_project_root()
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from config.token_manager import TokenManager
        token_manager = TokenManager()
        token = token_manager.get_token()
        if token:
            print_ok("API Token 已配置")
            results["token_configured"] = True
        else:
            print_fail("API Token 未配置")
            print_info("请在下一步骤中配置 Token")
    except Exception as e:
        print_fail(f"Token 检测失败: {e}")
    print()

    # 3. 测试 API 连通性(需要 Token 和终端)
    if results["token_configured"]:
        print_info("正在测试掘金 API 连通性(需要掘金终端运行)...")
        print_info("如长时间无响应,请确认掘金终端已启动并登录")
        try:
            from gm.api import set_token
            set_token(token)

            # 尝试调用一个基础接口(获取最新交易日)
            from gm.api import get_trading_dates
            trading_dates = get_trading_dates(exchange="SHSE", start_date="2025-01-01", end_date="2025-12-31")
            if trading_dates is not None:
                print_ok("掘金 API 连通性测试通过")
                print_info(f"获取到交易日数据({len(trading_dates)} 个交易日)")
                results["api_connected"] = True
            else:
                print_fail("掘金 API 返回空数据")
                print_info("可能原因:掘金终端未运行 / Token 权限不足 / 网络问题")
                _show_gm_terminal_guide()
        except Exception as e:
            print_fail(f"掘金 API 连通性测试失败: {e}")
            print_info("最常见原因:掘金终端未启动")
            _show_gm_terminal_guide()
    else:
        print_info("跳过 API 连通性测试(需先配置 Token)")
        _show_gm_terminal_guide()

    return results


def _show_gm_terminal_guide():
    """显示掘金终端图文教程引导"""
    print()
    print_info("掘金终端使用教程:")
    print("  1. 下载并安装掘金量化终端")
    print_link("掘金官网", "https://www.myquant.cn/")
    print("  2. 注册账号并完成实名认证")
    print("  3. 启动终端并登录")
    print("  4. 进入「系统设置」→「密钥管理」生成 Token")
    print()
    print_info("详细图文教程:")
    guide_path = os.path.join(get_project_root(), "docs", "gm_guide.html")
    if os.path.exists(guide_path):
        print_link("本地图文教程", f"file:///{guide_path}")
        # 询问是否自动打开
        try:
            open_now = input("  是否现在打开图文教程? (y/n): ").strip().lower()
            if open_now == 'y':
                import webbrowser
                webbrowser.open(f"file:///{guide_path}")
                print_ok("已打开图文教程")
        except (EOFError, KeyboardInterrupt):
            pass
    else:
        print_link("在线教程", "https://www.myquant.cn/docs/python/")
    print()


# ============================================================
# 步骤4: Token 配置
# ============================================================

def configure_token():
    """配置 API Token

    返回:
        bool: 是否配置成功
    """
    print("\n[阶段 4/5] Token 配置")
    print("=" * 70)
    print("请在东财掘金终端生成 API Token 后,粘贴到下方:\n")
    print("Token 获取步骤:")
    print("  1. 打开东财掘金量化终端")
    print("  2. 进入「系统设置」→「密钥管理」")
    print("  3. 点击「生成 Token」按钮")
    print("  4. 复制生成的 Token\n")

    try:
        token = input("请粘贴您的 API Token (或直接回车跳过): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n用户中断")
        return False

    if not token:
        print_warn("未输入 Token,跳过配置")
        print_info("可稍后运行 python setup_wizard.py 重新配置")
        return False

    # 验证 Token 格式
    if len(token) < 16 or len(token) > 64:
        print_fail("Token 格式不正确(应为 16-64 个字符)")
        return False

    # 保存 Token
    try:
        project_root = get_project_root()
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from config.token_manager import TokenManager

        token_manager = TokenManager()
        token_manager.save_token(token)
        print_ok("Token 配置成功(已加密存储)")

        # 验证 Token
        if token_manager.validate_token():
            print_ok("Token 验证通过")
            return True
        else:
            print_warn("Token 验证失败,请检查 Token 是否正确")
            return False

    except Exception as e:
        print_fail(f"Token 配置失败: {e}")
        return False


# ============================================================
# 步骤5: 桌面快捷方式自动创建
# ============================================================

def create_desktop_shortcut():
    """自动创建桌面快捷方式

    创建以下快捷方式:
        - QuantScout 启动器(调用 launcher.py)
        - 启动策略控制器.bat
        - 启动参数优化器.bat
        - 一键启动全部.bat

    返回:
        bool: 是否创建成功
    """
    print("\n[阶段 5/5] 桌面快捷方式创建")
    print("=" * 70)
    print("正在创建桌面快捷方式,让用户双击即可启动...\n")

    project_root = get_project_root()
    desktop_dir = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")),
                               "Desktop")

    if not os.path.exists(desktop_dir):
        print_fail(f"桌面目录不存在: {desktop_dir}")
        return False

    # 检测 .bat 启动脚本是否存在
    bat_files = [
        ("启动策略控制器.bat", "QuantScout - 策略控制器"),
        ("启动参数优化器.bat", "QuantScout - 参数优化器"),
        ("一键启动全部.bat", "QuantScout - 一键启动"),
    ]

    created_count = 0
    for bat_file, shortcut_name in bat_files:
        bat_path = os.path.join(project_root, bat_file)
        if not os.path.exists(bat_path):
            print_warn(f"启动脚本不存在,跳过: {bat_file}")
            continue

        shortcut_path = os.path.join(desktop_dir, f"{shortcut_name}.lnk")

        # 使用 PowerShell 创建快捷方式
        ps_script = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$s = $ws.CreateShortcut("{shortcut_path}"); '
            f'$s.TargetPath = "{bat_path}"; '
            f'$s.WorkingDirectory = "{project_root}"; '
            f'$s.IconLocation = "{sys.executable},0"; '
            f'$s.Description = "QuantScout 量化选股系统"; '
            f'$s.Save()'
        )

        returncode, _, stderr = run_command(
            ["powershell", "-NoProfile", "-Command", ps_script]
        )

        if returncode == 0:
            print_ok(f"已创建: {shortcut_name}")
            created_count += 1
        else:
            print_fail(f"创建失败: {shortcut_name} ({stderr})")

    if created_count > 0:
        print_info(f"共创建 {created_count} 个桌面快捷方式")
        print_info("用户现在可以双击桌面图标直接启动应用,无需打开终端")
        return True
    else:
        print_warn("未创建任何快捷方式")
        print_info("请先运行 .bat 启动脚本的生成(参见文档)")
        return False


# ============================================================
# 快速测试
# ============================================================

def run_quick_test():
    """运行快速测试验证后端功能

    返回:
        bool: 测试是否成功
    """
    print("\n[快速测试] 验证后端选股功能")
    print("-" * 70)

    try:
        project_root = get_project_root()
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from strategies.multi_dim_strategy import run_multi_dim_strategy_screener

        print_info("正在运行选股测试(测试模式,最多 5 只)...")
        results = run_multi_dim_strategy_screener(test_mode=True, max_results=5)

        if results:
            print_ok(f"测试成功!找到 {len(results)} 只符合条件的股票")
        else:
            print_ok("测试完成(未找到符合条件的股票,可能是市场条件所致)")
        return True

    except Exception as e:
        print_fail(f"测试过程中出现错误: {e}")
        print_info("提示:请确保东财掘金终端已启动并登录,且 Token 已配置")
        return False


# ============================================================
# 诊断报告模式 (--diagnose)
# ============================================================

def run_diagnose():
    """输出完整诊断报告,供 Agent 分析

    Agent 可调用 `python setup_wizard.py --diagnose` 获取结构化报告
    """
    print("=" * 70)
    print("QuantScout 诊断报告")
    print("=" * 70)
    print(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"操作系统: {platform.platform()}")
    print()

    # 1. Python 环境
    print("## Python 环境")
    py_ok = check_python_version()
    pip_ok = check_pip()
    conda_ok = check_conda()
    git_ok = check_git()
    in_env, env_name = check_in_conda_env()
    print(f"  在虚拟环境内: {in_env} ({env_name or 'N/A'})")
    print(f"  在 dcquant 环境: {env_name == 'dcquant'}")
    print()

    # 2. 依赖包
    print("## 项目依赖")
    missing = check_dependencies()
    print(f"  缺失依赖: {missing if missing else '无'}")
    print()

    # 3. 掘金终端
    print("## 掘金终端")
    gm_results = check_gm_terminal()
    print()

    # 4. 桌面快捷方式状态
    print("## 桌面快捷方式")
    desktop_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    for bat_file, label in [
        ("启动策略控制器.bat", "策略控制器"),
        ("启动参数优化器.bat", "参数优化器"),
        ("一键启动全部.bat", "一键启动"),
    ]:
        bat_path = os.path.join(get_project_root(), bat_file)
        lnk_path = os.path.join(desktop_dir, f"QuantScout - {label}.lnk")
        bat_exists = os.path.exists(bat_path)
        lnk_exists = os.path.exists(lnk_path)
        print(f"  {label}: bat={'存在' if bat_exists else '缺失'}, "
              f"快捷方式={'存在' if lnk_exists else '缺失'}")
    print()

    # 5. 总结与建议
    print("## 诊断总结")
    print(f"  Python: {'OK' if py_ok else 'FAIL'}")
    print(f"  pip:    {'OK' if pip_ok else 'FAIL'}")
    print(f"  conda:  {'OK' if conda_ok else 'WARN(可选)'}")
    print(f"  git:    {'OK' if git_ok else 'WARN(可选)'}")
    print(f"  依赖:   {'OK' if not missing else f'缺失 {len(missing)} 个'}")
    print(f"  掘金:   {'OK' if gm_results['api_connected'] else 'FAIL'}")
    print()
    print("## Agent 建议下一步")
    if not py_ok:
        print("  -> 引导用户安装 Python 3.8+")
    elif not pip_ok:
        print("  -> 重新安装 Python(勾选 pip)")
    elif missing:
        print("  -> 运行 `python setup_wizard.py --auto-fix` 自动安装依赖")
    elif not conda_ok:
        print("  -> 引导用户安装 Anaconda/Miniconda(可选,推荐)")
    elif not in_env:
        print("  -> 创建并激活 dcquant 环境: conda create -n dcquant python=3.10 -y && conda activate dcquant")
    elif not gm_results['token_configured']:
        print("  -> 引导用户配置 Token")
    elif not gm_results['api_connected']:
        print("  -> 引导用户启动掘金终端并登录")
    else:
        print("  -> 环境就绪!可创建桌面快捷方式并启动应用")


# ============================================================
# 主流程
# ============================================================

def main():
    """主函数:按顺序执行各阶段配置"""
    # 解析参数
    args = sys.argv[1:]
    check_env_only = "--check-env" in args
    auto_fix = "--auto-fix" in args
    diagnose_mode = "--diagnose" in args
    shortcut_only = "--create-shortcut" in args

    # 诊断模式:输出结构化报告
    if diagnose_mode:
        run_diagnose()
        return

    # 仅创建快捷方式
    if shortcut_only:
        print_banner()
        create_desktop_shortcut()
        return

    print_banner()

    # 仅检测模式
    if check_env_only:
        check_base_environment(auto_fix=False)
        check_dependencies()
        check_gm_terminal()
        print("\n" + "=" * 70)
        print("环境检测完成(仅检测,未修改任何内容)")
        print("如需自动修复,请运行: python setup_wizard.py --auto-fix")
        print("=" * 70)
        return

    # 完整流程
    TOTAL_STEPS = 5

    # 阶段1: 基础环境检测
    print_step(1, TOTAL_STEPS, "基础环境检测 (Python / pip / conda / git)")
    env_results = check_base_environment(auto_fix=auto_fix)

    # Python 是必需的,失败则终止
    if not env_results["python_ok"]:
        print("\n" + "=" * 70)
        print_fail("基础环境检测未通过(Python 缺失),请先安装 Python 3.8+")
        print_link("Python 下载", "https://www.python.org/downloads/")
        print("=" * 70)
        return

    # 阶段2: 依赖安装
    print_step(2, TOTAL_STEPS, "项目依赖检测与安装")
    missing_packages = check_dependencies()
    if missing_packages:
        if auto_fix:
            print_info("--auto-fix 模式:自动安装缺失依赖")
            install_dependencies(missing_packages)
        else:
            try:
                install_now = input("\n是否立即安装缺失的依赖包? (y/n): ").strip().lower()
                if install_now == 'y':
                    if not install_dependencies(missing_packages):
                        print_fail("依赖安装失败,请手动安装")
                        return
                else:
                    print_warn("跳过依赖安装,请稍后手动执行:")
                    print("  pip install -r requirements.txt")
            except (EOFError, KeyboardInterrupt):
                print("\n用户中断")
                return
    else:
        print_ok("所有项目依赖已安装")

    # 阶段3: 掘金终端检测
    print_step(3, TOTAL_STEPS, "东财掘金终端检测")
    gm_results = check_gm_terminal()

    # 阶段4: Token 配置
    print_step(4, TOTAL_STEPS, "Token 配置")
    if gm_results.get("token_configured"):
        print_ok("Token 已配置,跳过本步骤")
    else:
        try:
            configure_now = input("\n是否现在配置 API Token? (y/n): ").strip().lower()
            if configure_now == 'y':
                configure_token()
            else:
                print_warn("跳过 Token 配置,可稍后运行 setup_wizard 重新配置")
        except (EOFError, KeyboardInterrupt):
            print("\n用户中断")
            return

    # 阶段5: 桌面快捷方式
    print_step(5, TOTAL_STEPS, "桌面快捷方式创建(一键启动)")
    try:
        create_shortcut = input("\n是否创建桌面快捷方式(双击即可启动)? (y/n): ").strip().lower()
        if create_shortcut == 'y':
            create_desktop_shortcut()
        else:
            print_info("跳过桌面快捷方式创建,可稍后运行:")
            print("  python setup_wizard.py --create-shortcut")
    except (EOFError, KeyboardInterrupt):
        print("\n用户中断")
        return

    # 完成
    print("\n" + "=" * 70)
    print("配置向导完成!")
    print("=" * 70)
    print("\n下一步:")
    print("  方式1(推荐): 双击桌面快捷方式启动")
    print("  方式2: 运行启动器  python launcher.py")
    print("  方式3: 直接启动单个应用")
    print("    streamlit run strategy_controller/main.py --server.port 8502")
    print("    streamlit run ulti-para-seeker/app.py --server.port 8501")
    print("\n可选模式:")
    print("  1. 启动策略控制器 (端口: 8502)")
    print("  2. 启动参数优化器 (端口: 8501)")
    print("  3. 同时启动两个应用")
    print("=" * 70)


if __name__ == "__main__":
    main()
