# SQL2CSV Configuration Guide

**Version**: 2.0
**Date**: 2026-01-14

---

## Overview

SQL2CSV使用YAML配置文件来管理数据库连接、数据提取参数、性能设置等。本指南帮助您理解和配置这些参数。

---

## Configuration Files

SQL2CSV使用3个配置文件：

1. **`config/paths.yaml`** - 基础路径配置
2. **`config/db.yaml`** - 数据库连接配置
3. **`config/sql2csv.yaml`** - SQL2CSV特定配置

---

## Quick Start

### 最小配置

```yaml
# config/sql2csv.yaml
extraction:
  market: "ALL"
  start_date: "20250101"
  end_date: null

database:
  connection_key: "host2"  # 引用 db.yaml 中的连接

output:
  csv_output_dir: "./csv_data"
```

### 运行

```python
from qlib_code.sql2csv_refactored import run_sql2csv

result = run_sql2csv(
    market='ALL',
    start_date='20250101'
)
```

---

## Configuration Sections

### 1. Extraction (数据提取)

控制提取哪些数据。

```yaml
extraction:
  market: "ALL"              # 市场代码或股票列表
  start_date: "20250101"     # 开始日期 (YYYYMMDD)
  end_date: null             # 结束日期 (null = 今天)
```

**market 参数选项**:
- `"ALL"` - 所有股票
- `"zz500"` - 中证500成分股
- `"hs300"` - 沪深300成分股
- `["000001.SZ", "600000.SH"]` - 自定义股票列表

**日期格式**: YYYYMMDD (例如: 20250101)

---

### 2. Performance (性能调优)

控制处理性能和资源使用。

```yaml
performance:
  batch_size: 1000           # 每批处理的股票数量
  max_workers: 8             # 最大并发worker数
  batch_sleep_seconds: 0.1   # 批次间休眠时间（秒）
  query_timeout_seconds: 30  # 数据库查询超时（秒）
```

**参数说明**:

| 参数 | 默认值 | 范围 | 说明 |
|------|--------|------|------|
| `batch_size` | 1000 | 100-10000 | 批量大小，越大越快但内存占用越高 |
| `max_workers` | 8 | 1-32 | 并发数，建议为CPU核心数的2倍 |
| `batch_sleep_seconds` | 0.1 | 0-1.0 | 批次间休眠，减少数据库压力 |
| `query_timeout_seconds` | 30 | 10-300 | 查询超时时间 |

**性能调优建议**:

```yaml
# 小数据集 (<100只股票)
performance:
  batch_size: 50
  max_workers: 2

# 中等数据集 (100-1000只股票)
performance:
  batch_size: 500
  max_workers: 4

# 大数据集 (>1000只股票)
performance:
  batch_size: 2000
  max_workers: 16
```

---

### 3. Database (数据库配置)

配置数据库连接。

**方式1: 引用 db.yaml 中的连接**

```yaml
database:
  connection_key: "host2"  # 使用 db.yaml 中定义的连接
```

**方式2: 直接指定连接参数**

```yaml
database:
  host: "localhost"
  port: 3306
  database: "stock_db"
  user: "username"
  password: "password"
```

---

### 4. Schema (表和列映射)

映射数据库表名和列名到Qlib格式。

```yaml
schema:
  tables:
    stock: "data_stock"              # 股票数据表
    index: "data_index"              # 指数数据表
    component: "data.indexcomponent" # 成分股表

  stock_columns:
    date: "valuation_date"
    code: "code"
    open: "open"
    high: "high"
    low: "low"
    close: "close"
    volume: "volume"
    amount: "amt"
    factor: "COALESCE(adjfactor, adjfactor_jy, adjfactor_wind)"

  index_columns:
    date: "valuation_date"
    code: "code"
    open: "open"
    high: "high"
    low: "low"
    close: "close"
    volume: "volume"
    amount: "amt"
```

**注意**: `factor` 列支持SQL表达式（如COALESCE）

---

### 5. Markets (市场定义)

定义市场代码和对应的指数。

```yaml
markets:
  zz500:
    name: "中证500"
    index_code: "000905.SH"
  hs300:
    name: "沪深300"
    index_code: "000300.SH"
  zz1000:
    name: "中证1000"
    index_code: "000852.SH"
```

**添加自定义市场**:

```yaml
markets:
  my_portfolio:
    name: "我的投资组合"
    index_code: "000001.SH"  # 可选
```

---

### 6. Output (输出配置)

配置CSV输出格式和位置。

```yaml
output:
  csv_output_dir: "${base_dir}/csv_data"  # 输出目录
  provider_uri: "${base_dir}/csv_data"    # Qlib provider URI
  columns: ["date", "open", "close", "high", "low", "volume", "factor", "money"]
  date_format: "%Y-%m-%d"                 # 日期格式
```

**变量替换**: `${base_dir}` 会被替换为项目根目录

---

### 7. Logging (日志配置)

配置日志输出。

```yaml
logging:
  level: "INFO"                                    # 日志级别
  console: true                                    # 控制台输出
  file: true                                       # 文件输出
  file_path: "${base_dir}/logs/sql2csv_{date}.log" # 日志文件路径
  rotation: "daily"                                # 轮转策略
  retention_days: 30                               # 保留天数
```

