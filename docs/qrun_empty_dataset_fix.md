# Qrun 空数据集错误修复指南

## 错误信息

```
ValueError: Empty data from dataset, please check your dataset config.
```

## 问题原因

运行 `qrun qlib_code/workflow_config_lightgbm.yaml` 时出现数据集为空的错误，主要有以下几个可能原因：

### 1. ✅ **已修复：fit_end_time 配置为空**

**原问题：**
```yaml
data_handler_config: &data_handler_config
    start_time: 2023-01-01
    end_time: 2023-03-02
    fit_start_time: 2023-01-01
    fit_end_time:                  # ← 空值！导致数据处理器无法正确获取数据
    instruments: *market
```

**修复后：**
```yaml
data_handler_config: &data_handler_config
    start_time: 2023-01-01
    end_time: 2023-03-02
    fit_start_time: 2023-01-01
    fit_end_time: 2023-02-24       # ← 与训练集结束时间一致
    instruments: *market
```

### 2. ⚠️ **待检查：日期范围超出数据范围**

**问题：**
配置文件使用的日期是 2023-01-01 到 2023-03-02，但你的数据可能不包含这个时间段。

**检查方法：**
```bash
python qlib_code/check_qlib_data.py
```

**可能的输出：**
```
❌ 警告: 指定日期范围内没有数据
   请检查:
   1. 数据是否包含 2023-01-01 到 2023-03-02 的日期
   2. 是否需要更新数据或调整日期范围
```

### 3. ⚠️ **待检查：数据路径或数据文件问题**

**当前数据路径：**
```
E:/qlib_data/tushare_qlib_data/qlib_bin
```

**检查清单：**
- [ ] 路径是否存在
- [ ] 是否包含 `calendars/` 目录
- [ ] 是否包含 `instruments/` 目录
- [ ] 是否包含 `features/` 目录
- [ ] 特征数据文件是否存在

## 诊断步骤

### 步骤 1：运行数据诊断脚本

```bash
python qlib_code/check_qlib_data.py
```

这个脚本会检查：
1. ✅ 数据路径是否存在
2. ✅ 交易日历是否可用
3. ✅ 股票列表是否可用
4. ✅ 特征数据是否可加载
5. ✅ 配置的日期范围是否有数据

### 步骤 2：查看诊断结果

#### 情况 A：交易日历日期范围不匹配

```
交易日历检查
日期范围: 2020-01-01 到 2022-12-31  # ← 数据只到 2022 年

日期范围数据检查
检查日期范围: 2023-01-01 到 2023-03-02  # ← 配置要求 2023 年
❌ 警告: 指定日期范围内没有数据
```

**解决方案：** 更新配置文件中的日期范围

#### 情况 B：数据路径错误

```
数据路径检查
❌ 错误: 数据路径不存在
```

**解决方案：** 检查并修正数据路径

#### 情况 C：数据未下载

```
股票列表检查
❌ 错误: 股票列表为空
```

**解决方案：** 下载并转换数据

## 解决方案

### 解决方案 1：更新日期范围（推荐）

如果数据诊断显示数据日期范围与配置不匹配，更新配置文件：

```bash
# 1. 运行诊断查看实际数据日期范围
python qlib_code/check_qlib_data.py

# 2. 根据诊断结果，编辑配置文件
nano qlib_code/workflow_config_lightgbm.yaml
```

**修改示例：**

假设数据日期范围是 2020-01-01 到 2022-12-31，更新配置为：

```yaml
data_handler_config: &data_handler_config
    start_time: 2020-01-01          # 修改为数据起始日期
    end_time: 2022-12-31            # 修改为数据结束日期
    fit_start_time: 2020-01-01
    fit_end_time: 2022-10-31        # 训练集结束日期
    instruments: *market

# ... 同时更新 segments
segments:
    train: [2020-01-01, 2022-10-31]    # 训练集
    valid: [2022-11-01, 2022-11-30]    # 验证集
    test: [2022-12-01, 2022-12-31]     # 测试集
```

### 解决方案 2：重新下载数据

如果数据不存在或不完整：

```bash
# 从数据库导出数据
python qlib_code/sql2csv.py

# 或从 Tushare 获取数据
python qlib_code/tushare2csv.py

# 然后转换为 Qlib 格式
# （具体命令取决于你的数据导入脚本）
```

### 解决方案 3：检查数据路径配置

确保 `workflow_config_lightgbm.yaml` 中的数据路径正确：

```yaml
qlib_init:
    provider_uri: "E:\\qlib_data\\tushare_qlib_data\\qlib_bin"  # 确认路径正确
    region: cn
```

