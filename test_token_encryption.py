#!/usr/bin/env python
# coding=utf-8
"""
测试Token管理器的加密和解密功能
"""

from config.token_manager import token_manager

print("=== Token管理器加密测试 ===")

# 测试1: 保存一个测试token
print("\n1. 保存测试token...")
test_token = "actual_test_token_1234567890"
save_result = token_manager.save_token(test_token, "测试加密token")
print(f"   保存结果: {'成功' if save_result else '失败'}")

# 测试2: 读取加密后的token文件
print("\n2. 读取加密后的token文件...")
with open(token_manager.token_file, 'r', encoding='utf-8') as f:
    import json
    config = json.load(f)
    print(f"   加密后的token: {config['token']}")
    print(f"   token_hash: {config['token_hash']}")

# 测试3: 获取解密后的token
print("\n3. 获取解密后的token...")
decrypted_token = token_manager.get_token()
print(f"   解密后的token: {decrypted_token}")
print(f"   解密结果是否正确: {decrypted_token == test_token}")

# 测试4: 验证token
print("\n4. 验证token...")
verify_result = token_manager.verify_token(test_token)
print(f"   验证结果: {'通过' if verify_result else '失败'}")

print("\n=== 测试完成 ===")