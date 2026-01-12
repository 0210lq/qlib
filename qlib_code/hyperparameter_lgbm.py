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


warnings.simplefilter("ignore", category=FutureWarning)
warnings.filterwarnings("ignore")
import logging
log = logging.getLogger(__name__)

def objective(trial, dataset):
    task = {
        "model": {
            "class": "LGBModel",
            "module_path": "qlib.contrib.model.gbdt",
            "kwargs": {
                "loss": "mse",
                "colsample_bytree": trial.suggest_uniform("colsample_bytree", 0.5, 1),
                "learning_rate": trial.suggest_uniform("learning_rate", 0, 1),
                "subsample": trial.suggest_uniform("subsample", 0, 1),
                "lambda_l1": trial.suggest_loguniform("lambda_l1", 1e-8, 1e4),
                "lambda_l2": trial.suggest_loguniform("lambda_l2", 1e-8, 1e4),
                "max_depth": 10,
                "num_leaves": trial.suggest_int("num_leaves", 1, 1024),
                "feature_fraction": trial.suggest_uniform("feature_fraction", 0.4, 1.0),
                "bagging_fraction": trial.suggest_uniform("bagging_fraction", 0.4, 1.0),
                "bagging_freq": trial.suggest_int("bagging_freq", 1, 7),
                "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 1, 50),
                "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
            },
        },
    }
    evals_result = dict()
    model = init_instance_by_config(task["model"])
    model.fit(dataset, evals_result=evals_result)
  
    return min(evals_result["valid"]["l2"])


def run_hyperparameter_optimization_auto():
    """
    每天自动更新的超参数优化函数
    自动计算训练/验证/测试日期范围，进行超参数优化并保存结果到数据库
    """
    from config_utils import load_config_with_substitution
    from time_utils import last_workday_auto, last_workday_calculate

    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'paths.yaml'))
    cfg = load_config_with_substitution(config_path)
    provider_uri = cfg['provider_uri']

    # 减少并行工作进程数以降低内存使用
    # 设置为1表示不使用并行处理，适合内存较小的环境
    os.environ['QLIB_NUM_WORKERS'] = '1'
    os.environ['NUMEXPR_MAX_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'

    qlib.init(provider_uri=provider_uri, region="cn", kernels=1)

    global_tools = cfg["global_tools"]
    custom_path = os.getenv(global_tools)
    sys.path.append(custom_path)

    last_workday = last_workday_auto()

    test_end = str(last_workday)
    last_workday1 = str(last_workday_calculate(test_end))
    last_workday2 = str(last_workday_calculate(last_workday1))
    test_start = str(last_workday_calculate(last_workday2))
    valid_end = test_start
    valid_start = str(last_workday_calculate(valid_end))
    # 注意: 训练数据范围较大会消耗大量内存
    # 如果遇到内存错误，可以缩短 train_start 日期（例如改为 "2024-01-01"）
    train_start = "2023-01-01"
    train_end = str(last_workday_calculate(valid_start))

    custom_dataset_config = {
        "class": "DatasetH",
        "module_path": "qlib.data.dataset",
        "kwargs": {
            "handler": {
                "class": "Alpha158",
                "module_path": "qlib.contrib.data.handler",
                "kwargs": {
                    "start_time": train_start,
                    "end_time": test_end,
                    "instruments": "all",
                },
            },
            "segments": {
                "train": (train_start, train_end),
                "valid": (valid_start, valid_end),
                "test": (test_start, test_end),
            },
        },
    }
    dataset = init_instance_by_config(custom_dataset_config)

    study = optuna.create_study(study_name="LGBM_158", storage="sqlite:///db1.sqlite3", load_if_exists=True, direction="minimize")

    # R.start(experiment_name="lgbm_optuna", recorder_name="run_1")
    # 可以通过调整n_trials的数量，去控制模型训练次数
    study.optimize(lambda trial: objective(trial, dataset), n_trials=2, n_jobs=1)


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
    from config_utils import load_config_with_substitution
    from time_utils import last_workday_calculate

    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'paths.yaml'))
    cfg = load_config_with_substitution(config_path)
    provider_uri = cfg['provider_uri']

    # 减少并行工作进程数以降低内存使用
    os.environ['QLIB_NUM_WORKERS'] = '1'
    os.environ['NUMEXPR_MAX_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'

    qlib.init(provider_uri=provider_uri, region="cn", kernels=1)

    global_tools = cfg["global_tools"]
    custom_path = os.getenv(global_tools)
    sys.path.append(custom_path)

    last_workday = last_workday_calculate(today)

    test_end = str(last_workday)
    last_workday1 = str(last_workday_calculate(test_end))
    last_workday2 = str(last_workday_calculate(last_workday1))
    test_start = str(last_workday_calculate(last_workday2))
    valid_end = test_start
    valid_start = str(last_workday_calculate(valid_end))
    train_end = str(last_workday_calculate(valid_start))

    custom_dataset_config = {
        "class": "DatasetH",
        "module_path": "qlib.data.dataset",
        "kwargs": {
            "handler": {
                "class": "Alpha158",
                "module_path": "qlib.contrib.data.handler",
                "kwargs": {
                    "start_time": train_start,
                    "end_time": test_end,
                    "instruments": "all",
                },
            },
            "segments": {
                "train": (train_start, train_end),
                "valid": (valid_start, valid_end),
                "test": (test_start, test_end),
            },
        },
    }
    dataset = init_instance_by_config(custom_dataset_config)

    study = optuna.create_study(study_name="LGBM_158", storage="sqlite:///db1.sqlite3", load_if_exists=True, direction="minimize")

    # 可以通过调整n_trials的数量，去控制模型训练次数
    study.optimize(lambda trial: objective(trial, dataset), n_trials=2, n_jobs=1)


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
    # 默认执行自动更新函数
    run_hyperparameter_optimization_auto()