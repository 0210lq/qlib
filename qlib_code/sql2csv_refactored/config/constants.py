"""
常量定义模块

从 sql2csv.py 中提取的所有硬编码常量
"""


class Defaults:
    """默认配置值"""

    # 批处理配置
    BATCH_SIZE = 1000
    MAX_WORKERS = 8
    BATCH_SLEEP_SECONDS = 0.1

    # 查询配置
    QUERY_TIMEOUT = 30

    # 日期配置
    START_DATE = "20150101"

    # 市场配置
    MARKET = "ALL"


class DatabaseDefaults:
    """数据库默认配置"""

    HOST = "localhost:3306"
    PORT = 3306
    DATABASE = "data_prepared_new"
    USER = "root"
    PASSWORD = ""


class TableNames:
    """数据库表名"""

    STOCK = "data_stock"
    INDEX = "data_index"
    COMPONENT = "data.indexcomponent"


class ColumnNames:
    """数据库列名"""

    # 股票数据列
    STOCK_COLUMNS = {
        'valuation_date': 'valuation_date',
        'code': 'code',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
        'amt': 'amt',
        'adjfactor': 'COALESCE(adjfactor, adjfactor_jy, adjfactor_wind)',
    }

    # 指数数据列
    INDEX_COLUMNS = {
        'valuation_date': 'valuation_date',
        'code': 'code',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
        'amt': 'amt',
    }


class QlibFormat:
    """Qlib输出格式配置"""

    # 输出列名（按顺序）
    COLUMNS = ["date", "open", "close", "high", "low", "volume", "factor", "money"]

    # 日期格式
    DATE_FORMAT = "%Y-%m-%d"

    # 指数的复权因子（指数没有复权，固定为1.0）
    INDEX_FACTOR = 1.0

    # 列名映射：数据库列名 -> Qlib列名
    COLUMN_MAPPING = {
        'valuation_date': 'date',
        'open': 'open',
        'close': 'close',
        'high': 'high',
        'low': 'low',
        'volume': 'volume',
        'amt': 'money',
        'adjfactor': 'factor',
    }


class MarketDefinitions:
    """市场定义"""

    # 指数代码映射
    INDEX_MAPPING = {
        'zz500': ['000905.SH'],
        'hs300': ['000300.SH'],
        'sz50': ['000016.SH'],
        'zz1000': ['000852.SH'],
        'zz2000': ['932000.CSI'],
        'ALL': ['000905.SH', '000300.SH', '000016.SH', '000852.SH', '932000.CSI'],
    }

    # 市场名称
    MARKET_NAMES = {
        'zz500': '中证500',
        'hs300': '沪深300',
        'sz50': '上证50',
        'zz1000': '中证1000',
        'zz2000': '中证2000',
        'ALL': '全市场',
    }


class ConfigPaths:
    """配置文件路径"""

    # 相对于项目根目录的配置文件路径
    DB_CONFIG = "config/db.yaml"
    PATHS_CONFIG = "config/paths.yaml"
    SQL2CSV_CONFIG = "config/sql2csv.yaml"
