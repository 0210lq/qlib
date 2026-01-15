"""
日志配置模块

提供统一的日志配置，支持控制台和文件输出，以及日志轮转
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_level='DEBUG',
    console_output=True,
    file_output=True,
    log_file_path=None,
    rotation='daily',
    retention_days=30,
    log_format=None
):
    """
    设置日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL) 或配置字典
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        log_file_path: 日志文件路径（如果为None，使用默认路径）
        rotation: 日志轮转方式 ('daily', 'hourly', 'weekly')
        retention_days: 日志保留天数
        log_format: 日志格式（如果为None，使用默认格式）

    Returns:
        logging.Logger: 配置好的logger对象

    Example:
        logger = setup_logging(
            log_level='DEBUG',
            console_output=True,
            file_output=True,
            log_file_path='logs/sql2csv.log'
        )
        logger.info("Processing started")
    """
    # 如果第一个参数是配置对象（dict或ConfigSection），从中提取参数
    if not isinstance(log_level, str) and hasattr(log_level, 'get'):
        config = log_level
        log_level = config.get('level', 'DEBUG')
        console_output = config.get('console', True)
        file_output = config.get('file', True)
        log_file_path = config.get('file_path', None)
        rotation = config.get('rotation', 'daily')
        retention_days = config.get('retention_days', 30)
        log_format = config.get('format', None)

    # 创建logger
    logger = logging.getLogger('sql2csv')
    logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有的处理器（避免重复添加）
    logger.handlers.clear()

    # 设置日志格式
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # 控制台使用INFO级别，减少输出
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件处理器
    if file_output:
        # 确定日志文件路径
        if log_file_path is None:
            # 默认路径：项目根目录/logs/sql2csv_YYYYMMDD.log
            log_dir = Path(__file__).resolve().parent.parent.parent.parent / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file_path = log_dir / f"sql2csv_{datetime.now().strftime('%Y%m%d')}.log"
        else:
            log_file_path = Path(log_file_path)
            # 替换日期占位符
            if '{date}' in str(log_file_path):
                log_file_path = Path(str(log_file_path).replace(
                    '{date}',
                    datetime.now().strftime('%Y%m%d')
                ))
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 根据轮转方式设置参数
        rotation_params = {
            'daily': {'when': 'midnight', 'interval': 1},
            'hourly': {'when': 'H', 'interval': 1},
            'weekly': {'when': 'W0', 'interval': 1},  # W0 = Monday
        }
        params = rotation_params.get(rotation, rotation_params['daily'])

        # 创建文件处理器（带轮转）
        file_handler = TimedRotatingFileHandler(
            filename=str(log_file_path),
            when=params['when'],
            interval=params['interval'],
            backupCount=retention_days,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # 文件使用DEBUG级别，记录详细信息
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name='sql2csv'):
    """
    获取已配置的logger

    Args:
        name: logger名称

    Returns:
        logging.Logger: logger对象

    Example:
        logger = get_logger()
        logger.debug("Debug message")
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    装饰器：记录函数调用

    Example:
        @log_function_call
        def process_stock(code):
            # function body
            pass
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise
    return wrapper


def log_execution_time(func):
    """
    装饰器：记录函数执行时间

    Example:
        @log_execution_time
        def process_all_stocks():
            # function body
            pass
    """
    import time

    def wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = time.time()
        logger.debug(f"Starting {func.__name__}")

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f} seconds")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f} seconds: {e}")
            raise

    return wrapper
