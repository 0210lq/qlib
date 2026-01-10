# Qlib Optimizer

这是一个用于量化策略训练、预测与优化的仓库，结合了 Qlib（用于数据和模型流程）和 Matlab 优化脚本，包含数据导入、模型训练/预测、以及将预测结果写入数据库的流程。

## 目录概览

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细安装步骤](#详细安装步骤)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [项目结构](#项目结构)
- [常见问题](#常见问题)

## 系统要求

### 必需环境

- **Python**: 3.10 或更高版本（推荐 3.12）
- **MATLAB**: R2018b 或更高版本（用于优化和回测）
- **MySQL**: 用于数据存储和读取
- **Git**: 用于克隆 qlib 仓库

### 推荐工具

- **Conda**: 可选的环境管理工具

## 主要功能

- 从数据库或外部数据源（例如 Tushare）构建 Qlib 二进制数据并运行模型做单日预测
- 使用 Matlab 脚本对预测分数做组合优化并回测（`Optimizer_matlab/`）
- 提供示例的超参数搜索（Optuna）脚本与 qrun 配置，方便在 Qlib 上训练/调参

## 仓库结构概览

- `qlib_code/` — Qlib 相关的 Python 脚本与工具：
  - `run_daily_update.py` — 日常流水线入口：拉取/转换数据（调用 qlib 的 dump_bin）、运行预测、导出 CSV、写入 DB
  - `update_new.py` — 加载训练好的模型并对指定日期生成预测文件
  - `sql2csv.py`、`importer.py` — 数据获取与导入工具
  - `hyperparameter_lgbm.py` — Optuna 超参搜索示例（LightGBM）
  - `import_weight_to_mysql.py` — 将导出的权重/回测结果导入 MySQL 的工具
  - `update_yaml.py` — 将优化得到的超参数自动写入配置文件的工具

- `Optimizer_matlab/` — Matlab 优化与回测：
  - `run_optimizer.m`, `run_backtest.m`, `batch_run_optimizer.m` 等脚本
  - `BacktestToolbox/` — 回测工具集（多个辅助函数）
  - `config/` — Matlab 端的配置（数据库、项目参数等）

- `config/` — YAML 配置（项目根目录）：
  - `paths.yaml` — provider uri、模型路径、预测输出目录等
  - `db.yaml` — 数据库连接配置（用于 Python / Matlab 的导入器）
  - `db.example.yaml` — 数据库配置示例文件

- `logs/` — 运行日志
  - `score_prediction_日期.log` — 生成预测分数时候的log
  - `weight_optimizer_日期.log` — 优化得到权重时候的log

- `requirements.txt` — Python 依赖清单（用于创建虚拟环境）

## 快速开始



### 方法一：使用 Conda

**Windows (PowerShell):**

```powershell
# 创建并激活虚拟环境
conda create -n qlib_env python=3.12 -y
conda activate qlib_env

# 安装依赖
pip install -r requirements.txt

# 复制修改后的源代码到虚拟环境
Copy-Item -Path "record_temp.py" -Destination "\path\to\your\conda\envs\qlib_env\Lib\site-packages\qlib\workflow\record_temp.py" -Force
```

**Linux:**

```bash
# 创建并激活虚拟环境
conda create -n qlib_env python=3.12 -y
conda activate qlib_env

# 安装依赖
pip install -r requirements.txt

# 复制修改后的源代码到虚拟环境
sudo cp record_temp.py /home/your_username/miniconda3/envs/qlib_env/lib/python3.12/site-packages/qlib/workflow/record_temp.py
```

### 方法二：使用标准 Python venv

**Windows (PowerShell):**

Windows 下 PyTorch 的 c10.dll 依赖了较新版本的 Microsoft Visual C++ Redistributable（俗称 VC_redist）。

安装包

https://aka.ms/vs/17/release/vc_redist.x64.exe

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 应用补丁
Copy-Item -Path "record_temp.py" -Destination ".\venv\Lib\site-packages\qlib\workflow\record_temp.py" -Force
```

**Linux:**

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 应用补丁
cp record_temp.py "./venv/lib/python3.12/site-packages/qlib/workflow/record_temp.py"s
```

## 详细安装步骤

### 1. 克隆仓库

```bash
git clone <repository-url>
cd qlib-optimizer
```

### 2. 安装 Python 依赖

按照上述"快速开始"中的任一方法安装依赖。

### 3. 配置项目文件

#### 3.1 配置数据库连接

项目提供了示例配置文件，请根据实际情况进行配置：

**Python 配置文件：**

```bash
# Linux/Mac
cp config/db.example.yaml config/db.yaml

# Windows (PowerShell)
Copy-Item config\db.example.yaml config\db.yaml
```

然后编辑 `config/db.yaml`，填入实际的数据库连接信息：
- `host`: MySQL 服务器地址
- `port`: MySQL 端口（默认 3306）
- `user`: 数据库用户名
- `password`: 数据库密码
- `database`: 数据库名称
- 其他相关配置项

**MATLAB 配置文件：**

```bash
# Linux/Mac
cp Optimizer_matlab/config/config_db.example.m Optimizer_matlab/config/config_db.m

# Windows (PowerShell)
Copy-Item Optimizer_matlab\config\config_db.example.m Optimizer_matlab\config\config_db.m
```

然后编辑 `Optimizer_matlab/config/config_db.m`，填入实际的数据库连接信息。

#### 3.2 配置路径文件

编辑 `config/paths.yaml`，根据你的实际环境修改以下路径：
- `csv_output_dir`: CSV 数据输出目录
- `provider_uri`: Qlib 二进制数据目录
- `model_path`: 训练好的模型路径
- `prediction_output_dir`: 预测结果输出目录
- `python_exe`: Python 可执行文件路径（如果使用 MATLAB 调用 Python）
- `yaml_matlab`: YAMLMatlab 工具路径

### 4. 准备 Qlib

仓库不会内置 qlib 的 `dump_bin.py`，请按需 clone 官方 qlib：

```bash
git clone https://github.com/microsoft/qlib.git
```

然后确保在 PATH 或脚本中能找到 qlib 的工具，或在 `config/paths.yaml` 中配置 `qlib_workdir` 路径。

### 5. 准备数据

准备 qlib 需要的 CSV 数据，运行：

```bash
# 从数据库导出数据
python qlib_code/sql2csv.py

# 或从 Tushare 获取数据
python qlib_code/tushare2csv.py
```

## 配置说明

### 配置文件说明

项目使用以下配置文件：

1. **`config/db.yaml`** - Python 端数据库配置
   - 包含多个数据库连接配置
   - 包含表名、chunk_size、workers 等参数
   - ⚠️ **注意**: 此文件包含敏感信息，不会被提交到 Git
   - 首次使用请复制 `config/db.example.yaml` 并重命名为 `db.yaml`

2. **`config/paths.yaml`** - 路径配置
   - 包含数据目录、模型路径、输出目录等
   - 需要根据实际环境修改路径

3. **`Optimizer_matlab/config/config_db.m`** - MATLAB 端数据库配置
   - MATLAB 脚本使用的数据库连接配置
   - ⚠️ **注意**: 此文件包含敏感信息，不会被提交到 Git
   - 首次使用请复制 `Optimizer_matlab/config/config_db.example.m` 并重命名为 `config_db.m`

4. **`Optimizer_matlab/config/opt_project_config_*.xlsx`** - MATLAB 优化器项目配置
   - 包含优化器的参数配置

### 示例文件使用

项目提供了示例配置文件（`.example` 文件），这些文件不包含敏感信息，可以安全地提交到 Git：

- `config/db.example.yaml` - 数据库配置示例
- `Optimizer_matlab/config/config_db.example.m` - MATLAB 数据库配置示例

**使用步骤：**

1. 复制示例文件为实际配置文件
2. 编辑配置文件，填入实际的连接信息
3. 确保配置文件不会被提交到 Git（已在 `.gitignore` 中配置）

## 使用方法

### 运行日常预测流水线

在仓库根目录并激活虚拟环境后运行：

**使用 MATLAB（推荐）：**

```bash
# Windows
matlab .\main_daily.m

# Linux
matlab -r "run('main_daily.m')"
```

**或直接使用 Python：**

```bash
# Windows
python .\qlib_code\run_daily_update.py --date 2025-10-27

# Linux
python qlib_code/run_daily_update.py --date 2025-10-27
```

### 运行历史预测流水线

```bash
# Windows
matlab .\main_history.m

# Linux
matlab -r "run('main_history.m')"
```

该流程通常会：
- 拉取或读取最新 CSV 数据
- 调用 qlib 的 `dump_bin.py` 将 CSV 转为 qlib 格式（需提前准备 qlib）
- 加载已训练的模型并运行 `update_new.py` 以产出 `prediction_YYYYMMDD.csv`
- 根据 `config/db.yaml` 将结果写入数据库
- 调用 Matlab 优化器（可选）生成并导出权重数据

输出位置：`config/paths.yaml` 中的 `prediction_output_dir`（默认为仓库内某目录，请检查配置）。

### 使用 Matlab 优化

`Optimizer_matlab/` 内包含基于预测分数的优化与回测脚本。典型流程：

- 将生成的 `prediction_YYYYMMDD.csv` 提供给 Matlab 脚本作为 score 源（或从数据库中读取）
- 运行 `run_optimizer.m` 来生成组合权重

### 模型训练与超参数调优（Optuna + qrun）

1. 运行超参搜索脚本：

```bash
# Windows
python .\qlib_code\hyperparameter_lgbm.py

# Linux
python qlib_code/hyperparameter_lgbm.py
```

可以调整脚本里面的 `n_trials` 参数，去控制模型训练次数。

2. 更新配置文件：

```bash
# Windows
python .\qlib_code\update_yaml.py

# Linux
python qlib_code/update_yaml.py
```

3. 执行 qrun，生成需要的模型：

```bash
qrun qlib_code/workflow_config_lightgbm.yaml
```

注意：运行 `qrun` 时，请在工作目录中正确放置或引用配置文件路径。

## 项目结构

```
qlib-optimizer/
├── config/                          # 配置文件目录
│   ├── db.yaml                      # 数据库配置（不提交到 Git）
│   ├── db.example.yaml              # 数据库配置示例
│   └── paths.yaml                   # 路径配置
├── Optimizer_matlab/                # MATLAB 优化器
│   ├── config/
│   │   ├── config_db.m              # MATLAB 数据库配置（不提交到 Git）
│   │   ├── config_db.example.m      # MATLAB 数据库配置示例
│   │   └── opt_project_config_*.xlsx # 优化器项目配置
│   ├── BacktestToolbox/             # 回测工具集
│   ├── tools/                       # 工具函数
│   ├── utils/                       # 工具函数
│   └── *.m                          # MATLAB 脚本
├── qlib_code/                       # Python 代码
│   ├── *.py                         # Python 脚本
│   └── workflow_config_*.yaml       # Qlib 工作流配置
├── logs/                            # 日志目录
├── main_daily.m                     # 日常预测入口
├── main_history.m                   # 历史预测入口
├── requirements.txt                 # Python 依赖
├── .gitignore                       # Git 忽略文件
└── README.md                        # 本文档
```

## 常见问题与排查建议

### 安装问题

- **uv 安装失败**: 确保网络连接正常，或使用 pip 安装：`pip install uv`
- **依赖安装缓慢**: 使用 uv 可以显著加快安装速度
- **虚拟环境激活失败**: 
  - Windows: 确保 PowerShell 执行策略允许运行脚本：`Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
  - Linux: 确保有执行权限：`chmod +x venv/bin/activate`

### 配置问题

- **找不到配置文件**: 确保已从示例文件创建实际配置文件（`db.yaml` 和 `config_db.m`）
- **数据库连接失败**: 
  - 检查 `config/db.yaml` 和 `Optimizer_matlab/config/config_db.m` 的连接信息
  - 确保数据库服务器可访问且防火墙规则正确
  - 验证用户名和密码是否正确

### 运行问题

- **`run_daily_update.py` 未能找到 qlib 的 `dump_bin.py`**: 
  - 确认已 clone qlib 仓库
  - 检查 `config/paths.yaml` 中的 `qlib_workdir` 配置
  - 或将 qlib 路径加入环境变量 PATH

- **数据库写入失败**: 
  - 检查 `config/db.yaml` 的连接信息
  - 确保目标数据库可访问且表权限正确
  - 查看日志文件获取详细错误信息

- **MATLAB 运行问题**: 
  - 确认 MATLAB 的路径和依赖（如 `yamlmatlab`）已安装
  - 检查 MATLAB 脚本中引用的配置文件路径是否正确
  - 确保 `config/paths.yaml` 中的 `yaml_matlab` 路径正确

- **Python 脚本执行失败**: 
  - 确保虚拟环境已激活
  - 检查 Python 版本是否符合要求（3.10+）
  - 查看错误日志获取详细信息

### 性能优化

- **安装速度慢**: 使用 uv 替代 pip 可以显著提升安装速度
- **数据加载慢**: 检查数据库连接配置和网络状况
- **模型训练慢**: 考虑使用 GPU 或调整 `workers` 参数

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

[在此添加许可证信息]
