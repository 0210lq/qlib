"""查找指数CSV文件"""
from pathlib import Path

# 查找所有 csv_data 目录
print("查找csv_data目录...")
csv_dirs = list(Path('.').rglob('csv_data'))

print(f'\n找到 {len(csv_dirs)} 个csv_data目录:')
for d in csv_dirs:
    print(f'  {d}')
    # 检查指数文件
    index_files = list(d.glob('000*.csv')) + list(d.glob('932*.csv'))
    if index_files:
        print(f'    包含 {len(index_files)} 个指数文件:')
        for f in index_files:
            size = f.stat().st_size
            print(f'      {f.name} ({size} bytes)')
