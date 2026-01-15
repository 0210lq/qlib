"""
集成测试脚本

测试SQL2CSV重构模块的完整流程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from qlib_code.sql2csv_refactored.config.config_loader import ConfigLoader
from qlib_code.sql2csv_refactored.config.config_validator import ConfigValidator
from qlib_code.sql2csv_refactored.core.database import DatabaseConnection
from qlib_code.sql2csv_refactored.core.query_builder import QueryBuilder
from qlib_code.sql2csv_refactored.core.converter import DataConverter
from qlib_code.sql2csv_refactored.core.file_manager import CSVFileManager
from qlib_code.sql2csv_refactored.utils.logging_config import setup_logging


def test_config_loading():
    """测试1: 配置加载"""
    print("=" * 60)
    print("测试1: 配置加载")
    print("=" * 60)

    try:
        config_path = project_root / 'config' / 'sql2csv.yaml'
        config = ConfigLoader.load(str(config_path))

        print(f"[PASS] 配置加载成功")
        print(f"  - Market: {config.extraction.get('market')}")
        print(f"  - Start date: {config.extraction.get('start_date')}")
        print(f"  - Batch size: {config.performance.get('batch_size')}")

        return True

    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """测试2: 配置验证"""
    print("\n" + "=" * 60)
    print("测试2: 配置验证")
    print("=" * 60)

    try:
        config_path = project_root / 'config' / 'sql2csv.yaml'
        config = ConfigLoader.load(str(config_path))

        # 验证配置
        ConfigValidator.validate(config)

        print(f"[PASS] 配置验证通过")
        return True

    except Exception as e:
        print(f"[FAIL] 配置验证失败: {e}")
        return False


def test_database_connection():
    """测试3: 数据库连接"""
    print("\n" + "=" * 60)
    print("测试3: 数据库连接")
    print("=" * 60)

    try:
        config_path = project_root / 'config' / 'sql2csv.yaml'
        config = ConfigLoader.load(str(config_path))

        # 创建数据库连接
        db = DatabaseConnection(config.database)

        # 测试简单查询
        with db.get_connection() as conn:
            from sqlalchemy import text
            result = db.execute_query(conn, text("SELECT 1 as test"))

        print(f"[PASS] 数据库连接成功")
        print(f"  - Test query result: {result}")

        db.close()
        return True

    except Exception as e:
        print(f"[FAIL] 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_builder():
    """测试4: SQL查询构建"""
    print("\n" + "=" * 60)
    print("测试4: SQL查询构建")
    print("=" * 60)

    try:
        config_path = project_root / 'config' / 'sql2csv.yaml'
        config = ConfigLoader.load(str(config_path))

        # 创建查询构建器
        builder = QueryBuilder(config.schema)

        # 构建股票查询
        query, params = builder.build_stock_query(
            ['000001.SZ', '000002.SZ'],
            '20250101',
            '20250110'
        )

        print(f"[PASS] 查询构建成功")
        print(f"  - Query type: {type(query)}")
        print(f"  - Params: {params}")

        return True

    except Exception as e:
        print(f"[FAIL] 查询构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_converter():
    """测试5: 数据格式转换"""
    print("\n" + "=" * 60)
    print("测试5: 数据格式转换")
    print("=" * 60)

    try:
        config_path = project_root / 'config' / 'sql2csv.yaml'
        config = ConfigLoader.load(str(config_path))

        # 创建数据转换器
        converter = DataConverter(config.output)

        # 模拟数据库记录
        mock_rows = [
            {
                'date': '20250101',
                'code': '000001.SZ',
                'open': 10.0,
                'high': 10.5,
                'low': 9.8,
                'close': 10.2,
                'volume': 1000000,
                'amount': 10200000,
                'factor': 1.0
            },
            {
                'date': '20250102',
                'code': '000001.SZ',
                'open': 10.2,
                'high': 10.8,
                'low': 10.0,
                'close': 10.5,
                'volume': 1200000,
                'amount': 12600000,
                'factor': 1.0
            }
        ]

        # 转换为DataFrame
        df = converter.convert_to_dataframe(mock_rows, 'stock')

        print(f"[PASS] 数据转换成功")
        print(f"  - DataFrame shape: {df.shape}")
        print(f"  - Columns: {list(df.columns)}")

        return True

    except Exception as e:
        print(f"[FAIL] 数据转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_csv_file_manager():
    """测试6: CSV文件管理"""
    print("\n" + "=" * 60)
    print("测试6: CSV文件管理")
    print("=" * 60)

    try:
        import pandas as pd
        import tempfile

        # 使用临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建文件管理器
            file_manager = CSVFileManager(temp_dir)

            # 创建测试数据
            test_data = pd.DataFrame({
                'date': ['2025-01-01', '2025-01-02'],
                'open': [10.0, 10.2],
                'close': [10.2, 10.5],
                'high': [10.5, 10.8],
                'low': [9.8, 10.0],
                'volume': [1000000, 1200000],
                'factor': [1.0, 1.0],
                'money': [10200000, 12600000]
            })

            # 写入CSV
            file_manager.write_csv('000001.SZ', test_data)

            # 读取CSV
            read_data = file_manager.read_csv('000001.SZ')

            print(f"[PASS] CSV文件管理成功")
            print(f"  - Written rows: {len(test_data)}")
            print(f"  - Read rows: {len(read_data)}")

            return True

    except Exception as e:
        print(f"[FAIL] CSV文件管理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logging_setup():
    """测试7: 日志系统设置"""
    print("\n" + "=" * 60)
    print("测试7: 日志系统设置")
    print("=" * 60)

    try:
        config_path = project_root / 'config' / 'sql2csv.yaml'
        config = ConfigLoader.load(str(config_path))

        # 设置日志
        logger = setup_logging(config.logging)

        # 测试日志输出
        logger.debug("Debug message test")
        logger.info("Info message test")

        print(f"[PASS] 日志系统设置成功")
        return True

    except Exception as e:
        print(f"[FAIL] 日志系统设置失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n开始SQL2CSV重构模块集成测试\n")

    # 运行所有测试
    results = []
    results.append(("配置加载", test_config_loading()))
    results.append(("配置验证", test_config_validation()))
    results.append(("数据库连接", test_database_connection()))
    results.append(("SQL查询构建", test_query_builder()))
    results.append(("数据格式转换", test_data_converter()))
    results.append(("CSV文件管理", test_csv_file_manager()))
    results.append(("日志系统设置", test_logging_setup()))

    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n[PASS] 所有集成测试通过！")
        print("重构模块的核心组件工作正常。")
    else:
        print("\n[FAIL] 部分测试失败，需要修复。")

    sys.exit(0 if all_passed else 1)
