import os
import glob

# 检查可能的输出路径
paths_to_check = [
    r'D:\github\qlib_0210lq\${base_dir}\csv_data',
    r'D:\github\qlib_data\csv_data',
    r'D:\qlib_data\csv_data',
]

print("=" * 60)
print("Check data output paths")
print("=" * 60)

for path in paths_to_check:
    print(f"\nPath: {path}")
    if os.path.exists(path):
        print("  [OK] Path exists")
        files = os.listdir(path)
        csv_files = [f for f in files if f.endswith('.csv')]
        print(f"  Total files: {len(files)}")
        print(f"  CSV files: {len(csv_files)}")
        if csv_files:
            print(f"  Sample files: {csv_files[:5]}")
            # 检查最新修改的文件
            csv_paths = [os.path.join(path, f) for f in csv_files]
            latest = max(csv_paths, key=os.path.getmtime)
            import time
            mtime = os.path.getmtime(latest)
            print(f"  Latest file: {os.path.basename(latest)}")
            print(f"  Modified time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))}")
    else:
        print("  [X] Path does not exist")

print("\n" + "=" * 60)
print("Check configuration loading")
print("=" * 60)

try:
    from qlib_code.sql2csv_refactored.config.config_loader import ConfigLoader
    config = ConfigLoader.load()
    output_dir = config.output.get('csv_output_dir')
    print(f"Output dir in config: {output_dir}")
    print(f"Path exists: {os.path.exists(output_dir)}")
except Exception as e:
    print(f"Failed to load config: {e}")
