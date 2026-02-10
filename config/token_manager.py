#!/usr/bin/env python
# coding=utf-8
"""
Token管理器 - 安全管理API Token
支持加密存储和验证
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
import base64


class TokenManager:
    """Token管理器 - 提供安全的Token存储和验证功能"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化Token管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(__file__).parent
        self.token_file = self.config_dir / "token_config.json"
        self._ensure_config_dir()
        
        # 从环境变量获取密钥，或使用固定的默认密钥
        # 优先从环境变量获取密钥
        env_key = os.environ.get('GM_ENCRYPTION_KEY')
        if env_key:
            # 确保密钥是有效的Fernet密钥格式
            try:
                self._key = base64.urlsafe_b64decode(env_key.encode())
                self._cipher_suite = Fernet(self._key)
                print("✅ 从环境变量加载加密密钥成功")
            except Exception as e:
                print(f"⚠️  环境变量密钥格式无效，使用默认密钥: {e}")
                # 使用固定的默认密钥
                self._key = b'rJI3qu21cPycjDjSovn9DPm1xbMFZh35Fb00U7Nb3PQ='
                self._cipher_suite = Fernet(self._key)
        else:
            # 使用固定的默认密钥，确保Token可以被正确解密
            self._key = b'rJI3qu21cPycjDjSovn9DPm1xbMFZh35Fb00U7Nb3PQ='
            self._cipher_suite = Fernet(self._key)
            print("⚠️  未设置环境变量GM_ENCRYPTION_KEY，使用默认密钥")
            print("💡 建议在生产环境中设置环境变量GM_ENCRYPTION_KEY以提高安全性")
        
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _hash_token(self, token: str) -> str:
        """
        对Token进行哈希处理
        
        Args:
            token: 原始Token字符串
            
        Returns:
            哈希后的Token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def save_token(self, token: str, description: str = "") -> bool:
        """
        保存Token到配置文件
        
        Args:
            token: API Token
            description: Token描述（可选）
            
        Returns:
            是否保存成功
        """
        try:
            # 验证Token格式
            if not self._validate_token_format(token):
                raise ValueError("Token格式无效，请检查Token是否正确")
            
            # 对Token进行加密
            encrypted_token = self._cipher_suite.encrypt(token.encode()).decode()
            
            # 对Token进行哈希处理（用于验证）
            token_hash = self._hash_token(token)
            
            # 准备配置数据
            config = {
                "token": encrypted_token,  # 保存加密后的token
                "token_hash": token_hash,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # 保存到文件
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Token保存成功: {self.token_file}")
            return True
            
        except Exception as e:
            print(f"❌ Token保存失败: {e}")
            return False
    
    def get_token(self) -> Optional[str]:
        """
        获取存储的原始Token
        
        Returns:
            Token字符串，如果不存在则返回None
        """
        try:
            if not self.token_file.exists():
                print(f"❌ Token配置文件不存在: {self.token_file}")
                return None
            
            with open(self.token_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            encrypted_token = config.get("token")
            if not encrypted_token:
                print(f"❌ Token配置错误: token_config.json文件中缺少token字段")
                print(f"   请重新配置Token")
                return None
            
            # 尝试使用当前密钥解密
            try:
                token = self._cipher_suite.decrypt(encrypted_token.encode()).decode()
                print(f"✅ 获取Token成功")
                return token
            except Exception as e:
                print(f"⚠️  当前密钥解密失败: {e}")
                print(f"   尝试使用备用密钥解密...")
                
                # 尝试使用旧的默认密钥解密
                old_default_key = b'rJI3qu21cPycjDjSovn9DPm1xbMFZh35Fb00U7Nb3PQ='
                old_cipher_suite = Fernet(old_default_key)
                
                try:
                    token = old_cipher_suite.decrypt(encrypted_token.encode()).decode()
                    print(f"✅ 使用备用密钥解密成功")
                    # 重新使用新密钥加密并保存Token
                    print(f"   正在使用新密钥重新加密Token...")
                    self.save_token(token, config.get("description", ""))
                    return token
                except Exception as e2:
                    print(f"❌ 备用密钥解密也失败: {e2}")
                    print(f"   请重新配置Token")
                    return None
            
        except Exception as e:
            print(f"❌ 获取Token失败: {e}")
            print(f"   请检查token_config.json文件或加密密钥是否正确")
            print(f"   配置文件路径: {self.token_file}")
            return None
    
    def load_token_hash(self) -> Optional[str]:
        """
        加载存储的Token哈希值
        
        Returns:
            Token哈希值，如果不存在则返回None
        """
        try:
            if not self.token_file.exists():
                return None
            
            with open(self.token_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("token_hash")
                
        except Exception as e:
            print(f"❌ 加载Token哈希值失败: {e}")
            return None
    
    def verify_token(self, token: str) -> bool:
        """
        验证Token是否正确
        
        Args:
            token: 待验证的Token
            
        Returns:
            Token是否正确
        """
        try:
            stored_hash = self.load_token_hash()
            if not stored_hash:
                return False
            
            input_hash = self._hash_token(token)
            return input_hash == stored_hash
            
        except Exception as e:
            print(f"❌ Token验证失败: {e}")
            return False
    
    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """
        获取Token信息（不包含实际Token）
        
        Returns:
            Token信息字典
        """
        try:
            if not self.token_file.exists():
                return None
            
            with open(self.token_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 移除敏感信息
                info = {
                    "description": config.get("description", ""),
                    "created_at": config.get("created_at", ""),
                    "updated_at": config.get("updated_at", ""),
                    "is_configured": True
                }
                return info
                
        except Exception as e:
            print(f"❌ 获取Token信息失败: {e}")
            return None
    
    def _validate_token_format(self, token: str) -> bool:
        """
        验证Token格式
        
        Args:
            token: 待验证的Token
            
        Returns:
            Token格式是否有效
        """
        # 基本验证：长度应该在16-64个字符之间
        if not token or len(token) < 16 or len(token) > 64:
            return False
        
        # Token应该只包含字母、数字和部分特殊字符
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        return all(c in valid_chars for c in token)
    
    def delete_token(self) -> bool:
        """
        删除存储的Token
        
        Returns:
            是否删除成功
        """
        try:
            if self.token_file.exists():
                os.remove(self.token_file)
                print(f"✅ Token已删除: {self.token_file}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ 删除Token失败: {e}")
            return False
    
    def is_configured(self) -> bool:
        """
        检查是否已配置Token
        
        Returns:
            是否已配置Token
        """
        if not self.token_file.exists():
            return False
        
        # 检查文件中是否包含有效的token字段
        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return bool(config.get("token"))
        except Exception:
            return False
    
    def update_token(self, new_token: str, description: str = "") -> bool:
        """
        更新Token
        
        Args:
            new_token: 新的Token
            description: Token描述
            
        Returns:
            是否更新成功
        """
        return self.save_token(new_token, description)
    
    def validate_token(self) -> bool:
        """
        验证Token配置
        
        Returns:
            Token配置是否有效
        """
        return self.is_configured()


# 全局Token管理器实例
token_manager = TokenManager()


# 便捷函数
def get_token_manager() -> TokenManager:
    """获取全局Token管理器实例"""
    return token_manager


def get_token() -> Optional[str]:
    """快速获取Token"""
    return token_manager.get_token()


def validate_token() -> bool:
    """快速验证Token"""
    return token_manager.validate_token()


def update_token(new_token: str, description: str = "") -> bool:
    """快速更新Token"""
    return token_manager.update_token(new_token, description)


def get_token_info() -> Optional[Dict[str, Any]]:
    """快速获取Token信息"""
    return token_manager.get_token_info()


def is_configured() -> bool:
    """快速检查Token是否已配置"""
    return token_manager.is_configured()


def delete_token() -> bool:
    """快速删除Token"""
    return token_manager.delete_token()


def save_token(token: str, description: str = "") -> bool:
    """快速保存Token"""
    return token_manager.save_token(token, description)


def verify_token(token: str) -> bool:
    """快速验证Token"""
    return token_manager.verify_token(token)


__all__ = [
    'TokenManager',
    'token_manager',
    'get_token_manager',
    'get_token',
    'validate_token',
    'update_token',
    'get_token_info',
    'is_configured',
    'delete_token',
    'save_token',
    'verify_token'
]
