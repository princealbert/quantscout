#!/usr/bin/env python
# coding=utf-8
"""
终端日志输出器

给 logger 装一个 sink，把日志同时输出到当前 Streamlit 启动的终端窗口中。
不依赖 WebSocket/状态管理，简单可靠。

注意：用户的工作流是"启动项目时打开 Trae IDE 的 PowerShell 终端"，
该终端就是项目主进程的标准输出，所有 logger 输出都在那里可见。
"""

import os
import sys
import json
import threading
import atexit
from datetime import datetime

# 安装标志（防止重复安装）
_SINK_INSTALLED = False
_SINK_LOCK = threading.Lock()


def _install_stdout_sink():
    """
    给 logger 装一个 stdout sink：每次 log() 调用同时把日志打印到终端
    幂等：rerun 不会重复包装
    """
    try:
        from strategy_controller.utils.logger import logger
    except ImportError:
        return False

    # 关键：检查原始 log 方法是否被包装过
    # 如果 logger.log 已经是 patched 版本（带 _original_log 属性），说明已包装
    if hasattr(logger.log, '_is_patched_sink'):
        return True

    # 启用 Windows 终端 ANSI 颜色
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass

    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[37m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'SUCCESS': '\033[32m',
        'BOLD': '\033[1m',
        'RESET': '\033[0m',
    }

    # 保存当前 logger.log（可能是原始版本，也可能是被 rerun 替换的版本）
    # 注意：第一次调用时 logger.log 是原始方法
    current_log = logger.log

    def patched_log(level, message):
        """包装后的 log 方法 - 既有原行为，又输出到 stdout"""
        # 1. 调用当前 logger.log（被rerun重新包装时这里指向最新包装版本，但_current_log属性避免嵌套）
        current_log(level, message)
        # 2. 输出到终端（带颜色）
        try:
            color = COLORS.get(level, COLORS['INFO'])
            timestamp = datetime.now().strftime('%H:%M:%S')
            line = f"{color}[{level:<7}]{COLORS['RESET']} {timestamp} {message}"
            print(line, file=sys.stderr, flush=True)
        except Exception:
            pass

    # 标记这是包装后的方法
    patched_log._is_patched_sink = True
    patched_log._original_log = current_log

    # 替换 logger.log 方法
    logger.log = patched_log
    return True


def start_log_terminal():
    """
    启动日志输出到当前终端
    Streamlit rerun 时会重新执行模块，但 sink 是幂等的不会重复安装
    """
    # Streamlit 的 ScriptRunner 会多次执行模块代码（每次rerun），用环境变量跨调用保护
    if os.environ.get('QS_LOG_TERMINAL_LAUNCHED') == '1':
        # 即使已启动也要装一次 sink（防止 rerun 时 monkey-patch 被重置）
        _install_stdout_sink()
        return
    os.environ['QS_LOG_TERMINAL_LAUNCHED'] = '1'

    # 安装 stdout sink
    if not _install_stdout_sink():
        return

    # 启动时打印横幅到终端（让用户知道日志输出已激活）
    try:
        print('', file=sys.stderr, flush=True)
        print('=' * 80, file=sys.stderr, flush=True)
        print('📺 QuantScout 实时日志输出已激活', file=sys.stderr, flush=True)
        print('=' * 80, file=sys.stderr, flush=True)
        print('所有策略/优化日志将显示在此终端中（与 Streamlit 输出混在同一终端）', file=sys.stderr, flush=True)
        print('=' * 80, file=sys.stderr, flush=True)
        print('', file=sys.stderr, flush=True)
    except Exception:
        pass
