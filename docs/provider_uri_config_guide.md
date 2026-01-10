# Provider URI 配置管理指南

## 概述

本文档说明如何管理 Qlib 数据路径配置 (`provider_uri`)，避免配置不一致问题。

## 问题背景

### 配置重复问题

之前存在两个地方配置 `provider_uri`:

1. **config/paths.yaml**
   ```yaml
   provider_uri: "${base_dir}/qlib_bin"
   ```

2. **qlib_code/workflow_config_lightgbm.yaml**
   ```yaml
   qlib_init:
       provider_uri: "E:\\qlib_data\\tushare_qlib_data\\qlib_bin"
   ```

### 存在的问题

- **配置不一致**: 两个文件中的路径可能不同步
- **维护困难**: 修改数据路径需要同时更新两个文件
- **硬编码路径**: workflow 配置使用绝对路径，不利于跨环境部署
- **容易出错**: 修改一处忘记另一处会导致运行错误

## 解决方案

### 统一配置管理

现在采用 **统一配置** 方案:

1. **主配置文件**: `config/paths.yaml` - 唯一数据路径定义处
2. **自动同步**: 使用脚本自动同步到 workflow 配置
3. **清晰标注**: workflow 配置中添加注释说明配置来源

### 配置架构

```
config/paths.yaml (主配置)
        ↓
        ↓ (自动同步)
        ↓
qlib_code/workflow_config_lightgbm.yaml
        ↓
        ↓ (qrun 使用)
        ↓
    Qlib 数据加载
```

## 使用方法

### 方法 1: 单独同步路径配置（推荐）

当你只需要更新数据路径时:

```bash
# 1. 修改 config/paths.yaml 中的 provider_uri
nano config/paths.yaml

# 2. 运行同步脚本
python qlib_code/sync_provider_uri.py
```

**优点**:
- 快速简单
- 不需要数据库连接
- 只更新路径配置

**输出示例**:
```
============================================================
Provider URI 同步工具
============================================================

📖 读取配置: D:\github\qlib_sql-master\config\paths.yaml
✅ 读取到 provider_uri: E:\qlib_data\tushare_qlib_data\qlib_bin

📖 读取 Workflow 配置: D:\github\qlib_sql-master\qlib_code\workflow_config_lightgbm.yaml
📍 当前 provider_uri: E:\qlib_data\old_path\qlib_bin

🔄 更新 provider_uri...
✅ 成功更新 provider_uri
   从: E:\qlib_data\old_path\qlib_bin
   到: E:\qlib_data\tushare_qlib_data\qlib_bin

============================================================
✅ 同步完成
============================================================
```

### 方法 2: 使用 update_yaml.py 全量更新

当你需要同时更新模型参数和路径时:

```bash
# 运行完整更新（从数据库读取参数 + 同步路径）
python qlib_code/update_yaml.py
```

**优点**:
- 一次性更新所有配置
- 包括模型超参数、日期范围、数据路径

**输出示例**:
```
数据库连接成功
📁 从配置文件读取 provider_uri: E:\qlib_data\tushare_qlib_data\qlib_bin
✅ 已更新 provider_uri: E:\qlib_data\tushare_qlib_data\qlib_bin
✅ 成功更新YAML文件: D:\github\qlib_sql-master\qlib_code\workflow_config_lightgbm.yaml
```

## 配置文件说明

### config/paths.yaml

这是 **主配置文件**，所有路径配置的唯一来源:

```yaml
# 基础目录
base_dir: "../qlib_data"

# Qlib 数据路径（主配置）
provider_uri: "${base_dir}/qlib_bin"
```

**配置说明**:
- 支持环境变量: `${HOME}`, `${USERPROFILE}`
- 支持相对路径: `../qlib_data`
- 支持绝对路径: `E:\qlib_data`

**推荐配置**:
```yaml
# Windows
base_dir: "E:\\qlib_data\\tushare_qlib_data"
provider_uri: "${base_dir}\\qlib_bin"

# Linux/Mac
base_dir: "${HOME}/qlib_data/tushare_qlib_data"
provider_uri: "${base_dir}/qlib_bin"
```

