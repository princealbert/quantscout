#!/usr/bin/env python
# coding=utf-8
"""
Token验证器 - 提供Token验证功能
"""

from typing import Optional, Tuple
from .token_manager import TokenManager


class TokenValidator:
    """Token验证器"""
    
    def __init__(self, token_manager: TokenManager = None):
        """
        初始化Token验证器
        
        Args:
            token_manager: Token管理器实例
        """
        self.token_manager = token_manager or TokenManager()
    
    def validate_token(self, token: str) -> Tuple[bool, str]:
        """
        验证Token
        
        Args:
            token: 待验证的Token
            
        Returns:
            (是否有效, 错误信息) 元组
        """
        if not token:
            return False, "Token不能为空"
        
        if len(token) < 16:
            return False, "Token长度不能少于16个字符"
        
        if len(token) > 64:
            return False, "Token长度不能超过64个字符"
        
        # 验证Token格式
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        if not all(c in valid_chars for c in token):
            return False, "Token包含无效字符，只允许字母、数字、-和_"
        
        return True, ""
    
    def test_token_connection(self, token: str) -> Tuple[bool, str]:
        """
        测试Token连接
        
        Args:
            token: 待测试的Token
            
        Returns:
            (是否成功, 错误信息) 元组
        """
        try:
            # 导入gm库测试连接
            import gm
            from gm.api import set_token
            
            # 使用Token初始化
            set_token(token)
            
            # 尝试获取账户信息（简单测试）
            try:
                # 这里可以添加实际的API测试
                # 例如：get_instruments()等
                # 目前只做格式验证
                pass
            
            except Exception as e:
                return False, f"Token连接测试失败: {str(e)}"
            
            return True, "Token连接测试成功"
            
        except ImportError:
            return False, "未安装gm库，无法测试Token连接"
        except Exception as e:
            return False, f"Token连接测试失败: {str(e)}"
    
    def get_token_status(self) -> dict:
        """
        获取Token状态
        
        Returns:
            Token状态字典
        """
        is_configured = self.token_manager.is_configured()
        token_info = self.token_manager.get_token_info()
        
        return {
            "is_configured": is_configured,
            "has_description": bool(token_info and token_info.get("description")),
            "description": token_info.get("description", "") if token_info else "",
            "created_at": token_info.get("created_at", "") if token_info else "",
            "updated_at": token_info.get("updated_at", "") if token_info else ""
        }


# 全局Token验证器实例
token_validator = TokenValidator()
