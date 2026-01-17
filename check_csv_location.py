import os
import glob

# Check all possible locations
locations = [
    r'D:\github\qlib_0210lq\${base_dir}\csv_data',
    r'D:\github\qlib_0210lq\qlib_data\csv_data',
    r'D:\github\qlib_data\csv_data',
]

print("Checking CSV file locations:")
print("=" * 60)

for loc in locations:
    print(f"\nLocation: {loc}")
    print(f"Exists: {os.path.exists(loc)}")
    if os.path.exists(loc):
        csv_files = glob.glob(os.path.join(loc, '*.csv'))
        print(f"CSV files: {len(csv_files)}")
        if csv_files:
            print("Sample files:")
            for f in sorted(csv_files)[:5]:
                print(f"  - {os.path.basename(f)}")

# Also check what's in ${base_dir} directory
base_dir_literal = r'D:\github\qlib_0210lq\${base_dir}'
if os.path.exists(base_dir_literal):
    print(f"\n\nContents of literal '${base_dir}' directory:")
    print("=" * 60)
    items = os.listdir(base_dir_literal)
    for item in items:
        item_path = os.path.join(base_dir_literal, item)
        if os.path.isdir(item_path):
            print(f"  [DIR]  {item}")
        else:
            print(f"  [FILE] {item}")
