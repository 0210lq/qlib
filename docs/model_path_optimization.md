# Model Path 配置优化报告

## 概述

优化了 `model_path` 配置，从外部路径改为项目内路径，避免模型文件复制，简化部署流程。

## 问题分析

### 原始配置

```yaml
# config/paths.yaml
model_path: "${base_dir}/models/trained_model"
```

其中 `base_dir: "../qlib_data"`，因此实际路径为：`../qlib_data/models/trained_model`

### 存在的问题

1. **需要复制模型**: 训练后的模型需要从项目内复制到 `../qlib_data/models/` 目录
2. **增加维护成本**: 需要维护两份模型文件（项目内训练 + 项目外使用）
3. **容易不同步**: 更新模型时容易忘记复制，导致使用旧模型
4. **部署复杂**: 部署时需要同时处理项目代码和外部模型文件
5. **版本控制困难**: 模型不在项目内，难以与代码版本对应

## 优化方案

### 配置变更

**之前**:
```yaml
model_path: "${base_dir}/models/trained_model"  # ../qlib_data/models/trained_model
```

**现在**:
```yaml
model_path: "./models/trained_model.pkl"  # 项目内路径
```

### 实现细节

#### 1. 创建 models 目录

```bash
D:\github\qlib_sql-master\
├── models/                    # ← 新增目录
│   ├── .gitkeep              # Git 跟踪占位符
│   ├── README.md             # 使用说明
│   └── trained_model.pkl     # 模型文件（被 .gitignore）
├── mlruns/                   # MLflow 模型存储
├── config/
│   └── paths.yaml           # 更新配置
└── ...
```

#### 2. 更新配置文件

**config/paths.yaml**:
```yaml
# 训练好的模型存放路径（推荐使用项目内路径）
# 使用项目内相对路径，避免复制模型文件到外部目录
#
# 推荐路径：
#   - "./models/trained_model.pkl" - 项目内 models 目录
#   - "./mlruns/<experiment_id>/<run_id>/artifacts/model.pkl" - MLflow 默认路径
#
# 示例（不推荐使用外部路径）：
#   - "${base_dir}/models/trained_model" - 需要复制模型到项目外
model_path: "./models/trained_model.pkl"
```

#### 3. Git 忽略配置

**.gitignore** 已包含：
```gitignore
*.pkl          # 忽略所有 pkl 文件（模型文件）
```

**models/.gitkeep**:
```
# This file ensures the models directory is tracked by Git
# Model files (*.pkl, *.model) are ignored by .gitignore
```

这样可以：
- ✅ Git 跟踪 `models/` 目录
- ✅ Git 忽略模型文件（避免大文件提交）
- ✅ 保持目录结构

## 使用方法

### 训练并保存模型

```python
import pickle

# 训练模型
model = ...  # 你的 LightGBM 或其他模型

# 保存到项目内
with open('./models/trained_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("模型已保存到 ./models/trained_model.pkl")
```

### 加载模型

代码无需修改，仍然从配置读取：

```python
from config_utils import load_config_with_substitution
import pickle

# 读取配置
cfg = load_config_with_substitution('config/paths.yaml')
model_path = cfg['model_path']  # 自动解析为 ./models/trained_model.pkl

# 加载模型
with open(model_path, 'rb') as f:
    model = pickle.load(f)
```

### MLflow 集成

如果使用 MLflow，可以直接引用 MLflow 模型：

```yaml
# config/paths.yaml
model_path: "./mlruns/781286402524117512/dd95d1e8f80544e186adcb105f5b4008/artifacts/model.pkl"
```

或使用符号链接：

```bash
# Linux/Mac
ln -s mlruns/latest_experiment/latest_run/artifacts/model.pkl models/trained_model.pkl

# Windows
mklink models\trained_model.pkl mlruns\latest_experiment\latest_run\artifacts\model.pkl
```

## 优化效果

### 之前的流程

```
1. 训练模型 → mlruns/xxx/model.pkl
2. 复制模型 → ../qlib_data/models/trained_model
3. 配置路径 → config/paths.yaml
4. 运行预测 → 读取 ../qlib_data/models/trained_model
```

### 现在的流程

```
1. 训练模型 → mlruns/xxx/model.pkl
2. 复制/链接 → ./models/trained_model.pkl (项目内)
3. 运行预测 → 直接读取 ./models/trained_model.pkl
```

**减少步骤**: 不需要复制到外部目录
**简化管理**: 模型文件与代码在同一项目
**便于部署**: 只需部署项目目录即可

## 模型命名规范

推荐使用以下命名规范便于管理：

```
models/
├── trained_model.pkl              # 当前使用的模型
├── model_20260110.pkl             # 按日期
├── model_lgbm_v1.pkl              # 按版本
├── model_best_ic_0.05.pkl         # 按性能指标
└── backup/
    └── model_20260109.pkl         # 备份模型
```

## 兼容性说明

### 向后兼容

- ✅ 如果需要使用外部路径，仍然支持：
  ```yaml
  model_path: "${base_dir}/models/trained_model"
  ```

