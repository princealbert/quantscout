#!/usr/bin/env python
# coding=utf-8
"""
Token导入工具 - 用于向后兼容旧的token_config.py
"""

import os
from typing import Optional
from .token_manager import TokenManager


def import_old_token() -> bool:
    """
    从旧的token_config.py导入Token
    
    Returns:
        是否导入成功
    """
    try:
        # 读取旧的token_config.py文件
        old_token_file = "token_config.py"
        
        if not os.path.exists(old_token_file):
            print("❌ 未找到旧的token_config.py文件")
            return False
        
        # 读取文件内容
        with open(old_token_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取Token值
        import re
        match = re.search(r'TOKEN\s*=\s*["\']([^"\']+)["\']', content)
        
        if not match:
            print("❌ 未在token_config.py中找到TOKEN定义")
            return False
        
        old_token = match.group(1)
        
        # 验证Token
        if not old_token or len(old_token) < 16:
            print("❌ 旧Token格式无效")
            return False
        
        # 保存到新的Token管理器
        token_manager = TokenManager()
        success = token_manager.save_token(old_token, "从旧token_config.py导入")
        
        if success:
            print(f"✅ Token导入成功")
            print(f"💡 您可以删除或重命名旧的token_config.py文件")
        
        return success
        
    except Exception as e:
        print(f"❌ Token导入失败: {e}")
        return False


def get_token_from_config() -> Optional[str]:
    """
    从旧的token_config.py获取Token（仅用于临时过渡）
    
    Returns:
        Token字符串，如果不存在则返回None
    """
    try:
        # 尝试导入旧的token_config
        import token_config as old_config
        
        token = getattr(old_config, 'TOKEN', None)
        
        if token and len(token) >= 16:
            return token
        
        return None
        
    except ImportError:
        return None
    except Exception as e:
        print(f"❌ 读取旧Token配置失败: {e}")
        return None


def migrate_to_new_system() -> bool:
    """
    迁移到新的Token管理系统
    
    Returns:
        是否迁移成功
    """
    print("🔄 开始迁移到新的Token管理系统...")
    
    # 检查是否已经配置了新系统
    token_manager = TokenManager()
    if token_manager.is_configured():
        print("✅ 新Token管理系统已配置，跳过迁移")
        return True
    
    # 尝试从旧系统导入
    old_token = get_token_from_config()
    
    if old_token:
        print("📦 检测到旧Token配置...")
        success = token_manager.save_token(old_token, "自动从旧系统迁移")
        
        if success:
            print("✅ Token迁移成功")
            print("💡 建议删除或重命名token_config.py文件")
            return True
        else:
            print("❌ Token迁移失败")
            return False
    else:
        print("⚠️  未检测到旧Token配置")
        return False


if __name__ == "__main__":
    # 测试迁移功能
    migrate_to_new_system()
