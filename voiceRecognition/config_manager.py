import os
import configparser
from log_manager import LogManager

# 全局配置缓存
_config_cache = None
_log_manager = LogManager()

def get_config():
    """获取配置信息，避免重复读取"""
    global _config_cache
    if _config_cache is None:
        config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            _log_manager.log_error("配置文件不存在")
            raise FileNotFoundError("配置文件不存在")
        config.read('config.ini', encoding='utf-8')
        _config_cache = config
    return _config_cache

class ConfigManager:
    def __init__(self, config_path='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        self.logger = LogManager()

    def get_value(self, section, option, fallback=None):
        try:
            return self.config.get(section, option, fallback=fallback)
        except Exception as e:
            self.logger.log_error(f"获取配置失败: {str(e)}")
            return fallback

    def get_int(self, section, option, fallback=0):
        try:
            return self.config.getint(section, option, fallback=fallback)
        except Exception as e:
            self.logger.log_error(f"获取整数配置失败: {str(e)}")
            return fallback

    def get_float(self, section, option, fallback=0.0):
        try:
            return self.config.getfloat(section, option, fallback=fallback)
        except Exception as e:
            self.logger.log_error(f"获取浮点数配置失败: {str(e)}")
            return fallback

    def get_bool(self, section, option, fallback=False):
        try:
            return self.config.getboolean(section, option, fallback=fallback)
        except Exception as e:
            ErrorHandler.handle_error(e)
            return fallback