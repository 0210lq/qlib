# Workflow 时间配置说明文档

## 文件说明

- **配置文件**: `workflow_config_lightgbm.yaml`
- **用途**: LightGBM 模型训练和回测的完整工作流配置

---

## 当前配置概览

### 当前时间配置

```yaml
data_handler_config:
    start_time: 2017-06-30
    end_time: 2025-07-01
    fit_start_time: 2017-06-30
    fit_end_time: 2025-06-25

segments:
    train: [2017-06-30, 2025-06-25]
    valid: [2025-06-26, 2025-06-27]
    test: [2025-06-30, 2025-07-01]

backtest:
    start_time: 2025-06-28
    end_time: 2025-06-29
```

### 时间线可视化

```
2017-06-30                    2025-06-25  2025-06-26  2025-06-27  2025-06-28  2025-06-29  2025-06-30  2025-07-01
    |                              |           |           |           |           |           |           |
    |<-------- Train Period ------>|           |           |           |           |           |           |
    |                              |<- Valid ->|           |           |           |           |           |
    |                              |           |           |           |<-Backtest>|           |           |
    |                              |           |           |           |           |           |<- Test -->|
    |                                                                                                      |
    |<--------------------------------- Data Loading Range ------------------------------------------->|
    |<-------- Processor Fit ------>|
```

### ⚠️ 当前配置存在的问题

1. **Valid 和 Test 时间不连续**
   - Valid 结束: 2025-06-27
   - Test 开始: 2025-06-30
   - 中间缺少 2025-06-28 和 2025-06-29

2. **Backtest 时间与 Test 时间不匹配**
   - Backtest: 2025-06-28 ~ 2025-06-29
   - Test: 2025-06-30 ~ 2025-07-01
   - Backtest 时间段不在 Test 范围内

3. **时间范围过短**
   - Valid 只有 2 天
   - Test 只有 2 天
   - Backtest 只有 2 天
   - 这些时间范围可能不足以进行有效的模型评估

---

## 一、数据处理时间配置 (data_handler_config)

### 1.1 start_time 和 end_time

**配置项**:
```yaml
data_handler_config:
    start_time: 2017-06-30
    end_time: 2025-07-01
```

**作用**: 定义数据加载的完整时间范围

**详细说明**:
- `start_time`: 从数据源加载数据的最早日期
- `end_time`: 从数据源加载数据的最晚日期
- 这两个参数决定了 DataHandler 从 Qlib 数据存储中读取的数据范围
- 必须覆盖所有 train/valid/test 的时间范围

**代码位置**: `qlib/data/dataset/handler.py:106-152`

**注意事项**:
1. **必须包含所有数据集时间段**
   - `start_time` ≤ `train_start`
   - `end_time` ≥ `test_end`

2. **时间序列数据需要额外历史数据**
   - 如果使用 TSDatasetH（时间序列数据集），需要在 `start_time` 之前预留 `step_len` 个交易日的数据
   - 例如：如果 `step_len=8`，`train_start=2017-06-30`，则 `start_time` 应该设置为 2017-06-30 之前至少 8 个交易日

3. **闭合区间**
   - Qlib 使用闭合区间 `[start_time, end_time]`，包含两端的日期
   - 这与 pandas 的 `.loc` 行为一致

---

### 1.2 fit_start_time 和 fit_end_time

**配置项**:
```yaml
data_handler_config:
    fit_start_time: 2017-06-30
    fit_end_time: 2025-06-25
```

**作用**: 定义数据预处理器（Processor）拟合统计参数的时间范围

**详细说明**:
- 用于归一化处理器（如 ZScoreNorm, MinMaxNorm, RobustZScoreNorm）计算统计参数
- 这些处理器会在 `fit_start_time` 到 `fit_end_time` 范围内计算：
  - 均值（mean）
  - 标准差（std）
  - 最小值（min）
  - 最大值（max）
  - 中位数（median）

**代码位置**: `qlib/contrib/data/handler.py:196-295`

**⚠️ 关键警告 - 防止数据泄露**:

```python
# 来自源码的警告注释
# NOTE: It is very important to set the correct fit_start_time and fit_end_time !!!
# The fit_end_time **must not** include any information from the test data !!!
```

**数据泄露场景示例**:

