import json
import os

file_path = 'config/current_backtest_config.json'

# 读取现有文件
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 添加selected_stocks字段
data['selected_stocks'] = ['SHSE.600036', 'SHSE.601318', 'SZSE.000858', 'SZSE.000001', 'SHSE.600519']

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('✅ 已成功添加selected_stocks字段到current_backtest_config.json文件')