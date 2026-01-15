"""
配置加载模块

提供配置文件的加载、合并、验证和类型转换功能
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# 添加父目录到路径，以便导入 config_utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config_utils import load_config_with_substitution, _substitute_string

from ..exceptions import ConfigurationError
from .constants import Defaults, DatabaseDefaults, TableNames, ConfigPaths


class Config:
    """
    配置对象类

    将字典配置转换为类型化的配置对象，提供属性访问
    """

    def __init__(self, config_dict: Dict[str, Any]):
        """
        初始化配置对象

        Args:
            config_dict: 配置字典
        """
        self._config = config_dict

        # 提取各个部分的配置
        self.extraction = self._get_section('extraction', {})
        self.performance = self._get_section('performance', {})
        self.database = self._get_section('database', {})
        self.schema = self._get_section('schema', {})
        self.markets = self._get_section('markets', {})
        self.output = self._get_section('output', {})
        self.logging = self._get_section('logging', {})

    def _get_section(self, section_name: str, default: Any) -> 'ConfigSection':
        """获取配置节"""
        section_data = self._config.get(section_name, default)
        return ConfigSection(section_data)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._config.copy()


class ConfigSection:
    """
    配置节对象

    支持属性访问和字典访问
    """

    def __init__(self, data: Dict[str, Any]):
        self._data = data if isinstance(data, dict) else {}

    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return self._data.get(name)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """支持字典访问: section['key']"""
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """支持字典赋值: section['key'] = value"""
        self._data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._data.copy()


class ConfigLoader:
    """
    配置加载器

    负责加载、合并和处理配置文件
    """

    @staticmethod
    def load(config_path: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None) -> Config:
        """
        加载配置

        Args:
            config_path: sql2csv.yaml 的路径（None = 使用默认路径）
            overrides: 覆盖配置的字典

        Returns:
            Config: 配置对象

        Raises:
            ConfigurationError: 配置加载或验证失败

        Example:
            config = ConfigLoader.load()
            config = ConfigLoader.load(overrides={'extraction.market': 'zz500'})
        """
        try:
            # 加载基础配置文件
            base_configs = ConfigLoader._load_base_configs(config_path)

            # 合并配置
            merged = ConfigLoader._merge_configs(base_configs)

            # 应用覆盖参数
            if overrides:
                merged = ConfigLoader._apply_overrides(merged, overrides)

            # 创建配置对象
            return Config(merged)

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    @staticmethod
    def _load_base_configs(sql2csv_config_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        加载基础配置文件

        Args:
            sql2csv_config_path: sql2csv.yaml 的路径

        Returns:
            包含所有配置文件内容的字典
        """
        # 确定项目根目录
        project_root = Path(__file__).resolve().parent.parent.parent.parent

        # 加载 paths.yaml
        paths_config_path = project_root / ConfigPaths.PATHS_CONFIG
        paths_cfg = load_config_with_substitution(str(paths_config_path))

        # 加载 db.yaml
        db_config_path = project_root / ConfigPaths.DB_CONFIG
        db_cfg = load_config_with_substitution(str(db_config_path))

        # 加载 sql2csv.yaml
        if sql2csv_config_path is None:
            sql2csv_config_path = project_root / ConfigPaths.SQL2CSV_CONFIG
        sql2csv_cfg = load_config_with_substitution(str(sql2csv_config_path))

        return {
            'paths': paths_cfg,
            'db': db_cfg,
            'sql2csv': sql2csv_cfg
        }

    @staticmethod
    def _merge_configs(configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并配置文件

        Args:
            configs: 包含所有配置的字典

        Returns:
            合并后的配置字典
        """
        paths_cfg = configs['paths']
        db_cfg = configs['db']
        sql2csv_cfg = configs['sql2csv']

        # 创建合并后的配置
        merged = {}

        # 合并 sql2csv 配置（主配置）
        merged.update(sql2csv_cfg)

        # 如果 sql2csv 中没有 output 配置，从 paths 中获取
        if 'output' not in merged:
            merged['output'] = {}
        if 'csv_output_dir' not in merged.get('output', {}):
            merged['output']['csv_output_dir'] = paths_cfg.get('csv_output_dir')
        if 'provider_uri' not in merged.get('output', {}):
            merged['output']['provider_uri'] = paths_cfg.get('provider_uri')

        return merged

    @staticmethod
    def _apply_overrides(config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用覆盖参数

        支持点号分隔的键名，如 'extraction.market'

        Args:
            config: 原始配置
            overrides: 覆盖参数

        Returns:
            应用覆盖后的配置
        """
        result = config.copy()

        for key, value in overrides.items():
            if '.' in key:
                # 处理嵌套键
                keys = key.split('.')
                current = result
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                # 直接键
                result[key] = value

        return result
