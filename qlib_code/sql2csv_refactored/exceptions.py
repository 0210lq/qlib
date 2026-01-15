"""
自定义异常模块

定义 sql2csv 模块使用的所有自定义异常
"""


class SQL2CSVError(Exception):
    """
    所有 sql2csv 错误的基类

    所有自定义异常都应该继承此类，以便统一捕获和处理

    Example:
        try:
            # some sql2csv operation
            pass
        except SQL2CSVError as e:
            logger.error(f"SQL2CSV operation failed: {e}")
    """
    pass


class ConfigurationError(SQL2CSVError):
    """
    配置验证或加载错误

    当配置文件缺失、格式错误或包含无效值时抛出

    Example:
        if not config.get('db_host'):
            raise ConfigurationError("Missing required configuration: db_host")
    """
    pass


class DatabaseError(SQL2CSVError):
    """
    数据库连接或查询错误

    当数据库操作失败时抛出，包含查询和参数信息以便调试

    Attributes:
        query: 失败的SQL查询（可选）
        params: 查询参数（可选）

    Example:
        try:
            result = engine.execute(query, params)
        except Exception as e:
            raise DatabaseError(
                "Failed to execute query",
                query=query,
                params=params
            ) from e
    """

    def __init__(self, message, query=None, params=None):
        super().__init__(message)
        self.query = query
        self.params = params

    def __str__(self):
        msg = super().__str__()
        if self.query:
            msg += f"\nQuery: {self.query}"
        if self.params:
            msg += f"\nParams: {self.params}"
        return msg


class DataValidationError(SQL2CSVError):
    """
    数据验证错误

    当数据不符合预期格式或包含无效值时抛出

    Attributes:
        data: 导致错误的数据（可选）

    Example:
        if df.empty:
            raise DataValidationError(
                "DataFrame is empty",
                data={'shape': df.shape}
            )
    """

    def __init__(self, message, data=None):
        super().__init__(message)
        self.data = data

    def __str__(self):
        msg = super().__str__()
        if self.data:
            msg += f"\nData: {self.data}"
        return msg


class FileOperationError(SQL2CSVError):
    """
    文件I/O错误

    当文件读写操作失败时抛出

    Attributes:
        file_path: 操作失败的文件路径（可选）

    Example:
        try:
            df.to_csv(file_path)
        except Exception as e:
            raise FileOperationError(
                f"Failed to write CSV file",
                file_path=file_path
            ) from e
    """

    def __init__(self, message, file_path=None):
        super().__init__(message)
        self.file_path = file_path

    def __str__(self):
        msg = super().__str__()
        if self.file_path:
            msg += f"\nFile: {self.file_path}"
        return msg


class DataConversionError(SQL2CSVError):
    """
    数据格式转换错误

    当数据格式转换失败时抛出（例如日期格式转换、列名映射等）

    Example:
        try:
            date_str = datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
        except ValueError as e:
            raise DataConversionError(
                f"Invalid date format: {date}"
            ) from e
    """
    pass