❌ **错误配置**（会导致数据泄露）:
```yaml
fit_start_time: 2017-06-30
fit_end_time: 2025-07-01      # 包含了 test 数据！

segments:
    train: [2017-06-30, 2025-06-25]
    valid: [2025-06-26, 2025-06-27]
    test: [2025-06-30, 2025-07-01]  # test 数据被用于计算归一化参数
```

✅ **正确配置**:
```yaml
fit_start_time: 2017-06-30
fit_end_time: 2025-06-25      # 只包含 train 数据

segments:
    train: [2017-06-30, 2025-06-25]
    valid: [2025-06-26, 2025-06-27]
    test: [2025-06-30, 2025-07-01]
```

**最佳实践**:
1. **fit_end_time 应该等于 train_end**
   ```
   fit_end_time = segments.train[1]
   ```

2. **绝对不能包含验证集和测试集**
   ```
   fit_end_time < segments.valid[0]
   fit_end_time < segments.test[0]
   ```

3. **时间关系约束**
   ```
   fit_start_time ≤ fit_end_time ≤ train_end < valid_start < test_start
   ```

---

## 二、数据集分割时间配置 (segments)

### 2.1 segments 配置

**配置项**:
```yaml
segments:
    train: [2017-06-30, 2025-06-25]
    valid: [2025-06-26, 2025-06-27]
    test: [2025-06-30, 2025-07-01]
```

**作用**: 定义训练集、验证集和测试集的时间范围

**详细说明**:
- `train`: 训练集时间范围，用于模型训练
- `valid`: 验证集时间范围，用于模型调参和早停
- `test`: 测试集时间范围，用于最终模型评估

**代码位置**: `qlib/data/dataset/__init__.py:72-248`

---

### 2.2 Train 时间段

**当前配置**: `[2017-06-30, 2025-06-25]`

**用途**:
- 模型训练的数据范围
- 处理器拟合的数据范围（通过 fit_end_time 控制）

**注意事项**:
1. **训练集应该足够大**
   - 当前配置约 8 年的数据，这是合理的
   - 对于日频数据，建议至少 3-5 年

2. **与 fit_end_time 的关系**
   - 通常 `fit_end_time = train_end`
   - 当前配置正确：`fit_end_time: 2025-06-25 = train_end`

3. **时间序列数据的额外需求**
   - 如果使用 TSDatasetH，系统会自动向前扩展 `step_len` 个交易日
   - 确保 `start_time` 有足够的历史数据支持这个扩展

---

### 2.3 Valid 时间段

**当前配置**: `[2025-06-26, 2025-06-27]`

**用途**:
- 模型超参数调优
- 早停（Early Stopping）判断
- 模型选择

**⚠️ 当前配置问题**:
1. **时间范围过短**
   - 只有 2 天的数据
   - 建议至少 1-3 个月的数据

2. **与 Test 不连续**
   - Valid 结束: 2025-06-27
   - Test 开始: 2025-06-30
   - 中间缺少 2025-06-28 和 2025-06-29

**建议配置**:
```yaml
# 方案 1: 连续的时间段
segments:
    train: [2017-06-30, 2024-12-31]
    valid: [2025-01-01, 2025-03-31]    # 3 个月
    test: [2025-04-01, 2025-07-01]     # 3 个月

# 方案 2: 更长的验证期
segments:
    train: [2017-06-30, 2024-06-30]
    valid: [2024-07-01, 2024-12-31]    # 6 个月
    test: [2025-01-01, 2025-07-01]     # 6 个月
```

---

### 2.4 Test 时间段

**当前配置**: `[2025-06-30, 2025-07-01]`

**用途**:
- 最终模型性能评估
- 模拟真实交易环境

**⚠️ 当前配置问题**:
1. **时间范围过短**
   - 只有 2 天的数据
   - 无法充分评估模型性能
   - 建议至少 1-3 个月的数据

2. **与 Backtest 不匹配**
   - Test: 2025-06-30 ~ 2025-07-01
   - Backtest: 2025-06-28 ~ 2025-06-29
   - Backtest 应该在 Test 范围内

**建议配置**:
```yaml
segments:
    test: [2025-04-01, 2025-07-01]     # 3 个月

backtest:
    start_time: 2025-04-01             # 与 test 开始对齐
    end_time: 2025-07-01               # 与 test 结束对齐
```

---

### 2.5 时间段连续性

**最佳实践**:

