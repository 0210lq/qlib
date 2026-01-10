#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置文件初始化脚本

用途：
    自动从示例配置文件创建实际配置文件，并帮助用户设置路径

使用方法：
    python setup_config.py
"""

import os
import sys
import shutil
from pathlib import Path


def setup_config():
    """设置配置文件"""

    project_root = Path(__file__).parent
    config_dir = project_root / "config"
    matlab_config_dir = project_root / "Optimizer_matlab" / "config"

    # 配置文件映射
    config_files = [
        (config_dir / "db.example.yaml", config_dir / "db.yaml"),
        (config_dir / "paths.example.yaml", config_dir / "paths.yaml"),
        (matlab_config_dir / "config_db.example.m", matlab_config_dir / "config_db.m"),
    ]

    print("=" * 60)
    print("Qlib Optimizer - 配置文件初始化")
    print("=" * 60)
    print()

    for example_file, target_file in config_files:
        if not example_file.exists():
            print(f"⚠️  警告: 示例文件不存在: {example_file}")
            continue

        if target_file.exists():
            print(f"ℹ️  配置文件已存在: {target_file}")
            response = input("   是否覆盖? (y/N): ").strip().lower()
            if response != 'y':
                print("   跳过")
                continue

        # 复制文件
        shutil.copy2(example_file, target_file)
        print(f"✅ 已创建: {target_file}")

    print()
    print("=" * 60)
    print("下一步操作：")
    print("=" * 60)
    print()
    print("1. 编辑 config/db.yaml，填入 MySQL 数据库连接信息")
    print("2. 编辑 config/paths.yaml，配置数据存储路径")
    print("   推荐使用相对路径，例如：")
    print("   - base_dir: \"../qlib_data\"")
    print("   - qlib_workdir: \"../qlib\"")
    print("   - python_exe: \"python\"")
    print()
    print("3. 编辑 Optimizer_matlab/config/config_db.m（如果使用 MATLAB）")
    print()
    print("详细配置说明请查看 README.md 文件")
    print()


if __name__ == "__main__":
    try:
        setup_config()
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)
