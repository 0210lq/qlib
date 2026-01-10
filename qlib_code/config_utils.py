"""
配置工具模块 - 用于加载和处理 YAML 配置文件
支持变量替换，例如 ${base_dir} 会被替换为实际的 base_dir 值
"""

import os
import re
import yaml


def load_config_with_substitution(config_path):
  
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    
    # 进行变量替换
    config = _substitute_variables(config)
    
    return config


def _substitute_variables(config, max_iterations=10):
    """
    递归替换配置中的变量引用
    
    Args:
        config: 配置字典
        max_iterations: 最大迭代次数，防止循环引用
        
    Returns:
        替换后的配置字典
    """
    # 多次迭代以处理嵌套的变量引用
    for _ in range(max_iterations):
        changed = False
        config = _substitute_once(config, config)
        
        # 检查是否还有未替换的变量
        if not _has_variables(config):
            break
            
    return config


def _substitute_once(obj, context):
    """
    单次遍历并替换变量
    
    Args:
        obj: 要处理的对象（可以是字典、列表或字符串）
        context: 包含变量值的上下文字典
        
    Returns:
        替换后的对象
    """
    if isinstance(obj, dict):
        return {k: _substitute_once(v, context) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_substitute_once(item, context) for item in obj]
    elif isinstance(obj, str):
        return _substitute_string(obj, context)
    else:
        return obj


def _substitute_string(s, context):
    """
    替换字符串中的变量引用
    
    Args:
        s: 要处理的字符串
        context: 包含变量值的上下文字典
        
    Returns:
        替换后的字符串
    """
    # 匹配 ${variable_name} 格式
    pattern = re.compile(r'\$\{([^}]+)\}')
    
    def replace_match(match):
        var_name = match.group(1)
        if var_name in context:
            value = context[var_name]
            # 如果值本身也是字符串，确保它也被替换
            if isinstance(value, str):
                return value
            else:
                return str(value)
        else:
            # 如果找不到变量，保持原样
            return match.group(0)
    
    return pattern.sub(replace_match, s)


def _has_variables(obj):
    """
    检查对象中是否还有未替换的变量
    
    Args:
        obj: 要检查的对象
        
    Returns:
        如果还有未替换的变量返回 True，否则返回 False
    """
    if isinstance(obj, dict):
        return any(_has_variables(v) for v in obj.values())
    elif isinstance(obj, list):
        return any(_has_variables(item) for item in obj)
    elif isinstance(obj, str):
        return '${' in obj
    else:
        return False


def load_paths_config():
    """
    加载 paths.yaml 配置文件（便捷函数）
    
    Returns:
        处理后的配置字典
    """
    cfg_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'config', 'paths.yaml'
    ))
    return load_config_with_substitution(cfg_path)
