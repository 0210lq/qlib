import os
import qlib
import optuna
from qlib.constant import REG_CN
from qlib.utils import init_instance_by_config
from qlib.workflow.exp import Experiment
from qlib.tests.data import GetData
from qlib.workflow import R
import warnings
import yaml
import numpy as np
import sys
import datetime
from sqlalchemy import create_engine, text
import json
from config_utils import load_config_with_substitution
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'paths.yaml'))
cfg = load_config_with_substitution(config_path)
provider_uri = cfg['provider_uri']
global_tools = cfg["global_tools"]
custom_path = os.getenv(global_tools)
if custom_path and custom_path not in sys.path:
    sys.path.append(custom_path)
    from time_utils import last_workday_auto, last_workday_calculate

# 加载超参数优化配置
frequent_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'hyperparameter_frequent_config.yaml'))
with open(frequent_config_path, 'r', encoding='utf-8') as f:
    FREQUENT_CFG = yaml.safe_load(f)

static_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'hyperparameter_static_config.yaml'))
with open(static_config_path, 'r', encoding='utf-8') as f:
    STATIC_CFG = yaml.safe_load(f)

warnings.simplefilter("ignore", category=FutureWarning)
warnings.filterwarnings("ignore")
import logging
log = logging.getLogger(__name__)

def objective(trial, dataset):
    """
    Optuna 优化的目标函数
    从配置文件读取模型参数和搜索空间
    """
    # 从配置文件读取模型基础配置
    model_cfg = STATIC_CFG['model']
    param_space = STATIC_CFG['parameter_search_space']

    # 构建模型参数，根据配置文件动态生成
    kwargs = dict(model_cfg['kwargs'])

    # 遍历参数搜索空间，动态调用 trial.suggest_* 方法
    for param_name, param_config in param_space.items():
        if param_config['type'] == 'uniform':
            kwargs[param_name] = trial.suggest_uniform(param_name, param_config['low'], param_config['high'])
        elif param_config['type'] == 'loguniform':
            kwargs[param_name] = trial.suggest_loguniform(param_name, param_config['low'], param_config['high'])
        elif param_config['type'] == 'int':
            kwargs[param_name] = trial.suggest_int(param_name, param_config['low'], param_config['high'])

    task = {
        "model": {
            "class": model_cfg['class'],
            "module_path": model_cfg['module_path'],
            "kwargs": kwargs,
        },
    }
    evals_result = dict()
    model = init_instance_by_config(task["model"])
    model.fit(dataset, evals_result=evals_result)

    return min(evals_result["valid"]["l2"])


def _ensure_qlib_initialized():
    """
    确保 qlib 只初始化一次
    返回配置对象和自定义工具路径
    """
    from config_utils import load_config_with_substitution

    # 检查 qlib 是否已经初始化
    if not hasattr(qlib, '_initialized') or not qlib._initialized:
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'paths.yaml'))
        cfg = load_config_with_substitution(config_path)
        provider_uri = cfg['provider_uri']

        # 从配置文件读取环境变量设置
        env_cfg = STATIC_CFG['environment']
        for key, value in env_cfg.items():
            os.environ[key] = value

        qlib.init(provider_uri=provider_uri, region="cn", kernels=1)

        global_tools = cfg["global_tools"]
        custom_path = os.getenv(global_tools)
        if custom_path and custom_path not in sys.path:
            sys.path.append(custom_path)
            from time_utils import last_workday_auto, last_workday_calculate
    else:
        # 如果已经初始化，重新加载配置
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'paths.yaml'))
        cfg = load_config_with_substitution(config_path)

    return cfg


def _build_dataset_config(train_start, train_end, valid_start, valid_end, test_start, test_end):
    """
    根据配置文件和日期范围构建数据集配置
    """
    dataset_cfg = STATIC_CFG['dataset']
    handler_cfg = dataset_cfg['handler']

    return {
        "class": dataset_cfg['class'],
        "module_path": dataset_cfg['module_path'],
        "kwargs": {
            "handler": {
                "class": handler_cfg['class'],
                "module_path": handler_cfg['module_path'],
                "kwargs": {
                    "start_time": train_start,
                    "end_time": test_end,
                    "instruments": handler_cfg['instruments'],
                },
            },
            "segments": {
                "train": (train_start, train_end),
                "valid": (valid_start, valid_end),
                "test": (test_start, test_end),
            },
        },
    }


def _create_study(study_name):
    """
    根据配置文件创建 Optuna study
    """
    optuna_cfg = FREQUENT_CFG['optuna']
    return optuna.create_study(
        study_name=study_name,
        storage=optuna_cfg['storage'],
        load_if_exists=optuna_cfg['load_if_exists'],
        direction=optuna_cfg['direction']
    )


