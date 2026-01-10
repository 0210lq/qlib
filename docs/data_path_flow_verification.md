# 数据路径流程验证报告

## 概述

本文档详细说明 `run_daily_update.py` 脚本的完整数据流，验证存储路径和读取路径的一致性。

## 配置基础

### paths.yaml 配置

```yaml
base_dir: "../qlib_data"
csv_daily_dir: "${base_dir}/daily"        # ../qlib_data/daily
provider_uri: "${base_dir}/qlib_bin"      # ../qlib_data/qlib_bin
model_path: "./models/trained_model.pkl"
```

### 运行命令

```bash
python qlib_code/run_daily_update.py --date 2026-01-09
```

## 完整数据流

### 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│               run_daily_update.py --date 2026-01-09             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤 1: update_latest_days.py                                   │
│                                                                 │
│ • 接收环境变量: TARGET_PREDICT_DATE = "2026-01-09"             │
│ • 转换日期格式: "2026-01-09" → "20260109"                      │
│ • 创建目录: ../qlib_data/daily/20260109/                       │
│ • 从数据库获取 2026-01-09 的股票数据                           │
│ • 存储 CSV: ../qlib_data/daily/20260109/*.csv                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤 2: 确定 CSV 数据目录                                       │
│                                                                 │
│ • 解析 --date 参数: "2026-01-09"                                │
│ • 转换格式: date_str = "20260109"                              │
│ • 构建路径: csv_path = csv_daily_dir / "20260109"              │
│ • 结果: ../qlib_data/daily/20260109/                           │
│                                                                 │
│ ✅ 与步骤 1 存储路径一致                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤 3: dump_bin.py（转换为 Qlib 格式）                        │
│                                                                 │
│ • 模式检测:                                                     │
│   - 检查: ../qlib_data/qlib_bin/calendars/day.txt              │
│   - 首次运行: dump_all（全量导入）                             │
│   - 后续运行: dump_update（增量更新）                          │
│                                                                 │
│ • 读取 CSV: ../qlib_data/daily/20260109/*.csv                  │
│ • 写入二进制: ../qlib_data/qlib_bin/                           │
│   - calendars/day.txt                                          │
│   - instruments/all.txt                                        │
│   - features/{symbol}/...                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 步骤 4: update_new.py（模型预测）                              │
│                                                                 │
│ • 初始化 Qlib:                                                  │
│   - provider_uri = "../qlib_data/qlib_bin"                     │
│   - qlib.init(provider_uri=provider_uri)                       │
│                                                                 │
│ • 加载模型:                                                     │
│   - model_path = "./models/trained_model.pkl"                  │
│   - model = pickle.load(model_path)                            │
│                                                                 │
│ • 读取数据:                                                     │
│   - 从 ../qlib_data/qlib_bin/ 读取 2026-01-09 的数据           │
│   - TARGET_PREDICT_DATE = "2026-01-09"                         │
│                                                                 │
│ • 生成预测:                                                     │
│   - 预测结果写入数据库                                          │
│                                                                 │
│ ✅ provider_uri 与步骤 3 写入路径一致                           │
└─────────────────────────────────────────────────────────────────┘
```

## 路径一致性验证

### 验证表格

| 步骤 | 操作 | 路径 | 配置来源 | 状态 |
|-----|------|------|---------|------|
| 1 | update_latest_days.py **写入** CSV | `../qlib_data/daily/20260109/` | `csv_daily_dir` + `TARGET_PREDICT_DATE` | ✅ |
| 2 | run_daily_update.py **确定** CSV 目录 | `../qlib_data/daily/20260109/` | `csv_daily_dir` + `--date` 参数 | ✅ |
| 3 | dump_bin.py **读取** CSV | `../qlib_data/daily/20260109/` | `args.data_csv_dir` | ✅ |
| 3 | dump_bin.py **写入** Qlib 数据 | `../qlib_data/qlib_bin/` | `provider_uri` | ✅ |
| 4 | update_new.py **读取** Qlib 数据 | `../qlib_data/qlib_bin/` | `provider_uri` | ✅ |
| 4 | update_new.py **读取** 模型 | `./models/trained_model.pkl` | `model_path` | ✅ |

### 关键路径映射

| 配置项 | 配置值 | 实际路径 | 用途 |
|-------|--------|---------|------|
| `csv_daily_dir` | `"${base_dir}/daily"` | `../qlib_data/daily/` | CSV 数据基础目录 |
| 指定日期子目录 | `{csv_daily_dir}/20260109/` | `../qlib_data/daily/20260109/` | 特定日期的 CSV 数据 |
| `provider_uri` | `"${base_dir}/qlib_bin"` | `../qlib_data/qlib_bin/` | Qlib 二进制数据 |
| `model_path` | `"./models/trained_model.pkl"` | `./models/trained_model.pkl` | 训练好的模型 |

## 已修复的问题

### 问题 1: `_latest_subdir` 逻辑不准确

**原始问题**:

```python
# 原始代码（有问题）
latest_csv_path = str(_latest_subdir(base_csv_dir))  # 按修改时间查找
args.data_csv_dir = latest_csv_path
```

**问题场景**:
```
../qlib_data/daily/
├── 20260108/   (修改时间: 昨天)
├── 20260109/   (修改时间: 刚创建)  ← 用户指定的日期
└── 20260110/   (修改时间: 今天早上) ← _latest_subdir 会选这个！
```

运行 `--date 2026-01-09`:
- ❌ update_latest_days.py 存储到 `daily/20260109/`
- ❌ dump_bin.py 读取 `daily/20260110/`（错误！）

**修复方案**:

```python
# 修复后的代码
if getattr(args, "date", None):
    # 如果指定了日期，直接使用对应的目录
    date_str = args.date.replace("-", "")  # 2026-01-09 → 20260109
    csv_path = base_csv_dir / date_str
    args.data_csv_dir = str(csv_path)
    print(f"使用指定日期的数据目录: {args.data_csv_dir}")
else:
    # 没有指定日期，使用最新修改的子目录
    latest_csv_path = str(_latest_subdir(base_csv_dir))
    args.data_csv_dir = latest_csv_path
    print(f"使用最新的数据目录: {args.data_csv_dir}")
```

**修复效果**:
- ✅ 指定 `--date 2026-01-09` → 直接使用 `daily/20260109/`
- ✅ 不指定日期 → 使用修改时间最新的目录（向后兼容）

## 环境变量传递

### TARGET_PREDICT_DATE 的传递路径

```python
# run_daily_update.py (第171-173行)
env_for_update_latest = os.environ.copy()
if getattr(args, "date", None):
    env_for_update_latest["TARGET_PREDICT_DATE"] = args.date  # "2026-01-09"

# update_latest_days.py (第528-532行)
env_date = os.getenv('TARGET_PREDICT_DATE')  # 接收 "2026-01-09"
if '-' in env_date:
    target_date = datetime.strptime(env_date, '%Y-%m-%d').strftime('%Y%m%d')  # 转换为 "20260109"

# run_daily_update.py (第219-227行)
env = os.environ.copy()
if getattr(args, "date", None):
    env["TARGET_PREDICT_DATE"] = args.date  # 传递给 update_new.py

# update_new.py (第14-23行)
TARGET_PREDICT_DATE = os.getenv("TARGET_PREDICT_DATE")  # 接收 "2026-01-09"
if TARGET_PREDICT_DATE is None:
    TARGET_PREDICT_DATE = date.today().strftime("%Y-%m-%d")
```

**验证**: ✅ 环境变量在所有脚本间正确传递

## 目录结构示例

### 运行前

```
E:\jzq\qlib\                          # 项目根目录
├── qlib_code\
│   ├── run_daily_update.py
│   ├── update_latest_days.py
│   └── update_new.py
├── models\
│   └── trained_model.pkl             # 需要存在
├── config\
│   └── paths.yaml
└── logs\                             # 自动创建

E:\jzq\qlib_data\                     # 数据目录（项目外）
├── daily\                            # CSV 数据
│   └── (可能为空或有旧数据)
└── qlib_bin\                         # Qlib 数据（可能不存在）
```

### 运行后

```
E:\jzq\qlib\
├── qlib_code\
├── models\
│   └── trained_model.pkl
├── config\
└── logs\
    └── score_prediction_20260109.log # 新建

E:\jzq\qlib_data\
├── daily\
│   └── 20260109\                     # 新建
│       ├── SH600000.csv
│       ├── SH600001.csv
│       └── ...
└── qlib_bin\                         # 新建或更新
    ├── calendars\
    │   └── day.txt
    ├── instruments\
    │   └── all.txt
    └── features\
        └── ...
```

## 测试验证

### 测试用例 1: 首次运行（指定日期）

```bash
python qlib_code/run_daily_update.py --date 2026-01-09
```

**预期流程**:
1. ✅ 创建 `../qlib_data/daily/20260109/`
2. ✅ 存储 CSV 到 `../qlib_data/daily/20260109/*.csv`
3. ✅ 读取 CSV 从 `../qlib_data/daily/20260109/`
4. ✅ 使用 `dump_all` 创建 `../qlib_data/qlib_bin/`
5. ✅ 读取 Qlib 数据从 `../qlib_data/qlib_bin/`
6. ✅ 加载模型从 `./models/trained_model.pkl`
7. ✅ 生成预测并写入数据库

**验证命令**:
```bash
# 检查 CSV 数据
ls ../qlib_data/daily/20260109/

# 检查 Qlib 数据
ls ../qlib_data/qlib_bin/calendars/
ls ../qlib_data/qlib_bin/instruments/
ls ../qlib_data/qlib_bin/features/

# 检查日志
cat logs/score_prediction_20260109.log | grep "使用指定日期的数据目录"
```

### 测试用例 2: 后续运行（增量更新）

```bash
python qlib_code/run_daily_update.py --date 2026-01-10
```

**预期流程**:
1. ✅ 创建 `../qlib_data/daily/20260110/`
2. ✅ 存储新 CSV 到 `../qlib_data/daily/20260110/*.csv`
3. ✅ 读取 CSV 从 `../qlib_data/daily/20260110/`
4. ✅ 使用 `dump_update` 更新 `../qlib_data/qlib_bin/`
5. ✅ 预测使用更新后的数据

### 测试用例 3: 不指定日期（使用最新）

```bash
python qlib_code/run_daily_update.py
```

**预期流程**:
1. ✅ 使用今天日期获取数据
2. ✅ 使用 `_latest_subdir` 查找最新目录
3. ✅ 其余流程与测试用例 1 相同

## 常见问题

### Q1: 如何验证路径配置是否正确？

**方法 1: 运行诊断脚本**
```bash
python qlib_code/check_qlib_data.py
```

**方法 2: 手动检查路径**
```bash
# 检查配置
grep -E "csv_daily_dir|provider_uri" config/paths.yaml

# 检查目录是否存在
ls ../qlib_data/daily/
ls ../qlib_data/qlib_bin/
```

### Q2: 数据存储和读取不一致怎么办？

**检查步骤**:

1. 确认日期格式一致（YYYY-MM-DD vs YYYYMMDD）
2. 确认路径配置一致
3. 查看日志中的实际路径

```bash
# 查看日志中的路径
cat logs/score_prediction_20260109.log | grep "数据目录"
cat logs/score_prediction_20260109.log | grep "data_path"
cat logs/score_prediction_20260109.log | grep "qlib_dir"
```

### Q3: 如何强制重建数据？

```bash
# 删除现有 Qlib 数据
rm -rf ../qlib_data/qlib_bin

# 重新运行（会自动使用 dump_all）
python qlib_code/run_daily_update.py --date 2026-01-09
```

## 总结

### 路径一致性检查清单

- ✅ **CSV 存储路径** = **CSV 读取路径**
  - 存储: `csv_daily_dir/YYYYMMDD/`
  - 读取: `csv_daily_dir/YYYYMMDD/` (根据 --date 参数)

- ✅ **Qlib 写入路径** = **Qlib 读取路径**
  - 写入: `provider_uri`
  - 读取: `provider_uri`

- ✅ **环境变量传递**
  - TARGET_PREDICT_DATE 在所有脚本间正确传递

- ✅ **日期格式转换**
  - 命令行: YYYY-MM-DD
  - 目录名: YYYYMMDD
  - 自动转换

### 关键改进

1. **修复 `_latest_subdir` 问题**: 指定日期时直接使用对应目录
2. **添加路径日志**: 明确显示使用的数据目录
3. **自动模式选择**: dump_all vs dump_update
4. **自动创建目录**: logs 目录

### 用户无需担心

- ❌ 不需要手动管理目录
- ❌ 不需要担心路径不一致
- ❌ 不需要手动选择 dump 模式
- ✅ 只需运行一条命令

---

**验证日期**: 2026-01-10
**版本**: v2.0
**作者**: Claude Code Assistant
