"""
数据模型模块

定义系统中使用的数据结构，包括股票数据、指数数据和查询参数
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import pandas as pd


@dataclass
class QueryParams:
    """
    查询参数数据模型

    封装数据库查询所需的参数

    Attributes:
        start_date: 开始日期 (YYYYMMDD格式)
        end_date: 结束日期 (YYYYMMDD格式)
        codes: 股票或指数代码列表
        market: 市场代码 (zz500, hs300, sz50, zz1000, zz2000, ALL)
        batch_size: 批处理大小

    Example:
        params = QueryParams(
            start_date='20250101',
            end_date='20251231',
            codes=['000001.SZ', '000002.SZ'],
            market='zz500',
            batch_size=1000
        )
    """
    start_date: str
    end_date: str
    codes: List[str] = field(default_factory=list)
    market: str = 'ALL'
    batch_size: int = 1000

    def __post_init__(self):
        """验证参数"""
        # 验证日期格式
        if not self._is_valid_date(self.start_date):
            raise ValueError(f"Invalid start_date format: {self.start_date}, expected YYYYMMDD")
        if not self._is_valid_date(self.end_date):
            raise ValueError(f"Invalid end_date format: {self.end_date}, expected YYYYMMDD")

        # 验证日期范围
        if self.start_date > self.end_date:
            raise ValueError(f"start_date ({self.start_date}) must be before end_date ({self.end_date})")

        # 验证批处理大小
        if self.batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got: {self.batch_size}")

    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """验证日期格式是否为 YYYYMMDD"""
        if not isinstance(date_str, str) or len(date_str) != 8:
            return False
        try:
            datetime.strptime(date_str, '%Y%m%d')
            return True
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'codes': self.codes,
            'market': self.market,
            'batch_size': self.batch_size
        }


@dataclass
class StockData:
    """
    股票数据模型

    封装单只股票的行情数据

    Attributes:
        code: 股票代码 (如 '000001.SZ')
        date: 交易日期
        open: 开盘价
        high: 最高价
        low: 最低价
        close: 收盘价
        volume: 成交量
        amount: 成交额
        factor: 复权因子

    Example:
        stock = StockData(
            code='000001.SZ',
            date='2025-01-01',
            open=10.0,
            high=10.5,
            low=9.8,
            close=10.2,
            volume=1000000,
            amount=10200000,
            factor=1.0
        )
    """
    code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    factor: float = 1.0

    def __post_init__(self):
        """验证数据"""
        # 验证价格为正数
        if self.open < 0 or self.high < 0 or self.low < 0 or self.close < 0:
            raise ValueError(f"Prices must be non-negative for {self.code} on {self.date}")

        # 验证价格关系
        if self.high < self.low:
            raise ValueError(f"High price must be >= low price for {self.code} on {self.date}")
        if self.high < self.close or self.high < self.open:
            raise ValueError(f"High price must be >= open and close for {self.code} on {self.date}")
        if self.low > self.close or self.low > self.open:
            raise ValueError(f"Low price must be <= open and close for {self.code} on {self.date}")

        # 验证成交量和成交额
        if self.volume < 0:
            raise ValueError(f"Volume must be non-negative for {self.code} on {self.date}")
        if self.amount < 0:
            raise ValueError(f"Amount must be non-negative for {self.code} on {self.date}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'date': self.date,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'amount': self.amount,
            'factor': self.factor
        }

    def to_qlib_format(self) -> Dict[str, Any]:
        """
        转换为 Qlib 格式

        Returns:
            包含 Qlib 所需列的字典
        """
        return {
            'date': self.date,
            'open': self.open,
            'close': self.close,
            'high': self.high,
            'low': self.low,
            'volume': self.volume,
            'factor': self.factor,
            'money': self.amount  # Qlib 使用 'money' 而不是 'amount'
        }


@dataclass
class IndexData:
    """
    指数数据模型

    封装指数的行情数据

    Attributes:
        code: 指数代码 (如 '000905.SH')
        date: 交易日期
        open: 开盘点位
        high: 最高点位
        low: 最低点位
        close: 收盘点位
        volume: 成交量
        amount: 成交额
        factor: 复权因子 (指数通常为1.0)

    Example:
        index = IndexData(
            code='000905.SH',
            date='2025-01-01',
            open=5000.0,
            high=5100.0,
            low=4950.0,
            close=5050.0,
            volume=1000000000,
            amount=50000000000,
            factor=1.0
        )
    """
    code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    factor: float = 1.0

    def __post_init__(self):
        """验证数据"""
        # 验证点位为正数
        if self.open < 0 or self.high < 0 or self.low < 0 or self.close < 0:
            raise ValueError(f"Index values must be non-negative for {self.code} on {self.date}")

        # 验证点位关系
        if self.high < self.low:
            raise ValueError(f"High must be >= low for {self.code} on {self.date}")
        if self.high < self.close or self.high < self.open:
            raise ValueError(f"High must be >= open and close for {self.code} on {self.date}")
        if self.low > self.close or self.low > self.open:
            raise ValueError(f"Low must be <= open and close for {self.code} on {self.date}")

        # 验证成交量和成交额
        if self.volume < 0:
            raise ValueError(f"Volume must be non-negative for {self.code} on {self.date}")
        if self.amount < 0:
            raise ValueError(f"Amount must be non-negative for {self.code} on {self.date}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'date': self.date,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'amount': self.amount,
            'factor': self.factor
        }

    def to_qlib_format(self) -> Dict[str, Any]:
        """
        转换为 Qlib 格式

        Returns:
            包含 Qlib 所需列的字典
        """
        return {
            'date': self.date,
            'open': self.open,
            'close': self.close,
            'high': self.high,
            'low': self.low,
            'volume': self.volume,
            'factor': self.factor,
            'money': self.amount  # Qlib 使用 'money' 而不是 'amount'
        }


@dataclass
class ProcessingResult:
    """
    处理结果数据模型

    封装数据处理的结果统计

    Attributes:
        success: 是否成功
        total_count: 总数量
        success_count: 成功数量
        failed_count: 失败数量
        duration_seconds: 处理耗时（秒）
        errors: 错误列表
        metadata: 额外的元数据

    Example:
        result = ProcessingResult(
            success=True,
            total_count=6000,
            success_count=5998,
            failed_count=2,
            duration_seconds=240.5,
            errors=[{'code': '000001.SZ', 'error': 'No data found'}]
        )
    """
    success: bool
    total_count: int
    success_count: int
    failed_count: int
    duration_seconds: float
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """验证数据"""
        if self.total_count < 0:
            raise ValueError("total_count must be non-negative")
        if self.success_count < 0:
            raise ValueError("success_count must be non-negative")
        if self.failed_count < 0:
            raise ValueError("failed_count must be non-negative")
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")

        # 验证计数一致性
        if self.success_count + self.failed_count != self.total_count:
            raise ValueError(
                f"success_count ({self.success_count}) + failed_count ({self.failed_count}) "
                f"must equal total_count ({self.total_count})"
            )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'total_count': self.total_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'duration_seconds': self.duration_seconds,
            'errors': self.errors,
            'metadata': self.metadata
        }

    def get_success_rate(self) -> float:
        """计算成功率"""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100

    def summary(self) -> str:
        """生成摘要字符串"""
        return (
            f"Processing completed: {self.success_count}/{self.total_count} succeeded "
            f"({self.get_success_rate():.2f}%), {self.failed_count} failed, "
            f"duration: {self.duration_seconds:.2f}s"
        )