- ✅ 支持绝对路径：
  ```yaml
  model_path: "E:\\models\\trained_model.pkl"
  ```

### 迁移指南

如果你之前使用外部路径存储模型：

**选项 1: 移动模型到项目内**
```bash
# 移动模型文件
mv ../qlib_data/models/trained_model ./models/trained_model.pkl

# 更新配置
vim config/paths.yaml
# 修改: model_path: "./models/trained_model.pkl"
```

**选项 2: 创建符号链接**
```bash
# Linux/Mac
ln -s ../qlib_data/models/trained_model ./models/trained_model.pkl

# Windows (管理员权限)
mklink models\trained_model.pkl ..\qlib_data\models\trained_model
```

**选项 3: 保持外部路径**
```yaml
# 不修改配置，继续使用外部路径
model_path: "${base_dir}/models/trained_model"
```

## 最佳实践

### 1. 模型版本管理

使用日期或版本号命名：

```python
from datetime import datetime

# 保存带日期的模型
date_str = datetime.now().strftime('%Y%m%d')
model_path = f'./models/model_{date_str}.pkl'

with open(model_path, 'wb') as f:
    pickle.dump(model, f)

# 创建符号链接到当前模型
import os
if os.path.exists('./models/trained_model.pkl'):
    os.remove('./models/trained_model.pkl')
os.symlink(model_path, './models/trained_model.pkl')
```

### 2. 模型备份

定期备份重要模型：

```bash
# 创建备份目录
mkdir -p models/backup

# 备份当前模型
cp models/trained_model.pkl models/backup/model_$(date +%Y%m%d).pkl
```

### 3. 大模型管理

对于大型模型（>100MB），考虑：

- **Git LFS**: 使用 Git Large File Storage
- **外部存储**: 使用云存储（OSS, S3 等）
- **模型压缩**: 使用模型量化或剪枝

### 4. CI/CD 集成

在部署脚本中：

```bash
#!/bin/bash
# deploy.sh

# 1. 克隆项目
git clone <repo>
cd qlib_sql-master

# 2. 下载模型（如果使用外部存储）
# wget https://your-storage/model.pkl -O models/trained_model.pkl

# 3. 配置路径
cp config/paths.example.yaml config/paths.yaml
# model_path 已经指向 ./models/trained_model.pkl

# 4. 运行预测
python qlib_code/update_new.py --date 2026-01-10
```

## 文档更新

### 更新的文件

1. **config/paths.yaml** - 主配置文件
2. **config/paths.example.yaml** - 示例配置
3. **README.md** - 使用说明
4. **models/.gitkeep** - Git 跟踪占位符
5. **models/README.md** - 模型目录说明
6. **docs/model_path_optimization.md** - 本文档

### 相关文档

- [路径配置优化](paths_yaml_optimization.md)
- [Provider URI 配置管理](provider_uri_config_guide.md)
- [数据库配置指南](database_config_guide.md)

## 常见问题

### Q: 为什么不把模型提交到 Git？

A: 模型文件通常很大（几 MB 到几 GB），不适合放在 Git 仓库中。建议使用：
- Git LFS（适合中等大小模型）
- 外部存储服务（适合大型模型）
- MLflow 模型注册表

### Q: 多个模型如何管理？

A: 推荐方案：
```yaml
# config/paths.yaml
model_path: "./models/trained_model.pkl"  # 当前使用的模型
```

```bash
# 多个模型文件
models/
├── trained_model.pkl → model_v3.pkl  # 符号链接
├── model_v1.pkl
├── model_v2.pkl
└── model_v3.pkl
```

### Q: 如何在不同环境使用不同模型？

A: 使用环境变量或配置文件：

```yaml
# config/paths.yaml
model_path: "${MODEL_PATH:-./models/trained_model.pkl}"
```

```bash
# 开发环境
export MODEL_PATH="./models/model_dev.pkl"

# 生产环境
export MODEL_PATH="./models/model_prod.pkl"
```

### Q: 团队协作时如何共享模型？

A: 推荐方案：

1. **小团队**: 使用共享存储（NAS, 云盘）
2. **大团队**: 使用 MLflow Model Registry
3. **开源项目**: 使用 Hugging Face Model Hub 或 GitHub Releases

## 总结

### 主要改进

1. ✅ **简化流程**: 无需复制模型到外部目录
2. ✅ **统一管理**: 模型与代码在同一项目
3. ✅ **便于部署**: 部署项目即包含模型
4. ✅ **版本对应**: 模型可以与代码版本关联
5. ✅ **灵活配置**: 仍支持外部路径和 MLflow

### 用户受益

- 🎯 减少人工操作（不需要手动复制模型）
- 🎯 降低出错概率（不会忘记更新模型）
- 🎯 提高部署效率（一次部署包含所有）
- 🎯 便于版本管理（模型与代码对应）

---

**优化日期**: 2026-01-10
**版本**: v1.0
**作者**: Claude Code Assistant
