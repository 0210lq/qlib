"""
测试数据模型功能

临时测试脚本，用于验证数据模型是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from qlib_code.sql2csv_refactored.models.data_models import (
    QueryParams, StockData, IndexData, ProcessingResult
)


def test_query_params():
    """测试 QueryParams 数据模型"""
    print("=" * 60)
    print("测试1: QueryParams 数据模型")
    print("=" * 60)

    try:
        # 测试有效参数
        params = QueryParams(
            start_date='20250101',
            end_date='20251231',
            codes=['000001.SZ', '000002.SZ'],
            market='zz500',
            batch_size=1000
        )
        print(f"[PASS] 创建 QueryParams 成功")
        print(f"  - start_date: {params.start_date}")
        print(f"  - end_date: {params.end_date}")
        print(f"  - codes: {params.codes}")
        print(f"  - market: {params.market}")
        print(f"  - batch_size: {params.batch_size}")

        # 测试 to_dict
        params_dict = params.to_dict()
        print(f"[PASS] to_dict() 方法正常工作")

        return True

    except Exception as e:
        print(f"[FAIL] QueryParams 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_params_validation():
    """测试 QueryParams 验证逻辑"""
    print("\n" + "=" * 60)
    print("测试2: QueryParams 验证逻辑")
    print("=" * 60)

    try:
        # 测试无效日期格式
        try:
            params = QueryParams(
                start_date='2025-01-01',  # 错误格式
                end_date='20251231'
            )
            print("[FAIL] 应该抛出 ValueError，但没有")
            return False
        except ValueError as e:
            print(f"[PASS] 正确捕获无效日期格式: {e}")

        # 测试日期范围错误
        try:
            params = QueryParams(
                start_date='20251231',
                end_date='20250101'  # end_date < start_date
            )
            print("[FAIL] 应该抛出 ValueError，但没有")
            return False
        except ValueError as e:
            print(f"[PASS] 正确捕获日期范围错误: {e}")

        return True

    except Exception as e:
        print(f"[FAIL] QueryParams 验证测试失败: {e}")
        return False


def test_stock_data():
    """测试 StockData 数据模型"""
    print("\n" + "=" * 60)
    print("测试3: StockData 数据模型")
    print("=" * 60)

    try:
        # 测试有效股票数据
        stock = StockData(
            code='000001.SZ',
            date='2025-01-01',
            open=10.0,
            high=10.5,
            low=9.8,
            close=10.2,
            volume=1000000,
            amount=10200000,
            factor=1.0
        )
        print(f"[PASS] 创建 StockData 成功")
        print(f"  - code: {stock.code}")
        print(f"  - date: {stock.date}")
        print(f"  - close: {stock.close}")

        # 测试 to_dict
        stock_dict = stock.to_dict()
        print(f"[PASS] to_dict() 方法正常工作")

        # 测试 to_qlib_format
        qlib_format = stock.to_qlib_format()
        print(f"[PASS] to_qlib_format() 方法正常工作")
        print(f"  - Qlib format keys: {list(qlib_format.keys())}")

        return True

    except Exception as e:
        print(f"[FAIL] StockData 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_data_validation():
    """测试 StockData 验证逻辑"""
    print("\n" + "=" * 60)
    print("测试4: StockData 验证逻辑")
    print("=" * 60)

    try:
        # 测试价格关系错误 (high < low)
        try:
            stock = StockData(
                code='000001.SZ',
                date='2025-01-01',
                open=10.0,
                high=9.5,  # high < low
                low=9.8,
                close=10.0,
                volume=1000000,
                amount=10000000
            )
            print("[FAIL] 应该抛出 ValueError，但没有")
            return False
        except ValueError as e:
            print(f"[PASS] 正确捕获价格关系错误: {e}")

        return True

    except Exception as e:
        print(f"[FAIL] StockData 验证测试失败: {e}")
        return False


def test_index_data():
    """测试 IndexData 数据模型"""
    print("\n" + "=" * 60)
    print("测试5: IndexData 数据模型")
    print("=" * 60)

    try:
        # 测试有效指数数据
        index = IndexData(
            code='000905.SH',
            date='2025-01-01',
            open=5000.0,
            high=5100.0,
            low=4950.0,
            close=5050.0,
            volume=1000000000,
            amount=50000000000,
            factor=1.0
        )
        print(f"[PASS] 创建 IndexData 成功")
        print(f"  - code: {index.code}")
        print(f"  - date: {index.date}")
        print(f"  - close: {index.close}")

        # 测试 to_qlib_format
        qlib_format = index.to_qlib_format()
        print(f"[PASS] to_qlib_format() 方法正常工作")

        return True

    except Exception as e:
        print(f"[FAIL] IndexData 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_processing_result():
    """测试 ProcessingResult 数据模型"""
    print("\n" + "=" * 60)
    print("测试6: ProcessingResult 数据模型")
    print("=" * 60)

    try:
        # 测试有效处理结果
        result = ProcessingResult(
            success=True,
            total_count=6000,
            success_count=5998,
            failed_count=2,
            duration_seconds=240.5,
            errors=[{'code': '000001.SZ', 'error': 'No data found'}]
        )
        print(f"[PASS] 创建 ProcessingResult 成功")
        print(f"  - total_count: {result.total_count}")
        print(f"  - success_count: {result.success_count}")
        print(f"  - failed_count: {result.failed_count}")
        print(f"  - duration: {result.duration_seconds}s")

        # 测试 get_success_rate
        success_rate = result.get_success_rate()
        print(f"[PASS] get_success_rate() = {success_rate:.2f}%")

        # 测试 summary
        summary = result.summary()
        print(f"[PASS] summary() = {summary}")

        return True

    except Exception as e:
        print(f"[FAIL] ProcessingResult 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_processing_result_validation():
    """测试 ProcessingResult 验证逻辑"""
    print("\n" + "=" * 60)
    print("测试7: ProcessingResult 验证逻辑")
    print("=" * 60)

    try:
        # 测试计数不一致
        try:
            result = ProcessingResult(
                success=True,
                total_count=100,
                success_count=50,
                failed_count=40,  # 50 + 40 != 100
                duration_seconds=10.0
            )
            print("[FAIL] 应该抛出 ValueError，但没有")
            return False
        except ValueError as e:
            print(f"[PASS] 正确捕获计数不一致错误: {e}")

        return True

    except Exception as e:
        print(f"[FAIL] ProcessingResult 验证测试失败: {e}")
        return False


if __name__ == '__main__':
    print("开始测试数据模型\n")

    results = []
    results.append(("QueryParams 数据模型", test_query_params()))
    results.append(("QueryParams 验证逻辑", test_query_params_validation()))
    results.append(("StockData 数据模型", test_stock_data()))
    results.append(("StockData 验证逻辑", test_stock_data_validation()))
    results.append(("IndexData 数据模型", test_index_data()))
    results.append(("ProcessingResult 数据模型", test_processing_result()))
    results.append(("ProcessingResult 验证逻辑", test_processing_result_validation()))

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n[PASS] 所有测试通过！数据模型工作正常。")
    else:
        print("\n[FAIL] 部分测试失败，需要修复。")

    sys.exit(0 if all_passed else 1)
