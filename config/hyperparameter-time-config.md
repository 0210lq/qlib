# 超参数优化时间配置说明

本文档说明如何使用 `hyperparameter_time_config.yaml` 配置文件来控制超参数优化的时间范围。

## 配置文件位置

- 配置文件：`config/hyperparameter_time_config.yaml`
- 示例文件：`config/hyperparameter_time_config.example.yaml`

## 三种优化模式

### 模式1: 自动优化模式 (auto_optimization)

**函数**: `run_hyperparameter_optimization_auto()`

**说明**: 每天自动更新的超参数优化，自动计算训练/验证/测试日期范围。

**配置项**:
```yaml
auto_optimization:
  train_start: "2023-01-01"  # 训练开始日期
```

**日期计算逻辑**:
- `train_start`: 从配置文件读取
- `train_end`: 自动计算（基于最后工作日）
- `valid_start`: 自动计算
- `valid_end`: 自动计算
- `test_start`: 自动计算
- `test_end`: 自动计算（最后工作日）

**使用方法**:
```python
from hyperparameter_lgbm import run_hyperparameter_optimization_auto

# 从配置文件读取 train_start
run_hyperparameter_optimization_auto()
```

---

### 模式2: 历史批量优化模式 (history_optimization)

**函数**: `history_hyperparameter_optimization()`

**说明**: 批量处理历史日期范围内的超参数优化，遍历指定日期范围内的每一天。

**配置项**:
```yaml
history_optimization:
  start_date: "2026-01-05"  # 批量处理开始日期
  end_date: "2026-01-06"    # 批量处理结束日期
  train_start: "2025-01-01" # 训练开始日期
```

**日期计算逻辑**:
- `start_date` 到 `end_date`: 从配置文件读取，遍历这个范围内的每一天
- `train_start`: 从配置文件读取
- 对于每一天，自动计算 `train_end`, `valid_start`, `valid_end`, `test_start`, `test_end`

**使用方法**:
```python
from hyperparameter_lgbm import history_hyperparameter_optimization

# 从配置文件读取所有参数
history_hyperparameter_optimization()

# 或者手动指定参数（覆盖配置文件）
history_hyperparameter_optimization(
    start_date='2026-01-05',
    end_date='2026-01-06',
    train_start="2025-01-01"
)
```

---

### 模式3: 手动日期模式 (manual_dates_optimization)

**函数**: `run_hyperparameter_optimization_manual_dates()`

**说明**: 完全手动指定所有日期的超参数优化，不进行任何自动计算。

**配置项**:
```yaml
manual_dates_optimization:
  train_start: "2023-01-01"  # 训练开始日期
  train_end: "2025-12-31"    # 训练结束日期
  valid_start: "2026-01-01"  # 验证开始日期
  valid_end: "2026-01-15"    # 验证结束日期
  test_start: "2026-01-16"   # 测试开始日期
  test_end: "2026-01-31"     # 测试结束日期
```

**日期计算逻辑**:
- 所有日期都从配置文件读取，不进行任何自动计算

**使用方法**:
```python
from hyperparameter_lgbm import run_hyperparameter_optimization_manual_dates

# 从配置文件读取所有日期
run_hyperparameter_optimization_manual_dates()

# 或者手动指定所有日期（覆盖配置文件）
run_hyperparameter_optimization_manual_dates(
    train_start="2023-01-01",
    train_end="2025-12-31",
    valid_start="2026-01-01",
    valid_end="2026-01-15",
    test_start="2026-01-16",
    test_end="2026-01-31"
)
```

---

## 配置文件示例

完整的 `hyperparameter_time_config.yaml` 示例：

```yaml
# 超参数优化时间配置文件

# 自动优化模式配置（run_hyperparameter_optimization_auto）
auto_optimization:
  train_start: "2023-01-01"  # 训练开始日期

# 历史批量优化模式配置（history_hyperparameter_optimization）
history_optimization:
  start_date: "2026-01-05"  # 批量处理开始日期
  end_date: "2026-01-06"    # 批量处理结束日期
  train_start: "2025-01-01" # 训练开始日期

# 手动日期模式配置（run_hyperparameter_optimization_manual_dates）
manual_dates_optimization:
  train_start: "2023-01-01"  # 训练开始日期
  train_end: "2025-12-31"    # 训练结束日期
  valid_start: "2026-01-01"  # 验证开始日期
  valid_end: "2026-01-15"    # 验证结束日期
  test_start: "2026-01-16"   # 测试开始日期
  test_end: "2026-01-31"     # 测试结束日期
```

---

## 运行方式

在 `hyperparameter_lgbm.py` 的 `__main__` 部分，选择要运行的模式：

```python
if __name__ == "__main__":
    # 模式1: 自动优化模式
    # run_hyperparameter_optimization_auto()

    # 模式2: 历史批量优化模式
    # history_hyperparameter_optimization()

    # 模式3: 手动日期模式
    run_hyperparameter_optimization_manual_dates()
```

---

## 注意事项

1. **日期格式**: 所有日期必须使用 `YYYY-MM-DD` 格式（例如：`2023-01-01`）

2. **内存使用**: 训练数据范围较大会消耗大量内存。如果遇到内存错误，可以：
   - 缩短 `train_start` 日期
   - 减少 `n_trials` 数量（在代码中修改）

3. **配置文件优先级**:
   - 如果函数调用时提供了参数，将使用提供的参数
   - 如果函数调用时未提供参数（或参数为 `None`），将从配置文件读取

4. **数据库保存**: 优化结果会自动保存到数据库中，使用 `train_start` 和 `train_end` 作为主键

---

## 常见使用场景

### 场景1: 每日自动运行
使用模式1（自动优化模式），配置定时任务每天运行：
```bash
python qlib_code/hyperparameter_lgbm.py
```

### 场景2: 回测历史数据
使用模式2（历史批量优化模式），批量处理历史日期：
```python
history_hyperparameter_optimization(
    start_date='2024-01-01',
    end_date='2024-12-31',
    train_start="2023-01-01"
)
```

### 场景3: 特定时间段测试
使用模式3（手动日期模式），精确控制所有日期范围：
```python
run_hyperparameter_optimization_manual_dates(
    train_start="2023-01-01",
    train_end="2024-12-31",
    valid_start="2025-01-01",
    valid_end="2025-06-30",
    test_start="2025-07-01",
    test_end="2025-12-31"
)
```
