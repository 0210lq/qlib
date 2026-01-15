"""
日期处理工具模块

提供日期格式转换、验证和计算功能
"""

from datetime import datetime, timedelta
from typing import Optional

from ..exceptions import DataValidationError


def validate_date_format(date_str: str, expected_format: str = '%Y%m%d') -> bool:
    """
    验证日期字符串格式

    Args:
        date_str: 日期字符串
        expected_format: 期望的日期格式（默认YYYYMMDD）

    Returns:
        bool: 格式是否有效

    Example:
        >>> validate_date_format('20250101')
        True
        >>> validate_date_format('2025-01-01')
        False
    """
    try:
        datetime.strptime(date_str, expected_format)
        return True
    except (ValueError, TypeError):
        return False


def convert_date_format(date_str: str, from_format: str, to_format: str) -> str:
    """
    转换日期格式

    Args:
        date_str: 原始日期字符串
        from_format: 原始格式
        to_format: 目标格式

    Returns:
        转换后的日期字符串

    Raises:
        DataValidationError: 日期格式无效

    Example:
        >>> convert_date_format('20250101', '%Y%m%d', '%Y-%m-%d')
        '2025-01-01'
    """
    try:
        dt = datetime.strptime(date_str, from_format)
        return dt.strftime(to_format)
    except (ValueError, TypeError) as e:
        raise DataValidationError(
            f"Invalid date format: {date_str}, expected format: {from_format}"
        ) from e


def normalize_date(date_str: str) -> str:
    """
    标准化日期为YYYYMMDD格式

    支持多种输入格式：
    - YYYYMMDD
    - YYYY-MM-DD
    - YYYY/MM/DD

    Args:
        date_str: 日期字符串

    Returns:
        YYYYMMDD格式的日期字符串

    Raises:
        DataValidationError: 无法识别的日期格式

    Example:
        >>> normalize_date('2025-01-01')
        '20250101'
        >>> normalize_date('20250101')
        '20250101'
    """
    # 尝试常见格式
    formats = ['%Y%m%d', '%Y-%m-%d', '%Y/%m/%d']

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y%m%d')
        except (ValueError, TypeError):
            continue

    raise DataValidationError(
        f"Unable to parse date: {date_str}. "
        f"Supported formats: YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD"
    )


def get_today(format: str = '%Y%m%d') -> str:
    """
    获取今天的日期

    Args:
        format: 日期格式（默认YYYYMMDD）

    Returns:
        今天的日期字符串

    Example:
        >>> get_today()
        '20250114'
        >>> get_today('%Y-%m-%d')
        '2025-01-14'
    """
    return datetime.now().strftime(format)


def add_days(date_str: str, days: int, format: str = '%Y%m%d') -> str:
    """
    日期加减天数

    Args:
        date_str: 日期字符串
        days: 要加减的天数（负数表示减）
        format: 日期格式

    Returns:
        计算后的日期字符串

    Raises:
        DataValidationError: 日期格式无效

    Example:
        >>> add_days('20250101', 10)
        '20250111'
        >>> add_days('20250101', -1)
        '20241231'
    """
    try:
        dt = datetime.strptime(date_str, format)
        new_dt = dt + timedelta(days=days)
        return new_dt.strftime(format)
    except (ValueError, TypeError) as e:
        raise DataValidationError(
            f"Invalid date: {date_str}, expected format: {format}"
        ) from e


def date_range_days(start_date: str, end_date: str, format: str = '%Y%m%d') -> int:
    """
    计算两个日期之间的天数

    Args:
        start_date: 开始日期
        end_date: 结束日期
        format: 日期格式

    Returns:
        天数差（end_date - start_date）

    Raises:
        DataValidationError: 日期格式无效

    Example:
        >>> date_range_days('20250101', '20250110')
        9
    """
    try:
        start_dt = datetime.strptime(start_date, format)
        end_dt = datetime.strptime(end_date, format)
        return (end_dt - start_dt).days
    except (ValueError, TypeError) as e:
        raise DataValidationError(
            f"Invalid date range: {start_date} to {end_date}, expected format: {format}"
        ) from e


def is_valid_date_range(start_date: str, end_date: str, format: str = '%Y%m%d') -> bool:
    """
    验证日期范围是否有效（start_date <= end_date）

    Args:
        start_date: 开始日期
        end_date: 结束日期
        format: 日期格式

    Returns:
        bool: 日期范围是否有效

    Example:
        >>> is_valid_date_range('20250101', '20251231')
        True
        >>> is_valid_date_range('20251231', '20250101')
        False
    """
    try:
        start_dt = datetime.strptime(start_date, format)
        end_dt = datetime.strptime(end_date, format)
        return start_dt <= end_dt
    except (ValueError, TypeError):
        return False


def parse_flexible_date(date_input: Optional[str], default_format: str = '%Y%m%d') -> Optional[str]:
    """
    灵活解析日期输入

    - None 或 'today' -> 今天
    - 'yesterday' -> 昨天
    - 其他 -> 尝试标准化

    Args:
        date_input: 日期输入（可能是None、特殊关键字或日期字符串）
        default_format: 输出格式

    Returns:
        标准化的日期字符串，或None

    Example:
        >>> parse_flexible_date(None)
        '20250114'  # today
        >>> parse_flexible_date('today')
        '20250114'
        >>> parse_flexible_date('yesterday')
        '20250113'
        >>> parse_flexible_date('2025-01-01')
        '20250101'
    """
    if date_input is None or date_input.lower() == 'today':
        return get_today(default_format)

    if date_input.lower() == 'yesterday':
        return add_days(get_today(), -1, default_format)

    try:
        return normalize_date(date_input)
    except DataValidationError:
        return None
