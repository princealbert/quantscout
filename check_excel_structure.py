import pandas as pd

# Excel文件路径
excel_path = r"c:\Users\Administrator\.emgm3\projects\1593121d-dda9-11f0-8409-e89c2599a417\ulti-para-seeker\parameter_optimization_results.xlsx"

# 读取Excel文件
excel_file = pd.ExcelFile(excel_path)

# 打印所有工作表名称
print("工作表名称:")
for sheet_name in excel_file.sheet_names:
    print(f"  - {sheet_name}")

# 打印每个工作表的结构
for sheet_name in excel_file.sheet_names:
    print(f"\n{sheet_name}工作表结构:")
    df = excel_file.parse(sheet_name)
    print(f"  列名: {list(df.columns)}")
    print(f"  行数: {len(df)}")
    print(f"  前5行数据:")
    print(df.head())
    print(f"  数据类型:")
    print(df.dtypes)
