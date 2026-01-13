# SQL2CSV 数据导出配置说明文档

## 文件说明

- **配置文件**: `sql2csv.yaml`
- **示例文件**: `sql2csv.example.yaml`

## 使用说明

1. 复制示例文件为配置文件: `cp sql2csv.example.yaml sql2csv.yaml`
2. 根据实际需求修改参数配置
3. 修改参数后，重新运行 `sql2csv.py` 脚本即可生效
4. 支持使用环境变量（如 `${HOME}`、`${USERPROFILE}`）和路径变量（如 `${base_dir}`）

---

## 输出路径配置

### csv_output_dir
- **说明**: CSV 数据输出目录，指定导出的 CSV 文件存放路径
- **支持格式**:
  - 相对路径（相对于项目根目录）
  - 绝对路径
  - 支持使用环境变量和路径变量（如 `${base_dir}`）
- **示例**:
  - 相对路径: `"../qlib_data/csv_data"`
  - 绝对路径: `"D:/qlib_data/csv_data"`
  - 使用变量: `"${base_dir}/csv_data"`
- **默认值**: `"${base_dir}/csv_data"`

### qlib_workdir
- **说明**: Qlib 安装路径，用于调用 Qlib 的 dump_bin.py 脚本将 CSV 数据转换为 Qlib 二进制格式
- **支持格式**:
  - 相对路径（相对于项目根目录）
  - 绝对路径
- **示例**:
  - 项目内路径: `"./qlib"`
  - 外部路径: `"../qlib"`
  - 绝对路径: `"D:/projects/qlib"`
- **默认值**: `"./qlib"`
- **注意**: 此路径应指向 Qlib 源码目录，其中包含 `scripts/dump_bin.py` 脚本

### provider_uri
- **说明**: Qlib 二进制数据存储路径，转换后的二进制数据将保存到此目录
- **支持格式**:
  - 相对路径（相对于项目根目录）
  - 绝对路径
  - 支持使用环境变量和路径变量（如 `${base_dir}`）
- **示例**:
  - 使用变量: `"${base_dir}/qlib_bin"`
  - 相对路径: `"../qlib_data/qlib_bin"`
  - 绝对路径: `"D:/qlib_data/qlib_bin"`
- **默认值**: `"${base_dir}/qlib_bin"`
- **注意**: 此路径将作为 Qlib 的 `provider_uri` 参数，用于初始化 Qlib 数据提供器

---

## 市场类型配置

### market
- **说明**: 指定要处理的股票池类型，用于从数据库获取指定股票池的股票列表，并处理这些股票的数据
- **可选值**:
  - `'ALL'`: 处理所有股票
  - `'zz500'`: 中证500指数成分股
  - `'hs300'`: 沪深300指数成分股
  - `'sz50'`: 上证50指数成分股
  - `'zz1000'`: 中证1000指数成分股
  - `'zz2000'`: 中证2000指数成分股
- **默认值**: `"ALL"`

---

## 日期范围配置

### start_date
- **说明**: 数据提取的起始日期，指定从哪个日期开始提取股票和指数数据
- **格式**: `'YYYYMMDD'`
- **示例**: `'20150101'`
- **建议**: 设置为足够早的日期，以确保获取完整的历史数据
- **默认值**: `"20150101"`

### end_date
- **说明**: 数据提取的结束日期
- **格式**: `'YYYYMMDD'` 或 `null`
- **说明**:
  - 如果设置为 `null` 或空值，将自动使用当前日期作为结束日期
  - 如果设置为具体日期，将提取到该日期为止的数据
- **建议**: 设置为 `null`，以便自动获取最新数据
- **示例**: `'20241231'` 或 `null`
- **默认值**: `null`

---

## 批处理配置

### batch_size
- **说明**: 批处理大小，指定每次批量处理股票的数量
- **影响**:
  - 较大的值可以提高处理速度，但会占用更多内存
  - 较小的值可以降低内存占用，但处理速度较慢
- **建议值**: 500-2000，根据系统内存和数据库性能调整
- **默认值**: `1000`

---

## 数据库连接配置

### db_host
- **说明**: 数据库主机地址
- **格式**: `"hostname:port"` 或 `"hostname"`
- **示例**:
  - `"localhost:3306"`
  - `"192.168.1.100:3306"`
  - `"rm-xxxxx.mysql.rds.aliyuncs.com:3306"`