✅ **推荐：连续的时间段**
```yaml
segments:
    train: [2017-06-30, 2024-12-31]
    valid: [2025-01-01, 2025-03-31]    # 紧接 train
    test: [2025-04-01, 2025-07-01]     # 紧接 valid
```

⚠️ **可接受：有间隔的时间段**（需要有充分理由）
```yaml
segments:
    train: [2017-06-30, 2024-06-30]
    valid: [2024-09-01, 2024-11-30]    # 跳过 7-8 月（如避开特殊市场事件）
    test: [2025-01-01, 2025-03-31]     # 跳过 12 月（如避开年末效应）
```

❌ **不推荐：当前配置**
```yaml
segments:
    train: [2017-06-30, 2025-06-25]
    valid: [2025-06-26, 2025-06-27]    # 只有 2 天
    test: [2025-06-30, 2025-07-01]     # 与 valid 不连续，只有 2 天
```

---

## 三、回测时间配置 (backtest)

### 3.1 backtest start_time 和 end_time

**配置项**:
```yaml
port_analysis_config:
    backtest:
        start_time: 2025-06-28
        end_time: 2025-06-29
```

**作用**: 定义投资组合回测的时间范围

**详细说明**:
- 在这个时间范围内模拟真实交易
- 使用模型预测结果生成交易信号
- 计算投资组合收益、风险等指标

**代码位置**: `qlib/backtest/backtest.py:26-110`

---

### 3.2 Backtest 与 Test 的关系

**标准配置**:
```yaml
segments:
    test: [2025-01-01, 2025-07-01]

backtest:
    start_time: 2025-01-01    # = test_start
    end_time: 2025-07-01      # = test_end
```

**⚠️ 当前配置问题**:
```yaml
segments:
    test: [2025-06-30, 2025-07-01]

backtest:
    start_time: 2025-06-28    # 不在 test 范围内！
    end_time: 2025-06-29      # 不在 test 范围内！
```

**问题分析**:
1. Backtest 时间段（06-28 ~ 06-29）完全不在 Test 时间段（06-30 ~ 07-01）内
2. 这意味着回测使用的数据和模型评估使用的数据不一致
3. 可能导致回测结果与模型性能指标不匹配

**修正建议**:
```yaml
# 方案 1: 扩大 test 范围，包含 backtest
segments:
    test: [2025-06-28, 2025-07-01]

backtest:
    start_time: 2025-06-28
    end_time: 2025-07-01

# 方案 2: 调整 backtest 到 test 范围内
segments:
    test: [2025-06-30, 2025-07-01]

backtest:
    start_time: 2025-06-30
    end_time: 2025-07-01
```

---

### 3.3 闭合区间说明

**重要**: Qlib 的回测使用闭合区间 `[start_time, end_time]`

```python
# 来自源码的说明
"""
Parameters:
    start_time: the closed start time for backtest (includes this time)
    end_time: the closed end time for backtest (includes this time)
"""
```

**示例**:
```yaml
backtest:
    start_time: 2025-01-01
    end_time: 2025-01-31
```
- 包含 2025-01-01 的交易
- 包含 2025-01-31 的交易
- 总共约 20 个交易日（假设没有节假日）

---

## 四、日历边界处理

### 4.1 交易日历对齐

**Qlib 的日历系统**:
- Qlib 使用交易日历（Trading Calendar），自动过滤非交易日
- 配置中的日期会自动对齐到最近的交易日

**代码位置**: `qlib/backtest/utils.py:23-201`

**示例**:
```yaml
# 如果 2025-01-01 是非交易日（元旦）
start_time: 2025-01-01
# Qlib 会自动调整到下一个交易日，如 2025-01-02
```

---

### 4.2 时间精度处理

**epsilon_change 函数**:
- 用于处理时间边界的精度问题
- 确保闭合区间的正确性

```python
# 来自源码
def get_step_time(self, trade_step):
    calendar_index = self.start_index + trade_step
    return (
        self._calendar[calendar_index],
        epsilon_change(self._calendar[calendar_index + 1])
    )
```

**作用**:
- 避免浮点数精度导致的边界问题
- 确保时间范围的包含性

---

### 4.3 TSDatasetH 的时间扩展

**自动扩展机制**:

当使用时间序列数据集（TSDatasetH）时，系统会自动向前扩展时间范围：

