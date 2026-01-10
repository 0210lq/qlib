#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Qlib 数据诊断脚本

用途：
    检查 Qlib 二进制数据的完整性和可用日期范围

使用方法：
    python qlib_code/check_qlib_data.py
"""

import qlib
from qlib.data import D
import pandas as pd
from pathlib import Path
import sys


def check_data_path(provider_uri):
    """检查数据路径是否存在"""
    data_path = Path(provider_uri)

    print("=" * 60)
    print("数据路径检查")
    print("=" * 60)
    print(f"数据路径: {data_path}")

    if not data_path.exists():
        print(f"❌ 错误: 数据路径不存在")
        return False

    print(f"✅ 数据路径存在")

    # 检查关键目录
    calendars_dir = data_path / "calendars"
    instruments_dir = data_path / "instruments"
    features_dir = data_path / "features"

    print(f"\n关键目录检查:")
    print(f"  calendars: {'✅' if calendars_dir.exists() else '❌'}")
    print(f"  instruments: {'✅' if instruments_dir.exists() else '❌'}")
    print(f"  features: {'✅' if features_dir.exists() else '❌'}")

    return True


def check_calendar(region='cn'):
    """检查可用的交易日历"""
    print("\n" + "=" * 60)
    print("交易日历检查")
    print("=" * 60)

    try:
        # 获取交易日历
        calendar = D.calendar(freq='day')

        if calendar is None or len(calendar) == 0:
            print("❌ 错误: 交易日历为空")
            return None

        print(f"✅ 交易日历加载成功")
        print(f"日期数量: {len(calendar)}")
        print(f"日期范围: {calendar[0]} 到 {calendar[-1]}")

        # 显示最近的交易日
        print(f"\n最早的10个交易日:")
        for date in calendar[:10]:
            print(f"  {date}")

        print(f"\n最近的10个交易日:")
        for date in calendar[-10:]:
            print(f"  {date}")

        return calendar

    except Exception as e:
        print(f"❌ 错误: 无法获取交易日历: {e}")
        return None


def check_instruments():
    """检查可用的股票列表"""
    print("\n" + "=" * 60)
    print("股票列表检查")
    print("=" * 60)

    try:
        # 获取所有股票
        instruments = D.instruments(market='all')

        if instruments is None or len(instruments) == 0:
            print("❌ 错误: 股票列表为空")
            return None

        print(f"✅ 股票列表加载成功")
        print(f"股票数量: {len(instruments)}")

        # 显示前20只股票
        print(f"\n前20只股票:")
        for i, stock in enumerate(instruments[:20]):
            print(f"  {i+1}. {stock}")

        return instruments

    except Exception as e:
        print(f"❌ 错误: 无法获取股票列表: {e}")
        return None


def check_features(instruments, calendar, sample_size=5):
    """检查特征数据"""
    print("\n" + "=" * 60)
    print("特征数据检查")
    print("=" * 60)

    if instruments is None or calendar is None:
        print("⚠️  跳过: 需要先加载股票列表和交易日历")
        return

    # 选择几只股票进行检查
    sample_stocks = instruments[:min(sample_size, len(instruments))]

    print(f"抽样检查 {len(sample_stocks)} 只股票的数据...")

    for stock in sample_stocks:
        try:
            # 尝试加载该股票的数据
            start_date = calendar[0]
            end_date = calendar[-1]

            # 加载收盘价数据
            data = D.features(
                [stock],
                ['$close'],
                start_time=start_date,
                end_time=end_date
            )

            if data is None or data.empty:
                print(f"  {stock}: ❌ 数据为空")
            else:
                print(f"  {stock}: ✅ 数据加载成功 ({len(data)} 条记录)")
                print(f"    日期范围: {data.index.get_level_values('datetime').min()} 到 {data.index.get_level_values('datetime').max()}")

        except Exception as e:
            print(f"  {stock}: ❌ 加载失败: {e}")


def check_date_range(start_time, end_time):
    """检查指定日期范围的数据可用性"""
    print("\n" + "=" * 60)
    print("日期范围数据检查")
    print("=" * 60)

    print(f"检查日期范围: {start_time} 到 {end_time}")

    try:
        # 尝试加载该日期范围的数据
        data = D.features(
            D.instruments(market='all'),
            ['$close'],
            start_time=start_time,
            end_time=end_time
        )

        if data is None or data.empty:
            print(f"❌ 警告: 指定日期范围内没有数据")
            print(f"   请检查:")
            print(f"   1. 数据是否包含 {start_time} 到 {end_time} 的日期")
            print(f"   2. 是否需要更新数据或调整日期范围")
            return False
        else:
            print(f"✅ 数据加载成功")
            print(f"   记录数: {len(data)}")
            print(f"   股票数: {len(data.index.get_level_values('instrument').unique())}")
            print(f"   日期数: {len(data.index.get_level_values('datetime').unique())}")
            return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """主函数"""
    # 从配置文件读取数据路径
    import yaml
    import os

    config_path = os.path.join(os.path.dirname(__file__), '..', 'qlib_code', 'workflow_config_lightgbm.yaml')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 错误: 无法读取配置文件: {e}")
        sys.exit(1)

    provider_uri = config['qlib_init']['provider_uri']

    # 初始化 Qlib
    try:
        qlib.init(provider_uri=provider_uri, region='cn')
        print(f"✅ Qlib 初始化成功")
    except Exception as e:
        print(f"❌ 错误: Qlib 初始化失败: {e}")
        sys.exit(1)

    # 运行检查
    check_data_path(provider_uri)

    calendar = check_calendar()
    instruments = check_instruments()
    check_features(instruments, calendar)

    # 检查配置文件中的日期范围
    if 'data_handler_config' in config:
        start_time = config['data_handler_config'].get('start_time')
        end_time = config['data_handler_config'].get('end_time')

        if start_time and end_time:
            check_date_range(start_time, end_time)

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    print("\n建议:")
    print("1. 如果日期范围检查失败，请更新配置文件中的日期")
    print("2. 确保数据已正确下载并转换为 Qlib 格式")
    print("3. 如需更新数据，运行: python qlib_code/sql2csv.py")


if __name__ == "__main__":
    main()
