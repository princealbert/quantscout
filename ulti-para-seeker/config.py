#!/usr/bin/env python
# coding=utf-8
"""
配置管理模块 - 包含Token管理和验证功能
"""

import os
import json
from typing import Dict, Any, Optional


class TokenManager:
    """
    Token管理器 - 负责Token的保存、读取和删除
    """
    
    def __init__(self):
        """
        初始化Token管理器
        """
        self.token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.json')
    
    def save_token(self, token: str, description: str = "") -> bool:
        """
        保存Token
        
        Args:
            token: API Token
            description: Token描述
            
        Returns:
            bool: 是否保存成功
        """
        try:
            token_data = {
                'token': token,
                'description': description,
                'created_at': self._get_current_time(),
                'updated_at': self._get_current_time()
            }
            
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存Token失败: {e}")
            return False
    
    def get_token(self) -> Optional[Dict[str, Any]]:
        """
        获取Token
        
        Returns:
            Optional[Dict[str, Any]]: Token数据
        """
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"读取Token失败: {e}")
            return None
    
    def delete_token(self) -> bool:
        """
        删除Token
        
        Returns:
            bool: 是否删除成功
        """
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
            return True
        except Exception as e:
            print(f"删除Token失败: {e}")
            return False
    
    def _get_current_time(self) -> str:
        """
        获取当前时间
        
        Returns:
            str: 当前时间字符串
        """
        from datetime import datetime
        return datetime.now().isoformat()


class TokenValidator:
    """
    Token验证器 - 负责Token的验证和测试
    """
    
    def __init__(self):
        """
        初始化Token验证器
        """
        self.token_manager = TokenManager()
    
    def get_token_status(self) -> Dict[str, Any]:
        """
        获取Token状态
        
        Returns:
            Dict[str, Any]: Token状态
        """
        token_data = self.token_manager.get_token()
        
        if token_data:
            return {
                'is_configured': True,
                'description': token_data.get('description', ''),
                'created_at': token_data.get('created_at', ''),
                'updated_at': token_data.get('updated_at', '')
            }
        else:
            return {
                'is_configured': False,
                'description': '',
                'created_at': '',
                'updated_at': ''
            }
    
    def validate_token(self, token: str) -> tuple[bool, str]:
        """
        验证Token格式
        
        Args:
            token: API Token
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        if not token:
            return False, "Token不能为空"
        
        if len(token) < 10:
            return False, "Token格式不正确"
        
        return True, "Token格式正确"
    
    def test_token_connection(self, token: str) -> tuple[bool, str]:
        """
        测试Token连接
        
        Args:
            token: API Token
            
        Returns:
            tuple[bool, str]: (是否连接成功, 消息)
        """
        # 这里只是模拟测试，实际应用中需要调用API
        try:
            # 模拟网络请求延迟
            import time
            time.sleep(0.5)
            
            # 简单验证Token格式
            if len(token) >= 10:
                return True, "Token连接测试成功"
            else:
                return False, "Token连接测试失败"
        except Exception as e:
            return False, f"测试连接失败: {e}"


def migrate_to_new_system() -> bool:
    """
    从旧系统迁移
    
    Returns:
        bool: 是否迁移成功
    """
    # 这里只是模拟迁移，实际应用中需要处理旧系统的数据
    return True


# 导出实例
token_manager = TokenManager()
token_validator = TokenValidator()
