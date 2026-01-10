#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
同步 provider_uri 配置脚本

功能：
    从 config/paths.yaml 读取 provider_uri 配置，
    自动更新到 workflow_config_lightgbm.yaml 的 qlib_init 部分

用途：
    当修改 paths.yaml 中的数据路径后，运行此脚本同步到 workflow 配置文件

使用方法：
    python qlib_code/sync_provider_uri.py
"""

import os
import re
import sys


def sync_provider_uri():
    """从 paths.yaml 同步 provider_uri 到 workflow config"""

    # 获取项目根目录
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # 配置文件路径
    paths_config = os.path.join(project_root, 'config', 'paths.yaml')
    workflow_config = os.path.join(project_root, 'qlib_code', 'workflow_config_lightgbm.yaml')

    # 检查文件是否存在
    if not os.path.exists(paths_config):
        print(f"❌ 错误: 配置文件不存在: {paths_config}")
        print("   请先复制 config/paths.example.yaml 为 config/paths.yaml")
        return False

    if not os.path.exists(workflow_config):
        print(f"❌ 错误: Workflow 配置文件不存在: {workflow_config}")
        return False

    # 读取 paths.yaml 中的 provider_uri
    print(f"📖 读取配置: {paths_config}")
    try:
        from config_utils import load_config_with_substitution
        cfg = load_config_with_substitution(paths_config)
        provider_uri = cfg.get('provider_uri')

        if not provider_uri:
            print("⚠️  警告: paths.yaml 中未找到 provider_uri 配置")
            return False

        print(f"✅ 读取到 provider_uri: {provider_uri}")

    except Exception as e:
        print(f"❌ 读取配置失败: {e}")
        return False

    # 读取 workflow config
    print(f"\n📖 读取 Workflow 配置: {workflow_config}")
    with open(workflow_config, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找当前的 provider_uri
    current_match = re.search(r'provider_uri:\s*["\']?([^"\'\n]+)["\']?', content)
    if current_match:
        current_uri = current_match.group(1)
        print(f"📍 当前 provider_uri: {current_uri}")
    else:
        print("⚠️  未找到当前的 provider_uri")
        current_uri = None

    # 如果相同则跳过
    if current_uri == provider_uri:
        print(f"\n✅ provider_uri 已是最新，无需更新")
        return True

    # 更新 provider_uri
    print(f"\n🔄 更新 provider_uri...")
    provider_pattern = r'(qlib_init:(?:\s*\n(?:[ \t]*[^\n]*\n)*?\s*)provider_uri:\s*["\']?)([^"\'\n]+)(["\']?)'

    if re.search(provider_pattern, content):
        # 保留原有的引号风格
        updated_content = re.sub(
            provider_pattern,
            rf'\g<1>{provider_uri}\g<3>',
            content
        )

        # 写回文件
        with open(workflow_config, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"✅ 成功更新 provider_uri")
        print(f"   从: {current_uri}")
        print(f"   到: {provider_uri}")
        return True

    else:
        print("❌ 错误: 未找到 qlib_init.provider_uri 配置项")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Provider URI 同步工具")
    print("=" * 60)
    print()

    success = sync_provider_uri()

    print()
    print("=" * 60)
    if success:
        print("✅ 同步完成")
    else:
        print("❌ 同步失败")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