- **默认值**: `"localhost:3306"`

### db_port
- **说明**: 数据库端口号
- **类型**: 整数
- **默认值**: `3306`
- **注意**: 如果 `db_host` 中已包含端口号（如 `"localhost:3306"`），此参数会被忽略

### db_database
- **说明**: 数据库名称
- **示例**: `"data_prepared_new"`
- **默认值**: `"data_prepared_new"`
- **注意**: 此数据库应包含以下表：
  - `data_stock`: 股票行情数据表
  - `data_index`: 指数行情数据表
  - `data.indexcomponent`: 指数成分股表（可选，用于获取指数成分股列表）

### db_user
- **说明**: 数据库用户名
- **示例**: `"your_username"`
- **默认值**: `"root"`

### db_password
- **说明**: 数据库密码
- **示例**: `"your_password"`
- **默认值**: `""`（空字符串）
- **安全提示**:
  - 请勿将包含真实密码的 `sql2csv.yaml` 提交到版本控制系统
  - 建议使用环境变量或密钥管理工具来管理密码

---

## 配置示例

### 完整配置示例

```yaml
# 输出路径配置
csv_output_dir: "${base_dir}/csv_data"

# Qlib 路径配置
qlib_workdir: "./qlib"
provider_uri: "${base_dir}/qlib_bin"

# 市场类型配置
market: "ALL"

# 日期范围配置
start_date: "20150101"
end_date: null

# 批处理配置
batch_size: 1000

# 数据库连接配置
db_host: "localhost:3306"
db_port: 3306
db_database: "data_prepared_new"
db_user: "your_username"
db_password: "your_password"
```

### 使用远程数据库示例

```yaml
csv_output_dir: "${base_dir}/csv_data"
qlib_workdir: "./qlib"
provider_uri: "${base_dir}/qlib_bin"

market: "hs300"
start_date: "20200101"
end_date: null
batch_size: 500

# 阿里云 RDS 数据库示例
db_host: "rm-xxxxx.mysql.rds.aliyuncs.com:3306"
db_port: 3306
db_database: "data_prepared_new"
db_user: "prod"
db_password: "YourSecurePassword123"
```

---

## 数据库表结构要求

### data_stock 表（必需）

股票行情数据表，应包含以下字段：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| valuation_date | DATE | 交易日期 |
| code | VARCHAR | 股票代码 |
| open | DECIMAL | 开盘价 |
| high | DECIMAL | 最高价 |
| low | DECIMAL | 最低价 |
| close | DECIMAL | 收盘价 |
| volume | BIGINT | 成交量 |
| amt | DECIMAL | 成交额 |
| adjfactor | DECIMAL | 复权因子（优先） |
| adjfactor_jy | DECIMAL | 复权因子（聚源，备用） |
| adjfactor_wind | DECIMAL | 复权因子（Wind，备用） |

**注意**: 复权因子字段会按 `adjfactor` → `adjfactor_jy` → `adjfactor_wind` 的优先级选择

### data_index 表（必需）

指数行情数据表，应包含以下字段：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| valuation_date | DATE | 交易日期 |
| code | VARCHAR | 指数代码 |
| open | DECIMAL | 开盘价 |
| high | DECIMAL | 最高价 |
| low | DECIMAL | 最低价 |
| close | DECIMAL | 收盘价 |
| volume | BIGINT | 成交量 |
| amt | DECIMAL | 成交额 |

### data.indexcomponent 表（可选）

指数成分股表，用于获取特定指数的成分股列表：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| code | VARCHAR | 股票代码 |
| organization | VARCHAR | 指数类型（如 'zz500', 'hs300'） |

**注意**: 如果不使用指数成分股功能（即 `market` 设置为 `'ALL'`），此表可以不存在

---

## 使用流程

### 1. 配置输出路径

编辑 `config/sql2csv.yaml`，设置数据输出路径：

```yaml
csv_output_dir: "${base_dir}/csv_data"  # CSV 文件输出目录
qlib_workdir: "./qlib"                   # Qlib 源码路径
provider_uri: "${base_dir}/qlib_bin"     # Qlib 二进制数据路径
```

### 2. 配置数据库连接

设置正确的数据库连接信息：

```yaml
db_host: "your_database_host:3306"
db_database: "your_database_name"
db_user: "your_username"
db_password: "your_password"
```

