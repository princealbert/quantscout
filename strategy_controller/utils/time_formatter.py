#!/usr/bin/env python
# coding=utf-8
"""
时间格式化工具 - 时间显示格式化函数
"""


def format_time(seconds: float) -> str:
    """格式化时间显示"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}分{remaining_seconds}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = int(seconds % 60)
        return f"{hours}时{minutes}分{remaining_seconds}秒"