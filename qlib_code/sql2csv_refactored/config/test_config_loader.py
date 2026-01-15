"""
测试 ConfigLoader 功能

临时测试脚本，用于验证配置加载是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from qlib_code.sql2csv_refactored.config.config_loader import ConfigLoader
from qlib_code.sql2csv_refactored.exceptions import ConfigurationError


def test_basic_load():
    """测试基本的配置加载"""
    print("=" * 60)
    print("测试1: 基本配置加载")
    print("=" * 60)

    try:
        config = ConfigLoader.load()

        # 验证配置节是否存在
        print(f"[PASS] 配置加载成功")
        print(f"  - extraction.market: {config.extraction.market}")
        print(f"  - extraction.start_date: {config.extraction.start_date}")
        print(f"  - extraction.end_date: {config.extraction.end_date}")
        print(f"  - performance.batch_size: {config.performance.batch_size}")
        print(f"  - performance.max_workers: {config.performance.max_workers}")
        print(f"  - database.host: {config.database.host}")
        print(f"  - database.database: {config.database.database}")
        print(f"  - output.csv_output_dir: {config.output.csv_output_dir}")
        print(f"  - logging.level: {config.logging.level}")

        return True

    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_overrides():
    """测试配置覆盖功能"""
    print("\n" + "=" * 60)
    print("测试2: 配置覆盖")
    print("=" * 60)

    try:
        # 测试点号分隔的覆盖
        config = ConfigLoader.load(overrides={
            'extraction.market': 'zz500',
            'performance.batch_size': 500
        })

        print(f"[PASS] 配置覆盖成功")
        print(f"  - extraction.market: {config.extraction.market} (应该是 'zz500')")
        print(f"  - performance.batch_size: {config.performance.batch_size} (应该是 500)")

        # 验证覆盖是否生效
        assert config.extraction.market == 'zz500', "market 覆盖失败"
        assert config.performance.batch_size == 500, "batch_size 覆盖失败"

        print(f"[PASS] 覆盖验证通过")
        return True

    except Exception as e:
        print(f"[FAIL] 配置覆盖失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_section_access():
    """测试配置节的访问方式"""
    print("\n" + "=" * 60)
    print("测试3: 配置节访问")
    print("=" * 60)

    try:
        config = ConfigLoader.load()

        # 测试属性访问
        market = config.extraction.market
        print(f"[PASS] 属性访问: config.extraction.market = {market}")

        # 测试字典访问
        market2 = config.extraction.get('market')
        print(f"[PASS] 字典访问: config.extraction.get('market') = {market2}")

        # 测试默认值
        nonexistent = config.extraction.get('nonexistent_key', 'default_value')
        print(f"[PASS] 默认值: config.extraction.get('nonexistent_key', 'default_value') = {nonexistent}")

        assert market == market2, "属性访问和字典访问结果不一致"
        assert nonexistent == 'default_value', "默认值不正确"

        print(f"[PASS] 访问方式验证通过")
        return True

    except Exception as e:
        print(f"[FAIL] 配置节访问失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_markets_config():
    """测试市场配置"""
    print("\n" + "=" * 60)
    print("测试4: 市场配置")
    print("=" * 60)

    try:
        config = ConfigLoader.load()

        # 测试市场定义
        markets_dict = config.markets.to_dict()
        print(f"[PASS] 市场配置加载成功，共 {len(markets_dict)} 个市场")

        for market_code, market_info in markets_dict.items():
            print(f"  - {market_code}: {market_info.get('name', 'N/A')}")

        return True

    except Exception as e:
        print(f"[FAIL] 市场配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("开始测试 ConfigLoader\n")

    results = []
    results.append(("基本配置加载", test_basic_load()))
    results.append(("配置覆盖", test_overrides()))
    results.append(("配置节访问", test_section_access()))
    results.append(("市场配置", test_markets_config()))

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n[PASS] 所有测试通过！ConfigLoader 工作正常。")
    else:
        print("\n[FAIL] 部分测试失败，需要修复。")

    sys.exit(0 if all_passed else 1)
