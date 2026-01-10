# 数据库配置文件说明文档

## 配置文件结构

本项目使用两个数据库配置文件：

| 文件 | 用途 | 是否提交到 Git |
|-----|------|--------------|
| `config/db.example.yaml` | 配置模板，不包含敏感信息 | ✅ 是 |
| `config/db.yaml` | 实际配置，包含真实连接信息 | ❌ 否 |

## 配置项分组说明

### 1. 基础配置

```yaml
type: "mysql"          # 数据库类型
port: 3306             # 默认端口
chunk_size: 20000      # 数据批处理大小
workers: 4             # 并行工作进程数
```

### 2. 主数据库配置（host + database）

**用途：** 数据准备库，存储因子、风险、指数等**输入数据**

```yaml
host: "rm-bp1o6we7s3o1h76x1to.mysql.rds.aliyuncs.com"
database: "data_prepared_new"
user: "prod"
password: "Abcd1234#"
```

**相关表：**
- `table_name: "data_score_dev"` 【写入】模型预测分数

**数据读取：**
- 因子暴露数据（data_factorexposure）
- 因子协方差（data_factorcov）
- 特异风险（data_factorspecificrisk）
- 指数成分股（data_indexcomponent）
- 指数因子暴露（data_factorindexexposure）
- 股票池（data_factorpool）

### 3. 投资组合数据库（host + database2/database5）

**用途：** 存储优化后的投资组合权重和约束条件

```yaml
# 使用相同的 host
database2: "portfolio_new"
database5: "portfolio_new"
```

**相关表：**
- `table_name2: "portfolio_dev"` 【写入】投资组合权重（开发）
- `table_name4: "portfolio_info_dev"` 【写入】组合信息（开发）
- `table_name5: "portfolio_info"` 【写入】组合信息（生产）
- `table_name6: "portfolio_constraint"` 【读取】组合约束
- `table_name7: "factor_constraint"` 【读取】因子约束

### 4. 备用数据库（host2 + database3）

**用途：** 开发环境，用于特定 score 数据（如 vp08）

```yaml
host2: "rm-bp1o6we7s3o1h76x1to.mysql.rds.aliyuncs.com"  # 与主库相同
database3: "data_prepared_new"
# 使用主库的 user 和 password
```

**数据读取：**
- vp08 开发环境分数（data_score_dev）

### 5. Qlib 配置数据库（host3 + database4）

**用途：** 存储 Qlib 超参数搜索结果

```yaml
host3: "rm-cn-fhh4gzo9900083vo.rwlb.rds.aliyuncs.com"  # 不同的服务器
database4: "qlib"
user2: "yfr"  # 不同的用户
# 使用主库的 password
```

**相关表：**
- `table_name3: "best_params"` 【读写】最佳超参数

## Host 和 Database 映射关系

### 数据库连接拓扑图

```
主服务器 (host)
├── data_prepared_new (database)      【读取】输入数据 + 【写入】预测分数
└── portfolio_new (database2/5)       【读写】投资组合数据

备用服务器 (host2)
└── data_prepared_new (database3)     【读取】特定 score 数据

Qlib 服务器 (host3)
└── qlib (database4)                  【读写】超参数配置
```

### 连接字符串示例

```
连接 1 - 主数据库：
  mysql://prod:Abcd1234#@rm-bp1o6we7s3o1h76x1to.mysql.rds.aliyuncs.com:3306/data_prepared_new
  mysql://prod:Abcd1234#@rm-bp1o6we7s3o1h76x1to.mysql.rds.aliyuncs.com:3306/portfolio_new

连接 2 - 备用数据库：
  mysql://prod:Abcd1234#@rm-bp1o6we7s3o1h76x1to.mysql.rds.aliyuncs.com:3306/data_prepared_new

连接 3 - Qlib 数据库：
  mysql://yfr:Abcd1234#@rm-cn-fhh4gzo9900083vo.rwlb.rds.aliyuncs.com:3306/qlib
```

## 数据流向

### 输入数据（读取）

```
data_prepared_new (host)
├── data_factorexposure          # 因子暴露数据
├── data_factorcov               # 因子协方差矩阵
├── data_factorspecificrisk      # 特异风险
├── data_indexcomponent          # 指数成分股
├── data_factorindexexposure     # 指数因子暴露
└── data_factorpool              # 股票池

portfolio_new (host)
├── portfolio_constraint         # 投资组合约束
└── factor_constraint            # 因子约束

qlib (host3)
└── best_params                  # 最佳超参数（Optuna 结果）
```

