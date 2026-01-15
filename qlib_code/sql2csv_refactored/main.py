"""
SQL2CSV主入口模块

提供函数式API，用于执行SQL到CSV的数据转换流程
"""

from typing import Optional, Dict, Any
from pathlib import Path

from .config.config_loader import ConfigLoader
from .config.config_validator import ConfigValidator
from .core.orchestrator import DataPipeline
from .models.data_models import ProcessingResult
from .utils.logging_config import setup_logging
from .utils.date_utils import parse_flexible_date
from .exceptions import SQL2CSVError, ConfigurationError


def run_sql2csv(
    market: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    batch_size: Optional[int] = None,
    max_workers: Optional[int] = None,
    config_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    db_config: Optional[Dict[str, Any]] = None,
    log_level: Optional[str] = None,
    **kwargs
) -> ProcessingResult:
    """
    SQL转CSV的主入口函数

    提供灵活的参数覆盖机制，允许通过函数参数覆盖配置文件中的设置

    Args:
        market: 市场代码 (ALL, zz500, hs300等)
        start_date: 开始日期 YYYYMMDD格式 (支持 'today', 'yesterday', None=使用配置)
        end_date: 结束日期 YYYYMMDD格式 (支持 'today', None=今天)
        batch_size: 每批股票数量
        max_workers: 最大并发worker数量
        config_path: sql2csv.yaml路径 (None=使用默认路径)
        output_dir: 覆盖输出目录
        db_config: 覆盖数据库配置字典
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        **kwargs: 其他覆盖参数

    Returns:
        ProcessingResult: 处理结果统计
            - success: 是否成功
            - total_count: 总股票数
            - success_count: 成功处理数
            - failed_count: 失败数
            - duration_seconds: 耗时（秒）
            - errors: 错误列表

    Raises:
        ConfigurationError: 配置加载或验证失败
        SQL2CSVError: 处理过程中的其他错误

    Example:
        # 使用默认配置
        result = run_sql2csv()

        # 覆盖特定参数
        result = run_sql2csv(
            market='zz500',
            start_date='20250101',
            end_date='today',
            batch_size=500
        )

        # 检查结果
        if result.success:
            print(f"Successfully processed {result.success_count} stocks")
        else:
            print(f"Failed: {len(result.errors)} errors")
    """
    try:
        # 1. 加载配置
        config = _load_config(config_path)

        # 2. 应用参数覆盖
        config = _apply_overrides(
            config,
            market=market,
            start_date=start_date,
            end_date=end_date,
            batch_size=batch_size,
            max_workers=max_workers,
            output_dir=output_dir,
            db_config=db_config,
            log_level=log_level,
            **kwargs
        )

        # 3. 验证配置
        ConfigValidator.validate(config)

        # 4. 设置日志
        logger = setup_logging(config.logging)
        logger.info("SQL2CSV process started")
        logger.info(f"Configuration loaded from: {config_path or 'default paths'}")

        # 5. 运行数据处理流程
        pipeline = DataPipeline(config)
        result = pipeline.run()

        # 6. 返回结果
        logger.info(f"SQL2CSV process completed: {result.summary()}")
        return result

    except ConfigurationError as e:
        # 配置错误 - 无法继续
        raise ConfigurationError(f"Configuration error: {e}") from e

    except SQL2CSVError as e:
        # 已知的业务错误
        raise

    except Exception as e:
        # 未预期的错误
        raise SQL2CSVError(f"Unexpected error in SQL2CSV process: {e}") from e


def _load_config(config_path: Optional[str] = None):
    """
    加载配置文件

    Args:
        config_path: 配置文件路径（None=使用默认）

    Returns:
        Config对象

    Raises:
        ConfigurationError: 配置加载失败
    """
    try:
        if config_path:
            # 使用指定的配置文件
            config = ConfigLoader.load(config_path)
        else:
            # 使用默认配置路径
            # 假设配置文件在项目根目录的config文件夹
            project_root = Path(__file__).resolve().parent.parent.parent
            default_config_path = project_root / 'config' / 'sql2csv.yaml'

            if not default_config_path.exists():
                raise ConfigurationError(
                    f"Default config file not found: {default_config_path}"
                )

            config = ConfigLoader.load(str(default_config_path))

        return config

    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {e}") from e


def _apply_overrides(config, **overrides):
    """
    应用参数覆盖到配置对象

    Args:
        config: 配置对象
        **overrides: 覆盖参数

    Returns:
        更新后的配置对象
    """
    # 提取配置
    extraction = config.extraction
    performance = config.performance
    output = config.output
    logging_config = config.logging
    database = config.database

    # 应用 extraction 覆盖
    if overrides.get('market') is not None:
        extraction['market'] = overrides['market']

    if overrides.get('start_date') is not None:
        # 支持灵活的日期输入
        parsed_date = parse_flexible_date(overrides['start_date'])
        if parsed_date:
            extraction['start_date'] = parsed_date

    if overrides.get('end_date') is not None:
        parsed_date = parse_flexible_date(overrides['end_date'])
        if parsed_date:
            extraction['end_date'] = parsed_date

    # 应用 performance 覆盖
    if overrides.get('batch_size') is not None:
        performance['batch_size'] = overrides['batch_size']

    if overrides.get('max_workers') is not None:
        performance['max_workers'] = overrides['max_workers']

    if overrides.get('batch_sleep_seconds') is not None:
        performance['batch_sleep_seconds'] = overrides['batch_sleep_seconds']

    # 应用 output 覆盖
    if overrides.get('output_dir') is not None:
        output['csv_dir'] = overrides['output_dir']

    # 应用 logging 覆盖
    if overrides.get('log_level') is not None:
        logging_config['level'] = overrides['log_level']

    # 应用 database 覆盖
    if overrides.get('db_config') is not None:
        db_override = overrides['db_config']
        for key, value in db_override.items():
            database[key] = value

    # 应用其他通用覆盖（使用点号表示法）
    for key, value in overrides.items():
        if key in ['market', 'start_date', 'end_date', 'batch_size', 'max_workers',
                   'output_dir', 'db_config', 'log_level', 'batch_sleep_seconds']:
            continue  # 已处理

        # 支持点号表示法，如 'extraction.market'
        if '.' in key:
            parts = key.split('.')
            if len(parts) == 2:
                section, field = parts
                section_obj = getattr(config, section, None)
                if section_obj and hasattr(section_obj, '__setitem__'):
                    section_obj[field] = value

    return config


# 向后兼容的别名
sql2csv = run_sql2csv
