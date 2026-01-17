"""
SQL2CSV - 适配层 (Adapter Layer)

这个文件提供向后兼容的接口，内部使用重构后的安全实现。

主要改进:
- 使用参数化查询防止SQL注入
- 改进的错误处理和日志记录
- 更好的并发处理
- 原子文件写入操作

使用方法:
    # 方式1: 使用原有的类接口（向后兼容）
    converter = QlibDataConverter(output_dir='./csv_data')
    converter.process_all_stocks(market='ALL', start_date='20250101', end_date='20250131')

    # 方式2: 直接使用新的函数接口（推荐）
    from qlib_code.sql2csv_refactored import run_sql2csv
    result = run_sql2csv(market='ALL', start_date='20250101', end_date='20250131')
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import date
import yaml

# 添加项目根目录到 Python 路径，支持直接运行此脚本
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 导入重构后的模块
from qlib_code.sql2csv_refactored import run_sql2csv
from config_utils import load_config_with_substitution

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)


class QlibDataConverter:
    """
    向后兼容的适配器类

    这个类保持与原始实现相同的接口，但内部使用重构后的安全实现。

    注意: 这个类主要用于向后兼容。新代码应该直接使用 run_sql2csv() 函数。
    """

    def __init__(self, output_dir, db_config=None):
        """
        初始化转换器

        Args:
            output_dir: CSV输出目录
            db_config: 数据库配置字典（可选）
        """
        self.csv_output_dir = output_dir
        self.db_config = db_config

        # 确保输出目录存在
        os.makedirs(self.csv_output_dir, exist_ok=True)

        log.info(f"QlibDataConverter 初始化完成，输出目录: {output_dir}")
        log.info("注意: 使用重构后的安全实现（防止SQL注入）")

    def get_hfq_data_from_sql(self, code, start_date, end_date):
        """
        从SQL数据库获取复权后数据

        注意: 此方法已弃用，保留仅用于向后兼容。
        新实现在内部使用安全的参数化查询。
        """
        log.warning("get_hfq_data_from_sql 方法已弃用，建议使用 process_stock 方法")
        # 这个方法在新实现中不再直接暴露，因为数据获取逻辑已封装
        # 如果需要，可以通过 process_stock 实现相同功能
        return None

    def get_hfq_data_batch(self, codes, start_date, end_date):
        """
        批量获取复权后数据

        注意: 此方法已弃用，保留仅用于向后兼容。
        新实现使用安全的参数化查询，防止SQL注入。
        """
        log.warning("get_hfq_data_batch 方法已弃用，建议使用 process_all_stocks 方法")
        return None

    def format_for_qlib(self, df, code=None):
        """
        格式化为Qlib需要的格式

        注意: 此方法已弃用，格式转换逻辑已内置到新实现中。
        """
        log.warning("format_for_qlib 方法已弃用，格式转换已自动处理")
        return df

    def process_stock(self, code, start_date='20200101', end_date='20250920'):
        """
        处理单只股票

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYYMMDD格式)
            end_date: 结束日期 (YYYYMMDD格式)

        Returns:
            bool: 处理是否成功
        """
        log.info(f"处理单只股票: {code}")

        try:
            # 调用新的实现 - 传入单个股票代码
            result = run_sql2csv(
                market=[code],  # 传入单个股票代码作为列表
                start_date=start_date,
                end_date=end_date,
                output_dir=self.csv_output_dir,
                db_config=self.db_config,
                log_level='INFO'
            )

            return result.success_count > 0

        except Exception as e:
            log.error(f"处理股票 {code} 失败: {e}")
            return False

    def _save_to_csv(self, df, csv_path):
        """
        保存数据到CSV文件

        注意: 此方法已弃用，文件写入逻辑已内置到新实现中。
        新实现使用原子写入操作，更加安全。
        """
        log.warning("_save_to_csv 方法已弃用，文件写入已自动处理")
        return True

    def get_index_data(self, index_code, start_date='20200101', end_date='20250920'):
        """
        从数据库获取指数数据

        注意: 此方法已弃用，保留仅用于向后兼容。
        """
        log.warning("get_index_data 方法已弃用，建议使用 process_index 方法")
        return None

    def process_index(self, index_code, start_date='20200101', end_date='20250920'):
        """
        处理单个指数数据

        Args:
            index_code: 指数代码
            start_date: 开始日期 (YYYYMMDD格式)
            end_date: 结束日期 (YYYYMMDD格式)

        Returns:
            bool: 处理是否成功
        """
        log.info(f"处理指数: {index_code}")

        try:
            # 调用新的实现
            result = run_sql2csv(
                market=[index_code],  # 传入指数代码
                start_date=start_date,
                end_date=end_date,
                output_dir=self.csv_output_dir,
                db_config=self.db_config,
                log_level='INFO'
            )

            return result.success_count > 0

        except Exception as e:
            log.error(f"处理指数 {index_code} 失败: {e}")
            return False

    def process_all_indices(self, market='ALL', start_date='20200101', end_date='20250920'):
        """
        处理所有指数

        Args:
            market: 市场代码 (ALL, zz500, hs300, sz50, zz1000, zz2000)
            start_date: 开始日期 (YYYYMMDD格式)
            end_date: 结束日期 (YYYYMMDD格式)
        """
        log.info(f"处理指数数据，市场: {market}")

        # 指数代码映射
        mapping = {
            'zz500': ['000905.SH'],
            'hs300': ['000300.SH'],
            'sz50': ['000016.SH'],
            'zz1000': ['000852.SH'],
            'zz2000': ['932000.CSI'],
            'ALL': ['000905.SH', '000300.SH', '000016.SH', '000852.SH', '932000.CSI'],
        }

        if isinstance(market, (list, tuple)):
            index_codes = market
        else:
            index_codes = mapping.get(market, [market])

        for idx in index_codes:
            try:
                if self.process_index(idx, start_date=start_date, end_date=end_date):
                    log.info(f"处理指数 {idx} 成功")
                else:
                    log.error(f"处理指数 {idx} 失败")
            except Exception as e:
                log.exception(f"处理指数 {idx} 失败: {e}")

    def get_all_stocks(self, market='ALL'):
        """
        从数据库获取股票列表

        注意: 此方法已弃用，股票列表获取逻辑已内置到新实现中。
        """
        log.warning("get_all_stocks 方法已弃用，股票列表获取已自���处理")
        return []

    def process_all_stocks(self, market='ALL', start_date='20200101', end_date='20250920', batch_size=10):
        """
        处理全部股票

        Args:
            market: 市场代码 (ALL, zz500, hs300, sz50, zz1000, zz2000)
            start_date: 开始日期 (YYYYMMDD格式)
            end_date: 结束日期 (YYYYMMDD格式)
            batch_size: 批次大小（已弃用，新实现使用配置文件中的值）

        Returns:
            dict: 处理结果统计
        """
        log.info(f"开始处理股票数据，市场: {market}, 日期范围: {start_date} - {end_date}")

        try:
            # 调用新的实现
            result = run_sql2csv(
                market=market,
                start_date=start_date,
                end_date=end_date,
                batch_size=batch_size,  # 传递batch_size参数
                output_dir=self.csv_output_dir,
                db_config=self.db_config,
                log_level='INFO'
            )

            # 输出汇总信息
            log.info(f"处理完成: 成功 {result.success_count} 只，失败 {result.failed_count} 只")
            log.info(f"总耗时: {result.duration_seconds:.2f} 秒")

            if result.errors:
                log.warning(f"发现 {len(result.errors)} 个错误")
                for error in result.errors[:5]:  # 只显示前5个错误
                    log.warning(f"  - {error}")

            return {
                'success_count': result.success_count,
                'failed_count': result.failed_count,
                'total_stocks': result.total_items,
                'duration_seconds': result.duration_seconds,
                'errors': result.errors
            }

        except Exception as e:
            log.error(f"处理股票数据失败: {e}")
            return {
                'success_count': 0,
                'failed_count': 0,
                'total_stocks': 0,
                'duration_seconds': 0,
                'errors': [str(e)]
            }


def main():
    """
    主入口函数 - 保持与原实现相同的接口

    这个函数维护原有的命令行接口和配置加载逻辑，
    但内部使用重构后的安全实现。
    """
    # 获取项目根目录
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # 先读取 paths.yaml 获取基础变量（如 base_dir），用于变量替换
    cfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'paths.yaml'))
    paths_cfg = load_config_with_substitution(cfg_path)

    # 从配置文件读取参数
    sql2csv_cfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'sql2csv.yaml'))
    sql2csv_cfg_raw = yaml.safe_load(open(sql2csv_cfg_path, 'r', encoding='utf-8')) or {}

    # 合并 paths.yaml 的变量到 sql2csv 配置的上下文中，以便替换 ${base_dir} 等变量
    from config_utils import _substitute_string
    merged_context = {**paths_cfg, **sql2csv_cfg_raw}
    sql2csv_cfg = {}
    for key, value in sql2csv_cfg_raw.items():
        if isinstance(value, str) and '${' in value:
            sql2csv_cfg[key] = _substitute_string(value, merged_context)
        else:
            sql2csv_cfg[key] = value

    # 从配置文件读取输出路径
    output_dir = sql2csv_cfg.get('csv_output_dir')
    if not output_dir:
        # 如果配置文件中没有，则从 paths.yaml 读取（向后兼容）
        output_dir = paths_cfg.get('csv_output_dir')
    if not output_dir:
        raise ValueError("未找到 csv_output_dir 配置，请在 config/sql2csv.yaml 或 config/paths.yaml 中设置")

    # 提取数据库配置
    db_config = {
        'db_host': sql2csv_cfg.get('db_host', 'localhost:3306'),
        'db_port': sql2csv_cfg.get('db_port', 3306),
        'db_database': sql2csv_cfg.get('db_database', 'data_prepared_new'),
        'db_user': sql2csv_cfg.get('db_user', 'root'),
        'db_password': sql2csv_cfg.get('db_password', ''),
    }

    # 创建转换器（使用适配器）
    converter = QlibDataConverter(output_dir, db_config=db_config)

    # 读取配置参数
    market = sql2csv_cfg.get('market', 'ALL')
    start_date = sql2csv_cfg.get('start_date', '20150101')
    end_date = sql2csv_cfg.get('end_date')
    batch_size = sql2csv_cfg.get('batch_size', 1000)

    # 如果 end_date 为 None 或空值，使用当前日期
    if end_date is None or end_date == '':
        end_date = date.today().strftime('%Y%m%d')
    else:
        # 确保 end_date 是字符串格式
        end_date = str(end_date)

    # 处理股票数据
    log.info("=" * 60)
    log.info("开始处理股票数据")
    log.info("=" * 60)
    converter.process_all_stocks(market=market, start_date=start_date, end_date=end_date, batch_size=batch_size)

    # 处理指数数据
    log.info("=" * 60)
    log.info("开始处理指数数据")
    log.info("=" * 60)
    converter.process_all_indices(market=market, start_date=start_date, end_date=end_date)

    logging.info("数据获取完成")
    logging.info("开始转换数据格式")

    # 从 sql2csv.yaml 读取 qlib 路径配置，如果没有则从 paths.yaml 读取（向后兼容）
    qlib_workdir = sql2csv_cfg.get('qlib_workdir')
    if not qlib_workdir:
        qlib_workdir = paths_cfg.get('qlib_workdir', './qlib')

    provider_uri = sql2csv_cfg.get('provider_uri')
    if not provider_uri:
        provider_uri = paths_cfg.get('provider_uri', '../qlib_data/qlib_bin')

    # 处理 qlib_workdir：如果是相对路径，转换为相对于项目根目录的绝对路径
    qlib_workdir_raw = Path(qlib_workdir)
    if not qlib_workdir_raw.is_absolute():
        DEFAULT_QLIB_PATH = str((project_root / qlib_workdir_raw).resolve())
    else:
        DEFAULT_QLIB_PATH = str(qlib_workdir_raw)

    DEFAULT_QLIB_DIR = provider_uri
    DEFAULT_FIELDS = "open,close,high,low,volume,factor,money"

    parser = argparse.ArgumentParser(description='Qlib 数据导出工具')
    parser.add_argument('--qlib_path', type=str, default=DEFAULT_QLIB_PATH,
                       help=f'Qlib 安装路径（默认: {DEFAULT_QLIB_PATH}）')

    parser.add_argument('--csv_output_dir', type=str, default=output_dir,)

    parser.add_argument('--qlib_dir', type=str, default=DEFAULT_QLIB_DIR,
                       help=f'Qlib 数据源路径（默认: {DEFAULT_QLIB_DIR}）')

    parser.add_argument('--include_fields', type=str, default=DEFAULT_FIELDS,
                       help=f'包含的字段（默认: {DEFAULT_FIELDS}）')

    args = parser.parse_args()

    # 验证路径
    qlib_scripts_path = Path(args.qlib_path) / "scripts"
    if not qlib_scripts_path.exists():
        logging.error(f"错误：找不到 Qlib scripts 目录: {qlib_scripts_path}")
        sys.exit(1)


    # 构建命令
    dump_script = qlib_scripts_path / "dump_bin.py"

    cmd = [
        sys.executable, str(dump_script),
        "dump_all",
        f'--data_path="{args.csv_output_dir}"',
        f'--qlib_dir="{args.qlib_dir}"',
        f'--include_fields={args.include_fields}'
    ]


    command_str = " ".join(cmd)
    logging.info(f"执行命令: {command_str}")

    # 执行命令
    try:
        os.system(command_str)
        logging.info("数据格式转换完成！")
    except Exception as e:
        logging.error(f"数据格式转换失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
