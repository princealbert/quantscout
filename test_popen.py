#!/usr/bin/env python
# coding=utf-8
"""
测试subprocess.Popen参数兼容性
"""

import subprocess

print("=== 测试subprocess.Popen参数 ===")

# 测试兼容的Popen参数
try:
    process = subprocess.Popen(
        ['python', '-c', 'import time; time.sleep(1); print("test")'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    print(f"✅ 成功! stdout: {stdout.strip()}, stderr: {stderr.strip()}")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试结束 ===")