### 输出数据（写入）

```
data_prepared_new (host)
└── data_score_dev               # 模型预测分数（开发环境）

portfolio_new (host)
├── portfolio_dev                # 投资组合权重（开发环境）
├── portfolio_info_dev           # 组合信息（开发环境）
└── portfolio_info               # 组合信息（生产环境）

qlib (host3)
└── best_params                  # 超参数搜索结果
```

## 配置标记说明

在配置文件中使用以下标记：

- **【读取】** - 仅从该表读取数据
- **【写入】** - 仅向该表写入数据
- **【读写】** - 既读取又写入数据

## 使用场景

### 场景 1：模型训练和预测

1. **读取** `data_prepared_new` (host) 的因子、风险、指数数据
2. 训练模型或加载已训练模型
3. **写入** 预测分数到 `data_score_dev` 表

### 场景 2：组合优化

1. **读取** `data_prepared_new` 的预测分数
2. **读取** `portfolio_new` 的约束条件
3. 运行优化器
4. **写入** 优化结果到 `portfolio_dev` 或 `portfolio_info`

### 场景 3：超参数调优

1. 运行 Optuna 搜索最佳参数
2. **写入** 最佳参数到 `qlib.best_params` (host3)
3. **读取** 最佳参数更新模型配置
4. 重新训练模型

### 场景 4：开发环境测试

1. **读取** `data_prepared_new` (host2) 的特定 score（如 vp08）
2. 测试新功能或算法
3. **写入** 结果到开发环境表

## 权限要求

### 主数据库 (user: prod)

- **读权限**：
  - `data_prepared_new` 数据库的所有表
  - `portfolio_new.portfolio_constraint`
  - `portfolio_new.factor_constraint`

- **写权限**：
  - `data_prepared_new.data_score_dev`
  - `portfolio_new.portfolio_dev`
  - `portfolio_new.portfolio_info_dev`
  - `portfolio_new.portfolio_info`

### Qlib 数据库 (user2: yfr)

- **读写权限**：
  - `qlib.best_params`

## 配置检查清单

在使用配置文件前，请确认：

- [ ] host 地址是否正确（包含端口号或使用默认端口）
- [ ] database 名称在服务器上是否存在
- [ ] user 用户名是否正确
- [ ] password 密码是否正确
- [ ] 用户是否有相应的数据库权限（SELECT/INSERT/UPDATE）
- [ ] 网络连接是否正常（如果是远程数据库）
- [ ] 防火墙是否允许连接
- [ ] 表名是否正确（区分开发环境和生产环境）

## 环境区分

### 开发环境表

- `data_score_dev`
- `portfolio_dev`
- `portfolio_info_dev`

### 生产环境表

- `data_score`（未配置，如需使用请修改 table_name）
- `portfolio`（未配置，如需使用请修改 table_name2）
- `portfolio_info`

## 常见问题

**Q: 为什么有 database2 和 database5？**

A: 都指向 `portfolio_new`，用于不同的代码模块读取。database2 用于主要的写入操作，database5 用于某些特定场景的读取。

**Q: host 和 host2 有什么区别？**

A: host 是主数据库服务器，host2 是备用服务器（在本配置中指向同一服务器）。host2 主要用于读取特定的 score 数据（如 vp08）。

**Q: user 和 user2 有什么区别？**

A: user 用于主数据库连接，user2 用于 Qlib 配置数据库（可能在不同服务器上，权限不同）。

**Q: 如何切换到生产环境？**

A: 修改表名配置：
- `table_name: "data_score"` （去掉 _dev）
- `table_name2: "portfolio"` （去掉 _dev）
- `table_name4: "portfolio_info"` （去掉 _dev）

## 配置示例对照

### 示例配置 (db.example.yaml)

```yaml
host: "localhost:3306"
database: "data_prepared_new"
user: "your_username"
password: "your_password"
```

### 实际配置 (db.yaml)

```yaml
host: "rm-bp1o6we7s3o1h76x1to.mysql.rds.aliyuncs.com"
database: "data_prepared_new"
user: "prod"
password: "Abcd1234#"
```

## 安全提醒

⚠️ **重要**:
- `db.yaml` 包含真实的用户名和密码，绝不应提交到 Git
- 定期更换密码，保持数据库安全
- 在生产环境中使用强密码
- 限制数据库用户的权限（最小权限原则）
- 定期审查数据库访问日志
