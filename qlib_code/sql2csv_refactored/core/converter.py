"""
数据格式转换模块

提供数据库记录到Qlib格式的转换功能
"""

from typing import List, Dict, Any
from datetime import datetime
import pandas as pd

from ..models.data_models import StockData, IndexData
from ..exceptions import DataConversionError, DataValidationError
from ..utils.logging_config import get_logger


class DataConverter:
    """
    数据格式转换器

    负责将数据库记录转换为Qlib格式，处理列名映射和数据验证

    Attributes:
        output_config: 输出配置
        logger: 日志记录器

    Example:
        converter = DataConverter(config.output)
        df = converter.convert_to_dataframe(rows, 'stock')
    """

    def __init__(self, output_config):
        """
        初始化数据转换器

        Args:
            output_config: 输出配置对象
        """
        self.output_config = output_config
        self.logger = get_logger()

        # 获取输出列顺序和日期格式
        self.output_columns = output_config.get('columns', [])
        self.date_format = output_config.get('date_format', '%Y-%m-%d')

    def _format_date(self, date_value: Any) -> str:
        """
        格式化日期为指定格式

        Args:
            date_value: 日期值（可能是字符串、datetime对象等）

        Returns:
            格式化后的日期字符串

        Raises:
            DataConversionError: 日期格式转换失败
        """
        try:
            # 如果已经是字符串，尝试解析
            if isinstance(date_value, str):
                # 尝试 YYYYMMDD 格式
                if len(date_value) == 8 and date_value.isdigit():
                    dt = datetime.strptime(date_value, '%Y%m%d')
                    return dt.strftime(self.date_format)
                # 尝试其他常见格式
                else:
                    dt = datetime.strptime(date_value, '%Y-%m-%d')
                    return dt.strftime(self.date_format)

            # 如果是datetime对象
            elif isinstance(date_value, datetime):
                return date_value.strftime(self.date_format)

            else:
                raise ValueError(f"Unsupported date type: {type(date_value)}")

        except Exception as e:
            raise DataConversionError(f"Failed to format date: {date_value}, error: {e}") from e

    def _is_valid_trading_day(self, row: Dict[str, Any]) -> bool:
        """
        检查是否为有效交易日（是否有完整的交易数据）

        Args:
            row: 数据行字典

        Returns:
            bool: True表示有完整的有效交易数据，False表示停牌或数据不完整
        """
        # 必需的交易字段：这些字段必须都有值才认为是有效交易日
        # 注意：必须包含所有会被转换为float的字段
        required_trading_fields = ['open', 'high', 'low', 'close', 'volume', 'amount']

        # 检查是否所有必需字段都有值（不为None）
        all_valid = all(row.get(field) is not None for field in required_trading_fields)

        return all_valid

    def _validate_row(self, row: Dict[str, Any], data_type: str) -> None:
        """
        验证数据行的完整性

        Args:
            row: 数据行字典
            data_type: 数据类型 ('stock' 或 'index')

        Raises:
            DataValidationError: 数据验证失败
        """
        # 必须存在的字段
        required_fields = ['date', 'code']

        # 检查必需字段
        missing_required = [field for field in required_fields if field not in row or row[field] is None]
        if missing_required:
            raise DataValidationError(
                f"Missing required fields in {data_type} data: {missing_required}",
                data=row
            )

        # 检查交易数据字段是否存在（可以为None）
        trading_fields = ['open', 'high', 'low', 'close', 'volume', 'amount']
        missing_fields = [field for field in trading_fields if field not in row]
        if missing_fields:
            raise DataValidationError(
                f"Missing fields in {data_type} data: {missing_fields}",
                data=row
            )

        # 检查数值字段是否为数字（允许None）
        numeric_fields = ['open', 'high', 'low', 'close', 'volume', 'amount']
        for field in numeric_fields:
            if row[field] is not None and not isinstance(row[field], (int, float)):
                raise DataValidationError(
                    f"Field '{field}' must be numeric or None, got: {type(row[field])}",
                    data=row
                )

    def convert_to_dataframe(self, rows: List[Dict[str, Any]], data_type: str = 'stock') -> pd.DataFrame:
        """
        将数据库记录转换为Qlib格式的DataFrame

        Args:
            rows: 数据库查询结果（字典列表）
            data_type: 数据类型 ('stock' 或 'index')

        Returns:
            Qlib格式的DataFrame

        Raises:
            DataConversionError: 数据转换失败
            DataValidationError: 数据验证失败

        Example:
            df = converter.convert_to_dataframe(rows, 'stock')
        """
        if not rows:
            self.logger.warning(f"No data to convert for {data_type}")
            return pd.DataFrame()

        try:
            # 转换每一行数据
            converted_rows = []
            skipped_count = 0

            for row in rows:
                # 验证数据
                self._validate_row(row, data_type)

                # 检查是否为有效交易日（跳过停牌日）
                if not self._is_valid_trading_day(row):
                    skipped_count += 1
                    continue

                # 格式化日期
                formatted_date = self._format_date(row['date'])

                # 构建Qlib格式的行
                qlib_row = {
                    'date': formatted_date,
                    'open': float(row['open']),
                    'close': float(row['close']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'volume': float(row['volume']),
                    'factor': float(row.get('factor', 1.0)),
                    'money': float(row['amount'])  # Qlib使用'money'而不是'amount'
                }

                converted_rows.append(qlib_row)

            # 记录跳过的停牌日数量
            if skipped_count > 0:
                self.logger.debug(f"Skipped {skipped_count} suspended/invalid trading days for {data_type}")

            # 创建DataFrame
            df = pd.DataFrame(converted_rows)

            # 按照配置的列顺序重新排列
            if self.output_columns:
                # 只保留配置中指定的列
                available_columns = [col for col in self.output_columns if col in df.columns]
                df = df[available_columns]

            self.logger.debug(f"Converted {len(converted_rows)} valid rows from {len(rows)} total {data_type} rows to DataFrame")
            return df

        except (DataValidationError, DataConversionError):
            raise
        except Exception as e:
            raise DataConversionError(f"Failed to convert {data_type} data to DataFrame: {e}") from e

