"""
性能分析脚本

使用cProfile分析SQL2CSV的性能瓶颈
"""

import os
import sys
import cProfile
import pstats
import io
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from qlib_code.sql2csv_refactored import run_sql2csv


def profile_small_batch():
    """分析小批量处理（10只股票）"""
    print("\n" + "=" * 80)
    print("性能分析: 小批量处理（10只股票）")
    print("=" * 80)

    test_stocks = [f"{i:06d}.SZ" for i in range(1, 6)] + [f"{600000+i:06d}.SH" for i in range(5)]

    profiler = cProfile.Profile()
    profiler.enable()

    result = run_sql2csv(
        market=test_stocks,
        start_date='20230601',
        end_date='20230610',
        output_dir=str(project_root / 'test_output' / 'profile_small'),
        batch_size=10,
        max_workers=2,
        log_level='WARNING'
    )

    profiler.disable()

    # 输出统计信息
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(30)  # 显示前30个函数

    print(f"\n处理结果: {result.success_count}/{result.total_count} 成功")
    print(f"总耗时: {result.duration_seconds:.3f} 秒")
    print("\n性能分析报告（按累计时间排序）:")
    print(s.getvalue())

    return profiler


def profile_medium_batch():
    """分析中批量处理（50只股票）"""
    print("\n" + "=" * 80)
    print("性能分析: 中批量处理（50只股票）")
    print("=" * 80)

    test_stocks = [f"{i:06d}.SZ" for i in range(1, 26)] + [f"{600000+i:06d}.SH" for i in range(25)]

    profiler = cProfile.Profile()
    profiler.enable()

    result = run_sql2csv(
        market=test_stocks,
        start_date='20230601',
        end_date='20230610',
        output_dir=str(project_root / 'test_output' / 'profile_medium'),
        batch_size=50,
        max_workers=4,
        log_level='WARNING'
    )

    profiler.disable()

    # 输出统计信息
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(30)

    print(f"\n处理结果: {result.success_count}/{result.total_count} 成功")
    print(f"总耗时: {result.duration_seconds:.3f} 秒")
    print("\n性能分析报告（按累计时间排序）:")
    print(s.getvalue())

    return profiler


def analyze_hotspots(profiler):
    """分析性能热点"""
    print("\n" + "=" * 80)
    print("性能热点分析")
    print("=" * 80)

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)

    # 按总时间排序
    print("\n[1] 按总时间排序（Top 20）:")
    ps.sort_stats('tottime')
    ps.print_stats(20)
    print(s.getvalue())

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)

    # 按调用次数排序
    print("\n[2] 按调用次数排序（Top 20）:")
    ps.sort_stats('ncalls')
    ps.print_stats(20)
    print(s.getvalue())


def generate_performance_report():
    """生成性能分析报告"""
    print("\n" + "=" * 80)
    print("SQL2CSV 性能分析报告")
    print("=" * 80)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 小批量分析
    profiler_small = profile_small_batch()

    # 中批量分析
    profiler_medium = profile_medium_batch()

    # 热点分析
    analyze_hotspots(profiler_medium)

    # 保存详细报告
    report_dir = project_root / 'test_output' / 'performance_reports'
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_dir / f'profile_report_{timestamp}.txt'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SQL2CSV 性能分析详细报告\n")
        f.write("=" * 80 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # 小批量统计
        f.write("\n" + "=" * 80 + "\n")
        f.write("小批量处理（10只股票）\n")
        f.write("=" * 80 + "\n")
        s = io.StringIO()
        ps = pstats.Stats(profiler_small, stream=s).sort_stats('cumulative')
        ps.print_stats(50)
        f.write(s.getvalue())

        # 中批量统计
        f.write("\n" + "=" * 80 + "\n")
        f.write("中批量处理（50只股票）\n")
        f.write("=" * 80 + "\n")
        s = io.StringIO()
        ps = pstats.Stats(profiler_medium, stream=s).sort_stats('cumulative')
        ps.print_stats(50)
        f.write(s.getvalue())

        # 热点分析
        f.write("\n" + "=" * 80 + "\n")
        f.write("性能热点分析（按总时间）\n")
        f.write("=" * 80 + "\n")
        s = io.StringIO()
        ps = pstats.Stats(profiler_medium, stream=s).sort_stats('tottime')
        ps.print_stats(30)
        f.write(s.getvalue())

    print(f"\n详细报告已保存到: {report_file}")
    print("\n" + "=" * 80)
    print("性能分析完成")
    print("=" * 80)


if __name__ == '__main__':
    generate_performance_report()
