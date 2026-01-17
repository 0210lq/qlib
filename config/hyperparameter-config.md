# 超参数优化配置说明

本文档说明超参数优化相关的配置文件的使用方法和参数含义。

## 配置文件概述

超参数优化的配置文件按照使用频率划分为两个文件：

1. **hyperparameter_frequent_config.yaml** - 经常修改的配置
2. **hyperparameter_static_config.yaml** - 很少修改的配置

## 1. 经常修改的配置 (hyperparameter_frequent_config.yaml)

这个配置文件包含您在日常使用中可能经常调整的参数。

### 配置参数说明

#### Optuna 配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `study_name_auto` | string | "LGBM_158_auto" | 自动优化模式的 study 名称 |
| `study_name_manual` | string | "LGBM_158_manual" | 手动优化模式的 study 名称 |
| `storage` | string | "sqlite:///db1.sqlite3" | Optuna 数据库存储路径 |
| `direction` | string | "minimize" | 优化方向，可选值：`minimize`（最小化）或 `maximize`（最大化） |
| `n_trials` | int | 2 | 每次优化的试验次数（控制模型训练次数） |
| `n_jobs` | int | 1 | 并行作业数（建议设为1以降低内存使用） |
| `load_if_exists` | bool | true | 是否加载已存在的 study |

### 使用场景

- 调整训练次数：修改 `n_trials` 参数
- 切换优化实验：修改 `study_name_auto` 或 `study_name_manual`
- 更改存储位置：修改 `storage` 参数

## 2. 很少修改的配置 (hyperparameter_static_config.yaml)

这个配置文件包含在项目初始化后很少改动的参数。

### 配置参数说明

#### 环境变量配置

用于控制内存和性能的环境变量：

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `QLIB_NUM_WORKERS` | string | '1' | Qlib 工作进程数（设为1可降低内存使用） |
| `NUMEXPR_MAX_THREADS` | string | '1' | 数值表达式最大线程数 |
| `OMP_NUM_THREADS` | string | '1' | OpenMP 线程数 |
| `MKL_NUM_THREADS` | string | '1' | MKL 线程数 |

#### 模型配置

基础模型配置：

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `class` | string | "LGBModel" | 模型类名 |
| `module_path` | string | "qlib.contrib.model.gbdt" | 模型模块路径 |
| `kwargs.loss` | string | "mse" | 损失函数 |
| `kwargs.max_depth` | int | 10 | 树的最大深度 |

#### 参数搜索空间配置

定义 Optuna 优化的参数范围。每个参数包含以下字段：

- `type`: 参数类型，可选值：
  - `uniform`: 均匀分布
  - `loguniform`: 对数均匀分布
  - `int`: 整数范围
- `low`: 最小值
- `high`: 最大值

支持的参数包括：

| 参数名 | 类型 | 范围 | 说明 |
|--------|------|------|------|
| `colsample_bytree` | uniform | 0.5 - 1.0 | 列采样比例 |
| `learning_rate` | uniform | 0.0 - 1.0 | 学习率 |
| `subsample` | uniform | 0.0 - 1.0 | 子样本比例 |
| `lambda_l1` | loguniform | 1e-8 - 1e4 | L1 正则化参数 |
| `lambda_l2` | loguniform | 1e-8 - 1e4 | L2 正则化参数 |
| `num_leaves` | int | 1 - 1024 | 叶子节点数量 |
| `feature_fraction` | uniform | 0.4 - 1.0 | 特征采样比例 |
| `bagging_fraction` | uniform | 0.4 - 1.0 | Bagging 采样比例 |
| `bagging_freq` | int | 1 - 7 | Bagging 频率 |
| `min_data_in_leaf` | int | 1 - 50 | 叶子节点最小数据量 |
| `min_child_samples` | int | 5 - 100 | 子节点最小样本数 |

#### 数据集配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `class` | string | "DatasetH" | 数据集类名 |
| `module_path` | string | "qlib.data.dataset" | 数据集模块路径 |
| `handler.class` | string | "Alpha158" | 特征处理器类名 |
| `handler.module_path` | string | "qlib.contrib.data.handler" | 特征处理器模块路径 |
| `handler.instruments` | string | "all" | 股票范围 |

