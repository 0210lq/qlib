# 数据库配置说明文档

## 文件说明

- **配置文件**: `db.yaml`
- **示例文件**: `db.example.yaml`

## 使用说明

1. 复制示例文件为配置文件: `cp db.example.yaml db.yaml`
2. 根据实际环境修改数据库连接信息
3. 注意：`db.yaml` 包含敏感信息，不会被提交到 Git

## 配置说明

- **【读取】** 标记的数据库/表：用于读取输入数据
- **【写入】** 标记的数据库/表：用于写入输出结果
- **【读写】** 标记的数据库/表：既读取又写入

---

## 基础配置

### type
- **说明**: 数据库类型（固定为 mysql）
- **默认值**: `"mysql"`

### port
- **说明**: 默认端口
- **默认值**: `3306`

### chunk_size
- **说明**: 数据批处理大小
- **影响**: 影响内存占用和处理速度
- **默认值**: `20000`

### workers
- **说明**: 并行工作进程数
- **建议**: 不超过 CPU 核心数
- **默认值**: `4`

---

## 主数据库配置 - 数据准备库【读取】

**用途**: 存储因子数据、风险数据、指数成分股等输入数据
**用于**: 数据读取、模型训练、预测

### host
- **说明**: 主机地址
- **格式**: `hostname:port` 或 `hostname`
- **示例**: `"localhost:3306"`

### database
- **说明**: 数据库名称
- **示例**: `"data_prepared_new"`

### user
- **说明**: 用户名
- **示例**: `"your_username"`

### password
- **说明**: 密码
- **示例**: `"your_password"`

### table_name
- **说明**: 【写入】分数数据表（模型预测输出）
- **示例**: `"data_score"`

---

## 投资组合数据库配置【写入】

**用途**: 存储优化后的投资组合权重、约束条件等输出数据
**用于**: 权重写入、回测分析

### database2
- **说明**: 数据库名称（与主数据库在同一主机）
- **示例**: `"portfolio_new"`

### table_name2
- **说明**: 【写入】投资组合权重表
- **示例**: `"portfolio"`

### table_name4
- **说明**: 【写入】投资组合信息表
- **示例**: `"portfolio_info"`

### table_name5
- **说明**: 【写入】投资组合详细信息表
- **示例**: `"portfolio_info"`

### table_name6
- **说明**: 【读取】投资组合约束条件表
- **示例**: `"portfolio_constraint"`

### table_name7
- **说明**: 【读取】因子约束条件表
- **示例**: `"factor_constraint"`

---

## 备用数据库配置 - 开发环境【读写】

**用途**: 用于特定的开发/测试数据源
**用于**: 某些特定的 score 数据读取

### host2
- **说明**: 主机地址
- **示例**: `"localhost:3306"`

### database3
- **说明**: 数据库名称
- **示例**: `"data_prepared_new"`
- **注意**: 使用与主数据库相同的用户名和密码

---

## Qlib 配置数据库【读写】

**用途**: 存储 Qlib 的超参数搜索结果
**用于**: 读取最佳参数、更新模型配置

### host3
- **说明**: 主机地址
- **示例**: `"localhost:3306"`

### database4
- **说明**: 数据库名称
- **示例**: `"qlib"`

### user2
- **说明**: 用户名（可以使用不同的用户）
- **示例**: `"your_username"`

### table_name3
- **说明**: 【读写】最佳参数表（Optuna 搜索结果）
- **示例**: `"best_params"`

**注意**:
- 使用主数据库的密码
- 如果需要不同密码，请添加 `password2` 配置

---

## 数据流向说明

### 数据读取流程

#### 1. 从 data_prepared_new 读取：
- 因子数据（data_factorexposure）
- 风险数据（data_factorcov, data_factorspecificrisk）
- 指数数据（data_indexcomponent, data_factorindexexposure）
- 股票池（data_factorpool）

#### 2. 从 portfolio_new 读取：
- 约束条件（portfolio_constraint, factor_constraint）

#### 3. 从 qlib 读取：
- 最佳参数（best_params）

### 数据写入流程

#### 1. 写入 data_prepared_new：
- 预测分数（data_score）

#### 2. 写入 portfolio_new：
- 投资组合权重（portfolio）
- 组合信息（portfolio_info）

#### 3. 写入 qlib：
- 超参数搜索结果（best_params）

---

## 数据库连接示例

### 主数据库连接：
```
mysql://user:password@host:port/database
示例：mysql://prod:Abcd1234#@localhost:3306/data_prepared_new
```

### Qlib 数据库连接：
```
mysql://user2:password@host3:port/database4
示例：mysql://yfr:Abcd1234#@localhost:3306/qlib
```

---

## 配置检查清单

配置完成后，请检查：

- [ ] host 地址是否正确（包含端口号）
- [ ] database 名称是否存在
- [ ] user 用户名是否正确
- [ ] password 密码是否正确
- [ ] 用户是否有相应的数据库权限（读/写）
- [ ] 网络连接是否正常（如果是远程数据库）
- [ ] 防火墙是否允许连接
