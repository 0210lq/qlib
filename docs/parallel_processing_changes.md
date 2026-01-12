# 并行处理配置变更说明

## 修改前的并行进程配置

### Qlib 默认配置

根据 Qlib 源码 `qlib/qlib/config.py:126-161`，默认的并行进程数配置为：

```python
# 默认并行进程数
NUM_USABLE_CPU = max(multiprocessing.cpu_count() - 2, 1)

# Qlib 默认配置
_default_config = {
    "kernels": NUM_USABLE_CPU,           # 数据处理并行核心数
    "joblib_backend": "multiprocessing", # 并行后端
    "maxtasksperchild": None,            # 每个进程的最大任务数
}
```

### 实际并行进程数计算

**公式**: `并行进程数 = max(CPU 核心数 - 2, 1)`

| CPU 核心数 | 计算过程 | 实际并行进程数 |
|-----------|---------|---------------|
| 4 核      | max(4-2, 1) | **2** |
| 8 核      | max(8-2, 1) | **6** |
| 12 核     | max(12-2, 1) | **10** |
| 16 核     | max(16-2, 1) | **14** |
| 24 核     | max(24-2, 1) | **22** |
| 32 核     | max(32-2, 1) | **30** |

### 修改前的代码

**文件**: `qlib_code/hyperparameter_lgbm.py`

```python
# 修改前 - 没有显式设置并行进程数
qlib.init(provider_uri=provider_uri, region="cn")
# 默认使用 NUM_USABLE_CPU = CPU核心数 - 2
```

### 内存消耗估算

**假设系统配置**: 16 核 CPU，16GB 物理内存

**修改前的并行进程数**: 14 个进程

**每个进程的内存占用**（大致估算）:
- Python 解释器基础: ~50 MB
- scipy/numpy 库加载: ~200-300 MB
- 数据缓存: ~100-200 MB
- **单进程总计**: ~350-550 MB

**总内存需求**:
```
14 个进程 × 450 MB/进程 = 6,300 MB ≈ 6.3 GB（仅工作进程）
+ 主进程数据集: ~2-3 GB
+ 系统开销: ~1 GB
= 总计约 9-10 GB
```

**问题**:
- 如果物理内存接近或超过限制，系统会使用虚拟内存
- Windows 默认虚拟内存可能不足（通常只有物理内存的 1.5 倍）
- 导致 `页面文件太小，无法完成操作` 错误

---

## 修改后的并行进程配置

### 代码修改

**文件**: `qlib_code/hyperparameter_lgbm.py` (第 58-65 行)

```python
# 修改后 - 显式限制并行进程数
# 减少并行工作进程数以降低内存使用
# 设置为1表示不使用并行处理，适合内存较小的环境
os.environ['QLIB_NUM_WORKERS'] = '1'      # Qlib 工作进程数
os.environ['NUMEXPR_MAX_THREADS'] = '1'   # NumExpr 线程数
os.environ['OMP_NUM_THREADS'] = '1'       # OpenMP 线程数
os.environ['MKL_NUM_THREADS'] = '1'       # Intel MKL 线程数

qlib.init(provider_uri=provider_uri, region="cn", kernels=1)
```

### 修改后的并行进程数

**固定值**: **1 个进程**（无论 CPU 核心数多少）

### 内存消耗对比

**修改后的内存需求**:
```
1 个进程 × 450 MB/进程 = 450 MB（工作进程）
+ 主进程数据集: ~2-3 GB
+ 系统开销: ~1 GB
= 总计约 3.5-4.5 GB
```

**节省**: 约 5.5 GB 内存（相比 16 核系统的修改前配置）

---

## 环境变量说明

### 设置的环境变量

| 环境变量 | 作用 | 修改前 | 修改后 |
|---------|-----|-------|-------|
| `QLIB_NUM_WORKERS` | Qlib 数据加载工作进程数 | 未设置（使用默认） | `'1'` |
| `NUMEXPR_MAX_THREADS` | NumExpr 表达式计算线程数 | 未设置（使用 CPU 核心数） | `'1'` |
| `OMP_NUM_THREADS` | OpenMP 并行线程数 | 未设置（使用 CPU 核心数） | `'1'` |
| `MKL_NUM_THREADS` | Intel MKL 数学库线程数 | 未设置（使用 CPU 核心数） | `'1'` |

### qlib.init() 参数

| 参数 | 说明 | 修改前 | 修改后 |
|-----|------|-------|-------|
| `kernels` | 数据处理并行核心数 | 未设置（使用默认 NUM_USABLE_CPU） | `1` |

---

## 性能影响分析

### 修改前 (14 进程并行)

**优势**:
- ✅ 数据加载速度快（多进程并行）
- ✅ CPU 利用率高
- ✅ 适合高性能服务器

**劣势**:
- ❌ 内存占用极大（6-10 GB 仅工作进程）
- ❌ 容易触发内存不足错误
- ❌ 不适合个人电脑或低配置环境

**适用场景**:
- 物理内存 >= 32 GB
- 服务器环境
- 生产环境大规模训练

