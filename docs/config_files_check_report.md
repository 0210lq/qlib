# 配置文件检查报告

## 检查日期
2026-01-10

## 检查结果

### ✅ 所有数据库配置文件都已有 example 版本

| 配置文件类型 | 实际配置文件 | 示例配置文件 | 状态 |
|------------|------------|------------|------|
| Python 数据库配置 | `config/db.yaml` | `config/db.example.yaml` | ✅ 已创建 |
| Python 路径配置 | `config/paths.yaml` | `config/paths.example.yaml` | ✅ 已创建 |
| MATLAB 数据库配置 | `Optimizer_matlab/config/config_db.m` | `Optimizer_matlab/config/config_db.example.m` | ✅ 已创建 |

## 创建的文件

### 1. config/db.example.yaml
- ✅ 新创建
- 内容：Python 端数据库连接配置示例
- 包含：主数据库、备用数据库、表名、性能参数等配置
- 特点：包含详细的中文注释和配置说明

### 2. config/paths.example.yaml
- ✅ 之前已创建
- 内容：路径配置示例
- 包含：相对路径、环境变量、变量引用等多种配置方式
- 特点：跨平台兼容，支持灵活的路径配置

### 3. Optimizer_matlab/config/config_db.example.m
- ✅ 新创建
- 内容：MATLAB 端数据库连接配置示例
- 包含：数据库连接信息、score 数据源配置
- 特点：MATLAB 格式的配置脚本，包含使用说明

### 4. Optimizer_matlab/config/ 目录
- ✅ 新创建目录
- 用途：存放 MATLAB 配置文件

## 配置文件说明

### config/db.example.yaml

**主要配置项：**
```yaml
# 数据库连接
user: "your_username"
password: "your_password"
host: "localhost:3306"

# 数据库名称
database: "data_prepared_new"
database2: "portfolio_new"

# 性能配置
chunk_size: 20000
workers: 4
```

**特点：**
- 支持多个数据库配置（主库、备用库等）
- 包含性能调优参数（chunk_size, workers）
- 支持多个表名配置
- 详细的中文注释

### Optimizer_matlab/config/config_db.example.m

**主要配置项：**
```matlab
% 数据库连接
db_config.host = 'localhost:3306';
db_config.username = 'your_username';
db_config.password = 'your_password';
db_config.dbname = 'data_prepared_new';

% Score 数据源
db_config.score_source = 'csv';  % 'db' 或 'csv'
db_config.local_score_dir = '../qlib_data/output/prediction';
```

**特点：**
- MATLAB 结构体格式
- 支持从数据库或 CSV 文件读取 score 数据
- 包含详细的配置说明和使用示例

## .gitignore 配置

已确保以下文件不会被提交到 Git：

```gitignore
# 实际配置文件（包含敏感信息）
config/db.yaml
config/paths.yaml
Optimizer_matlab/config/config_db.m

# 保留示例文件
!config/db.example.yaml
!config/paths.example.yaml
!Optimizer_matlab/config/config_db.example.m
```

## 使用指南

### 首次配置步骤

**1. 复制示例文件**

```bash
# Python 配置
cp config/db.example.yaml config/db.yaml
cp config/paths.example.yaml config/paths.yaml

# MATLAB 配置
cp Optimizer_matlab/config/config_db.example.m Optimizer_matlab/config/config_db.m
```

**2. 编辑配置文件**

修改以下文件，填入实际的连接信息：
- `config/db.yaml` - Python 数据库配置
- `config/paths.yaml` - 路径配置
- `Optimizer_matlab/config/config_db.m` - MATLAB 数据库配置

**3. 验证配置**

Python 验证：
```python
import yaml
with open('config/db.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print(config)
```

MATLAB 验证：
```matlab
addpath('Optimizer_matlab/config');
config_db;
disp(db_config);
```

## 安全说明

⚠️ **重要提醒：**

1. **.example 文件**：
   - 不包含真实的连接信息
   - 可以安全提交到 Git
   - 用作配置模板

2. **实际配置文件**：
   - 包含敏感信息（用户名、密码、主机地址）
   - 已添加到 .gitignore，不会被提交
   - 仅保存在本地

3. **团队协作**：
   - 每个开发者从 example 文件创建自己的配置
   - 不会共享敏感信息
   - 便于维护统一的配置格式

## 检查清单

- [x] 创建 config/db.example.yaml
- [x] 创建 config/paths.example.yaml
- [x] 创建 Optimizer_matlab/config 目录
- [x] 创建 Optimizer_matlab/config/config_db.example.m
- [x] 更新 .gitignore
- [x] 所有配置文件包含详细注释
- [x] 所有配置文件使用安全的示例值
- [x] README.md 包含配置说明

## 后续建议

1. **自动化配置脚本**：
   - 使用 `setup_config.py` 自动创建配置文件
   - 运行：`python setup_config.py`

2. **配置验证**：
   - 添加配置文件格式验证
   - 添加数据库连接测试脚本

3. **文档完善**：
   - 在 README.md 中添加详细的配置说明
   - 提供常见配置错误的解决方案
