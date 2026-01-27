# src/common/config_loader.py
import os
import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        
    def load_test_conditions(self) -> Dict[str, Any]:
        """加载测试条件配置"""
        config_file = self.config_dir / "test_conditions.yaml"
        
        if not config_file.exists():
            # 创建默认配置
            default_config = self._get_default_test_conditions()
            self.save_test_conditions(default_config)
            return default_config
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def save_test_conditions(self, config: Dict[str, Any]) -> bool:
        """保存测试条件配置"""
        config_file = self.config_dir / "test_conditions.yaml"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"保存测试条件配置失败: {e}")
            return False
    
    def _get_default_test_conditions(self) -> Dict[str, Any]:
        """获取默认测试条件配置"""
        # 返回上面定义的完整配置结构
        return { ... }  # 包含上面所有的配置内容