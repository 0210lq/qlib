"""
检查数据库中实际有哪些日期的数据
"""
from qlib_code.sql2csv_refactored.core.database import DatabaseConnection
from qlib_code.sql2csv_refactored.config.config_loader import ConfigLoader
from sqlalchemy import text

# 加载配置
config = ConfigLoader.load()

# 创建数据库连接
db_conn = DatabaseConnection(config.database)

print("检查数据库中的数据日期范围...")

try:
    with db_conn.get_connection() as conn:
        # 查询最早和最晚的日期
        query = text("""
            SELECT
                MIN(valuation_date) as min_date,
                MAX(valuation_date) as max_date,
                COUNT(DISTINCT valuation_date) as date_count,
                COUNT(DISTINCT code) as stock_count
            FROM data_stock
            WHERE close IS NOT NULL
        """)

        result = conn.execute(query).fetchone()

        if result:
            print(f"\n数据库统计:")
            print(f"  最早日期: {result[0]}")
            print(f"  最晚日期: {result[1]}")
            print(f"  交易日数量: {result[2]}")
            print(f"  股票数量: {result[3]}")

            # 查询最近10个交易日
            query2 = text("""
                SELECT DISTINCT valuation_date, COUNT(*) as stock_count
                FROM data_stock
                WHERE close IS NOT NULL
                GROUP BY valuation_date
                ORDER BY valuation_date DESC
                LIMIT 10
            """)

            print(f"\n最近10个交易日:")
            results = conn.execute(query2).fetchall()
            for row in results:
                print(f"  {row[0]}: {row[1]} 只股票")
        else:
            print("数据库中没有数据")

except Exception as e:
    print(f"查询失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    db_conn.close()
