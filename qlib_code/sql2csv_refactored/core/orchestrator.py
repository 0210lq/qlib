"""
数据处理流程编排模块

提供完整的数据提取、转换和存储流程的协调和管理
"""

import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .database import DatabaseConnection
from .query_builder import QueryBuilder
from .converter import DataConverter
from .file_manager import CSVFileManager
from ..models.data_models import QueryParams, ProcessingResult
from ..exceptions import SQL2CSVError, DatabaseError, DataConversionError, FileOperationError
from ..utils.logging_config import get_logger


class DataPipeline:
    """
    数据处理流程编排器

    协调整个SQL到CSV的转换流程，包括：
    - 获取股票/指数代码列表
    - 批量查询数据库
    - 数据格式转换
    - CSV文件写入
    - 并发处理和进度跟踪

    Attributes:
        config: 配置对象
        db: 数据库连接管理器
        query_builder: SQL查询构建器
        converter: 数据格式转换器
        file_manager: CSV文件管理器
        logger: 日志记录器

    Example:
        pipeline = DataPipeline(config)
        result = pipeline.run()
        print(f"Processed {result.success_count} stocks successfully")
    """

    def __init__(self, config):
        """
        初始化数据处理流程

        Args:
            config: 配置对象（来自ConfigLoader）
        """
        self.config = config
        self.logger = get_logger()

        # 初始化核心组件
        self.db = DatabaseConnection(
            config.database,
            max_retries=3,
            retry_delay=1.0
        )
        self.query_builder = QueryBuilder(config.schema)
        self.converter = DataConverter(config.output)
        self.file_manager = CSVFileManager(config.output.get('csv_output_dir'))

        self.logger.info("DataPipeline initialized")

    def run(self) -> ProcessingResult:
        """
        执行完整的数据处理流程

        Returns:
            ProcessingResult: 处理结果统计

        Example:
            result = pipeline.run()
        """
        start_time = time.time()
        self.logger.info("=" * 60)
        self.logger.info("Starting SQL2CSV data processing pipeline")
        self.logger.info("=" * 60)

        try:
            # 1. 获取查询参数
            query_params = self._build_query_params()
            self.logger.info(f"Query parameters: market={query_params.market}, "
                           f"date_range={query_params.start_date} to {query_params.end_date}")

            # 2. 获取股票代码列表
            stock_codes = self._get_stock_codes(query_params)
            self.logger.info(f"Found {len(stock_codes)} stocks to process")

            if not stock_codes:
                self.logger.warning("No stocks found to process")
                return ProcessingResult(
                    success=True,
                    total_count=0,
                    success_count=0,
                    failed_count=0,
                    duration_seconds=time.time() - start_time
                )

            # 3. 处理股票数据（批量 + 并发）
            result = self._process_stocks(stock_codes, query_params)

            # 4. 处理指数数据
            if query_params.market != 'ALL':
                self._process_index(query_params)

            # 5. 计算总耗时
            duration = time.time() - start_time
            result.duration_seconds = duration

            # 6. 输出汇总信息
            self._log_summary(result)

            return result

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                total_count=0,
                success_count=0,
                failed_count=0,
                duration_seconds=duration,
                errors=[{'error': str(e), 'type': type(e).__name__}]
            )
        finally:
            # 关闭数据库连接
            self.db.close()

    def _build_query_params(self) -> QueryParams:
        """
        从配置构建查询参数

        Returns:
            QueryParams: 查询参数对象
        """
        extraction = self.config.extraction
        performance = self.config.performance

        # 处理结束日期（None表示今天）
        end_date = extraction.get('end_date')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')

        return QueryParams(
            start_date=extraction.get('start_date'),
            end_date=end_date,
            market=extraction.get('market', 'ALL'),
            batch_size=performance.get('batch_size', 1000)
        )

    def _get_stock_codes(self, query_params: QueryParams) -> List[str]:
        """
        获取要处理的股票代码列表

        Args:
            query_params: 查询参数

        Returns:
            股票代码列表

        Raises:
            DatabaseError: 数据库查询失败
        """
        market = query_params.market

        try:
            # 如果market是列表，直接返回（用于处理指定的股票代码）
            if isinstance(market, (list, tuple)):
                self.logger.info(f"Using provided stock codes: {len(market)} stocks")
                return list(market)

            if market == 'ALL':
                # 获取所有股票
                self.logger.info("Fetching all stock codes from database")
                query, params = self.query_builder.build_all_stocks_query(
                    query_params.start_date,
                    query_params.end_date
                )
                rows = self.db.execute_query_with_retry(query, params)
                codes = [row['code'] for row in rows]

            else:
                # 获取特定市场的成分股
                self.logger.info(f"Fetching component stocks for market: {market}")
                query, params = self.query_builder.build_component_query(market)
                rows = self.db.execute_query_with_retry(query, params)
                codes = [row['code'] for row in rows]

            self.logger.info(f"Retrieved {len(codes)} stock codes")
            return codes

        except Exception as e:
            raise DatabaseError(f"Failed to get stock codes: {e}") from e

    def _process_stocks(self, stock_codes: List[str], query_params: QueryParams) -> ProcessingResult:
        """
        批量处理股票数据（支持并发）

        Args:
            stock_codes: 股票代码列表
            query_params: 查询参数

        Returns:
            ProcessingResult: 处理结果
        """
        total_count = len(stock_codes)
        success_count = 0
        failed_count = 0
        errors = []

        batch_size = query_params.batch_size
        max_workers = self._determine_optimal_workers(total_count)

        self.logger.info(f"Processing {total_count} stocks with batch_size={batch_size}, "
                        f"max_workers={max_workers}")

        # 分批处理
        batches = [stock_codes[i:i + batch_size] for i in range(0, total_count, batch_size)]
        self.logger.info(f"Split into {len(batches)} batches")

        # 使用线程池并发处理批次
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有批次任务
            future_to_batch = {
                executor.submit(self._process_batch, batch, query_params, batch_idx + 1, len(batches)): batch
                for batch_idx, batch in enumerate(batches)
            }

            # 收集结果
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    batch_result = future.result()
                    success_count += batch_result['success_count']
                    failed_count += batch_result['failed_count']
                    errors.extend(batch_result['errors'])

                except Exception as e:
                    self.logger.error(f"Batch processing failed: {e}")
                    failed_count += len(batch)
                    errors.append({
                        'batch': batch,
                        'error': str(e),
                        'type': type(e).__name__
                    })

        return ProcessingResult(
            success=failed_count == 0,
            total_count=total_count,
            success_count=success_count,
            failed_count=failed_count,
            duration_seconds=0,  # Will be set by caller
            errors=errors
        )

    def _process_batch(self, batch_codes: List[str], query_params: QueryParams,
                      batch_num: int, total_batches: int) -> Dict[str, Any]:
        """
        处理一个批次的股票

        Args:
            batch_codes: 批次中的股票代码列表
            query_params: 查询参数
            batch_num: 当前批次号
            total_batches: 总批次数

        Returns:
            批次处理结果字典
        """
        self.logger.info(f"Processing batch {batch_num}/{total_batches} "
                        f"({len(batch_codes)} stocks)")

        success_count = 0
        failed_count = 0
        errors = []

        try:
            # 1. 批量查询数据库
            query, params = self.query_builder.build_stock_query(
                batch_codes,
                query_params.start_date,
                query_params.end_date
            )
            rows = self.db.execute_query_with_retry(query, params)

            # 2. 按股票代码分组
            stock_data_map = {}
            for row in rows:
                code = row['code']
                if code not in stock_data_map:
                    stock_data_map[code] = []
                stock_data_map[code].append(row)

            # 3. 处理每只股票
            for code in batch_codes:
                try:
                    if code not in stock_data_map or not stock_data_map[code]:
                        self.logger.warning(f"No data found for stock: {code}")
                        failed_count += 1
                        errors.append({'code': code, 'error': 'No data found'})
                        continue

                    # 转换为DataFrame
                    df = self.converter.convert_to_dataframe(stock_data_map[code], 'stock')

                    # 写入CSV文件
                    self.file_manager.write_csv(code, df)

                    success_count += 1
                    self.logger.debug(f"Successfully processed stock: {code} ({len(df)} rows)")

                except (DataConversionError, FileOperationError) as e:
                    self.logger.error(f"Failed to process stock {code}: {e}")
                    failed_count += 1
                    errors.append({'code': code, 'error': str(e), 'type': type(e).__name__})

            self.logger.info(f"Batch {batch_num}/{total_batches} completed: "
                           f"{success_count} success, {failed_count} failed")

            # 批次间短暂休眠，避免数据库压力过大
            batch_sleep = self.config.performance.get('batch_sleep_seconds', 0.1)
            if batch_num < total_batches:
                time.sleep(batch_sleep)

        except DatabaseError as e:
            self.logger.error(f"Database error in batch {batch_num}: {e}")
            failed_count = len(batch_codes)
            errors.append({'batch': batch_codes, 'error': str(e), 'type': 'DatabaseError'})

        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors
        }

    def _process_index(self, query_params: QueryParams) -> None:
        """
        处理指数数据

        Args:
            query_params: 查询参数
        """
        market = query_params.market

        # 如果 market 是列表或元组，跳过指数处理（自定义股票列表不需要指数）
        if isinstance(market, (list, tuple)):
            self.logger.info("Skipping index processing for custom stock list")
            return

        markets_config = self.config.markets

        if market not in markets_config:
            self.logger.warning(f"Market {market} not found in configuration")
            return

        market_info = markets_config[market]
        index_code = market_info.get('index_code')

        if not index_code:
            self.logger.warning(f"No index_code configured for market: {market}")
            return

        try:
            self.logger.info(f"Processing index: {index_code} for market: {market}")

            # 查询指数数据
            query, params = self.query_builder.build_index_query(
                [index_code],
                query_params.start_date,
                query_params.end_date
            )
            rows = self.db.execute_query_with_retry(query, params)

            if not rows:
                self.logger.warning(f"No data found for index: {index_code}")
                return

            # 转换为DataFrame
            df = self.converter.convert_to_dataframe(rows, 'index')

            # 写入CSV文件
            self.file_manager.write_csv(index_code, df)

            self.logger.info(f"Successfully processed index: {index_code} ({len(df)} rows)")

        except Exception as e:
            self.logger.error(f"Failed to process index {index_code}: {e}")

    def _determine_optimal_workers(self, total_items: int) -> int:
        """
        根据工作负载确定最优worker数量

        Args:
            total_items: 总任务数量

        Returns:
            最优worker数量
        """
        max_workers = self.config.performance.get('max_workers', 8)

        # worker数量不超过任务数量
        optimal = min(max_workers, total_items)

        # 小批次使用更少worker以减少开销
        if total_items < 100:
            optimal = min(4, optimal)

        return max(1, optimal)

    def _log_summary(self, result: ProcessingResult) -> None:
        """
        输出处理结果汇总

        Args:
            result: 处理结果
        """
        self.logger.info("=" * 60)
        self.logger.info("Processing Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"Total stocks: {result.total_count}")
        self.logger.info(f"Success: {result.success_count}")
        self.logger.info(f"Failed: {result.failed_count}")
        self.logger.info(f"Success rate: {result.get_success_rate():.2f}%")
        self.logger.info(f"Duration: {result.duration_seconds:.2f} seconds")

        if result.errors:
            self.logger.warning(f"Encountered {len(result.errors)} errors")
            # 只显示前10个错误
            for i, error in enumerate(result.errors[:10]):
                self.logger.warning(f"  Error {i+1}: {error}")
            if len(result.errors) > 10:
                self.logger.warning(f"  ... and {len(result.errors) - 10} more errors")

        self.logger.info("=" * 60)