**日志级别**:
- `DEBUG` - 详细调试信息
- `INFO` - 一般信息（推荐）
- `WARNING` - 警告信息
- `ERROR` - 错误信息

**轮转策略**:
- `daily` - 每天轮转
- `hourly` - 每小时轮转
- `weekly` - 每周轮转

---

## Common Scenarios

### 场景1: 每日增量更新

```yaml
extraction:
  market: "ALL"
  start_date: "20250101"  # 固定起始日期
  end_date: null          # 自动使用今天

performance:
  batch_size: 2000
  max_workers: 16
```

### 场景2: 特定市场回测

```yaml
extraction:
  market: "zz500"
  start_date: "20200101"
  end_date: "20231231"

performance:
  batch_size: 500
  max_workers: 8
```

### 场景3: 自定义股票池

```python
# 通过代码覆盖配置
result = run_sql2csv(
    market=['000001.SZ', '600000.SH', '600519.SH'],
    start_date='20250101'
)
```

### 场景4: 开发调试

```yaml
extraction:
  market: ["000001.SZ", "600000.SH"]  # 少量股票
  start_date: "20250101"
  end_date: "20250110"                # 短时间范围

performance:
  batch_size: 10
  max_workers: 1

logging:
  level: "DEBUG"  # 详细日志
```

---

## Configuration Override

可以通过函数参数覆盖配置文件：

```python
result = run_sql2csv(
    market='zz500',           # 覆盖 extraction.market
    start_date='20250101',    # 覆盖 extraction.start_date
    end_date='20250131',      # 覆盖 extraction.end_date
    batch_size=500,           # 覆盖 performance.batch_size
    max_workers=4,            # 覆盖 performance.max_workers
    output_dir='/custom/path', # 覆盖 output.csv_output_dir
    log_level='DEBUG'         # 覆盖 logging.level
)
```

---

## Troubleshooting

### 问题1: 处理速度慢

**症状**: 处理6000只股票超过4分钟

**解决方案**:
```yaml
performance:
  batch_size: 2000  # 增大批量
  max_workers: 16   # 增加并发
  batch_sleep_seconds: 0  # 移除休眠
```

### 问题2: 数据库连接超时

**症状**: `DatabaseError: Connection timeout`

**解决方案**:
```yaml
performance:
  query_timeout_seconds: 60  # 增加超时时间
  max_workers: 4             # 减少并发
```

### 问题3: 内存占用过高

**症状**: 系统内存不足

**解决方案**:
```yaml
performance:
  batch_size: 500   # 减小批量
  max_workers: 4    # 减少并发
```

### 问题4: CSV文件未生成

**症状**: 运行完成但没有CSV文件

**检查**:
1. 检查 `output.csv_output_dir` 路径是否正确
2. 检查目录权限
3. 查看日志文件中的错误信息

```yaml
logging:
  level: "DEBUG"  # 启用详细日志
```

### 问题5: 数据库权限错误

**症状**: `SELECT command denied`

**解决方案**:
1. 检查数据库用户权限
2. 确认表名配置正确
3. 使用有足够权限的数据库用户

---

## Best Practices

### 1. 生产环境配置

```yaml
extraction:
  market: "ALL"
  start_date: "20150101"
  end_date: null

performance:
  batch_size: 2000
  max_workers: 16
  batch_sleep_seconds: 0.05

logging:
  level: "INFO"
  file: true
  rotation: "daily"
  retention_days: 30
```

### 2. 开发环境配置

```yaml
extraction:
  market: ["000001.SZ", "600000.SH"]
  start_date: "20250101"
  end_date: "20250110"

performance:
  batch_size: 10
  max_workers: 2

logging:
  level: "DEBUG"
  console: true
```

### 3. 配置文件管理

- 使用版本控制管理配置文件
- 敏感信息（密码）使用环境变量
- 为不同环境创建不同配置文件

```bash
config/
├── sql2csv.yaml          # 默认配置
├── sql2csv.dev.yaml      # 开发环境
├── sql2csv.prod.yaml     # 生产环境
└── sql2csv.test.yaml     # 测试环境
```

---

## Environment Variables

支持使用环境变量：

```yaml
database:
  host: "${DB_HOST}"
  port: "${DB_PORT}"
  user: "${DB_USER}"
  password: "${DB_PASSWORD}"
```

设置环境变量：

```bash
# Linux/Mac
export DB_HOST="localhost"
export DB_PASSWORD="secret"

# Windows
set DB_HOST=localhost
set DB_PASSWORD=secret
```

---

## Validation

配置文件会在启动时自动验证。常见验证错误：

### 错误1: 日期格式错误

```
ConfigurationError: extraction.start_date must be in YYYYMMDD format
```

**修复**: 使用正确的日期格式 `20250101`

### 错误2: 批量大小超出范围

```
ConfigurationError: performance.batch_size is too large (max 10000)
```

**修复**: 设置 `batch_size <= 10000`

### 错误3: 缺少必需字段

```
ConfigurationError: extraction.start_date is required
```

**修复**: 添加缺少的配置项

---

## Summary

- 使用 `config/sql2csv.yaml` 作为主配置文件
- 通过函数参数覆盖配置
- 根据数据量调整 `batch_size` 和 `max_workers`
- 生产环境使用 `INFO` 日志级别
- 开发调试使用 `DEBUG` 日志级别

---

**最后更新**: 2026-01-14
**版本**: 2.0
