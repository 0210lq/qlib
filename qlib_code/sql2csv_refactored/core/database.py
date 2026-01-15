"""
数据库连接管理模块

提供数据库连接管理、查询执行和连接池功能
"""

import time
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import pymysql
from sqlalchemy import create_engine, text, pool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, DatabaseError as SQLAlchemyDatabaseError

from ..exceptions import DatabaseError, ConfigurationError
from ..utils.logging_config import get_logger


class DatabaseConnection:
    """
    数据库连接管理器

    负责管理数据库连接生命周期、执行查询和处理连接池

    Attributes:
        config: 数据库配置
        engine: SQLAlchemy 引擎
        logger: 日志记录器

    Example:
        db = DatabaseConnection(config.database)
        with db.get_connection() as conn:
            result = db.execute_query(conn, query, params)
    """

    def __init__(self, db_config, max_retries: int = 3, retry_delay: float = 1.0):
        """
        初始化数据库连接管理器

        Args:
            db_config: 数据库配置对象
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.config = db_config
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = get_logger()
        self.engine = None

        # 初始化连接
        self._initialize_engine()

    def _initialize_engine(self):
        """初始化 SQLAlchemy 引擎"""
        try:
            # 构建连接字符串
            connection_string = self._build_connection_string()

            # 创建引擎（带连接池）
            self.engine = create_engine(
                connection_string,
                poolclass=pool.QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,  # 1小时回收连接
                echo=False
            )

            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            self.logger.info(f"Database connection initialized: {self.config.get('host')}")

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize database connection: {e}") from e

    def _build_connection_string(self) -> str:
        """构建数据库连接字符串"""
        host = self.config.get('host')
        port = self.config.get('port', 3306)
        database = self.config.get('database')
        user = self.config.get('user')
        password = self.config.get('password')

        if not all([host, database, user, password]):
            raise ConfigurationError("Missing required database configuration")

        # 使用 pymysql 驱动
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"

    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器

        Yields:
            数据库连接对象

        Example:
            with db.get_connection() as conn:
                result = conn.execute(query)
        """
        conn = None
        try:
            conn = self.engine.connect()
            yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Failed to get database connection: {e}") from e
        finally:
            if conn is not None:
                conn.close()

    def execute_query(self, conn, query, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        执行查询并返回结果

        Args:
            conn: 数据库连接对象
            query: SQL查询（text对象或字符串）
            params: 查询参数字典

        Returns:
            查询结果列表（每行为一个字典）

        Raises:
            DatabaseError: 查询执行失败

        Example:
            query = text("SELECT * FROM stocks WHERE code = :code")
            result = db.execute_query(conn, query, {'code': '000001.SZ'})
        """
        try:
            # 确保query是text对象
            if isinstance(query, str):
                query = text(query)

            # 执行查询
            if params:
                result = conn.execute(query, params)
            else:
                result = conn.execute(query)

            # 转换为字典列表
            rows = []
            for row in result:
                rows.append(dict(row._mapping))

            self.logger.debug(f"Query executed successfully, returned {len(rows)} rows")
            return rows

        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise DatabaseError(
                f"Failed to execute query: {e}",
                query=str(query),
                params=params
            ) from e

    def execute_query_with_retry(self, query, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        执行查询并在失败时自动重试

        Args:
            query: SQL查询（text对象或字符串）
            params: 查询参数字典

        Returns:
            查询结果列表

        Raises:
            DatabaseError: 重试后仍然失败

        Example:
            query = text("SELECT * FROM stocks WHERE code = :code")
            result = db.execute_query_with_retry(query, {'code': '000001.SZ'})
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                with self.get_connection() as conn:
                    return self.execute_query(conn, query, params)

            except (OperationalError, SQLAlchemyDatabaseError) as e:
                last_error = e
                self.logger.warning(
                    f"Query failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # 指数退避
                    continue
                else:
                    break

        # 所有重试都失败
        raise DatabaseError(
            f"Query failed after {self.max_retries} retries: {last_error}",
            query=str(query),
            params=params
        ) from last_error

    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("Database connection closed")

