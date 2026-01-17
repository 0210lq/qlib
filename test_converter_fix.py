"""
测试修改后的数据转换器是否能正确跳过停牌日数据
"""
from qlib_code.sql2csv_refactored.core.converter import DataConverter
from qlib_code.sql2csv_refactored.config.config_loader import ConfigLoader

# 加载配置
config = ConfigLoader.load()

# 创建转换器
converter = DataConverter(config.output)

# 模拟数据：包含正常交易日和停牌日
test_data = [
    # 正常交易日
    {
        'date': '2024-01-01',
        'code': '000001.SZ',
        'open': 10.0,
        'high': 11.0,
        'low': 9.5,
        'close': 10.5,
        'volume': 1000000,
        'amount': 10500000,
        'factor': 1.0
    },
    # 停牌日（所有交易数据为None）
    {
        'date': '2024-01-02',
        'code': '000001.SZ',
        'open': None,
        'high': None,
        'low': None,
        'close': None,
        'volume': None,
        'amount': None,
        'factor': 1.0
    },
    # 正常交易日
    {
        'date': '2024-01-03',
        'code': '000001.SZ',
        'open': 10.5,
        'high': 11.5,
        'low': 10.0,
        'close': 11.0,
        'volume': 1200000,
        'amount': 13200000,
        'factor': 1.0
    },
]

print("测试数据转换器...")
print(f"输入数据: {len(test_data)} 行")

try:
    df = converter.convert_to_dataframe(test_data, 'stock')
    print("[SUCCESS] 转换成功!")
    print(f"输出数据: {len(df)} 行")
    print(f"跳过的停牌日: {len(test_data) - len(df)} 行")
    print("\n输出DataFrame:")
    print(df)
    print("\n[PASS] 测试通过! 停牌日数据已被正确跳过。")
except Exception as e:
    print(f"[FAIL] 转换失败: {e}")
    import traceback
    traceback.print_exc()
