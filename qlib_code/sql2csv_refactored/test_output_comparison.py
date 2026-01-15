"""
CSV输出一致性验证脚本

对比新旧实现的CSV输出，确保完全一致
"""

import os
import sys
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def compare_csv_files(file1: Path, file2: Path, tolerance=1e-5) -> dict:
    """
    对比两个CSV文件

    Args:
        file1: 第一个CSV文件路径
        file2: 第二个CSV文件路径
        tolerance: 浮点数比较容差

    Returns:
        dict: 对比结果
    """
    result = {
        'identical': True,
        'errors': []
    }

    try:
        # 读取CSV文件
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        # 检查行数
        if len(df1) != len(df2):
            result['identical'] = False
            result['errors'].append(f"Row count mismatch: {len(df1)} vs {len(df2)}")
            return result

        # 检查列名
        if list(df1.columns) != list(df2.columns):
            result['identical'] = False
            result['errors'].append(f"Column mismatch: {list(df1.columns)} vs {list(df2.columns)}")
            return result

        # 逐列对比
        for col in df1.columns:
            # 日期列：精确匹配
            if col == 'date':
                if not df1[col].equals(df2[col]):
                    diff_rows = df1[df1[col] != df2[col]]
                    result['identical'] = False
                    result['errors'].append(f"Date column mismatch at {len(diff_rows)} rows")

            # 数值列：允许浮点误差
            elif pd.api.types.is_numeric_dtype(df1[col]):
                # 使用numpy的allclose进行浮点比较
                if not np.allclose(df1[col], df2[col], rtol=tolerance, atol=tolerance, equal_nan=True):
                    max_diff = np.abs(df1[col] - df2[col]).max()
                    result['identical'] = False
                    result['errors'].append(f"Numeric column '{col}' mismatch, max diff: {max_diff}")

            # 其他列：精确匹配
            else:
                if not df1[col].equals(df2[col]):
                    result['identical'] = False
                    result['errors'].append(f"Column '{col}' mismatch")

        return result

    except Exception as e:
        result['identical'] = False
        result['errors'].append(f"Comparison failed: {e}")
        return result


def run_comparison_test():
    """运行输出一致性测试"""
    print("=" * 80)
    print("CSV输出一致性验证")
    print("=" * 80)

    # 测试参数
    test_stocks = ['000001.SZ', '000002.SZ', '600000.SH']
    start_date = '20230601'
    end_date = '20230610'

    # 输出目录
    original_output = project_root / 'test_output' / 'original_output'
    new_output = project_root / 'test_output' / 'new_output'

    # 清理旧输出
    if original_output.exists():
        shutil.rmtree(original_output)
    if new_output.exists():
        shutil.rmtree(new_output)

    original_output.mkdir(parents=True, exist_ok=True)
    new_output.mkdir(parents=True, exist_ok=True)

    print(f"\n测试股票: {test_stocks}")
    print(f"日期范围: {start_date} - {end_date}")
    print(f"原始输出目录: {original_output}")
    print(f"新实现输出目录: {new_output}")

    # 运行原始实现
    print("\n[1/2] 运行原始实现...")
    try:
        from qlib_code.sql2csv_original_backup import QlibDataConverter as OriginalConverter

        original_converter = OriginalConverter(output_dir=str(original_output))
        for stock in test_stocks:
            try:
                original_converter.process_stock(stock, start_date, end_date)
                print(f"  [OK] {stock}")
            except Exception as e:
                print(f"  [FAIL] {stock}: {e}")

        print("[PASS] 原始实现运行完成")

    except Exception as e:
        print(f"[FAIL] 原始实现运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 运行新实现
    print("\n[2/2] 运行新实现...")
    try:
        from qlib_code.sql2csv_refactored import run_sql2csv

        result = run_sql2csv(
            market=test_stocks,
            start_date=start_date,
            end_date=end_date,
            output_dir=str(new_output),
            log_level='INFO'
        )

        print(f"  成功: {result.success_count}/{result.total_count}")
        print("[PASS] 新实现运行完成")

    except Exception as e:
        print(f"[FAIL] 新实现运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 对比CSV文件
    print("\n[3/3] 对比CSV输出...")
    all_identical = True

    for stock in test_stocks:
        original_file = original_output / f"{stock}.csv"
        new_file = new_output / f"{stock}.csv"

        # 检查文件是否存在
        if not original_file.exists():
            print(f"  [WARN] {stock}: 原始文件不存在")
            all_identical = False
            continue

        if not new_file.exists():
            print(f"  [WARN] {stock}: 新文件不存在")
            all_identical = False
            continue

        # 对比文件
        comparison = compare_csv_files(original_file, new_file)

        if comparison['identical']:
            print(f"  [PASS] {stock}: 输出完全一致")
        else:
            print(f"  [FAIL] {stock}: 输出不一致")
            for error in comparison['errors']:
                print(f"    - {error}")
            all_identical = False

    # 输出汇总
    print("\n" + "=" * 80)
    if all_identical:
        print("[SUCCESS] 所有CSV输出完全一致！")
        print("=" * 80)
        return True
    else:
        print("[FAIL] 部分CSV输出不一致")
        print("=" * 80)
        return False


if __name__ == '__main__':
    success = run_comparison_test()
    sys.exit(0 if success else 1)