### 使用场景

- 调整参数搜索范围：修改 `parameter_search_space` 中的参数范围
- 更换特征处理器：修改 `handler.class`
- 调整内存使用：修改 `environment` 中的线程数配置
- 更换模型：修改 `model.class` 和 `model.module_path`

## 配置文件使用流程

### 1. 初始化配置

```bash
# 复制示例文件
cp config/hyperparameter_frequent_config.example.yaml config/hyperparameter_frequent_config.yaml
cp config/hyperparameter_static_config.example.yaml config/hyperparameter_static_config.yaml
```

### 2. 修改配置

根据您的需求修改配置文件：

- 经常调整的参数（如 `n_trials`）在 `hyperparameter_frequent_config.yaml` 中修改
- 很少调整的参数（如参数搜索空间）在 `hyperparameter_static_config.yaml` 中修改

### 3. 运行优化

修改配置后，直接运行超参数优化脚本即可：

```bash
python qlib_code/hyperparameter_lgbm.py
```

## 高级配置示例

### 示例 1：增加训练次数

修改 `hyperparameter_frequent_config.yaml`：

```yaml
optuna:
  n_trials: 50  # 从 2 改为 50
```

### 示例 2：缩小学习率搜索范围

修改 `hyperparameter_static_config.yaml`：

```yaml
parameter_search_space:
  learning_rate:
    type: "uniform"
    low: 0.01    # 从 0.0 改为 0.01
    high: 0.1    # 从 1.0 改为 0.1
```

### 示例 3：添加新的参数到搜索空间

修改 `hyperparameter_static_config.yaml`：

```yaml
parameter_search_space:
  # ... 现有参数 ...

  # 添加新参数
  min_split_gain:
    type: "uniform"
    low: 0.0
    high: 1.0
```

### 示例 4：增加并行作业数（需要更多内存）

修改 `hyperparameter_frequent_config.yaml`：

```yaml
optuna:
  n_jobs: 4  # 从 1 改为 4（需要确保有足够内存）
```

同时修改 `hyperparameter_static_config.yaml`：

```yaml
environment:
  QLIB_NUM_WORKERS: '4'
  NUMEXPR_MAX_THREADS: '4'
  OMP_NUM_THREADS: '4'
  MKL_NUM_THREADS: '4'
```

## 注意事项

1. **内存管理**：如果遇到内存不足问题，请确保：
   - `n_jobs` 设为 1
   - 环境变量中的线程数都设为 '1'
   - 减小训练数据的日期范围（修改 `hyperparameter_time_config.yaml`）

2. **参数搜索空间**：
   - `loguniform` 类型适用于跨越多个数量级的参数（如正则化参数）
   - `uniform` 类型适用于均匀分布的参数（如学习率、采样比例）
   - `int` 类型适用于整数参数（如树的数量、叶子节点数）

3. **Optuna 存储**：
   - 默认使用 SQLite 数据库存储优化历史
   - 可以更换为其他数据库（如 MySQL、PostgreSQL）以支持分布式优化

4. **配置文件路径**：
   - 配置文件必须放在项目的 `config/` 目录下
   - 不要修改配置文件的文件名，除非同时修改代码中的加载路径

## 相关文件

- `config/hyperparameter_time_config.yaml` - 时间配置（训练、验证、测试日期范围）
- `config/db.yaml` - 数据库配置（用于保存最佳超参数）
- `config/paths.yaml` - 路径配置（数据路径等）

## 问题排查

### 问题 1：配置文件未找到

**错误信息**：`FileNotFoundError: [Errno 2] No such file or directory: '...'`

**解决方法**：确保配置文件存在于 `config/` 目录下，文件名正确。

### 问题 2：参数类型错误

**错误信息**：`TypeError: ...`

**解决方法**：检查配置文件中的参数类型是否正确（字符串用引号，数字不用引号）。

### 问题 3：内存不足

**错误信息**：`MemoryError` 或系统崩溃

**解决方法**：
1. 减小 `n_trials` 值
2. 确保 `n_jobs` 和所有线程数环境变量设为 '1'
3. 缩小训练数据的日期范围

## 更新日志

- 2026-01-17: 初始版本，支持按使用频率划分配置文件
