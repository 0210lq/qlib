"""
诊断指数数据问题的脚本
检查数据库中的指数表和数据
"""

import pymysql
import yaml
from pathlib import Path

# 读取配置
config_path = Path(__file__).parent / "config" / "sql2csv.yaml"
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

db_config = config['database']
schema = config['schema']

# 连接数据库
conn = pymysql.connect(
    host=db_config['host'],
    port=db_config['port'],
    user=db_config['user'],
    password=db_config['password'],
    database=db_config['database'],
    charset='utf8mb4'
)

cursor = conn.cursor()

print("=" * 80)
print("数据库诊断报告")
print("=" * 80)

# 1. 检查指数表是否存在
index_table = schema['tables']['index']
print(f"\n1. 检查表 '{index_table}' 是否存在...")

cursor.execute(f"SHOW TABLES LIKE '{index_table}'")
table_exists = cursor.fetchone()

if table_exists:
    print(f"   [OK] 表 '{index_table}' 存在")

    # 2. 查看表结构
    print(f"\n2. 表 '{index_table}' 的结构:")
    cursor.execute(f"DESCRIBE {index_table}")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   - {col[0]} ({col[1]})")

    # 3. 检查数据总量
    print(f"\n3. 表 '{index_table}' 的数据量:")
    cursor.execute(f"SELECT COUNT(*) FROM {index_table}")
    total_count = cursor.fetchone()[0]
    print(f"   总记录数: {total_count}")

    # 4. 检查指数代码列表
    code_col = schema['index_columns']['code']
    print(f"\n4. 表中的指数代码列表:")
    cursor.execute(f"SELECT DISTINCT {code_col} FROM {index_table} ORDER BY {code_col}")
    codes = cursor.fetchall()
    if codes:
        print(f"   找到 {len(codes)} 个不同的指数代码:")
        for code in codes[:20]:  # 只显示前20个
            print(f"   - {code[0]}")
        if len(codes) > 20:
            print(f"   ... 还有 {len(codes) - 20} 个")
    else:
        print("   [FAIL] 表中没有数据！")

    # 5. 检查目标指数是否存在
    print(f"\n5. 检查目标指数是否存在:")
    target_indices = ['000905.SH', '000300.SH', '000016.SH', '000852.SH', '932000.CSI']
    for idx_code in target_indices:
        cursor.execute(f"SELECT COUNT(*) FROM {index_table} WHERE {code_col} = %s", (idx_code,))
        count = cursor.fetchone()[0]
        status = "[OK]" if count > 0 else "[FAIL]"
        print(f"   {status} {idx_code}: {count} 条记录")

    # 6. 如果目标指数不存在，尝试模糊匹配
    print(f"\n6. 尝试模糊匹配指数代码:")
    for idx_code in target_indices:
        base_code = idx_code.split('.')[0]  # 提取数字部分
        cursor.execute(f"SELECT DISTINCT {code_col} FROM {index_table} WHERE {code_col} LIKE %s LIMIT 5", (f'%{base_code}%',))
        similar = cursor.fetchall()
        if similar:
            print(f"   {idx_code} 的相似代码:")
            for s in similar:
                print(f"     - {s[0]}")
        else:
            print(f"   {idx_code}: 未找到相似代码")

else:
    print(f"   [FAIL] 表 '{index_table}' 不存在！")
    print(f"\n   数据库中的所有表:")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    for table in tables:
        print(f"   - {table[0]}")

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)

cursor.close()
conn.close()
