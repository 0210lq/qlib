% 数据库配置文件（MATLAB）
% 使用说明：
% 1. 复制此文件为 config_db.m
%    Windows: Copy-Item config_db.example.m config_db.m
%    Linux/Mac: cp config_db.example.m config_db.m
% 2. 根据实际环境修改数据库连接信息
% 3. 注意：config_db.m 包含敏感信息，不会被提交到 Git

% ============================================
% 数据库配置结构体
% ============================================

% 创建数据库配置结构体
db_config = struct();

% ============================================
% 主数据库连接信息
% ============================================

% 主机地址（支持格式：'hostname:port' 或 'hostname'）
% 示例：
%   - 'localhost:3306'
%   - 'your-database-server.com:3306'
db_config.host = 'localhost:3306';

% 备用主机地址（可选，用于某些特定数据源）
db_config.host2 = 'localhost:3306';

% 数据库名称
db_config.dbname = 'data_prepared_new';

% 用户名
db_config.username = 'your_username';

% 密码
db_config.password = 'your_password';

% ============================================
% Score 数据源配置
% ============================================

% Score 数据来源：'db' 或 'csv'
%   - 'db': 从数据库读取 score 数据
%   - 'csv': 从本地 CSV 文件读取 score 数据
db_config.score_source = 'csv';

% 本地 score 文件目录（当 score_source = 'csv' 时使用）
% 示例：
%   - Windows: 'E:\qlib_data\output\prediction'
%   - Linux/Mac: '~/qlib_data/output/prediction'
%   - 相对路径: '../qlib_data/output/prediction'
db_config.local_score_dir = '../qlib_data/output/prediction';

% ============================================
% 配置说明
% ============================================

% 配置完成后，DatabaseConnector 类会自动读取此配置
%
% 使用示例：
%   config_db;  % 加载配置
%   connector = DatabaseConnector();  % 创建数据库连接器
%   conn = connector.openConnection();  % 打开连接
