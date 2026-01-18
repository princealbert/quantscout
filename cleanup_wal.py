#!/usr/bin/env python
# coding=utf-8
"""
数据库WAL文件定期清理脚本
用于清理过大的WAL文件，防止数据库锁定问题
"""

import sqlite3
import os
import time
from pathlib import Path


def check_wal_size(db_path: str) -> tuple:
    """检查WAL文件大小"""
    wal_path = f"{db_path}-wal"
    shm_path = f"{db_path}-shm"

    if not os.path.exists(db_path):
        return False, 0, 0, 0

    db_size = os.path.getsize(db_path)
    wal_size = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0
    shm_size = os.path.getsize(shm_path) if os.path.exists(shm_path) else 0

    total_size = db_size + wal_size + shm_size

    return True, db_size, wal_size, shm_size, total_size


def cleanup_wal(db_path: str, force: bool = False) -> dict:
    """清理WAL文件"""
    exists, db_size, wal_size, shm_size, total_size = check_wal_size(db_path)

    if not exists:
        return {
            "success": False,
            "error": "数据库文件不存在",
            "db_size": 0,
            "wal_size": 0,
            "shm_size": 0,
            "total_size": 0
        }

    # 判断是否需要清理
    threshold_mb = 100  # WAL文件超过100MB就清理
    wal_size_mb = wal_size / (1024 * 1024)

    if not force and wal_size_mb < threshold_mb:
        return {
            "success": True,
            "action": "skipped",
            "reason": f"WAL文件大小 ({wal_size_mb:.1f}MB) 未超过阈值 ({threshold_mb}MB)",
            "before": {
                "db_size_mb": db_size / (1024 * 1024),
                "wal_size_mb": wal_size_mb,
                "shm_size_mb": shm_size / (1024 * 1024),
                "total_mb": total_size / (1024 * 1024)
            },
            "after": None
        }

    # 执行清理
    try:
        # 确保没有其他进程在使用数据库
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        conn.execute('PRAGMA optimize')
        conn.commit()
        conn.close()

        # 等待文件系统同步
        time.sleep(0.5)

        # 检查清理后的大小
        _, after_db_size, after_wal_size, after_shm_size, after_total_size = check_wal_size(db_path)

        return {
            "success": True,
            "action": "cleaned",
            "before": {
                "db_size_mb": db_size / (1024 * 1024),
                "wal_size_mb": wal_size_mb,
                "shm_size_mb": shm_size / (1024 * 1024),
                "total_mb": total_size / (1024 * 1024)
            },
            "after": {
                "db_size_mb": after_db_size / (1024 * 1024),
                "wal_size_mb": after_wal_size / (1024 * 1024),
                "shm_size_mb": after_shm_size / (1024 * 1024),
                "total_mb": after_total_size / (1024 * 1024)
            },
            "reduced_wal_mb": wal_size_mb - after_wal_size / (1024 * 1024),
            "reduced_total_mb": total_size / (1024 * 1024) - after_total_size / (1024 * 1024)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "db_size_mb": db_size / (1024 * 1024),
            "wal_size_mb": wal_size_mb,
            "shm_size_mb": shm_size / (1024 * 1024),
            "total_mb": total_size / (1024 * 1024)
        }


def print_result(result: dict):
    """打印清理结果"""
    print("=" * 60, flush=True)
    if result["success"]:
        if result.get("action") == "skipped":
            print(f"[跳过] {result['reason']}", flush=True)
        else:
            print("[成功] WAL文件清理完成", flush=True)
            before = result["before"]
            after = result["after"]
            print(f"  清理前:", flush=True)
            print(f"    - 数据库: {before['db_size_mb']:.1f} MB", flush=True)
            print(f"    - WAL文件: {before['wal_size_mb']:.1f} MB", flush=True)
            print(f"    - SHM文件: {before['shm_size_mb']:.1f} MB", flush=True)
            print(f"    - 总大小: {before['total_mb']:.1f} MB", flush=True)
            print(f"  清理后:", flush=True)
            print(f"    - 数据库: {after['db_size_mb']:.1f} MB", flush=True)
            print(f"    - WAL文件: {after['wal_size_mb']:.1f} MB", flush=True)
            print(f"    - SHM文件: {after['shm_size_mb']:.1f} MB", flush=True)
            print(f"    - 总大小: {after['total_mb']:.1f} MB", flush=True)
            print(f"  减少:", flush=True)
            print(f"    - WAL文件: {result['reduced_wal_mb']:.1f} MB", flush=True)
            print(f"    - 总大小: {result['reduced_total_mb']:.1f} MB", flush=True)
    else:
        print(f"[失败] 清理失败: {result.get('error', '未知错误')}", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库WAL文件清理工具")
    parser.add_argument("--db", default="stock_data_cache.db", help="数据库文件路径")
    parser.add_argument("--force", action="store_true", help="强制清理，忽略阈值")
    parser.add_argument("--check-only", action="store_true", help="只检查，不清理")

    args = parser.parse_args()

    if args.check_only:
        exists, db_size, wal_size, shm_size, total_size = check_wal_size(args.db)
        if exists:
            print(f"[检查] 数据库文件状态:", flush=True)
            print(f"  - 数据库: {db_size / (1024 * 1024):.1f} MB", flush=True)
            print(f"  - WAL文件: {wal_size / (1024 * 1024):.1f} MB", flush=True)
            print(f"  - SHM文件: {shm_size / (1024 * 1024):.1f} MB", flush=True)
            print(f"  - 总大小: {total_size / (1024 * 1024):.1f} MB", flush=True)
        else:
            print("[错误] 数据库文件不存在", flush=True)
    else:
        result = cleanup_wal(args.db, force=args.force)
        print_result(result)
