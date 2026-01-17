#!/usr/bin/env python
# coding=utf-8
"""强制关闭WAL模式"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'stock_data_cache.db')

print("Connecting to database...")
conn = sqlite3.connect(db_path)

# 关闭WAL模式
print("Disabling WAL mode...")
conn.execute('PRAGMA journal_mode=DELETE')
conn.commit()

# 检查点
print("Running checkpoint...")
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
conn.commit()

# 关闭连接
conn.close()

print("Done! WAL mode disabled and checkpoint completed.")
