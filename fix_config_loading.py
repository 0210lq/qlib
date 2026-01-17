# -*- coding: utf-8 -*-
"""
修复配置加载问题的脚本

问题：sql2csv.yaml 中的 ${base_dir} 变量没有被正确替换
原因：load_config_with_substitution() 在加载每个文件时独立进行变量替换
解决：需要在加载 sql2csv.yaml 时传入 paths.yaml 的变量作为上下文
"""

import os
import yaml
from pathlib import Path

def load_config_with_context(config_path, context=None):
    """
    加载配置文件并使用提供的上下文进行变量替换

    Args:
        config_path: 配置文件路径
        context: 变量上下文字典

    Returns:
        替换后的配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    # 合并上下文和配置
    if context:
        merged_context = {**context, **config}
    else:
        merged_context = config

    # 进行变量替换
    config = _substitute_variables(config, merged_context)

    return config


def _substitute_variables(config, context, max_iterations=10):
    """递归替换配置中的变量引用"""
    import re

    def substitute_string(s, ctx):
        """替换字符串中的变量引用"""
        pattern = re.compile(r'\$\{([^}]+)\}')

        def replace_match(match):
            var_name = match.group(1)
            if var_name in ctx:
                value = ctx[var_name]
                if isinstance(value, str):
                    return value
                else:
                    return str(value)
            else:
                return match.group(0)

        return pattern.sub(replace_match, s)

    def substitute_once(obj, ctx):
        """单次遍历并替换变量"""
        if isinstance(obj, dict):
            return {k: substitute_once(v, ctx) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [substitute_once(item, ctx) for item in obj]
        elif isinstance(obj, str):
            return substitute_string(obj, ctx)
        else:
            return obj

    # 多次迭代以处理嵌套的变量引用
    for _ in range(max_iterations):
        config = substitute_once(config, context)

    return config


def test_fix():
    """测试修复后的配置加载"""
    project_root = Path(__file__).resolve().parent

    # 1. 加载 paths.yaml
    paths_config_path = project_root / 'config' / 'paths.yaml'
    print(f"Loading paths.yaml from: {paths_config_path}")

    with open(paths_config_path, 'r', encoding='utf-8') as f:
        paths_cfg = yaml.safe_load(f) or {}

    # 先替换 paths.yaml 自身的变量
    paths_cfg = _substitute_variables(paths_cfg, paths_cfg)
    print(f"base_dir from paths.yaml: {paths_cfg.get('base_dir')}")

    # 2. 加载 sql2csv.yaml，使用 paths.yaml 作为上下文
    sql2csv_config_path = project_root / 'config' / 'sql2csv.yaml'
    print(f"\nLoading sql2csv.yaml from: {sql2csv_config_path}")

    sql2csv_cfg = load_config_with_context(str(sql2csv_config_path), context=paths_cfg)

    # 3. 检查输出路径
    output_dir = sql2csv_cfg.get('output', {}).get('csv_output_dir')
    print(f"\nOutput directory after substitution: {output_dir}")

    # 4. 解析相对路径
    if output_dir and not Path(output_dir).is_absolute():
        # 相对于项目根目录
        output_dir_abs = (project_root / output_dir).resolve()
        print(f"Absolute path: {output_dir_abs}")
        print(f"Path exists: {output_dir_abs.exists()}")
    else:
        print(f"Path exists: {Path(output_dir).exists() if output_dir else 'N/A'}")

    return paths_cfg, sql2csv_cfg


if __name__ == '__main__':
    print("=" * 60)
    print("Testing configuration loading fix")
    print("=" * 60)

    try:
        paths_cfg, sql2csv_cfg = test_fix()
        print("\n" + "=" * 60)
        print("SUCCESS: Configuration loaded correctly")
        print("=" * 60)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
