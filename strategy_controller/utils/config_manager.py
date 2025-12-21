#!/usr/bin/env python
# coding=utf-8
"""
配置管理器 - 负责权重配置的保存、加载、删除等操作
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "web/configs"):
        """初始化配置管理器"""
        # 确保使用绝对路径
        self.config_dir = Path(__file__).parent.parent.parent / config_dir
        self.config_file = self.config_dir / "weight_configs.json"
        print(f"📁 [CONFIG_MANAGER] 配置文件绝对路径: {self.config_file}")
        self._ensure_config_dir()
        self._ensure_default_config()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _ensure_default_config(self):
        """确保默认配置存在"""
        if not self.config_file.exists():
            default_config = self._create_default_config()
            self._save_configs(default_config)
    
    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认配置"""
        return {
            "default": {
                "id": "default",
                "name": "默认配置",
                "description": "系统默认权重配置",
                "weights": {
                    "kdj_j": 25,
                    "trend": 25,
                    "deepv": 10,
                    "volume": 8,
                    "fundamental": 8,
                    "position": 4,
                    "risk_reward": 20
                },
                "sub_weights": {},
                "created_at": datetime.now().isoformat(),
                "is_default": True
            }
        }
    
    def _load_configs(self) -> Dict[str, Any]:
        """加载所有配置"""
        print(f"📁 [CONFIG_MANAGER] 配置文件路径: {self.config_file}")
        print(f"📁 [CONFIG_MANAGER] 配置文件存在: {self.config_file.exists()}")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
                print(f"📊 [CONFIG_MANAGER] 成功加载配置，配置数量: {len(configs)}")
                print(f"🔍 [CONFIG_MANAGER] 配置ID列表: {list(configs.keys())}")
                return configs
        except FileNotFoundError:
            print("❌ [CONFIG_MANAGER] 配置文件不存在，创建默认配置")
            return self._create_default_config()
        except json.JSONDecodeError as e:
            print(f"❌ [CONFIG_MANAGER] JSON解析错误: {str(e)}")
            print("🔄 [CONFIG_MANAGER] 创建默认配置")
            return self._create_default_config()
        except Exception as e:
            print(f"❌ [CONFIG_MANAGER] 加载配置异常: {str(e)}")
            import traceback
            print(f"🔍 [CONFIG_MANAGER] 异常详情: {traceback.format_exc()}")
            return self._create_default_config()
    
    def _save_configs(self, configs: Dict[str, Any]):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, ensure_ascii=False, indent=2)
            print(f"💾 [CONFIG_MANAGER] 配置保存成功到: {self.config_file}")
            print(f"📊 [CONFIG_MANAGER] 保存的配置数量: {len(configs)}")
        except IOError as e:
            print(f"❌ [CONFIG_MANAGER] 配置保存失败: {str(e)}")
            import traceback
            print(f"🔍 [CONFIG_MANAGER] 异常详情: {traceback.format_exc()}")
            raise
        except Exception as e:
            print(f"❌ [CONFIG_MANAGER] 配置保存失败（未知错误）: {str(e)}")
            import traceback
            print(f"🔍 [CONFIG_MANAGER] 异常详情: {traceback.format_exc()}")
            raise
    
    def get_all_configs(self) -> List[Dict[str, Any]]:
        """获取所有配置列表"""
        configs = self._load_configs()
        return [
            {**config_data, "config_id": config_id}
            for config_id, config_data in configs.items()
        ]
    
    def get_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取配置"""
        configs = self._load_configs()
        if config_id in configs:
            config_data = configs[config_id]
            # 确保配置数据包含必要的字段
            if "id" not in config_data:
                config_data["id"] = config_id
            return {**config_data, "config_id": config_id}
        return None
    
    def save_config(self, name: str, weights: Dict[str, int], 
                   sub_weights: Dict[str, Any] = None, 
                   description: str = "", 
                   config_id: str = None) -> str:
        """保存配置"""
        print(f"🔍 [SAVE_CONFIG] 开始保存配置，名称: {name}")
        print(f"🔍 [SAVE_CONFIG] 描述: {description}")
        print(f"🔍 [SAVE_CONFIG] 权重: {weights}")
        
        configs = self._load_configs()
        print(f"🔍 [SAVE_CONFIG] 当前配置数量: {len(configs)}")
        
        # 生成配置ID
        if not config_id:
            config_id = str(uuid.uuid4())
            print(f"🔍 [SAVE_CONFIG] 生成新配置ID: {config_id}")
        else:
            print(f"🔍 [SAVE_CONFIG] 使用指定配置ID: {config_id}")
        
        # 创建配置数据
        config_data = {
            "id": config_id,
            "name": name,
            "description": description,
            "weights": weights,
            "sub_weights": sub_weights or {},
            "created_at": datetime.now().isoformat(),
            "is_default": False
        }
        
        print(f"🔍 [SAVE_CONFIG] 配置数据准备完成")
        
        # 保存配置
        configs[config_id] = config_data
        print(f"🔍 [SAVE_CONFIG] 配置已添加到内存，准备保存到文件")
        
        self._save_configs(configs)
        print(f"✅ [SAVE_CONFIG] 配置保存到文件完成")
        
        # 验证保存结果
        saved_configs = self._load_configs()
        if config_id in saved_configs:
            print(f"✅ [SAVE_CONFIG] 配置保存验证成功，新配置数量: {len(saved_configs)}")
        else:
            print(f"❌ [SAVE_CONFIG] 配置保存验证失败，配置不存在: {config_id}")
            
        return config_id
    
    def update_config(self, config_id: str, name: str = None, weights: Dict[str, int] = None,
                     sub_weights: Dict[str, Any] = None, description: str = None):
        """更新配置"""
        configs = self._load_configs()
        
        if config_id not in configs:
            raise ValueError(f"配置不存在: {config_id}")
        
        # 更新配置数据
        config_data = configs[config_id]
        if name is not None:
            config_data["name"] = name
        if weights is not None:
            config_data["weights"] = weights
        if sub_weights is not None:
            config_data["sub_weights"] = sub_weights
        if description is not None:
            config_data["description"] = description
        
        config_data["updated_at"] = datetime.now().isoformat()
        
        self._save_configs(configs)
    
    def delete_config(self, config_id: str) -> bool:
        """删除配置"""
        print(f"🔍 [CONFIG_MANAGER] 开始删除配置: {config_id}")
        
        configs = self._load_configs()
        print(f"📊 [CONFIG_MANAGER] 当前配置总数: {len(configs)}")
        print(f"🔍 [CONFIG_MANAGER] 当前配置ID列表: {list(configs.keys())}")
        
        # 不能删除默认配置
        if config_id == "default":
            print(f"❌ [CONFIG_MANAGER] 不允许删除默认配置: {config_id}")
            return False
        
        if config_id in configs:
            config_name = configs[config_id].get('name', '未知配置')
            print(f"🗑️ [CONFIG_MANAGER] 正在删除配置: {config_id} - {config_name}")
            
            # 删除配置
            del configs[config_id]
            print(f"🗑️ [CONFIG_MANAGER] 配置已从内存中删除")
            
            # 保存到文件
            self._save_configs(configs)
            print(f"💾 [CONFIG_MANAGER] 配置已保存到文件")
            
            # 验证删除结果
            updated_configs = self._load_configs()
            if config_id not in updated_configs:
                print(f"✅ [CONFIG_MANAGER] 配置删除成功: {config_id} - {config_name}")
                print(f"📊 [CONFIG_MANAGER] 删除后配置总数: {len(updated_configs)}")
                return True
            else:
                print(f"❌ [CONFIG_MANAGER] 配置删除失败，配置仍存在: {config_id}")
                return False
        
        print(f"❌ [CONFIG_MANAGER] 配置不存在: {config_id}")
        return False
    
    def duplicate_config(self, config_id: str, new_name: str, new_description: str = None) -> str:
        """复制配置"""
        print(f"🔍 [DUPLICATE_CONFIG] 开始复制配置，原配置ID: {config_id}")
        print(f"🔍 [DUPLICATE_CONFIG] 新名称: {new_name}")
        print(f"🔍 [DUPLICATE_CONFIG] 新描述参数: {new_description}")
        
        # 验证输入参数
        if not new_name or not new_name.strip():
            print(f"❌ [DUPLICATE_CONFIG] 新配置名称不能为空")
            raise ValueError("新配置名称不能为空")
        
        config = self.get_config(config_id)
        if not config:
            print(f"❌ [DUPLICATE_CONFIG] 配置不存在: {config_id}")
            raise ValueError(f"配置不存在: {config_id}")
        
        print(f"✅ [DUPLICATE_CONFIG] 找到原配置: {config['name']}")
        
        # 创建新配置
        # 如果新描述为空或None，使用默认描述
        if not new_description or new_description.strip() == "":
            description = f"复制自: {config['name']}"
            print(f"🔍 [DUPLICATE_CONFIG] 使用默认描述: {description}")
        else:
            description = new_description.strip()
            print(f"🔍 [DUPLICATE_CONFIG] 使用自定义描述: {description}")
        
        print(f"🔍 [DUPLICATE_CONFIG] 调用save_config方法...")
        
        # 确保权重数据是有效的字典
        weights = config.get("weights", {})
        sub_weights = config.get("sub_weights", {})
        
        if not isinstance(weights, dict):
            print(f"⚠️ [DUPLICATE_CONFIG] 权重数据不是字典，使用空字典")
            weights = {}
        
        if not isinstance(sub_weights, dict):
            print(f"⚠️ [DUPLICATE_CONFIG] 子权重数据不是字典，使用空字典")
            sub_weights = {}
        
        new_config_id = self.save_config(
            name=new_name.strip(),
            weights=weights,
            sub_weights=sub_weights,
            description=description
        )
        
        print(f"✅ [DUPLICATE_CONFIG] 复制成功，新配置ID: {new_config_id}")
        
        # 验证新配置是否存在
        new_config = self.get_config(new_config_id)
        if new_config:
            print(f"✅ [DUPLICATE_CONFIG] 新配置验证成功: {new_config['name']}")
            # 验证新配置的权重数据
            if new_config.get('weights'):
                print(f"📊 [DUPLICATE_CONFIG] 新配置权重: {new_config['weights']}")
            else:
                print(f"⚠️ [DUPLICATE_CONFIG] 新配置权重为空")
        else:
            print(f"❌ [DUPLICATE_CONFIG] 新配置验证失败，配置不存在: {new_config_id}")
            raise ValueError("新配置创建失败")
            
        return new_config_id


# 全局配置管理器实例
config_manager = ConfigManager()