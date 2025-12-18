#!/usr/bin/env python
# coding=utf-8
"""
日志管理器 - 实时日志记录和管理
"""

import time
import threading
from queue import Queue, Empty
from datetime import datetime
from typing import List, Dict


class RealTimeLogger:
    """实时日志管理器"""
    
    def __init__(self, max_lines=300):
        self.log_queue = Queue()
        self.max_lines = max_lines
        self.lock = threading.Lock()
        self.log_lines = []
        
    def log(self, level: str, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        
        with self.lock:
            self.log_queue.put(log_entry)
            
            # 保持日志行数不超过最大值
            if len(self.log_lines) >= self.max_lines:
                self.log_lines = self.log_lines[-(self.max_lines//2):]
            
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


# 全局日志实例
logger = RealTimeLogger(max_lines=300)