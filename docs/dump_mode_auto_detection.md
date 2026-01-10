# Dump Mode 自动检测功能说明

## 概述

`run_daily_update.py` 脚本会智能判断使用 `dump_all`（全量导入）还是 `dump_update`（增量更新）模式，无需用户手动指定。

## 问题背景

### Qlib 数据导入的两种模式

Qlib 的 `dump_bin.py` 脚本支持两种数据导入模式：

1. **dump_all（全量导入）**
   - 用途：首次初始化 Qlib 二进制数据
   - 特点：重建整个数据目录
   - 速度：较慢（处理所有历史数据）

2. **dump_update（增量更新）**
   - 用途：更新已有的 Qlib 数据
   - 特点：只处理新增数据
   - 速度：较快（只处理增量）
   - **前提**：必须已有完整的 Qlib 数据目录

### 原始问题

**错误场景**：首次运行时使用 `dump_update`

```bash
python qlib_code/run_daily_update.py --date 2026-01-09
```

**错误信息**：
```
FileNotFoundError: [Errno 2] No such file or directory: '..\\qlib_data\\qlib_bin\\calendars\\day.txt'
Command failed (exit 1): ... dump_update ...
```

**原因**：
- `dump_update` 需要读取已有的 `calendars/day.txt` 文件
- 首次运行时该文件不存在
- 应该使用 `dump_all` 而不是 `dump_update`

## 解决方案

### 自动检测逻辑

脚本会自动检测 Qlib 数据目录的状态，智能选择正确的模式：

```python
# 检查关键文件是否存在
qlib_bin_path = Path(args.qlib_bin_dir)
calendar_file = qlib_bin_path / "calendars" / "day.txt"

if calendar_file.exists():
    # 已有数据，使用增量更新
    dump_mode = "dump_update"
    print(f"检测到已有 Qlib 数据，使用增量更新模式 (dump_update)")
else:
    # 首次运行或数据不完整，使用全量导入
    dump_mode = "dump_all"
    print(f"未检测到 Qlib 数据或数据不完整，使用全量导入模式 (dump_all)")
```

### 检测标准

**判断依据**: `{qlib_bin_dir}/calendars/day.txt` 是否存在

| 文件状态 | 判断结果 | 使用模式 | 原因 |
|---------|---------|---------|------|
| 存在 | 已初始化 | `dump_update` | 数据目录完整，可以增量更新 |
| 不存在 | 未初始化 | `dump_all` | 需要重建整个数据目录 |

**为什么选择 `calendars/day.txt`？**
- 这是 Qlib 数据目录的核心文件
- `dump_bin.py` 在读取数据时首先加载此文件
- 如果此文件不存在，说明数据目录未正确初始化

## 使用示例

### 场景 1: 首次运行（自动使用 dump_all）

**环境状态**:
```
../qlib_data/
└── daily/            # CSV 数据存在
    └── 20260109/
        └── *.csv

# qlib_bin/ 目录不存在或为空
```

**运行命令**:
```bash
python qlib_code/run_daily_update.py --date 2026-01-09
```

**输出**:
```
转换数据格式...
未检测到 Qlib 数据或数据不完整，使用全量导入模式 (dump_all)
  缺失文件: ..\qlib_data\qlib_bin\calendars\day.txt

>  python qlib\scripts\dump_bin.py dump_all --data_path ..\qlib_data\daily --qlib_dir ../qlib_data/qlib_bin ...
[全量导入过程]
```

### 场景 2: 日常更新（自动使用 dump_update）

**环境状态**:
```
../qlib_data/
├── daily/            # 新的 CSV 数据
│   └── 20260110/
│       └── *.csv
└── qlib_bin/         # 已有 Qlib 数据
    ├── calendars/
    │   └── day.txt   # ← 存在
    ├── instruments/
    └── features/
```

**运行命令**:
```bash
python qlib_code/run_daily_update.py --date 2026-01-10
```

**输出**:
```
转换数据格式...
检测到已有 Qlib 数据，使用增量更新模式 (dump_update)

>  python qlib\scripts\dump_bin.py dump_update --data_path ..\qlib_data\daily --qlib_dir ../qlib_data/qlib_bin ...
[增量更新过程]
```

### 场景 3: 数据损坏（自动使用 dump_all）

**环境状态**:
```
../qlib_data/
└── qlib_bin/         # 数据不完整
    ├── calendars/    # 目录存在
    │   # 但 day.txt 被删除或损坏
    └── features/
```

**运行命令**:
```bash
python qlib_code/run_daily_update.py --date 2026-01-09
```

**输出**:
```
转换数据格式...
未检测到 Qlib 数据或数据不完整，使用全量导入模式 (dump_all)
  缺失文件: ..\qlib_data\qlib_bin\calendars\day.txt

>  python qlib\scripts\dump_bin.py dump_all ...
[重建整个数据目录]
```

## 与其他脚本的区别

### sql2csv.py 和 tushare2csv.py

这两个脚本**总是使用 `dump_all`**：

```python
# sql2csv.py 和 tushare2csv.py
cmd = [
    sys.executable, str(dump_script),
    "dump_all",  # 固定使用 dump_all
    f'--data_path="{args.csv_output_dir}"',
    ...
]
```

**原因**:
- 这两个脚本用于**从数据源全量导出数据**
- 导出的是完整的历史数据，不是增量
- 适合用于数据初始化或完整重建

### run_daily_update.py

**智能判断模式**：

```python
# run_daily_update.py
dump_mode = "dump_update" if calendar_file.exists() else "dump_all"
```

**原因**:
- 这个脚本用于**日常运行**
- 首次运行需要全量导入
- 后续运行只需增量更新