### qlib_code/workflow_config_lightgbm.yaml

这是 **同步目标文件**，由脚本自动更新:

```yaml
qlib_init:
    # 数据路径配置
    # 注意：此路径应与 config/paths.yaml 中的 provider_uri 保持一致
    # 修改数据路径后，运行以下命令自动同步：
    #   python qlib_code/sync_provider_uri.py
    # 或使用 update_yaml.py 更新（会同时更新模型参数）：
    #   python qlib_code/update_yaml.py
    provider_uri: "E:\\qlib_data\\tushare_qlib_data\\qlib_bin"
    region: cn
```

**注意**:
- ⚠️ **不要直接修改此文件的 provider_uri**
- ✅ **应该修改 config/paths.yaml，然后运行同步脚本**

## 完整工作流程

### 场景 1: 迁移到新服务器

假设你要将项目从 `E:\qlib_data` 迁移到 `D:\data\qlib`:

```bash
# 1. 修改主配置
nano config/paths.yaml

# 修改为:
# base_dir: "D:\\data\\qlib\\tushare_qlib_data"
# provider_uri: "${base_dir}\\qlib_bin"

# 2. 同步到 workflow 配置
python qlib_code/sync_provider_uri.py

# 3. 验证配置
cat qlib_code/workflow_config_lightgbm.yaml | grep provider_uri

# 4. 测试运行
python qlib_code/check_qlib_data.py
```

### 场景 2: 开发环境切换数据集

假设你有多个数据集需要切换:

```bash
# 数据集 A: E:\qlib_data\dataset_a\qlib_bin
# 数据集 B: E:\qlib_data\dataset_b\qlib_bin

# 切换到数据集 B:
# 1. 修改 config/paths.yaml
base_dir: "E:\\qlib_data\\dataset_b"

# 2. 同步
python qlib_code/sync_provider_uri.py

# 3. 运行模型
qrun qlib_code/workflow_config_lightgbm.yaml
```

### 场景 3: 使用相对路径（跨环境部署）

适合团队协作或多环境部署:

```yaml
# config/paths.yaml
base_dir: "../qlib_data"
provider_uri: "${base_dir}/qlib_bin"
```

```bash
# 项目目录结构:
# /your_workspace/
# ├── qlib_sql-master/     # 项目代码
# └── qlib_data/           # 数据目录
#     └── qlib_bin/

# 同步配置
python qlib_code/sync_provider_uri.py

# 任何用户克隆项目后，只要保持相同的目录结构，无需修改配置
```

## 检查和验证

### 检查配置是否同步

```bash
# 查看 paths.yaml 配置
python -c "from config_utils import load_config_with_substitution; cfg = load_config_with_substitution('config/paths.yaml'); print(f'paths.yaml provider_uri: {cfg[\"provider_uri\"]}')"

# 查看 workflow 配置
grep -A 1 "provider_uri:" qlib_code/workflow_config_lightgbm.yaml
```

### 验证数据路径是否有效

```bash
# 运行数据诊断脚本
python qlib_code/check_qlib_data.py
```

**成功输出**:
```
============================================================
数据路径检查
============================================================
数据路径: E:\qlib_data\tushare_qlib_data\qlib_bin
✅ 数据路径存在

关键目录检查:
  calendars: ✅
  instruments: ✅
  features: ✅
```

## 故障排查

### 问题 1: sync_provider_uri.py 运行失败

**错误信息**:
```
❌ 错误: 配置文件不存在: D:\github\qlib_sql-master\config\paths.yaml
```

**解决方法**:
```bash
# 复制示例配置
cp config/paths.example.yaml config/paths.yaml

# 修改配置
nano config/paths.yaml
```

### 问题 2: 路径配置后数据加载失败

**错误信息**:
```
ValueError: Empty data from dataset, please check your dataset config.
```

**检查步骤**:

1. **验证路径是否正确**:
   ```bash
   # Windows
   dir "E:\qlib_data\tushare_qlib_data\qlib_bin"

   # Linux/Mac
   ls -la ~/qlib_data/tushare_qlib_data/qlib_bin
   ```

