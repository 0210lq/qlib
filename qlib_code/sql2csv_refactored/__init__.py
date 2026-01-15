"""
SQL2CSV重构模块

提供从SQL数据库提取数据并转换为Qlib格式CSV文件的完整解决方案

主要功能:
- 配置管理和验证
- 数据库连接和查询
- 数据格式转换
- CSV文件管理
- 流程编排和并发处理

使用示例:
    from qlib_code.sql2csv_refactored import run_sql2csv

    # 使用默认配置
    result = run_sql2csv()

    # 覆盖特定参数
    result = run_sql2csv(
        market='zz500',
        start_date='20250101',
        end_date='today',
        batch_size=500
    )
"""

from .main import run_sql2csv, sql2csv
from .exceptions import (
    SQL2CSVError,
    ConfigurationError,
    DatabaseError,
    DataValidationError,
    DataConversionError,
    FileOperationError
)

__version__ = '2.0.0'

__all__ = [
    # Main entry point
    'run_sql2csv',
    'sql2csv',

    # Exceptions
    'SQL2CSVError',
    'ConfigurationError',
    'DatabaseError',
    'DataValidationError',
    'DataConversionError',
    'FileOperationError',
]
