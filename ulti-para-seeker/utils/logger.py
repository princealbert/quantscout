#!/usr/bin/env python
# coding=utf-8
"""
参数优化器日志管理器 - 支持实时日志记录和文件持久化
"""

import time
import threading
from queue import Queue, Empty
from datetime import datetime
from typing import List, Dict
import os


class OptimizerLogger:
    """参数优化器日志管理器"""
    
    def __init__(self, log_file=None, max_lines=1000):
        self.log_queue = Queue()
        self.max_lines = max_lines
        self.lock = threading.Lock()
        self.log_lines = []
        self.log_file = log_file
        
        # 创建日志目录
        if self.log_file:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
        
    def log(self, level: str, message: str):
        """记录日志"""
        # 生成完整的时间戳（包含日期）
        full_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        short_timestamp = datetime.now().strftime("%H:%M:%S")
        
        log_entry = {
            'timestamp': short_timestamp,
            'level': level,
            'message': message
        }
        
        with self.lock:
            self.log_queue.put(log_entry)
            
            # 保持日志行数不超过最大值
            if len(self.log_lines) >= self.max_lines:
                self.log_lines = self.log_lines[-(self.max_lines//2):]
            
            # 写入日志文件
            if self.log_file:
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        log_str = f"[{full_timestamp}] [{level}] {message}\n"
                        f.write(log_str)
                except Exception:
                    # 日志写入失败不影响主程序
                    pass
            
            # 同时打印到控制台
            print(f"[{full_timestamp}] [{level}] {message}")
        
    def info(self, message: str):
        """记录信息日志"""
        self.log('INFO', message)
        
    def warning(self, message: str):
        """记录警告日志"""
        self.log('WARNING', message)
        
    def error(self, message: str):
        """记录错误日志"""
        self.log('ERROR', message)
        
    def success(self, message: str):
        """记录成功日志"""
        self.log('SUCCESS', message)
        
    def debug(self, message: str):
        """记录调试日志"""
        self.log('DEBUG', message)
        
    def get_logs(self) -> List[Dict]:
        """获取所有日志"""
        with self.lock:
            # 从队列中获取新日志
            while True:
                try:
                    log_entry = self.log_queue.get_nowait()
                    self.log_lines.append(log_entry)
                except Empty:
                    break
            
            # 保持日志行数不超过最大值
            if len(self.log_lines) > self.max_lines:
                self.log_lines = self.log_lines[-self.max_lines:]
                
            return self.log_lines.copy()
    
    def clear(self):
        """清空日志"""
        with self.lock:
            self.log_lines.clear()
            while not self.log_queue.empty():
                try:
                    self.log_queue.get_nowait()
                except Empty:
                    break
    
    def save_to_file(self, file_path=None):
        """将当前日志保存到文件"""
        if not file_path:
            file_path = self.log_file
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                for log_entry in self.log_lines:
                    full_timestamp = datetime.now().strftime("%Y-%m-%d") + " " + log_entry['timestamp']
                    log_str = f"[{full_timestamp}] [{log_entry['level']}] {log_entry['message']}\n"
                    f.write(log_str)


# 计算项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 创建日志文件路径
log_file_path = os.path.join(project_root, "../parameter_optimizer.log")

# 全局日志实例
logger = OptimizerLogger(log_file=log_file_path, max_lines=1000)