2. **检查数据完整性**:
   ```bash
   python qlib_code/check_qlib_data.py
   ```

3. **确认配置同步**:
   ```bash
   python qlib_code/sync_provider_uri.py
   ```

### 问题 3: 两个配置文件路径不一致

**检查方法**:
```bash
# 查看 paths.yaml
grep "provider_uri:" config/paths.yaml

# 查看 workflow 配置
grep "provider_uri:" qlib_code/workflow_config_lightgbm.yaml
```

**解决方法**:
```bash
# 重新同步
python qlib_code/sync_provider_uri.py
```

## 最佳实践

### 1. 统一路径管理

✅ **推荐**:
```bash
# 修改 config/paths.yaml
vim config/paths.yaml

# 同步到其他配置
python qlib_code/sync_provider_uri.py
```

❌ **避免**:
```bash
# 直接修改 workflow 配置（会被同步脚本覆盖）
vim qlib_code/workflow_config_lightgbm.yaml
```

### 2. 版本控制

```gitignore
# .gitignore
config/paths.yaml          # 实际配置不提交
!config/paths.example.yaml # 示例配置提交
```

### 3. 团队协作

**新成员加入流程**:

```bash
# 1. 克隆项目
git clone <repo_url>
cd qlib_sql-master

# 2. 创建配置
cp config/paths.example.yaml config/paths.yaml

# 3. 根据本地环境修改
nano config/paths.yaml

# 4. 同步配置
python qlib_code/sync_provider_uri.py

# 5. 验证
python qlib_code/check_qlib_data.py
```

### 4. 自动化部署

在 CI/CD 或部署脚本中:

```bash
#!/bin/bash
# deploy.sh

# 1. 设置环境变量
export QLIB_DATA_PATH="/data/qlib_data"

# 2. 使用环境变量生成配置
cat > config/paths.yaml <<EOF
base_dir: "${QLIB_DATA_PATH}/tushare_qlib_data"
provider_uri: "\${base_dir}/qlib_bin"
EOF

# 3. 同步配置
python qlib_code/sync_provider_uri.py

# 4. 运行任务
qrun qlib_code/workflow_config_lightgbm.yaml
```

## 代码实现说明

### sync_provider_uri.py 工作原理

```python
# 1. 读取 config/paths.yaml
from config_utils import load_config_with_substitution
cfg = load_config_with_substitution('config/paths.yaml')
provider_uri = cfg.get('provider_uri')

# 2. 读取 workflow_config_lightgbm.yaml
with open('workflow_config.yaml', 'r') as f:
    content = f.read()

# 3. 正则替换 provider_uri
pattern = r'(qlib_init:.*?provider_uri:\s*["\']?)([^"\'\n]+)(["\']?)'
updated = re.sub(pattern, rf'\g<1>{provider_uri}\g<3>', content)

# 4. 写回文件
with open('workflow_config.yaml', 'w') as f:
    f.write(updated)
```

### update_yaml.py 增强

```python
def update_yaml(yaml_file_path, best_params, provider_uri=None):
    # ... 更新模型参数 ...

    # 更新 provider_uri（新增功能）
    if provider_uri:
        updated_content = re.sub(
            provider_pattern,
            rf'\g<1>{provider_uri}\g<3>',
            updated_content
        )
```

## 总结

### 配置管理原则

1. **Single Source of Truth**: `config/paths.yaml` 是路径配置的唯一来源
2. **自动同步**: 使用脚本保持配置一致性
3. **清晰标注**: 配置文件中注释说明配置来源和更新方法
4. **版本控制**: 敏感配置不提交，示例配置提交

### 操作清单

- ✅ 修改路径后运行 `sync_provider_uri.py`
- ✅ 使用 `check_qlib_data.py` 验证数据
- ✅ 定期检查配置一致性
- ❌ 不要直接修改 workflow 配置的 provider_uri
- ❌ 不要在多个地方维护相同配置

### 相关文档

- [paths.yaml 优化指南](paths_yaml_optimization.md)
- [qrun 空数据集错误修复](qrun_empty_dataset_fix.md)
- [数据库配置指南](database_config_guide.md)
