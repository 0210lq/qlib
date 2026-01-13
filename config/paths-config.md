# 路径配置说明文档

## 文件说明

- **配置文件**: `paths.yaml`
- **示例文件**: `paths.example.yaml`

## 使用说明

1. 复制示例文件为配置文件: `cp paths.example.yaml paths.yaml`
2. 根据实际环境修改路径配置
3. 支持使用环境变量（如 `${HOME}`、`${USERPROFILE}`）
4. 支持相对路径（相对于项目根目录）

---

## 基础目录配置

### base_dir
- **说明**: 数据存储基础目录
- **支持格式**: 相对路径、绝对路径、环境变量
- **示例**:
  - Linux/Mac: `"../qlib_data"` 或 `"${HOME}/qlib_data"`
  - Windows: `"..\\qlib_data"` 或 `"${USERPROFILE}\\qlib_data"`
- **推荐**: 使用相对路径
- **默认值**: `"../qlib_data"`

---

## CSV 数据目录

### csv_output_dir
- **说明**: 存放 CSV 版本数据
- **默认值**: `"${base_dir}/csv_data"`

### csv_daily_dir
- **说明**: 存放每日更新需要的 CSV 数据
- **默认值**: `"${base_dir}/daily"`

---

## Qlib 相关路径

### provider_uri
- **说明**: Qlib 二进制数据存储路径
- **默认值**: `"${base_dir}/qlib_bin"`

### qlib_workdir
- **说明**: Qlib 仓库路径
- **注意**: qlib 已包含在项目中，使用项目内的相对路径
- **默认值**: `"./qlib"`
- **如果需要使用外部 qlib**，可以修改为：
  - 相对路径（项目外）: `"../qlib"`
  - Linux/Mac: `"${HOME}/qlib"`
  - Windows: `"${USERPROFILE}\\qlib"`

---

## 模型相关路径

### model_path
- **说明**: 训练好的模型存放路径
- **推荐**: 使用项目内路径，避免复制模型文件到外部目录
- **推荐路径**:
  - 项目内 models 目录: `"./models/trained_model.pkl"`
  - MLflow 默认路径: `"./mlruns/<experiment_id>/<run_id>/artifacts/model.pkl"`
- **不推荐**:
  - 外部路径（需要复制模型到项目外）: `"${base_dir}/models/trained_model"`
- **默认值**: `"./models/trained_model"`

### prediction_output_dir
- **说明**: 预测结果（score 文件）存放路径
- **默认值**: `"${base_dir}/output/prediction"`

---

## 临时和处理目录

### temp_dir
- **说明**: 临时存放合并后的优化后的权重文件
- **默认值**: `"${base_dir}/temp"`

### processing_data_dir
- **说明**: 输出的优化结果存放路径
- **默认值**: `"${base_dir}/processing"`

---

## 配置文件路径

### yaml_path
- **说明**: 模型配置文件路径（相对于项目根目录）
- **默认值**: `"./qlib_code/workflow_config_lightgbm.yaml"`

---

## Python 执行路径

### python_exe
- **说明**: Python 可执行文件路径
- **注意**:
  - 如果使用 conda 环境，激活环境后通常无需指定此路径
  - 如果 MATLAB 调用 Python，需要指定完整路径
  - 可以使用 `"python"` 让系统自动查找当前激活环境的 Python
- **示例**:
  - 自动检测: `"python"`
  - Windows Conda: `"${USERPROFILE}\\anaconda3\\envs\\qlib_env\\python.exe"`
  - Linux/Mac Conda: `"${HOME}/anaconda3/envs/qlib_env/bin/python"`
- **默认值**: `"python"`

---

## MATLAB 相关路径

### yaml_matlab
- **说明**: YAML MATLAB 工具路径（相对路径）
- **默认值**: `"./YAMLMatlab_0.4.3"`

### global_tools
- **说明**: 全局工具配置
- **默认值**: `"GLOBAL_TOOLSFUNC"`
