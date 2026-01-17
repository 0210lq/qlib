"""
CSV文件管理模块

提供CSV文件的高效读写、增量更新和原子写入功能
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from ..exceptions import FileOperationError
from ..utils.logging_config import get_logger


class CSVFileManager:
    """
    CSV文件管理器

    负责CSV文件的读写、增量更新和原子写入操作

    Attributes:
        output_dir: CSV输出目录
        logger: 日志记录器

    Example:
        manager = CSVFileManager('/path/to/csv_data')
        manager.write_csv('000001.SZ', df)
    """

    def __init__(self, output_dir: str):
        """
        初始化CSV文件管理器

        Args:
            output_dir: CSV输出目录路径（支持相对路径，相对于项目根目录）
        """
        output_path = Path(output_dir)
        
        # 如果是相对路径，转换为相对于项目根目录的绝对路径
        if not output_path.is_absolute():
            # 获取项目根目录（config目录的父目录）
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            output_path = (project_root / output_path).resolve()
        
        self.output_dir = output_path
        self.logger = get_logger()

        # 确保输出目录存在
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        """确保输出目录存在"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Output directory ensured: {self.output_dir}")
        except Exception as e:
            raise FileOperationError(
                f"Failed to create output directory: {e}",
                file_path=str(self.output_dir)
            ) from e

    def write_csv(self, code: str, df: pd.DataFrame, use_atomic: bool = True) -> None:
        """
        写入CSV文件

        Args:
            code: 股票或指数代码
            df: 要写入的DataFrame
            use_atomic: 是否使用原子写入

        Raises:
            FileOperationError: 文件写入失败

        Example:
            manager.write_csv('000001.SZ', df)
        """
        if df.empty:
            self.logger.warning(f"Empty DataFrame for {code}, skipping write")
            return

        file_path = self.output_dir / f"{code}.csv"

        try:
            if use_atomic:
                self._atomic_write(file_path, df)
            else:
                df.to_csv(file_path, index=False)

            self.logger.debug(f"Written {len(df)} rows to {file_path}")

        except Exception as e:
            raise FileOperationError(
                f"Failed to write CSV file for {code}: {e}",
                file_path=str(file_path)
            ) from e

    def read_csv(self, code: str) -> Optional[pd.DataFrame]:
        """
        读取CSV文件

        Args:
            code: 股票或指数代码

        Returns:
            DataFrame或None（如果文件不存在）

        Raises:
            FileOperationError: 文件读取失败

        Example:
            df = manager.read_csv('000001.SZ')
        """
        file_path = self.output_dir / f"{code}.csv"

        if not file_path.exists():
            self.logger.debug(f"CSV file not found: {file_path}")
            return None

        try:
            df = pd.read_csv(file_path, parse_dates=['date'])
            self.logger.debug(f"Read {len(df)} rows from {file_path}")
            return df

        except Exception as e:
            raise FileOperationError(
                f"Failed to read CSV file for {code}: {e}",
                file_path=str(file_path)
            ) from e

    def append_data(self, code: str, new_df: pd.DataFrame) -> None:
        """
        追加数据到现有CSV文件（增量更新）

        如果文件不存在，直接写入；如果存在，合并数据并去重

        Args:
            code: 股票或指数代码
            new_df: 要追加的DataFrame

        Raises:
            FileOperationError: 文件操作失败

        Example:
            manager.append_data('000001.SZ', new_df)
        """
        if new_df.empty:
            self.logger.warning(f"Empty DataFrame for {code}, skipping append")
            return

        try:
            # 读取现有数据
            existing_df = self.read_csv(code)

            if existing_df is None or existing_df.empty:
                # 文件不存在或为空，直接写入
                self.write_csv(code, new_df)
            else:
                # 合并数据
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)

                # 去重（保留最新的数据）
                combined_df.drop_duplicates(subset=['date'], keep='last', inplace=True)

                # 按日期排序
                combined_df.sort_values('date', inplace=True)

                # 写入合并后的数据
                self.write_csv(code, combined_df)

                self.logger.debug(
                    f"Appended {len(new_df)} rows to {code}, "
                    f"total {len(combined_df)} rows after merge"
                )

        except Exception as e:
            raise FileOperationError(
                f"Failed to append data for {code}: {e}",
                file_path=str(self.output_dir / f"{code}.csv")
            ) from e

    def _atomic_write(self, file_path: Path, df: pd.DataFrame) -> None:
        """
        原子写入CSV文件

        使用临时文件确保写入操作的原子性，避免写入过程中断导致文件损坏

        Args:
            file_path: 目标文件路径
            df: 要写入的DataFrame

        Raises:
            FileOperationError: 文件写入失败
        """
        temp_path = file_path.with_suffix('.tmp')

        try:
            # 写入临时文件
            df.to_csv(temp_path, index=False)

            # 原子替换（Windows上使用replace，Unix上是原子操作）
            temp_path.replace(file_path)

            self.logger.debug(f"Atomic write completed: {file_path}")

        except Exception as e:
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()

            raise FileOperationError(
                f"Failed to atomic write: {e}",
                file_path=str(file_path)
            ) from e

