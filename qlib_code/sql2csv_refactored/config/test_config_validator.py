"""
测试 ConfigValidator 功能

临时测试脚本，用于验证配置验证是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from qlib_code.sql2csv_refactored.config.config_loader import ConfigLoader
from qlib_code.sql2csv_refactored.config.config_validator import ConfigValidator
from qlib_code.sql2csv_refactored.exceptions import ConfigurationError


def test_valid_config():
    """测试有效配置"""
    print("=" * 60)
    print("测试1: 有效配置验证")
    print("=" * 60)

    try:
        config = ConfigLoader.load()
        ConfigValidator.validate(config)
        print("[PASS] 配置验证通过")
        return True

    except ConfigurationError as e:
        print(f"[FAIL] 配置验证失败: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] 意外错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_invalid_market():
    """测试无效的市场代码"""
    print("\n" + "=" * 60)
    print("测试2: 无效市场代码")
    print("=" * 60)

    try:
        config = ConfigLoader.load(overrides={'extraction.market': 'invalid_market'})
        ConfigValidator.validate(config)
        print("[FAIL] 应该抛出 ConfigurationError，但没有")
        return False

    except ConfigurationError as e:
        print(f"[PASS] 正确捕获配置错误: {e}")
        return True
    except Exception as e:
        print(f"[FAIL] 意外错误: {e}")
        return False


def test_invalid_date():
    """测试无效的日期格式"""
    print("\n" + "=" * 60)
    print("测试3: 无效日期格式")
    print("=" * 60)

    try:
        config = ConfigLoader.load(overrides={'extraction.start_date': '2025-01-01'})
        ConfigValidator.validate(config)
        print("[FAIL] 应该抛出 ConfigurationError，但没有")
        return False

    except ConfigurationError as e:
        print(f"[PASS] 正确捕获配置错误")
        if "YYYYMMDD" in str(e):
            print("[PASS] 错误消息包含正确的格式提示")
        return True
    except Exception as e:
        print(f"[FAIL] 意外错误: {e}")
        return False


def test_invalid_batch_size():
    """测试无效的批处理大小"""
    print("\n" + "=" * 60)
    print("测试4: 无效批处理大小")
    print("=" * 60)

    try:
        config = ConfigLoader.load(overrides={'performance.batch_size': -100})
        ConfigValidator.validate(config)
        print("[FAIL] 应该抛出 ConfigurationError，但没有")
        return False

    except ConfigurationError as e:
        print(f"[PASS] 正确捕获配置错误")
        if "positive integer" in str(e):
            print("[PASS] 错误消息包含正确的提示")
        return True
    except Exception as e:
        print(f"[FAIL] 意外错误: {e}")
        return False


if __name__ == '__main__':
    print("开始测试 ConfigValidator\n")

    results = []
    results.append(("有效配置验证", test_valid_config()))
    results.append(("无效市场代码", test_invalid_market()))
    results.append(("无效日期格式", test_invalid_date()))
    results.append(("无效批处理大小", test_invalid_batch_size()))

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n[PASS] 所有测试通过！ConfigValidator 工作正常。")
    else:
        print("\n[FAIL] 部分测试失败，需要修复。")

    sys.exit(0 if all_passed else 1)
