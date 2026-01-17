"""
测试指数数据处理修复
"""
import os
import sys
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qlib_code.sql2csv_refactored import run_sql2csv

def test_index_processing():
    """
    测试指数数据是否能正常处理和写入
    """
    print("=" * 60)
    print("测试指数数据处理修复")
    print("=" * 60)

    # 运行 SQL2CSV，只处理最近几天的数据以加快测试
    print("\n开始处理数据...")
    result = run_sql2csv(
        market='ALL',
        start_date='20260101',
        end_date='20260115'
    )

    print("\n" + "=" * 60)
    print("检查指数CSV文件是否生成")
    print("=" * 60)

    # 检查指数CSV文件是否存在
    csv_output_dir = Path("../qlib_data/csv_data")
    if not csv_output_dir.exists():
        # 尝试备选路径
        csv_output_dir = Path("${base_dir}/csv_data")

    expected_indices = [
        "000905.SH",  # 中证500
        "000300.SH",  # 沪深300
        "000016.SH",  # 上证50
        "000852.SH",  # 中证1000
        "932000.CSI"  # 中证2000
    ]

    found_indices = []
    missing_indices = []

    for index_code in expected_indices:
        csv_file = csv_output_dir / f"{index_code}.csv"
        if csv_file.exists():
            # 检查文件大小
            file_size = csv_file.stat().st_size
            # 读取行数
            with open(csv_file, 'r', encoding='utf-8') as f:
                line_count = len(f.readlines())

            print(f"✓ {index_code}: 文件存在 ({file_size} bytes, {line_count} 行)")
            found_indices.append(index_code)
        else:
            print(f"✗ {index_code}: 文件不存在")
            missing_indices.append(index_code)

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"预期指数数量: {len(expected_indices)}")
    print(f"成功生成: {len(found_indices)}")
    print(f"缺失: {len(missing_indices)}")

    if missing_indices:
        print(f"\n缺失的指数: {', '.join(missing_indices)}")

    if len(found_indices) == len(expected_indices):
        print("\n✓ 所有指数数据都已成功写入!")
        return True
    else:
        print(f"\n✗ 还有 {len(missing_indices)} 个指数数据未写入")
        return False

if __name__ == "__main__":
    try:
        success = test_index_processing()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
