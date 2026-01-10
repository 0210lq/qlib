# 日志目录自动创建功能说明

## 概述

为了提升用户体验，项目中的脚本会自动创建 `logs/` 目录，无需用户手动创建。

## 功能说明

### 自动创建逻辑

在运行 `run_daily_update.py` 时，脚本会：

1. 根据日期自动生成日志文件路径
2. **自动创建 logs 目录**（如果不存在）
3. 创建日志文件并开始记录

### 实现代码

**文件**: `qlib_code/run_daily_update.py`

```python
# 生成日志文件路径
default_log_path = WORKDIR.parent / "logs" / f"score_prediction_{log_date.strftime('%Y%m%d')}.log"
args.log_file = str(default_log_path)

# 确保日志目录存在（自动创建）
log_file_path = Path(args.log_file)
log_file_path.parent.mkdir(parents=True, exist_ok=True)

# 打开日志文件
log_f = open(args.log_file, "a", encoding="utf-8")
```

**关键参数**:
- `parents=True`: 创建所有必要的父目录
- `exist_ok=True`: 如果目录已存在，不报错

## 日志文件命名规范

### 默认命名

```
logs/score_prediction_YYYYMMDD.log
```

**示例**:
```
logs/score_prediction_20260109.log
logs/score_prediction_20260110.log
```

### 自定义日志路径

也可以通过命令行参数指定自定义日志路径：

```bash
python qlib_code/run_daily_update.py --date 2026-01-09 --log-file /path/to/custom.log
```

**注意**: 使用自定义路径时，也会自动创建所需的目录。

## 使用方法

### 方法 1: 默认日志（推荐）

```bash
# 直接运行，自动创建 logs 目录和日志文件
python qlib_code/run_daily_update.py --date 2026-01-09
```

**效果**:
```
qlib_sql-master/
├── logs/                              # ← 自动创建
│   └── score_prediction_20260109.log  # ← 自动创建
├── qlib_code/
│   └── run_daily_update.py
└── ...
```

### 方法 2: 自定义日志路径

```bash
# 指定自定义日志路径（目录会自动创建）
python qlib_code/run_daily_update.py --date 2026-01-09 --log-file custom_logs/my_log.log
```

**效果**:
```
qlib_sql-master/
├── custom_logs/        # ← 自动创建
│   └── my_log.log      # ← 自动创建
├── qlib_code/
└── ...
```

## Git 配置

### .gitignore 设置

日志文件不会被提交到 Git：

```gitignore
# 忽略日志目录及文件
logs/
*.log
```

### 目录管理

- ✅ **无需** `.gitkeep` 文件
- ✅ **无需** 手动创建 `logs/` 目录
- ✅ 脚本运行时自动创建

## 日志内容

日志文件记录完整的运行过程：

```log
2026-01-10 16:38:18,553 INFO 数据库连接成功
2026-01-10 16:38:18,553 INFO 正在获取 ALL 股票列表...
2026-01-10 16:38:29,198 INFO 获取到 5949 只股票
2026-01-10 16:38:29,198 INFO 开始处理 20260109 的股票数据，共 5949 只股票
...
```

**内容包括**:
1. 数据获取过程
2. 数据转换过程
3. 模型预测过程
4. 错误和警告信息

## 查看日志

### 方法 1: 直接查看最新日志

```bash
# Linux/Mac
tail -f logs/score_prediction_$(date +%Y%m%d).log

# Windows PowerShell
Get-Content logs\score_prediction_$(Get-Date -Format "yyyyMMdd").log -Wait
```

### 方法 2: 查看指定日期日志

```bash
# Linux/Mac
cat logs/score_prediction_20260109.log

# Windows
type logs\score_prediction_20260109.log
```

### 方法 3: 搜索错误信息

```bash
# Linux/Mac
grep -i error logs/score_prediction_*.log

# Windows PowerShell
Select-String -Path "logs\score_prediction_*.log" -Pattern "error" -CaseSensitive:$false
```

## 日志管理建议

### 1. 定期清理旧日志

```bash
# 删除30天前的日志（Linux/Mac）
find logs/ -name "*.log" -mtime +30 -delete

# 删除30天前的日志（Windows PowerShell）
Get-ChildItem logs\*.log | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item
```

### 2. 日志归档

```bash
# 创建归档目录
mkdir -p logs/archive

# 压缩并归档旧日志（Linux/Mac）
tar -czf logs/archive/logs_$(date +%Y%m).tar.gz logs/*.log
rm logs/*.log

# 压缩并归档旧日志（Windows PowerShell）
Compress-Archive -Path logs\*.log -DestinationPath "logs\archive\logs_$(Get-Date -Format 'yyyyMM').zip"
Remove-Item logs\*.log
```

### 3. 日志轮转配置

对于长期运行的服务，建议配置日志轮转：

```python
# 示例：使用 Python logging 模块的 RotatingFileHandler
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/score_prediction.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5           # 保留5个备份
)
```

## 故障排查

### 问题 1: 权限不足

**错误信息**:
```
PermissionError: [Errno 13] Permission denied: 'logs/score_prediction_20260109.log'
```

**解决方法**:
```bash
# Linux/Mac: 修改权限
chmod 755 logs/
chmod 644 logs/*.log

# Windows: 以管理员权限运行
# 或检查文件夹权限
```

### 问题 2: 磁盘空间不足

**错误信息**:
```
OSError: [Errno 28] No space left on device
```

**解决方法**:
```bash
# 检查磁盘空间
df -h  # Linux/Mac

# 清理旧日志
rm logs/*.log
```

### 问题 3: 路径中包含特殊字符

**问题描述**: 自定义日志路径包含空格或特殊字符

**解决方法**:
```bash
# 使用引号包裹路径
python qlib_code/run_daily_update.py --log-file "path with spaces/my log.log"
```

## 其他脚本

目前只有 `run_daily_update.py` 会创建日志文件。其他脚本使用标准输出：

- `sql2csv.py` - 使用 logging 输出到控制台
- `tushare2csv.py` - 使用 logging 输出到控制台
- `update_new.py` - 使用 print 输出到控制台

**如需保存其他脚本的日志**:
```bash
# 重定向输出到文件
python qlib_code/sql2csv.py > logs/sql2csv.log 2>&1
```

## 总结

### 关键特性

- ✅ **自动创建**: 无需手动创建 `logs/` 目录
- ✅ **智能命名**: 根据日期自动命名日志文件
- ✅ **灵活配置**: 支持自定义日志路径
- ✅ **完整记录**: 记录所有运行过程和错误信息

### 用户无需操作

- ❌ **不需要** 手动创建 `logs/` 目录
- ❌ **不需要** 添加 `.gitkeep` 文件
- ❌ **不需要** 担心目录不存在的错误

### 最佳实践

1. 使用默认日志路径（自动管理）
2. 定期清理或归档旧日志
3. 出现问题时查看日志文件排查

---

**更新日期**: 2026-01-10
**版本**: v1.0
**作者**: Claude Code Assistant
