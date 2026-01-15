"""
工具函数模块

提供日期处理、输入验证和日志配置功能
"""

from .date_utils import (
    validate_date_format,
    convert_date_format,
    normalize_date,
    get_today,
    add_days,
    date_range_days,
    is_valid_date_range,
    parse_flexible_date
)

from .validators import (
    validate_stock_code,
    validate_index_code,
    validate_market_code,
    validate_positive_integer,
    validate_non_negative_number,
    validate_range,
    validate_non_empty_string,
    validate_list_not_empty,
    validate_dict_has_keys,
    sanitize_sql_identifier,
    validate_file_path
)

from .logging_config import setup_logging, get_logger

__all__ = [
    # Date utilities
    'validate_date_format',
    'convert_date_format',
    'normalize_date',
    'get_today',
    'add_days',
    'date_range_days',
    'is_valid_date_range',
    'parse_flexible_date',

    # Validators
    'validate_stock_code',
    'validate_index_code',
    'validate_market_code',
    'validate_positive_integer',
    'validate_non_negative_number',
    'validate_range',
    'validate_non_empty_string',
    'validate_list_not_empty',
    'validate_dict_has_keys',
    'sanitize_sql_identifier',
    'validate_file_path',

    # Logging
    'setup_logging',
    'get_logger',
]
