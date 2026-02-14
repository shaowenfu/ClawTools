#!/usr/bin/env python3
"""
智能配置管理器 (Smart Config Manager)

一个强大的配置管理工具，支持多种配置格式（JSON、YAML、TOML、INI），
提供配置验证、合并、加密和版本控制功能。

功能特性：
- 多格式配置文件支持
- 配置验证和类型检查
- 配置文件合并和覆盖
- 敏感信息加密/解密
- 配置版本历史追踪
- 环境变量集成
- 配置模板生成

使用方法：
    python smart_config_manager.py --help
"""

import argparse
import json
import yaml
import toml
import configparser
import os
import sys
import hashlib
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import shutil


class ConfigManager:
    """智能配置管理器主类"""
    
    def __init__(self):
        self.supported_formats = {
            'json': self._load_json,
            'yaml': self._load_yaml,
            'yml': self._load_yaml,
            'toml': self._load_toml,
            'ini': self._load_ini
        }
        
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """加载 JSON 配置文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _load_toml(self, file_path: str) -> Dict[str, Any]:
        """加载 TOML 配置文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return toml.load(f)
            
    def _load_ini(self, file_path: str) -> Dict[str, Any]:
        """加载 INI 配置文件"""
        config = configparser.ConfigParser()
        config.read(file_path, encoding='utf-8')
        result = {}
        for section in config.sections():
            result[section] = dict(config[section])
        return result
        
    def detect_format(self, file_path: str) -> str:
        """自动检测配置文件格式"""
        ext = Path(file_path).suffix.lower().lstrip('.')
        if ext in self.supported_formats:
            return ext
        raise ValueError(f"Unsupported file format: {ext}")
        
    def load_config(self, file_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        format_type = self.detect_format(file_path)
        return self.supported_formats[format_type](file_path)
        
    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并两个配置字典（深度合并）"""
        def deep_merge(base, override):
            if isinstance(base, dict) and isinstance(override, dict):
                result = base.copy()
                for key, value in override.items():
                    if key in result:
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result
            return override
            
        return deep_merge(base_config, override_config)
        
    def validate_config(self, config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """验证配置是否符合指定的 schema"""
        # 简单的 schema 验证实现
        def validate_recursive(data, schema_item):
            if isinstance(schema_item, dict):
                if not isinstance(data, dict):
                    return False
                for key, expected_type in schema_item.items():
                    if key not in data:
                        return False
                    if isinstance(expected_type, dict):
                        if not validate_recursive(data[key], expected_type):
                            return False
                    elif isinstance(expected_type, type):
                        if not isinstance(data[key], expected_type):
                            return False
                    else:
                        # 假设是字符串类型描述
                        pass
                return True
            return True
            
        return validate_recursive(config, schema)
        
    def encrypt_sensitive_data(self, config: Dict[str, Any], keys_to_encrypt: List[str], password: str) -> Dict[str, Any]:
        """加密敏感数据"""
        def encrypt_value(value: str, pwd: str) -> str:
            # 简单的加密实现（实际应用中应使用更安全的加密方法）
            key = hashlib.sha256(pwd.encode()).digest()
            encoded = []
            for i, char in enumerate(value):
                key_char = key[i % len(key)]
                encoded_char = chr((ord(char) + key_char) % 256)
                encoded.append(encoded_char)
            return base64.b64encode(''.join(encoded).encode()).decode()
            
        def encrypt_recursive(data, pwd):
            if isinstance(data, dict):
                result = {}
                for key, value in data.items():
                    if key in keys_to_encrypt and isinstance(value, str):
                        result[key] = f"encrypted:{encrypt_value(value, pwd)}"
                    elif isinstance(value, (dict, list)):
                        result[key] = encrypt_recursive(value, pwd)
                    else:
                        result[key] = value
                return result
            elif isinstance(data, list):
                return [encrypt_recursive(item, pwd) for item in data]
            return data
            
        return encrypt_recursive(config, password)
        
    def decrypt_sensitive_data(self, config: Dict[str, Any], password: str) -> Dict[str, Any]:
        """解密敏感数据"""
        def decrypt_value(encrypted_value: str, pwd: str) -> str:
            if not encrypted_value.startswith("encrypted:"):
                return encrypted_value
            encrypted_data = encrypted_value[10:]
            decoded = base64.b64decode(encrypted_data).decode()
            key = hashlib.sha256(pwd.encode()).digest()
            decrypted = []
            for i, char in enumerate(decoded):
                key_char = key[i % len(key)]
                decrypted_char = chr((ord(char) - key_char) % 256)
                decrypted.append(decrypted_char)
            return ''.join(decrypted)
            
        def decrypt_recursive(data, pwd):
            if isinstance(data, dict):
                result = {}
                for key, value in data.items():
                    if isinstance(value, str) and value.startswith("encrypted:"):
                        result[key] = decrypt_value(value, pwd)
                    elif isinstance(value, (dict, list)):
                        result[key] = decrypt_recursive(value, pwd)
                    else:
                        result[key] = value
                return result
            elif isinstance(data, list):
                return [decrypt_recursive(item, pwd) for item in data]
            return data
            
        return decrypt_recursive(config, password)
        
    def save_config(self, config: Dict[str, Any], file_path: str, format_type: str = None):
        """保存配置到文件"""
        if format_type is None:
            format_type = self.detect_format(file_path)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            if format_type == 'json':
                json.dump(config, f, indent=2, ensure_ascii=False)
            elif format_type in ['yaml', 'yml']:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            elif format_type == 'toml':
                toml.dump(config, f)
            elif format_type == 'ini':
                config_parser = configparser.ConfigParser()
                for section, values in config.items():
                    config_parser[section] = values
                config_parser.write(f)
                
    def create_backup(self, file_path: str) -> str:
        """创建配置文件备份"""
        backup_dir = Path(file_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{Path(file_path).stem}_{timestamp}{Path(file_path).suffix}"
        shutil.copy2(file_path, backup_path)
        return str(backup_path)
        
    def integrate_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """集成环境变量"""
        def replace_env_vars(data):
            if isinstance(data, str):
                # 替换 ${VAR_NAME} 格式的环境变量
                import re
                def replace_match(match):
                    var_name = match.group(1)
                    return os.environ.get(var_name, match.group(0))
                return re.sub(r'\$\{([^}]+)\}', replace_match, data)
            elif isinstance(data, dict):
                return {k: replace_env_vars(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [replace_env_vars(item) for item in data]
            return data
            
        return replace_env_vars(config)


def main():
    parser = argparse.ArgumentParser(description="智能配置管理器")
    parser.add_argument("action", choices=["load", "merge", "validate", "encrypt", "decrypt", "backup", "env"], 
                       help="执行的操作")
    parser.add_argument("--config", "-c", required=True, help="配置文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--override", help="覆盖配置文件路径（用于 merge 操作）")
    parser.add_argument("--schema", help="验证 schema 文件路径（用于 validate 操作）")
    parser.add_argument("--keys", nargs="+", help="要加密的键名列表（用于 encrypt 操作）")
    parser.add_argument("--password", help="加密/解密密码")
    
    args = parser.parse_args()
    
    manager = ConfigManager()
    
    try:
        if args.action == "load":
            config = manager.load_config(args.config)
            output = json.dumps(config, indent=2, ensure_ascii=False)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
            else:
                print(output)
                
        elif args.action == "merge":
            if not args.override:
                print("错误: merge 操作需要 --override 参数")
                sys.exit(1)
            base_config = manager.load_config(args.config)
            override_config = manager.load_config(args.override)
            merged_config = manager.merge_configs(base_config, override_config)
            output = json.dumps(merged_config, indent=2, ensure_ascii=False)
            if args.output:
                manager.save_config(merged_config, args.output)
            else:
                print(output)
                
        elif args.action == "validate":
            if not args.schema:
                print("错误: validate 操作需要 --schema 参数")
                sys.exit(1)
            config = manager.load_config(args.config)
            with open(args.schema, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            is_valid = manager.validate_config(config, schema)
            print(f"配置验证结果: {'通过' if is_valid else '失败'}")
            if not is_valid:
                sys.exit(1)
                
        elif args.action == "encrypt":
            if not args.keys or not args.password:
                print("错误: encrypt 操作需要 --keys 和 --password 参数")
                sys.exit(1)
            config = manager.load_config(args.config)
            encrypted_config = manager.encrypt_sensitive_data(config, args.keys, args.password)
            if args.output:
                manager.save_config(encrypted_config, args.output)
            else:
                print(json.dumps(encrypted_config, indent=2, ensure_ascii=False))
                
        elif args.action == "decrypt":
            if not args.password:
                print("错误: decrypt 操作需要 --password 参数")
                sys.exit(1)
            config = manager.load_config(args.config)
            decrypted_config = manager.decrypt_sensitive_data(config, args.password)
            if args.output:
                manager.save_config(decrypted_config, args.output)
            else:
                print(json.dumps(decrypted_config, indent=2, ensure_ascii=False))
                
        elif args.action == "backup":
            backup_path = manager.create_backup(args.config)
            print(f"备份创建成功: {backup_path}")
            
        elif args.action == "env":
            config = manager.load_config(args.config)
            env_config = manager.integrate_env_vars(config)
            if args.output:
                manager.save_config(env_config, args.output)
            else:
                print(json.dumps(env_config, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()