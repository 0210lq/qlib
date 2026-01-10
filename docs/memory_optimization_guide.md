# 内存优化与故障排查指南

## 问题概述

在运行 `hyperparameter_lgbm.py` 或其他内存密集型脚本时，可能遇到以下错误:

```
MemoryError: Unable to allocate 452. KiB for an array with shape (158, 732)
ImportError: DLL load failed while importing _flapack: 页面文件太小，无法完成操作。
```

这表明系统内存不足，Windows 虚拟内存（页面文件）也已耗尽。

## 根本原因

1. **并行数据加载**: Qlib 默认使用多进程并行加载数据
2. **多进程内存开销**: 每个工作进程都会加载 scipy/numpy 等大型库
3. **Windows 页面文件限制**: 虚拟内存设置过小
4. **训练数据量过大**: 长时间范围的历史数据占用大量内存

## 解决方案

### 方案 1: 代码优化（已实施）

脚本已添加以下优化:

```python
# 减少并行工作进程数
os.environ['QLIB_NUM_WORKERS'] = '1'      # Qlib 工作进程
os.environ['NUMEXPR_MAX_THREADS'] = '1'   # NumExpr 线程
os.environ['OMP_NUM_THREADS'] = '1'       # OpenMP 线程
os.environ['MKL_NUM_THREADS'] = '1'       # MKL 线程

qlib.init(provider_uri=provider_uri, region="cn", kernels=1)
```

### 方案 2: 增加 Windows 虚拟内存（推荐）

#### 步骤 1: 打开系统属性

**方法 A: 通过控制面板**
1. 按 `Win + R`，输入 `sysdm.cpl`，回车
2. 切换到「高级」选项卡
3. 在「性能」区域点击「设置」

**方法 B: 通过设置**
1. 按 `Win + I` 打开设置
2. 搜索「高级系统设置」
3. 点击「性能」下的「设置」

#### 步骤 2: 配置虚拟内存

1. 在「性能选项」窗口中，切换到「高级」选项卡
2. 在「虚拟内存」区域点击「更改」
3. **取消勾选**「自动管理所有驱动器的分页文件大小」
4. 选择系统盘（通常是 C:）
5. 选择「自定义大小」
6. 设置虚拟内存大小:

**推荐配置**:
- **初始大小**: 物理内存的 1.5 倍（例如 16GB 内存 → 24576 MB）
- **最大值**: 物理内存的 3 倍（例如 16GB 内存 → 49152 MB）

**示例**（假设物理内存为 16GB）:
```
初始大小: 24576 MB
最大值:   49152 MB
```

7. 点击「设置」→「确定」
8. 重启计算机使设置生效

#### 快速计算表格

| 物理内存 | 初始大小（1.5x） | 最大值（3x） |
|---------|----------------|-------------|
| 8 GB    | 12288 MB       | 24576 MB    |
| 16 GB   | 24576 MB       | 49152 MB    |
| 32 GB   | 49152 MB       | 98304 MB    |
| 64 GB   | 98304 MB       | 196608 MB   |

### 方案 3: 减少训练数据范围

如果内存仍然不足，可以缩短训练数据时间范围:

**编辑 `qlib_code/hyperparameter_lgbm.py`**:

```python
# 修改前（2023年至今，约2年数据）
train_start = "2023-01-01"

# 修改后（2024年至今，约1年数据）
train_start = "2024-01-01"

# 或者更短（最近6个月）
train_start = "2024-07-01"
```

**数据量对比**:
- 2 年数据: 约 240 个交易日 × 5000 只股票 × 158 个特征 ≈ 3GB 内存
- 1 年数据: 约 120 个交易日 × 5000 只股票 × 158 个特征 ≈ 1.5GB 内存
- 6 个月: 约 60 个交易日 × 5000 只股票 × 158 个特征 ≈ 750MB 内存

### 方案 4: 减少股票范围

限制训练的股票池，只使用主要指数成分股:

**编辑 `qlib_code/hyperparameter_lgbm.py`**:

```python
# 修改前（全市场股票）
"instruments": "all",

# 修改后（仅沪深300）
"instruments": "csi300",

# 或仅上证50
"instruments": "sse50",
```

### 方案 5: 减少特征数量

使用更少的特征可以显著降低内存使用:

**编辑 `qlib_code/hyperparameter_lgbm.py`**:

```python
# 修改前（Alpha158，158个特征）
"class": "Alpha158",

# 修改后（Alpha360，360个特征，但可以自定义减少）
# 需要自定义 handler，这里仅作示例
```

### 方案 6: 减少超参数搜索次数

减少 Optuna 的试验次数:

```python
# 修改前
study.optimize(lambda trial: objective(trial, dataset), n_trials=2, n_jobs=1)

# 修改后（减少到1次试验用于测试）
study.optimize(lambda trial: objective(trial, dataset), n_trials=1, n_jobs=1)
```

## 推荐组合方案

### 场景 1: 物理内存 >= 16GB

1. ✅ 增加虚拟内存到 24GB 初始 / 48GB 最大
2. ✅ 使用代码优化（已实施）
3. ✅ 保持默认数据范围

### 场景 2: 物理内存 8GB - 16GB