## 性能对比

### dump_all（全量导入）

**数据量**: 假设 5000 只股票，5 年历史数据

| 阶段 | 耗时（估算） |
|-----|------------|
| 读取 CSV | 10-20 分钟 |
| 转换格式 | 15-30 分钟 |
| 写入二进制 | 10-20 分钟 |
| **总计** | **35-70 分钟** |

### dump_update（增量更新）

**数据量**: 假设 5000 只股票，1 天新数据

| 阶段 | 耗时（估算） |
|-----|------------|
| 读取 CSV | 10-30 秒 |
| 转换格式 | 20-60 秒 |
| 写入二进制 | 10-30 秒 |
| **总计** | **40-120 秒** |

**性能提升**: 约 **30-50 倍**

## 手动强制模式

虽然自动检测已经很可靠，但如果需要手动指定模式：

### 方法 1: 修改脚本（不推荐）

临时修改 `run_daily_update.py` 第 199 行：

```python
# 强制使用 dump_all
dump_mode = "dump_all"

# 或强制使用 dump_update
dump_mode = "dump_update"
```

### 方法 2: 直接调用 dump_bin.py

```bash
# 手动运行 dump_all
python qlib/scripts/dump_bin.py dump_all \
    --data_path ../qlib_data/daily \
    --qlib_dir ../qlib_data/qlib_bin \
    --include_fields open,close,high,low,volume,factor,money

# 手动运行 dump_update
python qlib/scripts/dump_bin.py dump_update \
    --data_path ../qlib_data/daily \
    --qlib_dir ../qlib_data/qlib_bin \
    --include_fields open,close,high,low,volume,factor,money
```

### 方法 3: 删除并重建（强制 dump_all）

```bash
# 删除现有 qlib_bin 目录
rm -rf ../qlib_data/qlib_bin

# 重新运行（会自动使用 dump_all）
python qlib_code/run_daily_update.py --date 2026-01-09
```

## 故障排查

### 问题 1: 误判为 dump_all

**现象**: 明明有数据，但每次都使用 dump_all

**可能原因**:
1. `calendars/day.txt` 文件损坏或被删除
2. 路径配置错误，指向了错误的目录

**检查方法**:
```bash
# 检查文件是否存在
ls ../qlib_data/qlib_bin/calendars/day.txt

# 检查路径配置
grep provider_uri config/paths.yaml
```

**解决方法**:
```bash
# 如果文件确实丢失，重建数据
rm -rf ../qlib_data/qlib_bin
python qlib_code/run_daily_update.py --date 2026-01-09
```

### 问题 2: dump_update 失败

**现象**: 使用 dump_update 但报错

**错误信息**:
```
FileNotFoundError: ... instruments/...
```

**可能原因**: 数据目录不完整（只有 calendars 但缺少其他文件）

**解决方法**:
```bash
# 删除不完整的数据，重新初始化
rm -rf ../qlib_data/qlib_bin
python qlib_code/run_daily_update.py --date 2026-01-09
```

### 问题 3: 性能过慢

**现象**: 每次都用 dump_all，速度很慢

**可能原因**: calendars/day.txt 每次都被删除

**检查方法**:
```bash
# 运行完成后立即检查
ls -la ../qlib_data/qlib_bin/calendars/day.txt
```

**解决方法**: 检查是否有其他进程或脚本在删除文件

## 最佳实践

### 1. 首次部署

```bash
# 1. 从数据源导出 CSV
python qlib_code/sql2csv.py

# 2. 运行日常更新（自动使用 dump_all）
python qlib_code/run_daily_update.py --date 2026-01-09

# 3. 后续每日运行（自动使用 dump_update）
python qlib_code/run_daily_update.py --date 2026-01-10
```

### 2. 定期全量重建

建议每月或每季度重建一次数据，确保数据完整性：

```bash
# 删除旧数据
rm -rf ../qlib_data/qlib_bin

# 重新导出和转换
python qlib_code/sql2csv.py
python qlib_code/run_daily_update.py --date $(date +%Y-%m-%d)
```

### 3. CI/CD 环境

在自动化环境中，首次部署自动使用 dump_all：

```bash
# deploy.sh
#!/bin/bash

# 部署代码
git clone <repo>
cd qlib_sql-master

# 配置环境
cp config/paths.example.yaml config/paths.yaml
# ... 修改配置 ...

# 首次运行（自动 dump_all）
python qlib_code/run_daily_update.py --date $(date +%Y-%m-%d)

# 定时任务（每日自动 dump_update）
echo "0 6 * * * cd /path/to/qlib && python qlib_code/run_daily_update.py --date \$(date +\%Y-\%m-\%d)" | crontab -
```

## 总结

### 关键特性

- ✅ **自动检测**: 无需手动指定模式
- ✅ **智能判断**: 基于数据目录状态
- ✅ **首次友好**: 首次运行自动全量导入
- ✅ **性能优化**: 日常运行自动增量更新
- ✅ **容错恢复**: 数据损坏时自动重建

### 用户无需操作

- ❌ **不需要** 手动指定 dump_all 或 dump_update
- ❌ **不需要** 判断是否首次运行
- ❌ **不需要** 担心模式选择错误

### 运行效果

| 场景 | 自动选择 | 原因 |
|-----|---------|------|
| 首次运行 | `dump_all` | 数据目录不存在 |
| 日常更新 | `dump_update` | 数据目录完整 |
| 数据损坏 | `dump_all` | 关键文件缺失 |

---

**实现日期**: 2026-01-10
**版本**: v1.0
**作者**: Claude Code Assistant