def run_hyperparameter_optimization_auto():
    """
    每天自动更新的超参数优化函数
    自动计算训练/验证/测试日期范围，进行超参数优化并保存结果到数据库
    """
    from time_utils import last_workday_auto, last_workday_calculate

    cfg = _ensure_qlib_initialized()

    # 从配置文件读取时间配置
    time_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'hyperparameter_time_config.yaml'))
    with open(time_config_path, 'r', encoding='utf-8') as f:
        time_cfg = yaml.safe_load(f)

    # 读取 train_start
    train_start = time_cfg['auto_optimization']['train_start']

    last_workday = last_workday_auto()

    test_end = str(last_workday)
    last_workday1 = str(last_workday_calculate(test_end))
    last_workday2 = str(last_workday_calculate(last_workday1))
    test_start = str(last_workday_calculate(last_workday2))
    valid_end = test_start
    valid_start = str(last_workday_calculate(valid_end))
    # 注意: 训练数据范围较大会消耗大量内存
    # 如果遇到内存错误，可以在配置文件中修改 train_start 日期
    train_end = str(last_workday_calculate(valid_start))

    # 使用辅助函数构建数据集配置
    custom_dataset_config = _build_dataset_config(train_start, train_end, valid_start, valid_end, test_start, test_end)
    dataset = init_instance_by_config(custom_dataset_config)

    # 使用辅助函数创建 study
    optuna_cfg = FREQUENT_CFG['optuna']
    study = _create_study(optuna_cfg['study_name_auto'])

    # R.start(experiment_name="lgbm_optuna", recorder_name="run_1")
    # 可以通过调整n_trials的数量，去控制模型训练次数
    study.optimize(lambda trial: objective(trial, dataset), n_trials=optuna_cfg['n_trials'], n_jobs=optuna_cfg['n_jobs'])


    if len(study.trials) > 0 and getattr(study, "best_trial", None) is not None:
        print("最佳超参数:")
        print(study.best_params)
    else:
        print("没有成功的试验。")

    db_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'db.yaml'))
    with open(db_config_path, 'r', encoding='utf-8') as f:
        db_cfg = yaml.safe_load(f) or {}
    try:
        db_url = f"mysql+pymysql://{db_cfg['user2']}:{db_cfg['password']}@{db_cfg['host3']}:{db_cfg['port']}/{db_cfg['database4']}"
        engine = create_engine(db_url)
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        engine = None
    # Save best params to database if available
    try:
        if engine is not None:
            table_name = db_cfg['table_name3']
            with engine.begin() as conn:
                # 获取最佳参数
                if len(study.trials) > 0 and getattr(study, "best_trial", None) is not None:
                    best_params = study.best_params
                    study_name = getattr(study, 'study_name', None)

                    # 创建表（如果不存在）
                    columns_def = []
                    columns_def.append("trial_num INT")
                    columns_def.append("study_name VARCHAR(255)")
                    # 根据参数类型定义列
                    for key, value in best_params.items():
                        if isinstance(value, (int, np.integer)):
                            col_def = f"{key} INT"
                        elif isinstance(value, float):
                            col_def = f"{key} DOUBLE"
                        elif isinstance(value, bool):
                            col_def = f"{key} BOOLEAN"
                        else:
                            col_def = f"{key} TEXT"
                        columns_def.append(col_def)

                    columns_def.append("train_start VARCHAR(20)")
                    columns_def.append("train_end VARCHAR(20)")

                    columns_def.append("PRIMARY KEY (train_start, train_end)")
                    columns_def.append("update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                    create_table_sql = f"""
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            {', '.join(columns_def)}
                        ) CHARACTER SET = utf8mb4
                    """
                    conn.execute(text(create_table_sql))
                    trial_num = getattr(study.best_trial, 'number', None)


                    columns = ["train_start", "train_end", "trial_num", "study_name"] + list(best_params.keys())
                    placeholders = ":" + ", :".join(columns)

                    values = {"train_start": str(train_start), "train_end": str(train_end), "trial_num": int(trial_num) if trial_num is not None else None, "study_name": study_name}
                    values.update(best_params)

                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"


                    update_cols = [c for c in columns if c not in ('train_start', 'train_end')]
                    if update_cols:
                        update_clause = ", ".join([f"{c}=VALUES({c})" for c in update_cols]) + ", update_time = CURRENT_TIMESTAMP"
                        insert_sql = insert_sql + " ON DUPLICATE KEY UPDATE " + update_clause

                    conn.execute(text(insert_sql), values)
                    print(f"最佳超参数已保存到数据库")
                else:
                    print("没有成功的试验; 未保存到数据库。")
        else:
            print("无法获取数据库引擎; 跳过保存最佳参数。")
    except Exception as e:
        print(f"导入数据库失败: {e}")


def run_hyperparameter_optimization_manual(train_start, today):
    """
    手动指定日期范围的超参数优化函数

    参数:
        train_start: 训练开始日期，格式如 "2023-01-01"
        today: 今天的日期，格式如 "2024-12-31"
    """
    # 确保 qlib 初始化
    _ensure_qlib_initialized()

    # 调用核心优化逻辑
    _run_optimization_core(train_start, today)


def run_hyperparameter_optimization_manual_dates(train_start=None, train_end=None,
                                                   valid_start=None, valid_end=None,
                                                   test_start=None, test_end=None):
    """
    完全手动指定所有日期的超参数优化函数
    如果不提供参数，将从配置文件中读取

    参数:
        train_start: 训练开始日期，格式如 "2023-01-01"，默认从配置文件读取
        train_end: 训练结束日期，格式如 "2025-12-31"，默认从配置文件读取
        valid_start: 验证开始日期，格式如 "2026-01-01"，默认从配置文件读取
        valid_end: 验证结束日期，格式如 "2026-01-15"，默认从配置文件读取
        test_start: 测试开始日期，格式如 "2026-01-16"，默认从配置文件读取
        test_end: 测试结束日期，格式如 "2026-01-31"，默认从配置文件读取
    """
    # 确保 qlib 初始化
    _ensure_qlib_initialized()

    # 从配置文件读取日期配置（如果参数未提供）
    if any(param is None for param in [train_start, train_end, valid_start, valid_end, test_start, test_end]):
        time_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'hyperparameter_time_config.yaml'))
        with open(time_config_path, 'r', encoding='utf-8') as f:
            time_cfg = yaml.safe_load(f)

        manual_cfg = time_cfg['manual_dates_optimization']
        if train_start is None:
            train_start = manual_cfg['train_start']
        if train_end is None:
            train_end = manual_cfg['train_end']
        if valid_start is None:
            valid_start = manual_cfg['valid_start']
        if valid_end is None:
            valid_end = manual_cfg['valid_end']
        if test_start is None:
            test_start = manual_cfg['test_start']
        if test_end is None:
            test_end = manual_cfg['test_end']

    # 调用核心优化逻辑
    _run_optimization_with_dates(train_start, train_end, valid_start, valid_end, test_start, test_end)


def history_hyperparameter_optimization(start_date=None, end_date=None, train_start=None):
    """
    批量处理历史日期范围内的超参数优化
    如果不提供参数，将从配置文件中读取

    参数:
        start_date: 开始日期，格式如 "2026-01-05"，默认从配置文件读取
        end_date: 结束日期，格式如 "2026-01-06"，默认从配置文件读取
        train_start: 训练开始日期，默认从配置文件读取
    """
    from datetime import datetime, timedelta

    # 确保 qlib 只初始化一次
    _ensure_qlib_initialized()

    # 从配置文件读取时间配置（如果参数未提供）
    if start_date is None or end_date is None or train_start is None:
        time_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'hyperparameter_time_config.yaml'))
        with open(time_config_path, 'r', encoding='utf-8') as f:
            time_cfg = yaml.safe_load(f)

        if start_date is None:
            start_date = time_cfg['history_optimization']['start_date']
        if end_date is None:
            end_date = time_cfg['history_optimization']['end_date']
        if train_start is None:
            train_start = time_cfg['history_optimization']['train_start']

    # 解析日期
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # 遍历日期范围
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        print(f"\n{'='*60}")
        print(f"处理日期: {date_str}")
        print(f"{'='*60}\n")

        try:
            # 调用手动优化函数，但不重新初始化 qlib
            _run_optimization_core(train_start, date_str)
        except Exception as e:
            print(f"处理日期 {date_str} 时出错: {e}")
            import traceback
            traceback.print_exc()

        current += timedelta(days=1)


def _run_optimization_core(train_start, today):
    """
    超参数优化的核心逻辑（不包含 qlib 初始化）
    用于被 history_hyperparameter_optimization 调用
    """
    from time_utils import last_workday_calculate

    last_workday = last_workday_calculate(today)

    test_end = str(last_workday)
    last_workday1 = str(last_workday_calculate(test_end))
    last_workday2 = str(last_workday_calculate(last_workday1))
    test_start = str(last_workday_calculate(last_workday2))
    valid_end = test_start
    valid_start = str(last_workday_calculate(valid_end))
    train_end = str(last_workday_calculate(valid_start))

    _run_optimization_with_dates(train_start, train_end, valid_start, valid_end, test_start, test_end)


def _run_optimization_with_dates(train_start, train_end, valid_start, valid_end, test_start, test_end):
    """
    使用指定日期进行超参数优化的核心逻辑（不包含 qlib 初始化）

    参数:
        train_start: 训练开始日期
        train_end: 训练结束日期
        valid_start: 验证开始日期
        valid_end: 验证结束日期
        test_start: 测试开始日期
        test_end: 测试结束日期
    """
    # 使用辅助函数构建数据集配置
    custom_dataset_config = _build_dataset_config(train_start, train_end, valid_start, valid_end, test_start, test_end)
    dataset = init_instance_by_config(custom_dataset_config)

    # 使用辅助函数创建 study
    optuna_cfg = FREQUENT_CFG['optuna']
    study = _create_study(optuna_cfg['study_name_manual'])

    # 可以通过调整n_trials的数量，去控制模型训练次数
    study.optimize(lambda trial: objective(trial, dataset), n_trials=optuna_cfg['n_trials'], n_jobs=optuna_cfg['n_jobs'])


    if len(study.trials) > 0 and getattr(study, "best_trial", None) is not None:
        print("最佳超参数:")
        print(study.best_params)
    else:
        print("没有成功的试验。")

    db_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'db.yaml'))
    with open(db_config_path, 'r', encoding='utf-8') as f:
        db_cfg = yaml.safe_load(f) or {}
    try:
        db_url = f"mysql+pymysql://{db_cfg['user2']}:{db_cfg['password']}@{db_cfg['host3']}:{db_cfg['port']}/{db_cfg['database4']}"
        engine = create_engine(db_url)
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        engine = None

    try:
        if engine is not None:
            table_name = db_cfg['table_name3']
            with engine.begin() as conn:
                if len(study.trials) > 0 and getattr(study, "best_trial", None) is not None:
                    best_params = study.best_params
                    study_name = getattr(study, 'study_name', None)

                    # 创建表（如果不存在）
                    columns_def = []
                    columns_def.append("trial_num INT")
                    columns_def.append("study_name VARCHAR(255)")
                    for key, value in best_params.items():
                        if isinstance(value, (int, np.integer)):
                            col_def = f"{key} INT"
                        elif isinstance(value, float):
                            col_def = f"{key} DOUBLE"
                        elif isinstance(value, bool):
                            col_def = f"{key} BOOLEAN"
                        else:
                            col_def = f"{key} TEXT"
                        columns_def.append(col_def)

                    columns_def.append("train_start VARCHAR(20)")
                    columns_def.append("train_end VARCHAR(20)")
                    columns_def.append("PRIMARY KEY (train_start, train_end)")
                    columns_def.append("update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                    create_table_sql = f"""
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            {', '.join(columns_def)}
                        ) CHARACTER SET = utf8mb4
                    """
                    conn.execute(text(create_table_sql))
                    trial_num = getattr(study.best_trial, 'number', None)

                    columns = ["train_start", "train_end", "trial_num", "study_name"] + list(best_params.keys())
                    placeholders = ":" + ", :".join(columns)

                    values = {"train_start": str(train_start), "train_end": str(train_end), "trial_num": int(trial_num) if trial_num is not None else None, "study_name": study_name}
                    values.update(best_params)

                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

                    update_cols = [c for c in columns if c not in ('train_start', 'train_end')]
                    if update_cols:
                        update_clause = ", ".join([f"{c}=VALUES({c})" for c in update_cols]) + ", update_time = CURRENT_TIMESTAMP"
                        insert_sql = insert_sql + " ON DUPLICATE KEY UPDATE " + update_clause

                    conn.execute(text(insert_sql), values)
                    print(f"最佳超参数已保存到数据库")
                else:
                    print("没有成功的试验; 未保存到数据库。")
        else:
            print("无法获取数据库引擎; 跳过保存最佳参数。")
    except Exception as e:
        print(f"导入数据库失败: {e}")


if __name__ == "__main__":
    # 模式1: 自动优化模式（每天自动更新，从配置文件读取 train_start）
    run_hyperparameter_optimization_auto()

    # 模式2: 历史批量优化模式（从配置文件读取参数）
    # history_hyperparameter_optimization()
    # 或者手动指定参数：
    # history_hyperparameter_optimization(start_date='2026-01-05', end_date='2026-01-06', train_start="2025-01-01")

    # 模式3: 手动日期模式（从配置文件读取所有日期）
    # run_hyperparameter_optimization_manual_dates()
    # 或者手动指定所有日期：
    # run_hyperparameter_optimization_manual_dates(
    #     train_start="2023-01-01",
    #     train_end="2025-12-31",
    #     valid_start="2026-01-01",
    #     valid_end="2026-01-15",
    #     test_start="2026-01-16",
    #     test_end="2026-01-31"
    # )