# config/paths.yaml 优化建议

## 当前问题分析

当前的 `config/paths.yaml` 存在以下问题：

### 1. 硬编码绝对路径
```yaml
base_dir: "E:\\qlib_data"  # 绑定到 E 盘
qlib_workdir: "E:\\qlib"   # 绑定到 E 盘
```

**问题：**
- 无法跨机器/用户使用
- Windows 特定路径（使用 E: 盘符），Linux/Mac 无法使用
- 团队协作困难，每个人需要手动修改路径

### 2. Python 路径硬编码
```yaml
python_exe: "E:\\ProgramData\\anaconda3\\envs\\new_qlib_env\\python.exe"
```

**问题：**
- 绑定到特定的 conda 环境名称和安装位置
- 环境名称变更后需要修改配置
- 无法使用当前激活的环境

### 3. 缺乏配置模板
**问题：**
- 新用户不知道如何配置
- 容易误提交包含本地路径的配置文件

## 优化方案

### 方案 1: 使用相对路径（推荐）

**优点：**
- 跨平台兼容
- 便于团队协作
- 便于项目迁移

**示例配置：**
```yaml
# 数据目录在项目外部
base_dir: "../qlib_data"

# Qlib 仓库在项目外部
qlib_workdir: "../qlib"

# Python 使用当前激活的环境
python_exe: "python"
```

**目录结构：**
```
workspace/
├── qlib_sql-master/      # 项目目录
│   ├── config/
│   │   └── paths.yaml
│   └── ...
├── qlib_data/            # 数据目录
│   ├── csv_data/
│   ├── qlib_bin/
│   └── models/
└── qlib/                 # Qlib 源码
```

### 方案 2: 使用环境变量

**优点：**
- 灵活性高
- 可以使用系统标准路径
- 便于部署到不同环境

**示例配置（Linux/Mac）：**
```yaml
base_dir: "${HOME}/qlib_data"
qlib_workdir: "${HOME}/qlib"
python_exe: "python"
```

**示例配置（Windows）：**
```yaml
base_dir: "${USERPROFILE}\\qlib_data"
qlib_workdir: "${USERPROFILE}\\qlib"
python_exe: "python"
```

### 方案 3: 混合使用（最佳实践）

结合相对路径和环境变量的优点：

```yaml
# 数据基础目录
base_dir: "../qlib_data"

# CSV 数据目录（使用变量引用）
csv_output_dir: "${base_dir}/csv_data"
csv_daily_dir: "${base_dir}/daily"

# Qlib 相关路径
provider_uri: "${base_dir}/qlib_bin"
qlib_workdir: "../qlib"

# 模型路径
model_path: "${base_dir}/models/trained_model"

# 预测输出路径
prediction_output_dir: "${base_dir}/output/prediction"

# 临时目录
temp_dir: "${base_dir}/temp"
processing_data_dir: "${base_dir}/processing"

# Python 执行路径（自动检测当前环境）
python_exe: "python"

# MATLAB 工具路径（相对于项目根目录）
yaml_matlab: "./YAMLMatlab_0.4.3"
```

## 实施步骤

### 1. 创建配置模板

已创建 `config/paths.example.yaml`，包含：
- 详细的配置说明
- 多种配置方案示例
- 跨平台兼容的路径格式

### 2. 更新 .gitignore

已将 `config/paths.yaml` 添加到 `.gitignore`：
```gitignore
# Configuration files with sensitive data
config/db.yaml
config/paths.yaml
Optimizer_matlab/config/config_db.m

# Keep example files
!config/db.example.yaml
!config/paths.example.yaml
!Optimizer_matlab/config/config_db.example.m
```

### 3. 使用配置脚本

运行自动配置脚本：
```bash
python setup_config.py
```

或手动复制：
```bash
# Linux/Mac
cp config/paths.example.yaml config/paths.yaml

# Windows
Copy-Item config\paths.example.yaml config\paths.yaml
```

### 4. 编辑配置文件

根据实际环境修改 `config/paths.yaml`。

## Python 路径配置最佳实践

### 推荐：使用 "python"
```yaml
python_exe: "python"
```

**工作原理：**
- 当 conda 环境激活后，`python` 会自动指向当前环境的 Python
- MATLAB 调用时会使用系统 PATH 中的 Python
- 无需硬编码路径

### 备选：使用 CONDA_PREFIX

如果确实需要指定完整路径，可以在代码中动态获取：

**Python 代码示例：**
```python
import os
import sys

# 获取当前 conda 环境的 Python 路径
if 'CONDA_PREFIX' in os.environ:
    python_exe = os.path.join(os.environ['CONDA_PREFIX'], 'python.exe')  # Windows
    # python_exe = os.path.join(os.environ['CONDA_PREFIX'], 'bin', 'python')  # Linux/Mac
else:
    python_exe = sys.executable
```

## YAML 路径变量解析

如果你的代码需要解析 `${variable}` 格式的变量，可以使用以下方法：

**Python 示例：**
```python
import os
import re
import yaml

def expand_path(path_str):
    """展开路径中的环境变量和变量引用"""
    # 展开环境变量
    path_str = os.path.expandvars(path_str)

    # 展开用户目录
    path_str = os.path.expanduser(path_str)

    return path_str

def load_config_with_expansion(config_path):
    """加载配置并展开所有路径"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 展开路径变量
    def expand_config(obj, context=None):
        if context is None:
            context = config

        if isinstance(obj, dict):
            return {k: expand_config(v, context) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [expand_config(item, context) for item in obj]
        elif isinstance(obj, str):
            # 替换配置文件内的变量引用 ${base_dir}
            for key, value in context.items():
                if isinstance(value, str):
                    obj = obj.replace(f"${{{key}}}", value)
            # 展开环境变量
            return expand_path(obj)
        return obj

    return expand_config(config)

# 使用示例
config = load_config_with_expansion('config/paths.yaml')
print(config['csv_output_dir'])  # 输出展开后的完整路径
```

## 总结

### ✅ 推荐做法
- 使用相对路径（`../qlib_data`）
- 使用变量引用（`${base_dir}/csv_data`）
- Python 路径设为 `"python"`
- 创建并使用配置模板文件

### ❌ 不推荐做法
- 硬编码绝对路径（`E:\\qlib_data`）
- 硬编码 Python 环境路径
- 直接提交包含本地路径的配置文件
- 使用 Windows 特定路径分隔符

### 📋 检查清单
- [ ] 创建 `paths.example.yaml` 模板文件
- [ ] 将 `paths.yaml` 添加到 `.gitignore`
- [ ] 从模板创建实际配置文件
- [ ] 使用相对路径或环境变量
- [ ] 测试跨平台兼容性
- [ ] 更新 README.md 文档
