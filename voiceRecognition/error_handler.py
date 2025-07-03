import tkinter as tk
from tkinter import messagebox
from log_manager import LogManager
import traceback
import configparser

class ErrorHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.max_retries = int(self.config.get('error_handling', 'max_retries', fallback=3))
        self.retry_delay = int(self.config.get('error_handling', 'retry_delay', fallback=1))
        self.timeout = int(self.config.get('error_handling', 'timeout', fallback=10))

    @classmethod
    def handle_error(cls, error, root=None, retries=0):
        instance = cls()
        log_manager = LogManager()
        error_msg = f"{str(error)}\n{traceback.format_exc()}"
        
        # 记录错误日志
        log_manager.log_error(error_msg)
        
        # 显示错误信息
        if root and hasattr(root, 'result_display'):
            root.result_display.delete(1.0, tk.END)
            root.result_display.insert(tk.END, f"发生错误: {str(error)}\n详细日志已记录")
        else:
            messagebox.showerror("系统错误", f"发生未处理异常: {str(error)}")

        # 重试逻辑
        if retries < instance.max_retries:
            return {
                'status': 'retry',
                'retries': retries + 1,
                'delay': instance.retry_delay
            }
        return {'status': 'failed'}

    @classmethod
    def wrap_async(cls, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return cls.handle_error(e)
        return wrapper