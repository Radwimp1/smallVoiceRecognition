import os
import logging
from datetime import datetime
import configparser

#错误日志模块
class LogManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        # 读取配置
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        
        # 设置日志格式
        log_format = '%(asctime)s | %(levelname)s | %(message)s'
        formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        
        # 配置日志文件
        log_path = config.get('logging', 'file_path')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # 设置文件处理器
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # 配置日志记录器
        self.logger = logging.getLogger('VoiceAssistant')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
    
    def log_error(self, error_msg):
        """记录错误日志"""
        self.logger.error(error_msg)
    
    def log_info(self, info_msg):
        """记录信息日志"""
        self.logger.info(info_msg)
    
    def get_recent_errors(self, count=5):
        """获取最近的错误日志"""
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        log_path = config.get('logging', 'file_path')
        
        if not os.path.exists(log_path):
            return ["暂无错误记录"]
            
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 筛选错误日志并返回最近的几条
        error_logs = [line.strip() for line in lines if '| ERROR |' in line]
        return error_logs[-count:] if error_logs else ["暂无错误记录"]