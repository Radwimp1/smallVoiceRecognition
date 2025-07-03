import os
import whisper
import torch
import sounddevice as sd
import numpy as np
import configparser
from log_manager import LogManager

# 全局变量
_config_cache = None
_log_manager = LogManager()
_model_cache = None  # 添加全局模型缓存
_model_loading = False  # 添加模型加载状态标志
_model_loaded = False  # 添加模型加载完成标志

def _get_config():
    """获取配置信息，避免重复读取"""
    global _config_cache
    if _config_cache is None:
        config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            raise FileNotFoundError("配置文件不存在")
        config.read('config.ini', encoding='utf-8')
        _config_cache = config
    return _config_cache

def _check_device():
    """检查并返回可用设备"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        torch.cuda.empty_cache()
        if torch.cuda.memory_allocated() > 0.9 * torch.cuda.get_device_properties(0).total_memory:
            device = "cpu"
            print("CUDA 内存不足，切换到 CPU 模式")
    print(f"使用设备: {device}")
    return device

def load_model_only():
    """只加载模型不进行识别，使用全局缓存"""
    global _model_cache, _model_loading, _model_loaded
    
    # 如果模型已加载，直接返回
    if _model_cache is not None and _model_loaded:
        print("使用已加载的模型")
        return _model_cache
        
    # 如果模型正在加载中，返回None
    if _model_loading:
        print("模型正在加载中，请稍候...")
        return None
    
    try:
        _model_loading = True  # 设置加载状态
        config = _get_config()
        
        # 检查必要的配置项
        required_configs = ['voice.samplerate', 'voice.duration', 'voice.model']
        for config_item in required_configs:
            section, option = config_item.split('.')
            if not config.has_option(section, option):
                _model_loading = False  # 重置加载状态
                raise ValueError(f"配置文件缺少必要项: {config_item}")
        
        device = _check_device()
        model_name = config.get('voice', 'model')
        print(f"加载模型: {model_name}")
        _model_cache = whisper.load_model(model_name, device=device)
        _model_loaded = True  # 设置加载完成标志
        _model_loading = False  # 重置加载状态
        return _model_cache
    except Exception as e:
        _model_loading = False  # 重置加载状态
        error_msg = f'模型加载失败: {str(e)}'
        _log_manager.log_error(error_msg)
        print(f"\n错误: {error_msg}")
        return None

# 添加检查模型是否已加载的函数
def is_model_loaded():
    """检查模型是否已加载完成"""
    global _model_loaded
    return _model_loaded

def is_model_loading():
    """检查模型是否正在加载中"""
    global _model_loading
    return _model_loading

def release_model():
    """释放模型资源"""
    global _model_cache, _model_loaded
    if _model_cache is not None:
        del _model_cache
        _model_cache = None
        _model_loaded = False
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("模型资源已释放")

def voice_recognize_with_model(model):
    """使用已加载的模型进行语音识别"""
    try:
        if model is None:
            raise ValueError("模型未加载或加载失败")
            
        config = _get_config()
        samplerate = config.getint('voice', 'samplerate')
        duration = config.getint('voice', 'duration')
        
        # 录音
        print("开始录音...")
        audio = _record_audio(samplerate, duration)
        
        # 识别
        result = model.transcribe(
            audio=audio,
            language="zh",
            task="transcribe",
            initial_prompt="以下是简体中文的转录："
        )
        print(result["text"])
        return result["text"]
    except Exception as e:
        error_msg = f'语音识别失败: {str(e)}'
        _log_manager.log_error(error_msg)
        print(f"\n错误: {error_msg}")
        return None

def _record_audio(samplerate, duration):
    """录制音频"""
    try:
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.float32)
        sd.wait()
        if not np.any(audio):  # 检查是否有声音输入
            raise ValueError("未检测到音频输入")
        return audio.flatten()
    except Exception as e:
        raise RuntimeError(f"录音失败: {str(e)}")

def voice_recognize():
    """语音识别主函数"""
    try:
        # 使用全局缓存的模型
        model = load_model_only()
        if model is None:
            raise ValueError("模型加载失败")
        return voice_recognize_with_model(model)
    except Exception as e:
        error_msg = f'语音识别失败: {str(e)}'
        _log_manager.log_error(error_msg)
        print(f"\n错误: {error_msg}")
        return None
     