如果路径不对，从 `config/paths.yaml` 读取正确路径：

```bash
# 查看 paths.yaml 中的配置
cat config/paths.yaml | grep provider_uri
```

## 快速修复命令

### 方案 A：使用 2024-2025 年数据（如果有）

```bash
# 1. 备份原配置
cp qlib_code/workflow_config_lightgbm.yaml qlib_code/workflow_config_lightgbm.yaml.bak

# 2. 使用 sed 快速更新日期（Linux/Mac）
sed -i 's/2023-01-01/2024-01-01/g' qlib_code/workflow_config_lightgbm.yaml
sed -i 's/2023-02-24/2024-02-24/g' qlib_code/workflow_config_lightgbm.yaml
sed -i 's/2023-02-27/2024-02-27/g' qlib_code/workflow_config_lightgbm.yaml
sed -i 's/2023-02-28/2024-02-28/g' qlib_code/workflow_config_lightgbm.yaml
sed -i 's/2023-03-01/2024-03-01/g' qlib_code/workflow_config_lightgbm.yaml
sed -i 's/2023-03-02/2024-03-02/g' qlib_code/workflow_config_lightgbm.yaml

# 3. 重新运行
qrun qlib_code/workflow_config_lightgbm.yaml
```

### 方案 B：使用诊断脚本自动建议日期

```python
# 在 check_qlib_data.py 的输出中会显示建议的日期范围
python qlib_code/check_qlib_data.py
```

## 验证修复

修复后重新运行：

```bash
qrun qlib_code/workflow_config_lightgbm.yaml
```

**成功的日志应该包含：**

```
[INFO] - Loading data Done
[INFO] - DropnaLabel Done
[INFO] - CSZScoreNorm Done
[INFO] - fit & process data Done
[INFO] - Init data Done
[INFO] - Training model...  # ← 应该开始训练，不再报错
```

## 常见错误和解决方法

### 错误 1：日期格式不正确

```
ValueError: Invalid date format
```

**解决：** 确保日期格式为 `YYYY-MM-DD`

### 错误 2：训练集为空

```
WARNING: train dataset is empty
```

**解决：** 检查 segments 中的日期范围是否在数据范围内

### 错误 3：数据加载超时

```
TimeoutError: Data loading timeout
```

**解决：**
- 减小日期范围
- 减少特征数量
- 增加内存

## 配置文件完整示例

以下是一个经过修复的完整配置示例：

```yaml
qlib_init:
    provider_uri: "E:\\qlib_data\\tushare_qlib_data\\qlib_bin"
    region: cn

market: &market all
benchmark: &benchmark 000300.sh

data_handler_config: &data_handler_config
    start_time: 2024-01-01          # 确保在数据范围内
    end_time: 2024-03-02
    fit_start_time: 2024-01-01
    fit_end_time: 2024-02-24        # ✅ 不能为空
    instruments: *market

task:
    model:
        class: LGBModel
        module_path: qlib.contrib.model.gbdt
        kwargs:
            loss: mse
            # ... 其他参数
    dataset:
        class: DatasetH
        module_path: qlib.data.dataset
        kwargs:
            handler:
                class: Alpha158
                module_path: qlib.contrib.data.handler
                kwargs: *data_handler_config
            segments:
                train: [2024-01-01, 2024-02-24]    # 与 fit_end_time 一致
                valid: [2024-02-27, 2024-02-28]
                test: [2024-03-01, 2024-03-02]
```

## 预防措施

1. **使用诊断脚本**：每次运行 qrun 前先检查数据
   ```bash
   python qlib_code/check_qlib_data.py
   ```

2. **保持日期一致性**：确保以下日期一致
   - `fit_end_time` = segments.train 的结束日期
   - `end_time` >= segments.test 的结束日期

3. **定期更新数据**：保持数据最新
   ```bash
   python qlib_code/sql2csv.py
   ```

4. **备份配置**：修改前备份
   ```bash
   cp qlib_code/workflow_config_lightgbm.yaml qlib_code/workflow_config_lightgbm.yaml.bak
   ```

## 总结

本次错误的主要原因是 `fit_end_time` 配置为空。修复步骤：

1. ✅ 已修复 `fit_end_time` 配置
2. ⚠️ 需运行 `python qlib_code/check_qlib_data.py` 检查数据日期范围
3. ⚠️ 根据诊断结果更新配置文件中的日期
4. ✅ 重新运行 `qrun qlib_code/workflow_config_lightgbm.yaml`
