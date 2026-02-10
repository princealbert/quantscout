#!/usr/bin/env python
# coding=utf-8
"""
测试Token是否可以被正确解密
"""

import os
import sys
from config import token_manager

# 测试获取Token
print("测试获取Token...")
token = token_manager.get_token()

if token:
    print(f"✅ 成功获取Token，长度: {len(token)}位")
    print(f"Token前10位: {token[:10]}...")
else:
    print("❌ 获取Token失败")

# 测试Token验证
print("\n测试Token验证...")
if token:
    is_valid = token_manager.verify_token(token)
    if is_valid:
        print("✅ Token验证成功")
    else:
        print("❌ Token验证失败")
else:
    print("❌ 无法验证Token，因为获取失败")

# 测试Token信息
print("\n测试Token信息...")
token_info = token_manager.get_token_info()
if token_info:
    print("✅ 获取Token信息成功")
    print(f"描述: {token_info.get('description', '无')}")
    print(f"创建时间: {token_info.get('created_at', '无')}")
    print(f"更新时间: {token_info.get('updated_at', '无')}")
else:
    print("❌ 获取Token信息失败")
