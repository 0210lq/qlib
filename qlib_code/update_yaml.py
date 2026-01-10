import yaml
from sqlalchemy import create_engine, text
import os
from copy import deepcopy
from ruamel.yaml import YAML
import sys
import time
import traceback

def read_best_params_from_db(db_config_path):
   
    
    with open(db_config_path, 'r', encoding='utf-8') as f:
            db_cfg = yaml.safe_load(f) or {}
    
    db_url = f"mysql+pymysql://{db_cfg['user2']}:{db_cfg['password']}@{db_cfg['host3']}:{db_cfg['port']}/{db_cfg['database4']}"
    try:
        engine = create_engine(db_url)
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        raise RuntimeError("数据库连接失败，无法读取最佳参数")
   
    
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT * FROM best_params 
                ORDER BY update_time DESC 
                LIMIT 1
            """)
        )
       
        latest_params = result.mappings().first()
        if latest_params is None:
            raise RuntimeError("No rows found in 'best_params' table. Aborting.")
    
    return latest_params

import re

def update_yaml(yaml_file_path, best_params):
 
    # 读取原始内容
    with open(yaml_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 构建要更新的参数字典
    param_updates = {
        "colsample_bytree": best_params["colsample_bytree"],
        "learning_rate": best_params["learning_rate"],
        "subsample": best_params["subsample"],
        "lambda_l1": best_params["lambda_l1"],
        "lambda_l2": best_params["lambda_l2"],
        "num_leaves": best_params["num_leaves"],
        "feature_fraction": best_params["feature_fraction"],
        "bagging_fraction": best_params["bagging_fraction"],
        "bagging_freq": best_params["bagging_freq"],
        "min_data_in_leaf": best_params["min_data_in_leaf"],
        "min_child_samples": best_params["min_child_samples"]
    }
    
    # 更新内容
    updated_content = content
    for param_name, param_value in param_updates.items():

        pattern = rf'(\s+{re.escape(param_name)}:\s*)([^\n#]+)'
        replacement = rf'\g<1>{param_value}'
        
        if re.search(pattern, updated_content):
            updated_content = re.sub(pattern, replacement, updated_content)
        
        else:
            print(f"警告: 未找到kwargs部分，无法添加参数 {param_name}")


    custom_path  = os.getenv('GLOBAL_TOOLSFUNC_test')
    sys.path.append(custom_path )
    
    from time_utils import next_workday_calculate

    valid_start = str(next_workday_calculate(best_params["train_end"]))
    valid_end = str(next_workday_calculate(valid_start))
    test_start = str(next_workday_calculate(valid_end))
    test_end = str(next_workday_calculate(test_start))

    date_updates = [
        ("start_time", best_params["train_start"]),
        ("end_time", test_end),
        ("fit_start_time", best_params["train_start"]),
        ("fit_end_time", best_params["train_end"])
    ]
    
    # 更新data_handler_config中的日期
    for param_name, param_value in date_updates:
        if param_value:
            pattern = rf'(\s+{param_name}:\s*)(\d{{4}}-\d{{2}}-\d{{2}})(\s*#.*)?'
            replacement = rf'\g<1>{param_value}\3'
            updated_content = re.sub(pattern, replacement, updated_content)
    
    
    segments_pattern = r'(dataset:(?:\s*\n(?:[ \t]*[^\n]*\n)*?(?:\s*)segments:(?:\s*\n(?:[ \t]*[^\n]*\n)*?\s*train:\s*\[)([^,\]]+),\s*([^,\]]+)(\](?:\s*\n(?:[ \t]*[^\n]*\n)*?\s*valid:\s*\[)([^,\]]+),\s*([^,\]]+)(\](?:\s*\n(?:[ \t]*[^\n]*\n)*?\s*test:\s*\[)([^,\]]+),\s*([^,\]]+)(\])))'
            
    lines = updated_content.split('\n')
    new_lines = []
    
    for line in lines:
        # 检查并替换train行
        if 'train:' in line and '[' in line and ']' in line:
            new_line = re.sub(r'(\s*train:\s*\[)[^]]+(\])', 
                                rf'\g<1>{best_params["train_start"]}, {best_params["train_end"]}\2', 
                                line)
        
            line = new_line
        
        # 检查并替换valid行
        elif 'valid:' in line and '[' in line and ']' in line:
            new_line = re.sub(r'(\s*valid:\s*\[)[^]]+(\])', 
                                rf'\g<1>{valid_start}, {valid_end}\2', 
                                line)

            line = new_line
        
        # 检查并替换test行
        elif 'test:' in line and '[' in line and ']' in line:
            new_line = re.sub(r'(\s*test:\s*\[)[^]]+(\])', 
                                rf'\g<1>{test_start}, {test_end}\2', 
                                line)
           
            line = new_line
        
        new_lines.append(line)
    
    updated_content = '\n'.join(new_lines)  

    # 更新port_analysis_config中的回测日期
    backtest_updates = [
        ("start_time", test_start, "backtest:"),
        ("end_time", test_end, "backtest:")
    ]
    
    for param_name, param_value, section in backtest_updates:
        if param_value:
        
            pattern = rf'({re.escape(section)}[^\n]*\n(?:\s+[^\n]*\n)*?\s+{param_name}:\s*)(\d{{4}}-\d{{2}}-\d{{2}})(\s*#.*)?'
            replacement = rf'\g<1>{param_value}\3'
            if re.search(pattern, updated_content):
                updated_content = re.sub(pattern, replacement, updated_content)
            else:
                print(f"警告: 未找到{section}部分的{param_name}")


    # 写回文件
    with open(yaml_file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    return True



if __name__ == "__main__":
    from config_utils import load_config_with_substitution

    # 获取项目根目录（qlib_code 的上一级目录）
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    db_config_path = os.path.join(project_root, 'config', 'db.yaml')
    config_path = os.path.join(project_root, 'config', 'paths.yaml')

    cfg = load_config_with_substitution(config_path)
    yaml_file_path = cfg['yaml_path']

    # 如果是相对路径，相对于项目根目录解析
    if not os.path.isabs(yaml_file_path):
        yaml_file_path = os.path.abspath(os.path.join(project_root, yaml_file_path))

    if not os.path.exists(yaml_file_path):
        raise FileNotFoundError(f"YAML 配置文件不存在: {yaml_file_path}")

    latest_params = read_best_params_from_db(db_config_path)

    # 更新YAML文件
    if update_yaml(yaml_file_path, latest_params):

        print(f"成功更新YAML文件")
    else:
        print("更新YAML文件失败")
        

