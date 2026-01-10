# Qlib 路径配置更新报告

## 更新日期
2026-01-10

## 更新原因
Qlib 源码已包含在项目的 `qlib/` 目录中，不再需要外部克隆，因此需要更新所有配置文件中的 qlib 路径引用。

## 更新内容

### 1. 配置文件更新

#### config/paths.yaml
**原配置：**
```yaml
qlib_workdir: "../qlib"  # 指向项目外部
```

**新配置：**
```yaml
qlib_workdir: "./qlib"  # 指向项目内部
```

#### config/paths.example.yaml
**原配置：**
```yaml
# Qlib 仓库克隆路径
# 推荐克隆到项目外部，避免污染项目目录
# 示例：
#   - Linux/Mac: "${HOME}/qlib"
#   - Windows: "${USERPROFILE}\\qlib"
#   - 相对路径: "../qlib"
qlib_workdir: "../qlib"
```

**新配置：**
```yaml
# Qlib 仓库路径
# 注意：qlib 已包含在项目中，使用项目内的相对路径
# 如果需要使用外部 qlib，可以修改为：
#   - 相对路径（项目外）: "../qlib"
#   - Linux/Mac: "${HOME}/qlib"
#   - Windows: "${USERPROFILE}\\qlib"
qlib_workdir: "./qlib"
```

### 2. README.md 更新

#### 快速开始 - 准备数据部分
**原说明：**
```bash
# 克隆 Qlib 仓库（如果还没有）
git clone https://github.com/microsoft/qlib.git

# 导出数据（选择其一）
python qlib_code/sql2csv.py        # 从数据库导出
```

**新说明：**
```bash
# 注意: Qlib 源码已包含在项目的 qlib/ 目录中，无需单独克隆。

# 导出数据（选择其一）
python qlib_code/sql2csv.py        # 从数据库导出
```

#### 配置说明部分
**原示例：**
```yaml
qlib_workdir: "../qlib"
```

**新示例：**
```yaml
qlib_workdir: "./qlib"  # Qlib 源码在项目内
```

#### 项目结构部分
**新增：**
```
├── qlib/                                # Qlib 源码（已包含在项目中）
```

#### 常见问题部分
**原说明：**
```bash
# 确保已克隆 qlib
git clone https://github.com/microsoft/qlib.git

# 在 config/paths.yaml 中配置 qlib_workdir 路径
```

**新说明：**
```
Qlib 源码已包含在项目的 qlib/ 目录中。

确保 config/paths.yaml 中的配置正确：
qlib_workdir: "./qlib"  # 指向项目内的 qlib 目录

dump_bin.py 位置：qlib/scripts/dump_bin.py
```

## 路径验证

### Qlib 目录结构验证
```
qlib_sql-master/
└── qlib/                    # ✅ 存在
    ├── scripts/             # ✅ 存在
    │   ├── dump_bin.py      # ✅ 存在（已验证）
    │   ├── get_data.py      # ✅ 存在
    │   └── ...
    ├── qlib/                # Qlib 主模块
    └── setup.py             # 安装脚本
```

### 路径解析说明

**配置值：** `"./qlib"`

**含义：**
- `.` 表示当前目录（项目根目录）
- `/qlib` 表示根目录下的 qlib 文件夹

**实际路径：**
```
D:\github\qlib_sql-master\qlib\
```

**关键文件位置：**
- dump_bin.py: `D:\github\qlib_sql-master\qlib\scripts\dump_bin.py`
- Qlib 主模块: `D:\github\qlib_sql-master\qlib\qlib\`

## 兼容性说明

### 如果需要使用外部 Qlib

如果用户想使用外部安装的 Qlib（例如通过 pip 安装或独立克隆），可以修改配置：

**选项 1：使用外部克隆的 Qlib**
```yaml
qlib_workdir: "../qlib"  # 项目外部
```

**选项 2：使用系统安装的 Qlib**
```yaml
qlib_workdir: "${HOME}/qlib"  # Linux/Mac
# 或
qlib_workdir: "${USERPROFILE}\\qlib"  # Windows
```

**选项 3：使用绝对路径**
```yaml
qlib_workdir: "/path/to/qlib"  # Linux/Mac
# 或
qlib_workdir: "D:\\path\\to\\qlib"  # Windows
```

## 影响的文件清单

### 更新的文件
- [x] `config/paths.yaml` - 实际配置文件
- [x] `config/paths.example.yaml` - 示例配置文件
- [x] `README.md` - 项目文档

### 不需要更新的文件
- Python 代码文件（自动从配置读取路径）
- MATLAB 代码文件（使用 paths.yaml 配置）

## 用户操作指南

### 对现有用户
如果您之前配置了外部的 qlib 路径，建议更新为项目内路径：

**步骤 1：** 更新 `config/paths.yaml`
```yaml
qlib_workdir: "./qlib"
```

**步骤 2：** 验证路径是否正确
```bash
# Linux/Mac
ls -la qlib/scripts/dump_bin.py

# Windows
dir qlib\scripts\dump_bin.py
```

**步骤 3：** 重新运行程序
```bash
python qlib_code/run_daily_update.py --date 2025-10-27
```

### 对新用户
按照 README.md 的快速开始部分配置即可，默认配置已指向项目内的 qlib。

## 优势说明

使用项目内的 Qlib 相比外部克隆的优势：

1. **简化部署** - 无需单独克隆 Qlib，减少安装步骤
2. **版本一致** - 确保所有开发者使用相同版本的 Qlib
3. **便于修改** - 可以直接修改 Qlib 源码进行调试
4. **跨平台兼容** - 相对路径 `./qlib` 在所有平台上都有效
5. **减少错误** - 避免路径配置错误导致的问题

## 注意事项

1. **Git 管理**: 确保 `qlib/` 目录被正确提交到 Git（如果需要）
2. **更新 Qlib**: 如需更新 Qlib 版本，可以在 `qlib/` 目录中拉取最新代码
3. **冲突处理**: 如果修改了 Qlib 源码，更新时注意处理冲突

## 验证清单

- [x] qlib 目录存在于项目中
- [x] dump_bin.py 文件存在
- [x] config/paths.yaml 已更新
- [x] config/paths.example.yaml 已更新
- [x] README.md 已更新（快速开始、配置说明、项目结构、常见问题）
- [x] 路径格式正确（相对路径 `./qlib`）
- [x] 文档说明清晰完整

## 总结

所有配置文件和文档已成功更新，现在项目使用内置的 Qlib 源码，路径配置为 `./qlib`。用户无需单独克隆 Qlib 仓库，即可直接使用项目。
