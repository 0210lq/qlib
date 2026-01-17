"""检查配置加载和输出路径"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from qlib_code.sql2csv_refactored.config.config_loader import ConfigLoader

# 加载配置
config = ConfigLoader()
sql2csv_config = config._load_base_configs()

print("配置信息:")
print(f"  paths配置: {sql2csv_config.get('paths', {})}")
print(f"\n  sql2csv.output配置: {sql2csv_config.get('sql2csv', {}).get('output', {})}")
print(f"\n  csv_output_dir: {sql2csv_config.get('sql2csv', {}).get('output', {}).get('csv_output_dir')}")

# 检查实际路径
csv_dir = sql2csv_config.get('sql2csv', {}).get('output', {}).get('csv_output_dir')
if csv_dir:
    csv_path = Path(csv_dir)
    print(f"\nCSV输出路径:")
    print(f"  配置值: {csv_dir}")
    print(f"  绝对路径: {csv_path.resolve()}")
    print(f"  是否存在: {csv_path.exists()}")

    if csv_path.exists():
        # 列出指数文件
        index_files = list(csv_path.glob('000*.csv')) + list(csv_path.glob('932*.csv'))
        print(f"  指数文件数量: {len(index_files)}")
        for f in index_files[:10]:
            print(f"    - {f.name} ({f.stat().st_size} bytes)")