1. ✅ 增加虚拟内存到 12GB 初始 / 24GB 最大
2. ✅ 使用代码优化（已实施）
3. ✅ 缩短训练数据到 1 年: `train_start = "2024-01-01"`
4. ⚠️ 考虑限制股票范围: `instruments = "csi300"`

### 场景 3: 物理内存 < 8GB

1. ✅ 增加虚拟内存到 12GB 初始 / 24GB 最大
2. ✅ 使用代码优化（已实施）
3. ✅ 缩短训练数据到 6 个月: `train_start = "2024-07-01"`
4. ✅ 限制股票范围: `instruments = "sse50"`
5. ✅ 减少试验次数: `n_trials=1`

## 验证内存使用

运行前检查可用内存:

### Windows PowerShell

```powershell
# 查看物理内存
Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum | Select-Object @{N="Total RAM (GB)"; E={[math]::round($_.sum / 1GB, 2)}}

# 查看可用内存
Get-CimInstance Win32_OperatingSystem | Select-Object @{N="Free RAM (GB)"; E={[math]::round($_.FreePhysicalMemory / 1MB, 2)}}

# 查看虚拟内存配置
Get-CimInstance Win32_PageFileUsage | Select-Object Name, AllocatedBaseSize, CurrentUsage
```

### 任务管理器监控

运行脚本时：
1. 按 `Ctrl + Shift + Esc` 打开任务管理器
2. 切换到「性能」选项卡
3. 观察「内存」和「虚拟内存」使用情况
4. 如果「已提交」接近最大值，说明需要增加虚拟内存

## 常见问题

### Q1: 增加虚拟内存后仍然报错？

**检查清单**:
- [ ] 是否重启计算机？（必须重启）
- [ ] 虚拟内存是否设置在系统盘？
- [ ] 系统盘是否有足够空间？（至少需要虚拟内存大小的空闲空间）
- [ ] 是否关闭了其他占用内存的程序？

### Q2: 虚拟内存设置后系统变慢？

**原因**: 虚拟内存使用硬盘空间，速度比物理内存慢得多。

**解决方法**:
1. 考虑升级物理内存
2. 使用 SSD 作为虚拟内存存储位置
3. 减少训练数据量（推荐）

### Q3: 如何确认设置是否生效？

**验证方法**:
```powershell
# PowerShell 查看当前虚拟内存配置
Get-CimInstance Win32_PageFileUsage
```

输出示例:
```
Name           AllocatedBaseSize CurrentUsage
----           ----------------- ------------
C:\pagefile.sys 24576            8192
```

### Q4: 还是内存不足怎么办？

**最终方案**: 使用更强大的机器
- 云服务器（AWS, Azure, 阿里云等）
- 本地高配置工作站
- 租用 GPU 服务器

## 性能优化总结

| 优化方法 | 内存节省 | 实施难度 | 效果影响 |
|---------|---------|---------|---------|
| 禁用并行处理 | 50-70% | 简单 ✅ | 训练速度变慢 |
| 增加虚拟内存 | 间接（避免崩溃） | 简单 ✅ | 可能变慢 |
| 缩短训练时间 | 30-50% | 简单 ✅ | 模型精度可能降低 |
| 减少股票数量 | 50-80% | 简单 ✅ | 覆盖范围减少 |
| 减少试验次数 | 无直接影响 | 简单 ✅ | 超参数可能不够优化 |
| 升级硬件 | 根本解决 | 困难 ❌ | 无负面影响 |

## 脚本运行建议

1. **首次运行**: 使用最小数据集测试
   ```python
   train_start = "2024-12-01"  # 仅1个月
   instruments = "sse50"        # 仅50只股票
   n_trials = 1                 # 仅1次试验
   ```

2. **测试成功后**: 逐步增加数据量
   ```python
   # 第二次测试
   train_start = "2024-06-01"  # 6个月
   instruments = "csi300"       # 300只股票
   n_trials = 2

   # 第三次测试
   train_start = "2024-01-01"  # 1年
   instruments = "all"          # 全部股票
   n_trials = 5
   ```

3. **生产环境**: 使用完整数据
   ```python
   train_start = "2023-01-01"
   instruments = "all"
   n_trials = 20
   ```

## 监控脚本运行

创建监控脚本 `monitor_memory.ps1`:

```powershell
# 每10秒检查一次内存使用
while ($true) {
    $mem = Get-CimInstance Win32_OperatingSystem
    $total = [math]::round($mem.TotalVisibleMemorySize / 1MB, 2)
    $free = [math]::round($mem.FreePhysicalMemory / 1MB, 2)
    $used = $total - $free
    $percent = [math]::round(($used / $total) * 100, 2)

    Write-Host "$(Get-Date -Format 'HH:mm:ss') - 内存使用: $used GB / $total GB ($percent%)"
    Start-Sleep -Seconds 10
}
```

运行:
```powershell
# 在另一个 PowerShell 窗口运行
.\monitor_memory.ps1
```

## 参考资料

- [Windows 虚拟内存官方文档](https://learn.microsoft.com/zh-cn/windows/client-management/introduction-page-file)
- [Qlib 官方文档](https://qlib.readthedocs.io/)
- [Optuna 内存优化](https://optuna.readthedocs.io/en/stable/faq.html#how-can-i-optimize-memory-consumption)

---

**更新日期**: 2026-01-10
**版本**: v1.0
**作者**: Claude Code Assistant
