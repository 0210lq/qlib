"""
配置验证模块

提供配置完整性和正确性验证功能
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..exceptions import ConfigurationError
from .constants import Defaults, MarketDefinitions


class ConfigValidator:
    """
    配置验证器

    验证配置的完整性和正确性，包括：
    - 必需字段检查
    - 日期格式验证
    - 市场代码验证
    - 数值范围验证
    - 数据库配置验证
    """

    @staticmethod
    def validate(config) -> None:
        """
        验证配置对象

        Args:
            config: Config 对象

        Raises:
            ConfigurationError: 配置验证失败

        Example:
            config = ConfigLoader.load()
            ConfigValidator.validate(config)
        """
        errors = []

        # 验证各个配置节
        errors.extend(ConfigValidator._validate_extraction(config.extraction))
        errors.extend(ConfigValidator._validate_performance(config.performance))
        errors.extend(ConfigValidator._validate_database(config.database))
        errors.extend(ConfigValidator._validate_schema(config.schema))
        errors.extend(ConfigValidator._validate_markets(config.markets))
        errors.extend(ConfigValidator._validate_output(config.output))
        errors.extend(ConfigValidator._validate_logging(config.logging))

        # 如果有错误，抛出异常
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ConfigurationError(error_msg)

    @staticmethod
    def _validate_extraction(extraction) -> List[str]:
        """验证数据提取配置"""
        errors = []

        # 验证 market
        market = extraction.get('market')
        if not market:
            errors.append("extraction.market is required")
        elif isinstance(market, (list, tuple)):
            # 如果是列表或元组，验证每个股票代码格式（可选）
            # 这里我们允许任意股票代码列表，不做严格验证
            if len(market) == 0:
                errors.append("extraction.market list cannot be empty")
        elif market not in MarketDefinitions.INDEX_MAPPING:
            valid_markets = ', '.join(MarketDefinitions.INDEX_MAPPING.keys())
            errors.append(f"extraction.market must be one of: {valid_markets} or a list of stock codes")

        # 验证 start_date
        start_date = extraction.get('start_date')
        if not start_date:
            errors.append("extraction.start_date is required")
        elif not ConfigValidator._is_valid_date(start_date):
            errors.append(f"extraction.start_date must be in YYYYMMDD format, got: {start_date}")

        # 验证 end_date（可选）
        end_date = extraction.get('end_date')
        if end_date is not None and not ConfigValidator._is_valid_date(end_date):
            errors.append(f"extraction.end_date must be in YYYYMMDD format or null, got: {end_date}")

        # 验证日期范围
        if start_date and end_date and ConfigValidator._is_valid_date(start_date) and ConfigValidator._is_valid_date(end_date):
            if start_date > end_date:
                errors.append(f"extraction.start_date ({start_date}) must be before end_date ({end_date})")

        return errors

    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """验证日期格式是否为 YYYYMMDD"""
        if not isinstance(date_str, str):
            return False
        if not re.match(r'^\d{8}$', date_str):
            return False
        try:
            datetime.strptime(date_str, '%Y%m%d')
            return True
        except ValueError:
            return False

    @staticmethod
    def _validate_performance(performance) -> List[str]:
        """验证性能配置"""
        errors = []

        # 验证 batch_size
        batch_size = performance.get('batch_size')
        if batch_size is None:
            errors.append("performance.batch_size is required")
        elif not isinstance(batch_size, int) or batch_size <= 0:
            errors.append(f"performance.batch_size must be a positive integer, got: {batch_size}")
        elif batch_size > 10000:
            errors.append(f"performance.batch_size is too large (max 10000), got: {batch_size}")

        # 验证 max_workers
        max_workers = performance.get('max_workers')
        if max_workers is None:
            errors.append("performance.max_workers is required")
        elif not isinstance(max_workers, int) or max_workers <= 0:
            errors.append(f"performance.max_workers must be a positive integer, got: {max_workers}")
        elif max_workers > 32:
            errors.append(f"performance.max_workers is too large (max 32), got: {max_workers}")

        # 验证 batch_sleep_seconds
        batch_sleep = performance.get('batch_sleep_seconds')
        if batch_sleep is not None:
            if not isinstance(batch_sleep, (int, float)) or batch_sleep < 0:
                errors.append(f"performance.batch_sleep_seconds must be non-negative, got: {batch_sleep}")

        # 验证 query_timeout_seconds
        query_timeout = performance.get('query_timeout_seconds')
        if query_timeout is not None:
            if not isinstance(query_timeout, (int, float)) or query_timeout <= 0:
                errors.append(f"performance.query_timeout_seconds must be positive, got: {query_timeout}")

        return errors

    @staticmethod
    def _validate_database(database) -> List[str]:
        """验证数据库配置"""
        errors = []

        # 验证必需字段
        required_fields = ['host', 'port', 'database', 'user', 'password']
        for field in required_fields:
            value = database.get(field)
            if not value:
                errors.append(f"database.{field} is required")

        # 验证 port
        port = database.get('port')
        if port is not None:
            if not isinstance(port, int) or port <= 0 or port > 65535:
                errors.append(f"database.port must be between 1 and 65535, got: {port}")

        return errors

    @staticmethod
    def _validate_schema(schema) -> List[str]:
        """验证数据库表和列映射配置"""
        errors = []

        # 验证 tables
        tables = schema.get('tables')
        if not tables:
            errors.append("schema.tables is required")
        else:
            required_tables = ['stock', 'index', 'component']
            for table in required_tables:
                if not tables.get(table):
                    errors.append(f"schema.tables.{table} is required")

        # 验证 stock_columns
        stock_columns = schema.get('stock_columns')
        if not stock_columns:
            errors.append("schema.stock_columns is required")
        else:
            required_columns = ['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount']
            for col in required_columns:
                if not stock_columns.get(col):
                    errors.append(f"schema.stock_columns.{col} is required")

        # 验证 index_columns
        index_columns = schema.get('index_columns')
        if not index_columns:
            errors.append("schema.index_columns is required")
        else:
            required_columns = ['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount']
            for col in required_columns:
                if not index_columns.get(col):
                    errors.append(f"schema.index_columns.{col} is required")

        return errors

    @staticmethod
    def _validate_markets(markets) -> List[str]:
        """验证市场配置"""
        errors = []

        # 验证市场定义不为空
        markets_dict = markets.to_dict() if hasattr(markets, 'to_dict') else markets
        if not markets_dict:
            errors.append("markets configuration is required")
            return errors

        # 验证每个市场的配置
        for market_code, market_info in markets_dict.items():
            if not isinstance(market_info, dict):
                errors.append(f"markets.{market_code} must be a dictionary")
                continue

            # 验证 name
            if not market_info.get('name'):
                errors.append(f"markets.{market_code}.name is required")

            # 验证 index_code 或 index_codes
            has_index_code = 'index_code' in market_info
            has_index_codes = 'index_codes' in market_info

            if not has_index_code and not has_index_codes:
                errors.append(f"markets.{market_code} must have either 'index_code' or 'index_codes'")
            elif has_index_codes:
                index_codes = market_info.get('index_codes')
                if not isinstance(index_codes, list) or not index_codes:
                    errors.append(f"markets.{market_code}.index_codes must be a non-empty list")

        return errors

    @staticmethod
    def _validate_output(output) -> List[str]:
        """验证输出配置"""
        errors = []

        # 验证 csv_output_dir
        csv_output_dir = output.get('csv_output_dir')
        if not csv_output_dir:
            errors.append("output.csv_output_dir is required")

        # 验证 provider_uri
        provider_uri = output.get('provider_uri')
        if not provider_uri:
            errors.append("output.provider_uri is required")

        # 验证 columns
        columns = output.get('columns')
        if not columns:
            errors.append("output.columns is required")
        elif not isinstance(columns, list) or not columns:
            errors.append("output.columns must be a non-empty list")
        else:
            # 验证必需的列
            required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
            for col in required_columns:
                if col not in columns:
                    errors.append(f"output.columns must include '{col}'")

        # 验证 date_format
        date_format = output.get('date_format')
        if not date_format:
            errors.append("output.date_format is required")

        return errors

    @staticmethod
    def _validate_logging(logging_config) -> List[str]:
        """验证日志配置"""
        errors = []

        # 验证 level
        level = logging_config.get('level')
        if not level:
            errors.append("logging.level is required")
        elif level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            errors.append(f"logging.level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL, got: {level}")

        # 验证 console
        console = logging_config.get('console')
        if console is not None and not isinstance(console, bool):
            errors.append(f"logging.console must be a boolean, got: {console}")

        # 验证 file
        file_output = logging_config.get('file')
        if file_output is not None and not isinstance(file_output, bool):
            errors.append(f"logging.file must be a boolean, got: {file_output}")

        # 如果启用文件输出，验证 file_path
        if file_output:
            file_path = logging_config.get('file_path')
            if not file_path:
                errors.append("logging.file_path is required when logging.file is true")

        # 验证 rotation
        rotation = logging_config.get('rotation')
        if rotation and rotation not in ['daily', 'hourly', 'weekly']:
            errors.append(f"logging.rotation must be one of: daily, hourly, weekly, got: {rotation}")

        # 验证 retention_days
        retention_days = logging_config.get('retention_days')
        if retention_days is not None:
            if not isinstance(retention_days, int) or retention_days <= 0:
                errors.append(f"logging.retention_days must be a positive integer, got: {retention_days}")

        return errors

