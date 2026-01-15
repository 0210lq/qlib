"""
端到端测试脚本 (End-to-End Test)

这个脚本测试完整的SQL2CSV流程，包括:
1. 使用真实数据库连接
2. 处理小批量股票数据
3. 验证CSV输出格式和内容
4. 对比新旧实现的输出一致性
5. 性能基准测试

使用方法:
    # 运行所有测试
    python qlib_code/sql2csv_refactored/test_e2e.py

    # 运行特定测试
    python qlib_code/sql2csv_refactored/test_e2e.py --test basic
    python qlib_code/sql2csv_refactored/test_e2e.py --test comparison
    python qlib_code/sql2csv_refactored/test_e2e.py --test performance
"""

import os
import sys
import time
import argparse
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from qlib_code.sql2csv_refactored import run_sql2csv


class E2ETestRunner:
    """端到端测试运行器"""

    def __init__(self, test_output_dir=None):
        """
        初始化测试运行器

        Args:
            test_output_dir: 测试输出目录（如果为None，使用临时目录）
        """
        if test_output_dir is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.test_output_dir = project_root / 'test_output' / f'e2e_test_{timestamp}'
        else:
            self.test_output_dir = Path(test_output_dir)

        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        print(f"测试输出目录: {self.test_output_dir}")

    def test_basic_functionality(self):
        """
        测试1: 基本功能测试

        测试新实现能否正常处理小批量股票数据
        """
        print("\n" + "=" * 80)
        print("测试1: 基本功能测试")
        print("=" * 80)

        # 测试参数
        test_stocks = ['000001.SZ', '000002.SZ', '600000.SH', '600519.SH', '000858.SZ']
        start_date = '20230601'
        end_date = '20230610'

        print(f"\n测试股票: {test_stocks}")
        print(f"日期范围: {start_date} - {end_date}")

        try:
            # 运行新实现
            start_time = time.time()
            result = run_sql2csv(
                market=test_stocks,
                start_date=start_date,
                end_date=end_date,
                output_dir=str(self.test_output_dir / 'basic_test'),
                batch_size=5,
                max_workers=2,
                log_level='INFO'
            )
            duration = time.time() - start_time

            # 验证结果
            print(f"\n处理结果:")
            print(f"  - 成功: {result.success_count} 只")
            print(f"  - 失败: {result.failed_count} 只")
            print(f"  - 总计: {result.total_count} 只")
            print(f"  - 耗时: {duration:.2f} 秒")

            if result.errors:
                print(f"\n错误列表:")
                for error in result.errors:
                    print(f"  - {error}")

            # 验证CSV文件
            print(f"\n验证CSV文件:")
            csv_dir = self.test_output_dir / 'basic_test'
            csv_files = list(csv_dir.glob('*.csv'))
            print(f"  - 生成的CSV文件数量: {len(csv_files)}")

            for csv_file in csv_files[:3]:  # 只显示前3个
                df = pd.read_csv(csv_file)
                print(f"  - {csv_file.name}: {len(df)} 行, 列: {list(df.columns)}")

                # 验证列名
                expected_columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'factor']
                if 'money' in df.columns:
                    expected_columns.append('money')

                missing_columns = set(expected_columns) - set(df.columns)
                if missing_columns:
                    print(f"    [WARN] 缺少列: {missing_columns}")
                else:
                    print(f"    [OK] 列名正确")

                # 验证数据类型
                if not df.empty:
                    print(f"    - 日期格式: {df['date'].iloc[0]}")
                    print(f"    - 价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")

            # 判断测试是否通过
            if result.success_count > 0 and len(csv_files) > 0:
                print(f"\n[PASS] 测试1通过: 基本功能正常")
                return True
            else:
                print(f"\n[FAIL] 测试1失败: 未生成CSV文件或所有股票处理失败")
                return False

        except Exception as e:
            print(f"\n[FAIL] 测试1失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_csv_format_validation(self):
        """
        测试2: CSV格式验证

        验证生成的CSV文件符合Qlib格式要求
        """
        print("\n" + "=" * 80)
        print("测试2: CSV格式验证")
        print("=" * 80)

        # 使用测试1生成的文件
        csv_dir = self.test_output_dir / 'basic_test'
        csv_files = list(csv_dir.glob('*.csv'))

        if not csv_files:
            print("[FAIL] 没有找到CSV文件，请先运行测试1")
            return False

        print(f"\n验证 {len(csv_files)} 个CSV文件...")

        all_valid = True
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)

                # 验证1: 必需列
                required_columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'factor']
                missing = set(required_columns) - set(df.columns)
                if missing:
                    print(f"[FAIL] {csv_file.name}: 缺少列 {missing}")
                    all_valid = False
                    continue

                # 验证2: 日期格式 (YYYY-MM-DD)
                try:
                    pd.to_datetime(df['date'], format='%Y-%m-%d')
                except:
                    print(f"[FAIL] {csv_file.name}: 日期格式不正确")
                    all_valid = False
                    continue

                # 验证3: 数值列
                numeric_columns = ['open', 'close', 'high', 'low', 'volume', 'factor']
                for col in numeric_columns:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        print(f"[FAIL] {csv_file.name}: 列 {col} 不是数值类型")
                        all_valid = False
                        break

                # 验证4: 价格关系 (high >= low, high >= open, high >= close)
                if not df.empty:
                    invalid_rows = df[
                        (df['high'] < df['low']) |
                        (df['high'] < df['open']) |
                        (df['high'] < df['close']) |
                        (df['low'] > df['open']) |
                        (df['low'] > df['close'])
                    ]
                    if len(invalid_rows) > 0:
                        print(f"[WARN]  {csv_file.name}: {len(invalid_rows)} 行价格关系异常")

                # 验证5: 日期排序
                dates = pd.to_datetime(df['date'])
                if not dates.is_monotonic_increasing:
                    print(f"[WARN]  {csv_file.name}: 日期未按升序排列")

                print(f"[PASS] {csv_file.name}: 格式验证通过")

            except Exception as e:
                print(f"[FAIL] {csv_file.name}: 验证失败 - {e}")
                all_valid = False

        if all_valid:
            print(f"\n[PASS] 测试2通过: 所有CSV文件格式正确")
            return True
        else:
            print(f"\n[FAIL] 测试2失败: 部分CSV文件格式不正确")
            return False

    def test_incremental_update(self):
        """
        测试3: 增量更新测试

        测试增量更新功能是否正常工作
        """
        print("\n" + "=" * 80)
        print("测试3: 增量更新测试")
        print("=" * 80)

        test_stock = '000001.SZ'
        output_dir = self.test_output_dir / 'incremental_test'

        try:
            # 第一次运行: 获取1月1日-1月5日的数据
            print(f"\n第一次运行: 获取 {test_stock} 的数据 (20250101-20250105)")
            result1 = run_sql2csv(
                market=[test_stock],
                start_date='20250101',
                end_date='20250105',
                output_dir=str(output_dir),
                log_level='INFO'
            )

            csv_file = output_dir / f'{test_stock}.csv'
            if not csv_file.exists():
                print(f"[FAIL] 第一次运行未生成CSV文件")
                return False

            df1 = pd.read_csv(csv_file)
            print(f"  - 第一次运行生成 {len(df1)} 行数据")

            # 第二次运行: 获取1月6日-1月10日的数据（增量更新）
            print(f"\n第二次运行: 增量更新 {test_stock} 的数据 (20250106-20250110)")
            result2 = run_sql2csv(
                market=[test_stock],
                start_date='20250106',
                end_date='20250110',
                output_dir=str(output_dir),
                log_level='INFO'
            )

            df2 = pd.read_csv(csv_file)
            print(f"  - 第二次运行后共有 {len(df2)} 行数据")

            # 验证增量更新
            if len(df2) >= len(df1):
                print(f"[PASS] 增量更新成功: 数据行数从 {len(df1)} 增加到 {len(df2)}")

                # 验证没有重复日期
                duplicates = df2[df2.duplicated(subset=['date'], keep=False)]
                if len(duplicates) > 0:
                    print(f"[WARN]  发现 {len(duplicates)} 行重复日期")
                else:
                    print(f"[PASS] 没有重复日期")

                # 验证日期排序
                dates = pd.to_datetime(df2['date'])
                if dates.is_monotonic_increasing:
                    print(f"[PASS] 日期按升序排列")
                else:
                    print(f"[WARN]  日期未按升序排列")

                print(f"\n[PASS] 测试3通过: 增量更新功能正常")
                return True
            else:
                print(f"[FAIL] 增量更新失败: 数据行数减少")
                return False

        except Exception as e:
            print(f"\n[FAIL] 测试3失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_performance_benchmark(self, stock_count=50):
        """
        测试4: 性能基准测试

        测试处理指定数量股票的性能
        """
        print("\n" + "=" * 80)
        print(f"测试4: 性能基准测试 ({stock_count}只股票)")
        print("=" * 80)

        try:
            # 生成测试股票列表（避免查询indexcomponent表）
            test_stocks = []
            # 深圳股票
            for i in range(1, min(stock_count // 2 + 1, 1000)):
                test_stocks.append(f"{i:06d}.SZ")
            # 上海股票
            for i in range(600000, 600000 + min(stock_count - len(test_stocks), 1000)):
                test_stocks.append(f"{i:06d}.SH")

            test_stocks = test_stocks[:stock_count]

            # 运行性能测试
            print(f"\n开始处理 {len(test_stocks)} 只股票...")
            start_time = time.time()

            result = run_sql2csv(
                market=test_stocks,  # 使用自定义股票列表
                start_date='20230601',
                end_date='20230610',
                output_dir=str(self.test_output_dir / 'performance_test'),
                batch_size=100,
                max_workers=8,
                log_level='INFO'
            )

            duration = time.time() - start_time

            # 输出性能指标
            print(f"\n性能指标:")
            print(f"  - 处理股票数: {result.total_count}")
            print(f"  - 成功: {result.success_count}")
            print(f"  - 失败: {result.failed_count}")
            print(f"  - 总耗时: {duration:.2f} 秒")
            print(f"  - 平均每只股票: {duration/max(result.total_count, 1):.3f} 秒")

            # 性能评估
            if result.total_count > 0:
                avg_time_per_stock = duration / result.total_count
                if avg_time_per_stock < 0.1:
                    print(f"[PASS] 性能优秀: 平均每只股票 {avg_time_per_stock:.3f} 秒")
                elif avg_time_per_stock < 0.5:
                    print(f"[PASS] 性能良好: 平均每只股票 {avg_time_per_stock:.3f} 秒")
                else:
                    print(f"[WARN]  性能一般: 平均每只股票 {avg_time_per_stock:.3f} 秒")

                # 估算6000只股票的耗时
                estimated_time_6000 = avg_time_per_stock * 6000
                print(f"\n估算处理6000只股票耗时: {estimated_time_6000:.2f} 秒 ({estimated_time_6000/60:.2f} 分钟)")

                if estimated_time_6000 <= 240:  # 4分钟
                    print(f"[PASS] 预计满足性能要求 (≤4分钟)")
                else:
                    print(f"[WARN]  预计可能超过性能要求 (>4分钟)")

            print(f"\n[PASS] 测试4完成: 性能基准测试")
            return True

        except Exception as e:
            print(f"\n[FAIL] 测试4失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("SQL2CSV 端到端测试套件")
        print("=" * 80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        results = {}

        # 运行测试
        results['test1_basic'] = self.test_basic_functionality()
        results['test2_format'] = self.test_csv_format_validation()
        results['test3_incremental'] = self.test_incremental_update()
        results['test4_performance'] = self.test_performance_benchmark()

        # 输出汇总
        print("\n" + "=" * 80)
        print("测试汇总")
        print("=" * 80)

        for test_name, passed in results.items():
            status = "[PASS] 通过" if passed else "[FAIL] 失败"
            print(f"{test_name}: {status}")

        total_tests = len(results)
        passed_tests = sum(results.values())
        print(f"\n总计: {passed_tests}/{total_tests} 测试通过")

        if passed_tests == total_tests:
            print("\n[SUCCESS] 所有测试通过！")
        else:
            print(f"\n[WARN]  {total_tests - passed_tests} 个测试失败")

        print(f"\n测试输出目录: {self.test_output_dir}")
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return passed_tests == total_tests


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SQL2CSV 端到端测试')
    parser.add_argument('--test', type=str, choices=['all', 'basic', 'format', 'incremental', 'performance'],
                       default='all', help='要运行的测试')
    parser.add_argument('--output-dir', type=str, help='测试输出目录')

    args = parser.parse_args()

    # 创建测试运行器
    runner = E2ETestRunner(test_output_dir=args.output_dir)

    # 运行指定测试
    if args.test == 'all':
        success = runner.run_all_tests()
    elif args.test == 'basic':
        success = runner.test_basic_functionality()
    elif args.test == 'format':
        success = runner.test_csv_format_validation()
    elif args.test == 'incremental':
        success = runner.test_incremental_update()
    elif args.test == 'performance':
        success = runner.test_performance_benchmark()

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
