# Models 目录

## 说明

此目录用于存放训练好的 Qlib 模型文件。

## 使用方法

### 模型存放

训练完成后，将模型文件（通常是 `.pkl` 格式）保存到此目录：

```python
import pickle

# 训练模型
model = ...  # 你的模型

# 保存模型
with open('./models/trained_model.pkl', 'wb') as f:
    pickle.dump(model, f)
```

### 模型加载

在 `config/paths.yaml` 中配置模型路径：

```yaml
# 使用项目内模型路径
model_path: "./models/trained_model.pkl"
```

然后在代码中加载：

```python
from config_utils import load_config_with_substitution
import pickle

cfg = load_config_with_substitution('config/paths.yaml')
model_path = cfg['model_path']

with open(model_path, 'rb') as f:
    model = pickle.load(f)
```

## 推荐命名规范

为了便于管理多个模型，建议使用以下命名规范：

- **按日期命名**: `model_20260110.pkl`
- **按版本命名**: `model_v1.pkl`, `model_v2.pkl`
- **按实验命名**: `model_lgbm_alpha158.pkl`
- **按性能命名**: `model_best.pkl`, `model_stable.pkl`

## MLflow 集成

如果使用 MLflow 管理实验，模型会自动保存在 `mlruns/` 目录下：

```
mlruns/
  └── <experiment_id>/
      └── <run_id>/
          └── artifacts/
              └── model.pkl
```

你可以在 `config/paths.yaml` 中直接引用 MLflow 模型：

```yaml
model_path: "./mlruns/781286402524117512/dd95d1e8f80544e186adcb105f5b4008/artifacts/model.pkl"
```

## 注意事项

1. **版本控制**: 模型文件（`*.pkl`）已添加到 `.gitignore`，不会被提交到 Git
2. **模型大小**: 大型模型建议使用外部存储（如云存储）
3. **模型备份**: 定期备份重要模型文件
4. **路径管理**: 统一使用 `config/paths.yaml` 管理模型路径

## 相关文档

- [配置文件说明](../config/paths.example.yaml)
- [模型训练指南](../README.md#模型训练与超参数调优)
- [路径配置优化](../docs/paths_yaml_optimization.md)