```python
def _extend_slice(slc: slice, cal: list, step_len: int) -> slice:
    start, end = slc.start, slc.stop
    start_idx = bisect.bisect_left(cal, pd.Timestamp(start))
    pad_start_idx = max(0, start_idx - step_len)
    pad_start = cal[pad_start_idx]
    return slice(pad_start, end)
```

**示例**:
```yaml
# 配置
segments:
    train: [2017-06-30, 2024-12-31]

# 如果 step_len = 8
# 实际加载的数据范围会扩展到 2017-06-30 之前 8 个交易日
# 例如: [2017-06-16, 2024-12-31]
```

**注意事项**:
1. 确保 `start_time` 有足够的历史数据
2. 如果 `step_len=8`，`start_time` 应该至少比 `train_start` 早 8 个交易日

---

## 五、注意事项和最佳实践

### 5.1 数据泄露防范

**关键原则**: 测试数据的任何信息都不能用于训练

**检查清单**:
- [ ] `fit_end_time` ≤ `train_end`
- [ ] `fit_end_time` < `valid_start`
- [ ] `fit_end_time` < `test_start`
- [ ] 处理器只在训练集上拟合
- [ ] 验证集和测试集只用于评估，不用于训练

**常见泄露场景**:
1. ❌ fit_end_time 包含验证集或测试集
2. ❌ 使用未来数据计算特征
3. ❌ 在整个数据集上进行归一化

---

### 5.2 时间范围建议

**训练集**:
- 日频数据: 至少 3-5 年
- 分钟数据: 至少 1-2 年
- 当前配置: 8 年 ✅

**验证集**:
- 日频数据: 1-6 个月
- 分钟数据: 1-3 个月
- 当前配置: 2 天 ❌（太短）

**测试集**:
- 日频数据: 1-6 个月
- 分钟数据: 1-3 个月
- 当前配置: 2 天 ❌（太短）

---

### 5.3 时间连续性建议

**推荐配置模式**:

```yaml
# 模式 1: 标准连续分割（推荐）
data_handler_config:
    start_time: 2015-01-01
    end_time: 2025-07-01
    fit_start_time: 2015-01-01
    fit_end_time: 2023-12-31

segments:
    train: [2015-01-01, 2023-12-31]    # 9 年
    valid: [2024-01-01, 2024-06-30]    # 6 个月
    test: [2024-07-01, 2025-07-01]     # 1 年

backtest:
    start_time: 2024-07-01
    end_time: 2025-07-01

# 模式 2: 滚动窗口（适用于在线学习）
data_handler_config:
    start_time: 2020-01-01
    end_time: 2025-07-01
    fit_start_time: 2020-01-01
    fit_end_time: 2024-06-30

segments:
    train: [2020-01-01, 2024-06-30]    # 4.5 年
    valid: [2024-07-01, 2024-09-30]    # 3 个月
    test: [2024-10-01, 2025-07-01]     # 9 个月

backtest:
    start_time: 2024-10-01
    end_time: 2025-07-01
```

---

### 5.4 当前配置修正建议

**问题总结**:
1. Valid 和 Test 时间范围过短（各 2 天）
2. Valid 和 Test 时间不连续
3. Backtest 时间不在 Test 范围内

**修正方案**:

```yaml
# 建议配置
data_handler_config:
    start_time: 2017-06-01          # 提前一个月，为 TSDatasetH 预留空间
    end_time: 2025-07-01
    fit_start_time: 2017-06-30
    fit_end_time: 2024-12-31        # 只用训练集拟合

segments:
    train: [2017-06-30, 2024-12-31] # 约 7.5 年
    valid: [2025-01-01, 2025-03-31] # 3 个月
    test: [2025-04-01, 2025-07-01]  # 3 个月

backtest:
    start_time: 2025-04-01          # 与 test 对齐
    end_time: 2025-07-01
```

---

### 5.5 配置验证脚本

可以使用以下 Python 代码验证时间配置的正确性:

