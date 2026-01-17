#!/usr/bin/env python
# coding=utf-8
"""修复数据库WAL文件"""
import sqlite3
import os
import shutil

db_path = os.path.join(os.path.dirname(__file__), 'stock_data_cache.db')
wal_path = db_path + '-wal'
shm_path = db_path + '-shm'

print(f"数据库路径: {db_path}")
print(f"WAL文件大小: {os.path.getsize(wal_path) / (1024**3):.2f} GB")
print(f"SHM文件大小: {os.path.getsize(shm_path) / (1024**2):.2f} MB")

try:
    # 尝试关闭WAL模式并提交
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA wal_checkpoint(FULL)')
    conn.close()
    print("[OK] WAL checkpoint completed")
except Exception as e:
    print(f"[ERROR] WAL checkpoint failed: {e}")

# 备份原WAL文件
if os.path.exists(wal_path):
    backup_wal = wal_path + '.backup'
    try:
        shutil.move(wal_path, backup_wal)
        print(f"[OK] Backed up WAL file to: {backup_wal}")
    except Exception as e:
        print(f"[ERROR] Cannot backup WAL file: {e}")

if os.path.exists(shm_path):
    backup_shm = shm_path + '.backup'
    try:
        shutil.move(shm_path, backup_shm)
        print(f"[OK] Backed up SHM file to: {backup_shm}")
    except Exception as e:
        print(f"[ERROR] Cannot backup SHM file: {e}")

# 验证数据库
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM kline_data")
    count = cursor.fetchone()[0]
    print(f"[OK] Database validated, kline_data has {count} records")
    conn.close()
except Exception as e:
    print(f"[ERROR] Database validation failed: {e}")

print("\nDone! Please restart the application.")