### 3. 配置数据提取参数

设置市场类型、日期范围等参数：

```yaml
market: "ALL"          # 或 'hs300', 'zz500' 等
start_date: "20150101"
end_date: null         # 自动使用当前日期
batch_size: 1000
```

### 4. 运行脚本

```bash
python qlib_code/sql2csv.py
```

脚本会自动完成以下步骤：
1. 从数据库提取股票和指数数据
2. 将数据保存为 CSV 格式到 `csv_output_dir`
3. 调用 Qlib 的 `dump_bin.py` 将 CSV 转换为二进制格式
4. 将二进制数据保存到 `provider_uri`

### 5. 查看输出

**CSV 文件**（中间格式）：
```
csv_data/
├── 000001.SZ.csv
├── 000002.SZ.csv
├── 000300.SH.csv  # 沪深300指数
└── ...
```

**Qlib 二进制数据**（最终格式）：
```
qlib_bin/
├── calendars/
├── instruments/
├── features/
└── ...
```

---

## 注意事项

### 1. 数据库连接

- **连接测试**: 首次使用前，建议先测试数据库连接是否正常
- **网络访问**: 如果使用远程数据库，确保网络可达且防火墙已开放相应端口
- **权限要求**: 数据库用户需要有 `SELECT` 权限

### 2. 数据安全

- **密码保护**: 不要将包含真实密码的配置文件提交到 Git
- **配置文件**: `sql2csv.yaml` 已在 `.gitignore` 中，不会被提交
- **示例文件**: 只提交 `sql2csv.example.yaml` 示例文件

### 3. 性能优化

- **批处理大小**: 根据数据库性能和网络状况调整 `batch_size`
  - 本地数据库: 可设置较大值（1000-2000）
  - 远程数据库: 建议设置较小值（500-1000）
- **增量更新**: 脚本会自动检测已有数据，只下载新增数据
- **并发控制**: 批量查询失败时会自动回退到多线程逐只查询

### 4. 数据完整性

- **复权因子**: 确保数据库中至少有一个复权因子字段有数据
- **日期连续性**: 建议数据库中的数据日期连续，避免缺失交易日
- **数据质量**: 定期检查导出的 CSV 文件，确保数据质量

---

## 故障排查

### 问题 1: 数据库连接失败

**错误信息**: `数据库连接失败: ...`

**解决方案**:
1. 检查 `db_host` 是否正确
2. 检查 `db_user` 和 `db_password` 是否正确
3. 检查数据库服务是否运行
4. 检查防火墙是否开放端口
5. 检查网络连接是否正常

### 问题 2: 找不到表

**错误信息**: `Table 'xxx.data_stock' doesn't exist`

**解决方案**:
1. 检查 `db_database` 是否正确
2. 确认数据库中存在 `data_stock` 和 `data_index` 表
3. 检查表名大小写是否匹配

### 问题 3: 数据为空

**错误信息**: `股票 xxx 在数据库中无数据`

**解决方案**:
1. 检查 `start_date` 和 `end_date` 范围是否合理
2. 确认数据库中该时间段有数据
3. 检查股票代码格式是否正确

### 问题 4: 批量查询失败

**错误信息**: `批量获取数据失败: ...，回退到逐只获取`

**解决方案**:
1. 这是正常的降级处理，脚本会自动回退到逐只查询
2. 如果频繁出现，可以减小 `batch_size`
3. 检查数据库连接是否稳定

---

## 配置检查清单

配置完成后，请检查：

**路径配置**:
- [ ] `csv_output_dir` 路径是否正确且有写入权限
- [ ] `qlib_workdir` 路径是否指向正确的 Qlib 源码目录
- [ ] `qlib_workdir/scripts/dump_bin.py` 文件是否存在
- [ ] `provider_uri` 路径是否正确且有写入权限

**数据库配置**:
- [ ] `db_host` 数据库地址是否正确
- [ ] `db_database` 数据库名称是否存在
- [ ] `db_user` 和 `db_password` 是否正确
- [ ] 数据库用户是否有 SELECT 权限
- [ ] 网络连接是否正常（如使用远程数据库）
- [ ] 防火墙是否开放数据库端口

**数据提取配置**:
- [ ] `market` 参数是否符合需求
- [ ] `start_date` 和 `end_date` 范围是否合理
- [ ] `batch_size` 是否适合当前环境

---
