"""
输入验证工具模块

提供各种输入数据的验证功能
"""

import re
from typing import Any, List, Optional

from ..exceptions import DataValidationError


def validate_stock_code(code: str) -> bool:
    """
    验证股票代码格式

    支持格式：
    - 6位数字.SZ (深圳)
    - 6位数字.SH (上海)

    Args:
        code: 股票代码

    Returns:
        bool: 格式是否有效

    Example:
        >>> validate_stock_code('000001.SZ')
        True
        >>> validate_stock_code('600000.SH')
        True
        >>> validate_stock_code('invalid')
        False
    """
    if not isinstance(code, str):
        return False

    # 匹配 6位数字.SZ 或 6位数字.SH
    pattern = r'^\d{6}\.(SZ|SH)$'
    return bool(re.match(pattern, code))


def validate_index_code(code: str) -> bool:
    """
    验证指数代码格式

    支持格式：
    - 6位数字.SH (上海指数)
    - 6位数字.SZ (深圳指数)

    Args:
        code: 指数代码

    Returns:
        bool: 格式是否有效

    Example:
        >>> validate_index_code('000905.SH')
        True
        >>> validate_index_code('399006.SZ')
        True
    """
    # 指数代码格式与股票代码相同
    return validate_stock_code(code)


def validate_market_code(market: str, valid_markets: List[str]) -> bool:
    """
    验证市场代码

    Args:
        market: 市场代码
        valid_markets: 有效市场代码列表

    Returns:
        bool: 市场代码是否有效

    Example:
        >>> validate_market_code('zz500', ['ALL', 'zz500', 'hs300'])
        True
        >>> validate_market_code('invalid', ['ALL', 'zz500'])
        False
    """
    return market in valid_markets


def validate_positive_integer(value: Any, name: str = "value") -> None:
    """
    验证正整数

    Args:
        value: 要验证的值
        name: 参数名称（用于错误消息）

    Raises:
        DataValidationError: 值不是正整数

    Example:
        >>> validate_positive_integer(100, "batch_size")
        >>> validate_positive_integer(-1, "batch_size")
        DataValidationError: batch_size must be a positive integer, got: -1
    """
    if not isinstance(value, int) or value <= 0:
        raise DataValidationError(
            f"{name} must be a positive integer, got: {value}"
        )


def validate_non_negative_number(value: Any, name: str = "value") -> None:
    """
    验证非负数

    Args:
        value: 要验证的值
        name: 参数名称

    Raises:
        DataValidationError: 值不是非负数

    Example:
        >>> validate_non_negative_number(0.5, "delay")
        >>> validate_non_negative_number(-1, "delay")
        DataValidationError: delay must be non-negative, got: -1
    """
    if not isinstance(value, (int, float)) or value < 0:
        raise DataValidationError(
            f"{name} must be non-negative, got: {value}"
        )


def validate_range(value: Any, min_val: float, max_val: float, name: str = "value") -> None:
    """
    验证数值范围

    Args:
        value: 要验证的值
        min_val: 最小值（包含）
        max_val: 最大值（包含）
        name: 参数名称

    Raises:
        DataValidationError: 值不在范围内

    Example:
        >>> validate_range(50, 0, 100, "percentage")
        >>> validate_range(150, 0, 100, "percentage")
        DataValidationError: percentage must be between 0 and 100, got: 150
    """
    if not isinstance(value, (int, float)):
        raise DataValidationError(
            f"{name} must be a number, got: {type(value).__name__}"
        )

    if not (min_val <= value <= max_val):
        raise DataValidationError(
            f"{name} must be between {min_val} and {max_val}, got: {value}"
        )


def validate_non_empty_string(value: Any, name: str = "value") -> None:
    """
    验证非空字符串

    Args:
        value: 要验证的值
        name: 参数名称

    Raises:
        DataValidationError: 值不是非空字符串

    Example:
        >>> validate_non_empty_string("hello", "name")
        >>> validate_non_empty_string("", "name")
        DataValidationError: name must be a non-empty string
    """
    if not isinstance(value, str) or not value.strip():
        raise DataValidationError(
            f"{name} must be a non-empty string"
        )


def validate_list_not_empty(value: Any, name: str = "value") -> None:
    """
    验证非空列表

    Args:
        value: 要验证的值
        name: 参数名称

    Raises:
        DataValidationError: 值不是非空列表

    Example:
        >>> validate_list_not_empty([1, 2, 3], "codes")
        >>> validate_list_not_empty([], "codes")
        DataValidationError: codes must be a non-empty list
    """
    if not isinstance(value, list) or len(value) == 0:
        raise DataValidationError(
            f"{name} must be a non-empty list"
        )


def validate_dict_has_keys(value: Any, required_keys: List[str], name: str = "value") -> None:
    """
    验证字典包含必需的键

    Args:
        value: 要验证的字典
        required_keys: 必需的键列表
        name: 参数名称

    Raises:
        DataValidationError: 字典缺少必需的键

    Example:
        >>> validate_dict_has_keys({'a': 1, 'b': 2}, ['a', 'b'], "config")
        >>> validate_dict_has_keys({'a': 1}, ['a', 'b'], "config")
        DataValidationError: config is missing required keys: ['b']
    """
    if not isinstance(value, dict):
        raise DataValidationError(
            f"{name} must be a dictionary, got: {type(value).__name__}"
        )

    missing_keys = [key for key in required_keys if key not in value]
    if missing_keys:
        raise DataValidationError(
            f"{name} is missing required keys: {missing_keys}"
        )


def sanitize_sql_identifier(identifier: str) -> str:
    """
    清理SQL标识符（表名、列名等）

    移除或转义潜在的危险字符

    Args:
        identifier: SQL标识符

    Returns:
        清理后的标识符

    Raises:
        DataValidationError: 标识符包含非法字符

    Example:
        >>> sanitize_sql_identifier("table_name")
        'table_name'
        >>> sanitize_sql_identifier("table; DROP TABLE users;")
        DataValidationError: Invalid SQL identifier
    """
    # 只允许字母、数字、下划线和点号
    if not re.match(r'^[a-zA-Z0-9_.]+$', identifier):
        raise DataValidationError(
            f"Invalid SQL identifier: {identifier}. "
            f"Only alphanumeric characters, underscores, and dots are allowed."
        )

    return identifier


def validate_file_path(path: str, must_exist: bool = False) -> None:
    """
    验证文件路径

    Args:
        path: 文件路径
        must_exist: 是否必须存在

    Raises:
        DataValidationError: 路径无效或不存在

    Example:
        >>> validate_file_path("/path/to/file.csv")
        >>> validate_file_path("", must_exist=True)
        DataValidationError: File path must be a non-empty string
    """
    from pathlib import Path

    validate_non_empty_string(path, "File path")

    if must_exist:
        if not Path(path).exists():
            raise DataValidationError(
                f"File does not exist: {path}"
            )
