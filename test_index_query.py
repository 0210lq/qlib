"""测试指数数据查询"""
import pymysql

conn = pymysql.connect(
    host='rm-bp1o6we7s3o1h76x1to.mysql.rds.aliyuncs.com',
    port=3306,
    user='kai',
    password='Abcd1234#',
    database='data_prepared_new'
)

cursor = conn.cursor(pymysql.cursors.DictCursor)

# 测试查询
query = """
SELECT
    valuation_date as date,
    code,
    open,
    high,
    low,
    close,
    volume,
    amt as amount,
    1.0 as factor
FROM data_index
WHERE code IN ('000905.SH')
AND valuation_date BETWEEN '2026-01-01' AND '2026-01-15'
ORDER BY code, valuation_date
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f'查询结果: {len(rows)} 行')
if rows:
    print('\n前3行数据:')
    for row in rows[:3]:
        print(f'  {row}')

    # 检查是否有 None 值
    print('\n检查 None 值:')
    for i, row in enumerate(rows):
        has_none = any(v is None for k, v in row.items() if k in ['open', 'high', 'low', 'close', 'volume', 'amount'])
        if has_none:
            print(f'  行 {i+1} 有 None 值: {row}')

cursor.close()
conn.close()
