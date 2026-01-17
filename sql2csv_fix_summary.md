# SQL2CSV 停牌日数据处理修复总结

## 问题描述

运行 `run_sql2csv()` 时遇到大量错误：
```
Failed to convert stock data to DataFrame: float() argument must be a string or a real number, not 'NoneType'
```

**原因**: 数据库中很多股票在某些日期停牌或数据不完整，部分或全部交易字段（open, high, low, close, volume, amount）为 `None`，但代码尝试将 `None` 转换为 `float` 导致错误。

## 修改方案

采用**方案A**: 自动跳过数据不完整的交易日，只保留所有必需字段都有值的有效交易数据。

## 代码修改

修改文件: `qlib_code/sql2csv_refactored/core/converter.py`

### 1. 新增方法: `_is_valid_trading_day()`

```python
def _is_valid_trading_day(self, row: Dict[str, Any]) -> bool:
    """
    检查是否为有效交易日（是否有完整的交易数据）

    只有当所有必需字段都不为None时，才认为是有效交易日
    """
    required_trading_fields = ['open', 'high', 'low', 'close', 'volume', 'amount']

    # 检查是否所有必需字段都有值（不为None）
    all_valid = all(row.get(field) is not None for field in required_trading_fields)

    return all_valid
```

**关键点**:
- 检查**所有**会被转换为float的字段（包括amount）
- 只有全部字段都有值才返回True
- 任何一个字段为None都会被跳过

### 2. 修改方法: `_validate_row()`

**修改前**:
- 要求 `close` 字段必须存在且不能为 None
- 导致停牌日数据验证失败

**修改后**:
- 只要求 `date` 和 `code` 必须存在
- 允许交易数据字段为 None
- 在后续处理中通过 `_is_valid_trading_day()` 跳过不完整数据

### 3. 修改方法: `convert_to_dataframe()`

**修改前**:
```python
for row in rows:
    self._validate_row(row, data_type)
    # 直接转换，遇到None会报错
    qlib_row = {
        'open': float(row['open']),  # None会导致错误
        'amount': float(row['amount']),  # None会导致错误
        ...
    }
```

**修改后**:
```python
skipped_count = 0
for row in rows:
    self._validate_row(row, data_type)

    # 检查是否为有效交易日（跳过数据不完整的日期）
    if not self._is_valid_trading_day(row):
        skipped_count += 1
        continue

    # 只转换有效交易日数据（保证所有字段都不是None）
    qlib_row = {
        'open': float(row['open']),  # 保证不是None
        'amount': float(row['amount']),  # 保证不是None
        ...
    }
```

## 测试结果

### 单元测试
```python
# 测试数据：3行（2个正常交易日 + 1个停牌日）
test_data = [
    {'date': '2024-01-01', 'open': 10.0, 'close': 10.5, ...},  # 正常
    {'date': '2024-01-02', 'open': None, 'close': None, ...},  # 停牌
    {'date': '2024-01-03', 'open': 10.5, 'close': 11.0, ...},  # 正常
]

# 结果
输入数据: 3 行
输出数据: 2 行
跳过的停牌日: 1 行
✓ 测试通过
```

### 完整运行对比

| 指标 | 修改前 | 修改后（预期） |
|------|--------|----------------|
| 总股票数 | 5949 | 5949 |
| 成功处理 | 5206 (87.51%) | ~5949 (100%) |
| 失败 | 743 (12.49%) | ~0 (0%) |
| 停牌日处理 | 报错失败 | 自动跳过 |

## 修改历史

### 第一次修改（不完整）
- 只检查了5个字段：open, high, low, close, volume
- **遗漏了 amount 字段**
- 导致当amount为None时仍然报错

### 第二次修改（完整）
- 检查所有6个字段：open, high, low, close, volume, **amount**
- 逻辑从"所有字段都为None才跳过"改为"任何字段为None就跳过"
- 确保传递给float()的值永远不会是None

## 数据库信息

- **最早日期**: 2012-01-04
- **最晚日期**: 2026-01-14
- **交易日数量**: 3408天
- **股票数量**: 5949只
- **最近交易日**: 2026-01-14 (5469只股票有数据)

## 使用方法

修改后的代码会自动跳过数据不完整的交易日，无需额外配置：

```python
from qlib_code.sql2csv_refactored import run_sql2csv

# 正常调用即可
run_sql2csv(
    market='ALL',
    start_date='20150106',
    end_date='20260114'
)
```

## 优点

1. **自动处理数据不完整的情况**: 无需手动处理 None 值
2. **数据质量更高**: CSV文件只包含完整的有效交易数据
3. **兼容性好**: 符合Qlib对数据格式的要求
4. **日志清晰**: 记录跳过的数据行数量
5. **健壮性强**: 处理各种数据缺失情况（全部缺失、部分缺失）

## 注意事项

- 数据不完整的交易日会被完全跳过，不会出现在CSV文件中
- 时间序列可能不连续（正常现象，因为不完整数据被移除）
- 如果需要保留不完整数据（用NaN填充），需要采用方案B（未实现）
- **任何一个必需字段为None都会导致该行被跳过**

## 修改日期

2026-01-15 (第二次修复)
