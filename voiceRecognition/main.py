import programBox
import recognition 
import tkinter as tk
from handle import process_voice_command
import os
import configparser
import time

def reset_parameters():
    """重置所有参数"""
    # 重置文本显示区域
    root = tk._default_root
    if hasattr(root, 'result_display'):
        root.result_display.delete(1.0, tk.END)
    
    # 重置错误日志
    if hasattr(root, 'error_log'):
        root.error_log = []

def start_process():
    # 检查模型是否已加载
    if not recognition.is_model_loaded():
        root = tk._default_root
        if hasattr(root, 'result_display'):
            root.result_display.delete(1.0, tk.END)
            root.result_display.insert(tk.END, "模型尚未加载完成，请稍候...")
        return
        
    # 重置所有参数
    reset_parameters()
    
    # 执行语音识别
    text = recognition.voice_recognize()
    # 识别完成后自动执行handle处理
    if text:
        process_voice_command(text)

def init_app():
    # 读取配置
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    # 创建日志目录
    log_path = os.path.dirname(config.get('logging', 'file_path'))
    if not os.path.exists(log_path):
        os.makedirs(log_path)

def main():
    # 初始化应用
    init_app()
    
    # 创建并获取GUI窗口
    root = programBox.create_gui()
    # 重新绑定开始按钮的功能
    for widget in root.winfo_children():
        if isinstance(widget, tk.Button):
            try:
                if widget['text'] == "开始运行":
                    widget.configure(command=start_process)
            except:
                continue
    
    # 启动GUI主循环
    root.mainloop()

if __name__ == "__main__":
    main()