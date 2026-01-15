"""
SQL查询构建模块

提供安全的参数化SQL查询构建功能，防止SQL注入
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy import text
from datetime import datetime

from ..exceptions import ConfigurationError
from ..utils.logging_config import get_logger


class QueryBuilder:
    """
    SQL查询构建器

    负责构建安全的参数化SQL查询，封装表名和列名映射

    Attributes:
        schema_config: 数据库表和列映射配置
        logger: 日志记录器

    Example:
        builder = QueryBuilder(config.schema)
        query, params = builder.build_stock_query(['000001.SZ'], '20250101', '20251231')
    """

    def __init__(self, schema_config):
        """
        初始化查询构建器

        Args:
            schema_config: 数据库表和列映射配置
        """
        self.schema_config = schema_config
        self.logger = get_logger()

        # 提取表名
        self.tables = schema_config.get('tables')
        if not self.tables:
            raise ConfigurationError("Missing tables configuration in schema")

        # 提取列映射
        self.stock_columns = schema_config.get('stock_columns')
        self.index_columns = schema_config.get('index_columns')

        if not self.stock_columns or not self.index_columns:
            raise ConfigurationError("Missing column mappings in schema")

    @staticmethod
    def _convert_date_format(date_str: str) -> str:
        """
        将日期从YYYYMMDD格式转换为YYYY-MM-DD格式

        Args:
            date_str: YYYYMMDD格式的日期字符串

        Returns:
            YYYY-MM-DD格式的日期字符串
        """
        return datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')

    def build_stock_query(self, codes: List[str], start_date: str, end_date: str) -> Tuple[text, Dict[str, Any]]:
        """
        构建股票数据查询（参数化，防止SQL注入）

        Args:
            codes: 股票代码列表
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            (query, params): SQL查询对象和参数字典

        Example:
            query, params = builder.build_stock_query(['000001.SZ'], '20250101', '20251231')
        """
        # 获取表名和列名
        table_name = self.tables.get('stock')
        date_col = self.stock_columns.get('date')
        code_col = self.stock_columns.get('code')
        open_col = self.stock_columns.get('open')
        high_col = self.stock_columns.get('high')
        low_col = self.stock_columns.get('low')
        close_col = self.stock_columns.get('close')
        volume_col = self.stock_columns.get('volume')
        amount_col = self.stock_columns.get('amount')
        factor_col = self.stock_columns.get('factor')

        # 为每个code创建占位符
        code_placeholders = ', '.join([f':code_{i}' for i in range(len(codes))])

        # 构建SQL查询
        query_str = f"""
            SELECT
                {date_col} as date,
                {code_col} as code,
                {open_col} as open,
                {high_col} as high,
                {low_col} as low,
                {close_col} as close,
                {volume_col} as volume,
                {amount_col} as amount,
                {factor_col} as factor
            FROM {table_name}
            WHERE {code_col} IN ({code_placeholders})
            AND {date_col} BETWEEN :start_date AND :end_date
            ORDER BY {code_col}, {date_col}
        """

        # 构建参数字典
        params = {
            'start_date': self._convert_date_format(start_date),
            'end_date': self._convert_date_format(end_date)
        }
        for i, code in enumerate(codes):
            params[f'code_{i}'] = code

        self.logger.debug(f"Built stock query for {len(codes)} codes")
        return text(query_str), params

    def build_index_query(self, codes: List[str], start_date: str, end_date: str) -> Tuple[text, Dict[str, Any]]:
        """
        构建指数数据查询（参数化，防止SQL注入）

        Args:
            codes: 指数代码列表
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            (query, params): SQL查询对象和参数字典

        Example:
            query, params = builder.build_index_query(['000905.SH'], '20250101', '20251231')
        """
        # 获取表名和列名
        table_name = self.tables.get('index')
        date_col = self.index_columns.get('date')
        code_col = self.index_columns.get('code')
        open_col = self.index_columns.get('open')
        high_col = self.index_columns.get('high')
        low_col = self.index_columns.get('low')
        close_col = self.index_columns.get('close')
        volume_col = self.index_columns.get('volume')
        amount_col = self.index_columns.get('amount')

        # 为每个code创建占位符
        code_placeholders = ', '.join([f':code_{i}' for i in range(len(codes))])

        # 构建SQL查询（指数的factor固定为1.0）
        query_str = f"""
            SELECT
                {date_col} as date,
                {code_col} as code,
                {open_col} as open,
                {high_col} as high,
                {low_col} as low,
                {close_col} as close,
                {volume_col} as volume,
                {amount_col} as amount,
                1.0 as factor
            FROM {table_name}
            WHERE {code_col} IN ({code_placeholders})
            AND {date_col} BETWEEN :start_date AND :end_date
            ORDER BY {code_col}, {date_col}
        """

        # 构建参数字典
        params = {
            'start_date': self._convert_date_format(start_date),
            'end_date': self._convert_date_format(end_date)
        }
        for i, code in enumerate(codes):
            params[f'code_{i}'] = code

        self.logger.debug(f"Built index query for {len(codes)} codes")
        return text(query_str), params

    def build_component_query(self, market: str) -> Tuple[text, Dict[str, Any]]:
        """
        构建成分股查询

        Args:
            market: 市场代码 (如 'zz500')

        Returns:
            (query, params): SQL查询对象和参数字典

        Example:
            query, params = builder.build_component_query('zz500')
        """
        # 获取表名
        table_name = self.tables.get('component')

        # 构建SQL查询
        query_str = f"""
            SELECT DISTINCT code
            FROM {table_name}
            WHERE organization = :market
            ORDER BY code
        """

        params = {'market': market}

        self.logger.debug(f"Built component query for market: {market}")
        return text(query_str), params

    def build_all_stocks_query(self, start_date: str, end_date: str) -> Tuple[text, Dict[str, Any]]:
        """
        构建所有股票代码查询

        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            (query, params): SQL查询对象和参数字典

        Example:
            query, params = builder.build_all_stocks_query('20250101', '20251231')
        """
        # 获取表名和列名
        table_name = self.tables.get('stock')
        date_col = self.stock_columns.get('date')
        code_col = self.stock_columns.get('code')

        # 构建SQL查询 - 获取日期范围内有数据的所有股票代码
        query_str = f"""
            SELECT DISTINCT {code_col} as code
            FROM {table_name}
            WHERE {date_col} BETWEEN :start_date AND :end_date
            ORDER BY {code_col}
        """

        params = {
            'start_date': start_date,
            'end_date': end_date
        }

        self.logger.debug(f"Built all stocks query for date range: {start_date} - {end_date}")
        return text(query_str), params
