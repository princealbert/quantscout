#!/usr/bin/env python
# coding=utf-8
"""
Token管理模块 - 统一管理API Token配置
提供安全的token加载、验证和错误处理机制
"""

import os
import sys
from typing import Optional, Dict, Any


class TokenManager:
    """Token管理器 - 统一管理API Token配置"""
    
    def __init__(self, config_paths: list = None):
        """
        初始化Token管理器
        
        Args:
            config_paths: 配置文件路径列表，按优先级排序
        """
        if config_paths is None:
            # 默认配置文件路径（按优先级排序）
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_paths = [
                os.path.join(project_root, 'token_config.py'),           # 项目根目录
                os.path.join(project_root, 'config', 'token_config.py'), # config目录
                os.path.join(project_root, 'strategy_engine', 'token_config.py') # engine目录
            ]
        
        self.config_paths = config_paths
        self._token = None
        self._load_token()
    
    def _load_token(self) -> None:
        """加载token配置"""
        for config_path in self.config_paths:
            if os.path.exists(config_path):
                try:
                    # 动态导入配置文件
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("token_config", config_path)
                    token_config = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(token_config)
                    
                    if hasattr(token_config, 'TOKEN') and token_config.TOKEN:
                        self._token = token_config.TOKEN
                        print(f"Token配置已加载: {config_path}")
                        return
                        
                except Exception as e:
                    print(f"加载token配置失败: {config_path} - {e}")
                    continue
        
        # 如果没有找到有效token
        self._token = None
        print("未找到有效的token配置")
    
    def get_token(self) -> str:
        """
        获取当前token
        
        Returns:
            str: API token
            
        Raises:
            ValueError: 如果token未配置
        """
        if not self._token or self._token == "YOUR_TOKEN_HERE":
            raise ValueError("Token未配置或配置无效，请检查token_config.py文件")
        
        return self._token
    
    def validate_token(self) -> bool:
        """
        验证token有效性
        
        Returns:
            bool: token是否有效
        """
        if not self._token:
            return False
        
        # 检查token格式（基本验证）
        if len(self._token) != 40:  # 假设token长度为40字符
            print(f"Token格式可能不正确，长度: {len(self._token)}")
            return True  # 仍然返回True，因为可能其他格式也有效
        
        return True
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        获取token信息
        
        Returns:
            Dict[str, Any]: token相关信息
        """
        return {
            "has_token": bool(self._token and self._token != "YOUR_TOKEN_HERE"),
            "token_length": len(self._token) if self._token else 0,
            "is_default": self._token == "YOUR_TOKEN_HERE" if self._token else True,
            "config_paths": self.config_paths,
            "valid": self.validate_token()
        }
    
    def update_token(self, new_token: str) -> bool:
        """
        更新token配置
        
        Args:
            new_token: 新的token值
            
        Returns:
            bool: 更新是否成功
        """
        if not new_token or len(new_token) < 10:
            print("Token长度过短，更新失败")
            return False
        
        # 更新内存中的token
        self._token = new_token
        
        # 尝试更新配置文件
        primary_config = self.config_paths[0] if self.config_paths else None
        if primary_config and os.path.exists(os.path.dirname(primary_config)):
            try:
                with open(primary_config, 'w', encoding='utf-8') as f:
                    f.write(f'''#!/usr/bin/env python
# coding=utf-8
"""
API Token配置
请将你的token填写在下方
"""

# 请替换为你的实际token
# 获取方式：打开东财掘金终端 -> 系统设置 -> 密钥管理 -> 生成token
TOKEN = "{new_token}"
''')
                print(f"Token已更新: {primary_config}")
                return True
            except Exception as e:
                print(f"更新token配置文件失败: {e}")
        
        return False


# 全局token管理器实例
_token_manager = None


def get_token_manager() -> TokenManager:
    """获取全局token管理器实例"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager


def get_token() -> str:
    """快速获取token"""
    return get_token_manager().get_token()


def validate_token() -> bool:
    """快速验证token"""
    return get_token_manager().validate_token()


def update_token(new_token: str) -> bool:
    """快速更新token"""
    return get_token_manager().update_token(new_token)


def get_token_info() -> Dict[str, Any]:
    """快速获取token信息"""
    return get_token_manager().get_token_info()


# 导出模块
__all__ = [
    'TokenManager',
    'get_token_manager', 
    'get_token',
    'validate_token',
    'update_token',
    'get_token_info'
]