```python
import pandas as pd

def validate_time_config(config):
    """验证时间配置的正确性"""

    # 提取时间配置
    start_time = pd.Timestamp(config['data_handler_config']['start_time'])
    end_time = pd.Timestamp(config['data_handler_config']['end_time'])
    fit_start = pd.Timestamp(config['data_handler_config']['fit_start_time'])
    fit_end = pd.Timestamp(config['data_handler_config']['fit_end_time'])

    train_start = pd.Timestamp(config['segments']['train'][0])
    train_end = pd.Timestamp(config['segments']['train'][1])
    valid_start = pd.Timestamp(config['segments']['valid'][0])
    valid_end = pd.Timestamp(config['segments']['valid'][1])
    test_start = pd.Timestamp(config['segments']['test'][0])
    test_end = pd.Timestamp(config['segments']['test'][1])

    backtest_start = pd.Timestamp(config['backtest']['start_time'])
    backtest_end = pd.Timestamp(config['backtest']['end_time'])

    # 验证规则
    checks = {
        'start_time <= train_start': start_time <= train_start,
        'end_time >= test_end': end_time >= test_end,
        'fit_start <= fit_end': fit_start <= fit_end,
        'fit_end <= train_end': fit_end <= train_end,
        'fit_end < valid_start': fit_end < valid_start,
        'train_end < valid_start': train_end < valid_start,
        'valid_end <= test_start': valid_end <= test_start,
        'backtest_start >= test_start': backtest_start >= test_start,
        'backtest_end <= test_end': backtest_end <= test_end,
    }

    # 打印验证结果
    print("时间配置验证结果:")
    print("=" * 50)
    for rule, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {rule}")

    # 计算时间范围
    print("\n时间范围统计:")
    print("=" * 50)
    print(f"训练集: {(train_end - train_start).days} 天")
    print(f"验证集: {(valid_end - valid_start).days} 天")
    print(f"测试集: {(test_end - test_start).days} 天")
    print(f"回测期: {(backtest_end - backtest_start).days} 天")

    return all(checks.values())

# 使用示例
config = {
    'data_handler_config': {
        'start_time': '2017-06-30',
        'end_time': '2025-07-01',
        'fit_start_time': '2017-06-30',
        'fit_end_time': '2025-06-25',
    },
    'segments': {
        'train': ['2017-06-30', '2025-06-25'],
        'valid': ['2025-06-26', '2025-06-27'],
        'test': ['2025-06-30', '2025-07-01'],
    },
    'backtest': {
        'start_time': '2025-06-28',
        'end_time': '2025-06-29',
    }
}

validate_time_config(config)
```

---

## 六、参考资料

### 6.1 相关代码文件

- `qlib/data/dataset/handler.py`: DataHandler 实现
- `qlib/data/dataset/__init__.py`: DatasetH 和 TSDatasetH 实现
- `qlib/contrib/data/handler.py`: Alpha158/Alpha360 和处理器实现
- `qlib/backtest/backtest.py`: 回测循环实现
- `qlib/backtest/utils.py`: 交易日历管理
- `qlib/backtest/executor.py`: 执行器实现

### 6.2 关键概念

| 概念 | 含义 | 作用范围 |
|-----|-----|--------|
| **start_time, end_time** | 数据加载范围 | DataHandler |
| **fit_start_time, fit_end_time** | 处理器拟合范围 | Processor |
| **segments** | 数据集分割 | DatasetH |
| **backtest start/end** | 回测时间范围 | Executor |
| **闭合区间** | 包含两端的时间范围 | 所有时间配置 |

---

## 七、总结

### 7.1 配置原则

1. **数据加载范围要足够大**: `start_time` 和 `end_time` 必须覆盖所有需要的数据
2. **处理器拟合只用训练集**: `fit_end_time` 必须等于 `train_end`，不能包含验证集和测试集
3. **时间段要连续**: train → valid → test 应该是连续的时间段
4. **时间范围要合理**: 验证集和测试集不能太短，建议至少 1-3 个月
5. **回测要在测试集内**: backtest 的时间范围应该在 test 的时间范围内

### 7.2 快速检查清单

配置完成后，请检查：

- [ ] `start_time` ≤ `train_start`
- [ ] `end_time` ≥ `test_end`
- [ ] `fit_end_time` = `train_end`
- [ ] `fit_end_time` < `valid_start`
- [ ] `train_end` < `valid_start` ≤ `valid_end` < `test_start` ≤ `test_end`
- [ ] `backtest_start` ≥ `test_start`
- [ ] `backtest_end` ≤ `test_end`
- [ ] 验证集至少 1 个月
- [ ] 测试集至少 1 个月
- [ ] 如果使用 TSDatasetH，`start_time` 要预留 `step_len` 个交易日

---