### 修改后 (1 进程串行)

**优势**:
- ✅ 内存占用低（3.5-4.5 GB）
- ✅ 稳定性高，不易崩溃
- ✅ 适合个人电脑和中低配置环境
- ✅ 可在虚拟内存较小的系统上运行

**劣势**:
- ❌ 数据加载速度慢（串行处理）
- ❌ CPU 利用率低
- ❌ 训练时间显著增加

**适用场景**:
- 物理内存 <= 16 GB
- 个人开发环境
- 测试和调试
- 虚拟内存受限的 Windows 系统

### 速度对比估算

**数据加载阶段**（Alpha158，5000只股票，2年历史数据）:

| 配置 | 并行进程数 | 预计耗时 | 说明 |
|-----|----------|---------|------|
| 修改前 | 14 | ~2-3 分钟 | 多进程并行加载 |
| 修改后 | 1 | ~10-15 分钟 | 单进程串行加载 |

**整体训练流程**（Optuna 2 次试验）:

| 配置 | 数据加载 | 模型训练 | 总计 | 说明 |
|-----|---------|---------|------|------|
| 修改前 | ~3 分钟 | ~10 分钟 | **~13 分钟** | 假设不崩溃 |
| 修改后 | ~15 分钟 | ~10 分钟 | **~25 分钟** | 稳定运行 |

**注意**: 实际速度取决于：
- CPU 性能
- 硬盘速度（SSD vs HDD）
- 数据量大小
- LightGBM 训练参数

---

## 从错误信息推断原配置

### 错误堆栈分析

从用户提供的错误信息中可以看到:

```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "C:\Users\qw\.conda\envs\qlib_env_test\Lib\multiprocessing\spawn.py", line 122, in spawn_main
...
ImportError: DLL load failed while importing _flapack: 页面文件太小，无法完成操作。
MemoryError: Unable to allocate 452. KiB for an array with shape (158, 732)
```

**多个重复的 Traceback**: 表明有多个工作进程同时启动并失败

**推测**: 基于错误信息中大量重复的堆栈追踪（约 10+ 个），原配置应该是:
- **CPU 核心数**: 12-16 核
- **原并行进程数**: 10-14 个进程
- **物理内存**: 可能 8-16 GB
- **虚拟内存**: 不足（导致错误）

---

## 如何根据系统配置选择并行进程数

### 推荐配置表

| 物理内存 | 虚拟内存配置 | 推荐并行进程数 | 设置方法 |
|---------|-------------|--------------|---------|
| <= 8 GB | 12 GB 初始 / 24 GB 最大 | **1** | `kernels=1` |
| 8-16 GB | 24 GB 初始 / 48 GB 最大 | **1-2** | `kernels=2` |
| 16-32 GB | 不需要额外设置 | **2-4** | `kernels=4` |
| >= 32 GB | 不需要额外设置 | **使用默认** | 不设置 `kernels` |

### 自定义并行进程数

如果希望在修复后使用更多进程（需要先增加虚拟内存），可以修改:

```python
# 示例：使用 4 个并行进程
os.environ['QLIB_NUM_WORKERS'] = '4'
os.environ['NUMEXPR_MAX_THREADS'] = '4'
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['MKL_NUM_THREADS'] = '4'

qlib.init(provider_uri=provider_uri, region="cn", kernels=4)
```

### 动态根据内存调整

也可以根据可用内存动态设置:

```python
import psutil

# 获取可用内存（GB）
available_memory_gb = psutil.virtual_memory().available / (1024**3)

# 根据可用内存决定并行进程数
if available_memory_gb >= 20:
    kernels = 8  # 充足内存，使用较多进程
elif available_memory_gb >= 10:
    kernels = 4  # 中等内存，使用中等进程数
elif available_memory_gb >= 5:
    kernels = 2  # 较少内存，使用较少进程
else:
    kernels = 1  # 内存紧张，使用单进程

os.environ['QLIB_NUM_WORKERS'] = str(kernels)
qlib.init(provider_uri=provider_uri, region="cn", kernels=kernels)
```

---

## 总结

### 关键变化

| 项目 | 修改前 | 修改后 | 变化 |
|-----|-------|-------|------|
| 并行进程数 | CPU核心数 - 2（动态） | **1**（固定） | ⬇️ 大幅减少 |
| 内存占用 | ~6-10 GB | ~3.5-4.5 GB | ⬇️ 减少 50-60% |
| 数据加载速度 | 快 | 慢 | ⬇️ 慢 3-5 倍 |
| 稳定性 | 低（易内存溢出） | 高 | ⬆️ 大幅提升 |
| 适用场景 | 高配置服务器 | 中低配置个人电脑 | 更广泛 |

### 建议

1. **开发/测试环境**: 使用修改后的配置（`kernels=1`），确保稳定性
2. **生产环境**: 根据服务器配置增加并行进程数以提升性能
3. **虚拟内存**: 无论并行进程数多少，都建议设置足够的虚拟内存

---

**文档创建日期**: 2026-01-10
**版本**: v1.0
**作者**: Claude Code Assistant
