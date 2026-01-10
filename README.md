# Qlib Optimizer

这是一个用于量化策略训练、预测与优化的仓库，结合了 Qlib（用于数据和模型流程）和 Matlab 优化脚本，包含数据导入、模型训练/预测、以及将预测结果写入数据库的流程。

## 目录概览

- [系统要求](#系统要求)
- [主要功能](#主要功能)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [项目结构](#项目结构)
- [常见问题](#常见问题)

## 系统要求

### 必需环境

- **Anaconda**: 用于 Python 环境管理（[下载地址](https://www.anaconda.com/download)）
- **Python**: 3.10 或更高版本（推荐 3.12，通过 Anaconda 安装）
- **MySQL**: 用于数据存储和读取
- **Git**: 用于克隆仓库

### 可选环境

- **MATLAB**: R2018b 或更高版本（用于优化和回测）

## 主要功能

- 从数据库或外部数据源（例如 Tushare）构建 Qlib 二进制数据并运行模型做单日预测
- 使用 Matlab 脚本对预测分数做组合优化并回测（`Optimizer_matlab/`）
- 提供示例的超参数搜索（Optuna）脚本与 qrun 配置，方便在 Qlib 上训练/调参

## 仓库结构概览

- `qlib_code/` — Qlib 相关的 Python 脚本与工具：
  - `run_daily_update.py` — 日常流水线入口：智能数据转换、模型预测（支持自动路径处理和模式检测）
  - `update_new.py` — 加载训练好的模型并对指定日期生成预测文件
  - `update_latest_days.py` — 从数据库获取最新交易日数据
  - `sql2csv.py`、`tushare2csv.py` — 数据获取与导入工具
  - `hyperparameter_lgbm.py` — Optuna 超参搜索示例（LightGBM）
  - `import_weight_to_mysql.py` — 将导出的权重/回测结果导入 MySQL 的工具
  - `update_yaml.py` — 将优化得到的超参数自动写入配置文件的工具
  - `sync_provider_uri.py` — 同步 provider_uri 配置
  - `check_qlib_data.py` — Qlib 数据诊断工具

- `Optimizer_matlab/` — Matlab 优化与回测：
  - `run_optimizer.m`, `run_backtest.m`, `batch_run_optimizer.m` 等脚本
  - `BacktestToolbox/` — 回测工具集（多个辅助函数）
  - `config/` — Matlab 端的配置（数据库、项目参数等）

- `config/` — YAML 配置（项目根目录）：
  - `paths.yaml` — provider uri、模型路径、预测输出目录等
  - `db.yaml` — 数据库连接配置（用于 Python / Matlab 的导入器）
  - `db.example.yaml` — 数据库配置示例文件

- `logs/` — 运行日志（自动创建）
  - `score_prediction_日期.log` — 生成预测分数时候的log
  - `weight_optimizer_日期.log` — 优化得到权重时候的log

- `requirements.txt` — Python 依赖清单（用于创建虚拟环境）

## 快速开始

### 前置要求

- **Anaconda**: 用于 Python 环境管理（[下载地址](https://www.anaconda.com/download)）
- **Python**: 3.10 或更高版本（推荐 3.12，通过 Anaconda 安装）
- **MySQL**: 已安装并运行
- **Git**: 用于克隆仓库
- **MATLAB**: R2018b 或更高版本（可选，用于优化和回测）

**Windows 用户注意**: PyTorch 需要 Microsoft Visual C++ Redistributable，请先安装：
https://aka.ms/vs/17/release/vc_redist.x64.exe

### 安装步骤

**1. 克隆仓库并进入目录**

```bash
git clone <repository-url>
cd qlib_sql-master
```

**2. 创建 Conda 虚拟环境并安装依赖**

```bash
# 创建虚拟环境
conda create -n qlib_env python=3.12 -y

# 激活虚拟环境
conda activate qlib_env

# 安装依赖
pip install -r requirements.txt
```

**3. 应用 Qlib 补丁**

```bash
# Windows (PowerShell)
Copy-Item -Path "record_temp.py" -Destination "$env:CONDA_PREFIX\Lib\site-packages\qlib\workflow\record_temp.py" -Force

# Linux/Mac
cp record_temp.py "$CONDA_PREFIX/lib/python3.12/site-packages/qlib/workflow/record_temp.py"
```

**4. 配置数据库连接**

```bash
# 复制配置文件模板
# Windows (PowerShell)
Copy-Item config\db.example.yaml config\db.yaml
Copy-Item config\paths.example.yaml config\paths.yaml
Copy-Item Optimizer_matlab\config\config_db.example.m Optimizer_matlab\config\config_db.m

# Linux/Mac
cp config/db.example.yaml config/db.yaml
cp config/paths.example.yaml config/paths.yaml
cp Optimizer_matlab/config/config_db.example.m Optimizer_matlab/config/config_db.m
```

编辑 `config/db.yaml`，填入你的 MySQL 连接信息。

**5. 配置路径**

编辑 `config/paths.yaml`，根据实际环境修改路径配置：

**推荐配置（使用相对路径）：**
```yaml
# 数据基础目录（项目外部）
base_dir: "../qlib_data"

# Qlib 仓库路径（项目内，已包含）
qlib_workdir: "./qlib"

# 模型路径（推荐使用项目内路径）
model_path: "./models/trained_model.pkl"

# Python 执行路径（使用当前激活的环境）
python_exe: "python"
```

**说明：**
- `base_dir`: 数据存储基础目录，推荐使用项目外的相对路径
- `qlib_workdir`: Qlib 源码路径，项目已包含，使用 `"./qlib"`
- `model_path`: 模型文件路径，推荐使用项目内路径 `"./models/"`
- 相对路径会自动转换为基于项目根目录的绝对路径
- 支持环境变量：`${HOME}` (Linux/Mac) 或 `${USERPROFILE}` (Windows)
- 更多配置说明请查看 `config/paths.example.yaml` 中的详细注释

**6. 准备数据**

> **注意**: Qlib 源码已包含在项目的 `qlib/` 目录中，无需单独克隆。

```bash
# 导出数据（选择其一）
python qlib_code/sql2csv.py        # 从数据库导出
# 或
python qlib_code/tushare2csv.py    # 从 Tushare 获取
```

**7. 运行预测**

```bash
# 使用 Python 运行日常预测
python qlib_code/run_daily_update.py --date 2025-10-27

# 或使用 MATLAB（需要安装 MATLAB）
matlab -r "run('main_daily.m')"
```


## 配置说明

### 核心配置文件

| 配置文件 | 说明 | 示例文件 | 是否提交到 Git |
|---------|------|---------|---------------|
| `config/db.yaml` | Python 端数据库配置 | `config/db.example.yaml` | ❌ 否（包含敏感信息） |
| `config/paths.yaml` | 路径配置（数据、模型、输出目录等） | `config/paths.example.yaml` | ❌ 否（包含本地路径） |
| `Optimizer_matlab/config/config_db.m` | MATLAB 端数据库配置 | `Optimizer_matlab/config/config_db.example.m` | ❌ 否（包含敏感信息） |
| `Optimizer_matlab/config/opt_project_config_*.xlsx` | MATLAB 优化器项目配置 | 无（直接修改） | ✅ 可以 |

### 配置安全说明

⚠️ **重要**:
- 所有 `.example` 文件都是模板，不包含敏感信息和本地路径，可以安全提交到 Git
- 实际配置文件（如 `db.yaml`、`paths.yaml`、`config_db.m`）已添加到 `.gitignore`
- 首次使用时必须从示例文件复制并填入实际配置

### 主要配置项

**`config/db.yaml`** - 数据库连接配置：
- `host`: MySQL 服务器地址
- `port`: MySQL 端口（默认 3306）
- `user`: 数据库用户名
- `password`: 数据库密码
- `database`: 数据库名称
- `chunk_size`: 数据批处理大小
- `workers`: 并行工作进程数

**`config/paths.yaml`** - 路径配置：

推荐使用相对路径或环境变量，避免硬编码绝对路径。配置示例：

```yaml
# 基础目录（推荐使用相对路径）
base_dir: "../qlib_data"

# CSV 数据目录
csv_output_dir: "${base_dir}/csv_data"
csv_daily_dir: "${base_dir}/daily"

# Qlib 相关路径
provider_uri: "${base_dir}/qlib_bin"
qlib_workdir: "./qlib"  # Qlib 源码在项目内

# 模型和预测路径（推荐使用项目内路径）
model_path: "./models/trained_model.pkl"  # 项目内模型路径，避免复制
prediction_output_dir: "${base_dir}/output/prediction"

# Python 执行路径（推荐使用 "python" 自动检测）
python_exe: "python"
```

**支持的路径格式：**
- 相对路径：`"../qlib_data"`、`"./models"`
- 环境变量：`"${HOME}/qlib_data"` (Linux/Mac)、`"${USERPROFILE}\\qlib_data"` (Windows)
- 变量引用：`"${base_dir}/csv_data"`

详细配置说明请参考 `config/paths.example.yaml` 文件中的注释。

### 配置管理工具

#### Provider URI 同步

为了避免配置不一致，`provider_uri` (Qlib 数据路径) 统一在 `config/paths.yaml` 中管理。

修改数据路径后，需要同步到 workflow 配置文件：

```bash
# 方法 1: 只同步路径配置（推荐）
python qlib_code/sync_provider_uri.py

# 方法 2: 同步路径并更新模型参数（需要数据库连接）
python qlib_code/update_yaml.py
```

**工作流程：**

```
config/paths.yaml (主配置)
        ↓ (自动同步)
qlib_code/workflow_config_lightgbm.yaml
        ↓ (qrun 使用)
    Qlib 数据加载
```

**注意事项：**
- ✅ 修改 `config/paths.yaml` 后运行同步脚本
- ❌ 不要直接修改 `workflow_config_lightgbm.yaml` 的 `provider_uri`

详细说明请参考 [Provider URI 配置管理指南](docs/provider_uri_config_guide.md)。

### 智能特性

项目包含多项自动化特性，简化使用流程：

#### 1. 自动路径处理

**相对路径自动转换**：
- 所有相对路径（如 `"./qlib"`、`"../qlib_data"`）会自动转换为基于项目根目录的绝对路径
- 无需担心当前工作目录的影响
- 支持跨平台路径格式

**示例**：
```yaml
# config/paths.yaml
qlib_workdir: "./qlib"              # → E:\jzq\qlib\qlib
provider_uri: "../qlib_data/qlib_bin"  # → E:\jzq\qlib_data\qlib_bin
model_path: "./models/model.pkl"    # → E:\jzq\qlib\models\model.pkl
```

#### 2. 智能模式检测

**dump_all vs dump_update 自动选择**：
- 首次运行：检测到 Qlib 数据不存在，自动使用 `dump_all`（全量导入）
- 后续运行：检测到 Qlib 数据已存在，自动使用 `dump_update`（增量更新）
- 性能提升：增量更新速度约为全量导入的 30-50 倍

**判断依据**：检查 `{provider_uri}/calendars/day.txt` 是否存在

#### 3. 自动目录创建

**无需手动创建目录**：
- `logs/` 目录在首次运行时自动创建
- 数据目录（如 `daily/YYYYMMDD/`）自动创建
- 中间目录（如 `qlib_bin/calendars/`）自动创建

#### 4. 日期参数智能处理

**指定日期时**：
- 自动使用对应日期的数据目录
- 格式转换：`2026-01-09` → `20260109`
- 环境变量传递到所有子脚本

**不指定日期时**：
- 自动使用当天日期
- 或使用最新修改的数据目录（向后兼容）

**相关文档**：
- [数据路径流程验证](docs/data_path_flow_verification.md)
- [Dump 模式自动检测](docs/dump_mode_auto_detection.md)
- [自动创建日志目录](docs/auto_create_logs_dir.md)

## 使用方法

### 1. 日常预测流水线

**方式一：使用 Python**

```bash
python qlib_code/run_daily_update.py --date 2026-01-09
```

**方式二：使用 MATLAB（推荐）**

```bash
# Windows
matlab -r "run('main_daily.m')"

# Linux
matlab -r "run('main_daily.m')"
```

**脚本特性**：
- ✅ **自动路径处理**: 相对路径自动转换为绝对路径
- ✅ **智能模式检测**: 首次运行自动全量导入，后续自动增量更新
- ✅ **自动创建目录**: logs 目录自动创建
- ✅ **日期参数传递**: 指定日期后自动使用对应的数据目录

**执行流程**：
1. 从数据库获取指定日期的 CSV 数据 → `../qlib_data/daily/YYYYMMDD/`
2. 智能检测并选择数据转换模式：
   - 首次运行：使用 `dump_all` (全量导入)
   - 后续运行：使用 `dump_update` (增量更新)
3. 转换 CSV 为 Qlib 二进制格式 → `../qlib_data/qlib_bin/`
4. 加载训练好的模型 (`./models/trained_model.pkl`)
5. 生成预测结果并写入数据库
6. 可选：调用 MATLAB 优化器生成组合权重

### 2. 历史预测流水线

```bash
# Windows
matlab -r "run('main_history.m')"

# Linux
matlab -r "run('main_history.m')"
```

### 3. MATLAB 组合优化

基于预测分数进行组合优化与回测：

```matlab
% 运行单次优化
run_optimizer.m

% 批量运行优化
batch_run_optimizer.m

% 运行回测
run_backtest.m
```

### 4. 模型训练与超参数调优

**步骤一：超参数搜索（使用 Optuna）**

```bash
python qlib_code/hyperparameter_lgbm.py
```

可以在脚本中调整 `n_trials` 参数控制训练次数。

**步骤二：更新配置文件**

```bash
python qlib_code/update_yaml.py
```

**步骤三：训练模型**

```bash
qrun qlib_code/workflow_config_lightgbm.yaml
```

### 5. 权重导入数据库

```bash
python qlib_code/import_weight_to_mysql.py
```

## 项目结构

```
qlib_sql-master/
├── config/                              # 配置文件目录
│   ├── db.yaml                          # 数据库配置（不提交到 Git）
│   ├── db.example.yaml                  # 数据库配置示例
│   └── paths.yaml                       # 路径配置
│
├── Optimizer_matlab/                    # MATLAB 优化器
│   ├── config/
│   │   ├── config_db.m                  # MATLAB 数据库配置（不提交到 Git）
│   │   ├── config_db.example.m          # MATLAB 数据库配置示例
│   │   └── opt_project_config_*.xlsx    # 优化器项目配置
│   ├── BacktestToolbox/                 # 回测工具集
│   ├── tools/                           # 工具函数
│   ├── utils/                           # 工具函数
│   └── *.m                              # MATLAB 脚本
│
├── qlib/                                # Qlib 源码（已包含在项目中）
│
├── qlib_code/                           # Python 代码
│   ├── run_daily_update.py              # 日常流水线入口
│   ├── update_new.py                    # 预测生成脚本
│   ├── sql2csv.py / tushare2csv.py      # 数据获取工具
│   ├── hyperparameter_lgbm.py           # 超参数搜索（Optuna）
│   ├── import_weight_to_mysql.py        # 权重导入工具
│   ├── update_yaml.py                   # 配置更新工具
│   └── workflow_config_*.yaml           # Qlib 工作流配置
│
├── logs/                                # 日志目录
│   ├── score_prediction_日期.log        # 预测日志
│   └── weight_optimizer_日期.log        # 优化日志
│
├── main_daily.m                         # 日常预测入口（MATLAB）
├── main_history.m                       # 历史预测入口（MATLAB）
├── requirements.txt                     # Python 依赖
├── record_temp.py                       # Qlib 补丁文件
├── setup_config.py                      # 配置文件初始化脚本
├── .gitignore                           # Git 忽略文件
└── README.md                            # 本文档
```

## 常见问题

### 安装问题

**Q: Anaconda 安装后无法使用 conda 命令？**

确保 Anaconda 已正确添加到系统环境变量：
- Windows: 重启命令行或 PowerShell
- Linux/Mac: 运行 `source ~/.bashrc` 或 `source ~/.zshrc`

**Q: conda 创建环境速度慢？**

```bash
# 使用国内镜像源加速
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --set show_channel_urls yes
```

**Q: Windows PowerShell 执行策略错误？**
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Q: conda 环境激活失败？**
- Windows: 确保使用 Anaconda Prompt 或配置好的 PowerShell
- Linux/Mac: 运行 `conda init bash` 或 `conda init zsh`

### 配置问题

**Q: 找不到配置文件？**

确保已从示例文件创建实际配置：
```bash
cp config/db.example.yaml config/db.yaml
cp Optimizer_matlab/config/config_db.example.m Optimizer_matlab/config/config_db.m
```

**Q: 数据库连接失败？**

检查清单：
- [ ] `config/db.yaml` 中的连接信息是否正确
- [ ] 数据库服务是否正在运行
- [ ] 防火墙是否允许连接
- [ ] 用户名和密码是否正确
- [ ] 数据库是否存在

### 运行问题

**Q: 找不到 qlib 的 dump_bin.py？**

> Qlib 源码已包含在项目的 `qlib/` 目录中。

确保 `config/paths.yaml` 中的配置正确：
```yaml
qlib_workdir: "./qlib"  # 指向项目内的 qlib 目录
```

dump_bin.py 位置：`qlib/scripts/dump_bin.py`

**说明**：相对路径会自动转换为基于项目根目录的绝对路径。

**Q: 首次运行遇到 "calendars/day.txt not found" 错误？**

这是正常的，脚本会自动检测并使用 `dump_all` 模式进行全量导入：

```
未检测到 Qlib 数据或数据不完整，使用全量导入模式 (dump_all)
  缺失文件: ..\qlib_data\qlib_bin\calendars\day.txt
```

后续运行会自动切换到 `dump_update` 增量更新模式。

**Q: 日志目录不存在？**

日志目录会自动创建，无需手动创建。如果遇到权限问题，请检查项目目录的写权限。

**Q: 数据路径配置错误？**

检查 `config/paths.yaml` 中的路径配置：
- `csv_daily_dir`: CSV 数据存储目录
- `provider_uri`: Qlib 二进制数据目录
- 相对路径基于项目根目录解析
- 使用 `${base_dir}` 引用基础目录路径

运行诊断脚本检查数据：
```bash
python qlib_code/check_qlib_data.py
```

**Q: 应用 Qlib 补丁失败？**

确保虚拟环境已激活，然后检查路径：
```bash
# 检查当前激活的环境
conda info --envs

# 检查 qlib 是否安装
pip show qlib

# 确认 CONDA_PREFIX 环境变量
echo $CONDA_PREFIX  # Linux/Mac
echo $env:CONDA_PREFIX  # Windows PowerShell
```

**Q: MATLAB 脚本运行失败？**

检查清单：
- [ ] MATLAB 版本是否为 R2018b 或更高
- [ ] `config/paths.yaml` 中的 `yaml_matlab` 路径是否正确
- [ ] MATLAB 依赖是否已安装（如 yamlmatlab）

**Q: 预测结果写入数据库失败？**

查看日志文件获取详细错误：
```bash
# 查看最新日志
cat logs/score_prediction_*.log
```

### 性能优化

**Q: 依赖安装速度慢？**

使用 pip 镜像加速：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Q: 数据加载缓慢？**

调整 `config/db.yaml` 中的参数：
- 增加 `chunk_size`: 提高批处理大小
- 增加 `workers`: 增加并行工作进程数

**Q: 模型训练太慢？**
- 考虑使用 GPU 加速
- 减少 `n_trials` 参数降低训练次数
- 使用更少的数据进行快速验证

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

[在此添加许可证信息]
