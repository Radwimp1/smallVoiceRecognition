import tkinter as tk
from tkinter import messagebox, Text, scrolledtext
import threading
import time
from weather_handler import get_search_results
from display_manager import display_search_results
from log_manager import LogManager
import recognition  # 直接导入模块

# 创建窗口模块
def create_gui():
    # 创建主窗口
    root = tk.Tk()
    root.title("控制面板")
    root.geometry("400x500+500+200")  # 增加窗口高度以容纳任务栏
    root.configure(bg="#f0f3ff")  # 设置背景色

    # 创建功能按钮框架
    control_frame = tk.Frame(root, bg="#f0f3ff")
    control_frame.pack(pady=20)

    # 中央开始按钮（绿色）
    start_btn = tk.Button(root,
                         text="开始运行", 
                         command=start_action,
                         bg="#4CAF50", fg="white",
                         font=("微软雅黑", 14, "bold"),
                         width=15, height=3,
                         state=tk.DISABLED)  # 初始状态为禁用
    start_btn.pack(pady=20)  # 减少padding以腾出空间
    
    # 保存按钮引用
    root.start_button = start_btn

    # 错误查看按钮（橙色）
    error_btn = tk.Button(root,
                         text="查看报错", 
                         command=show_error,
                         bg="#FF9800", fg="white",
                         font=("微软雅黑", 12),
                         width=10)
    error_btn.pack()

    # 添加定时任务栏框架
    timer_frame = tk.Frame(root, bg="#f0f3ff", bd=2, relief=tk.GROOVE)
    timer_frame.pack(pady=10, fill=tk.X, padx=20)
    
    # 定时任务栏标题
    timer_label = tk.Label(timer_frame, 
                          text="定时提醒任务", 
                          font=("微软雅黑", 12, "bold"),
                          bg="#f0f3ff")
    timer_label.pack(pady=5)
    
    # 创建定时任务列表框架
    tasks_frame = tk.Frame(timer_frame, bg="#f0f3ff")
    tasks_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 创建滚动条
    scrollbar = tk.Scrollbar(tasks_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 创建任务列表
    task_list = tk.Listbox(tasks_frame, 
                          height=5, 
                          bg="white",
                          font=("微软雅黑", 9),
                          selectbackground="#e0e0e0",
                          selectforeground="black",
                          yscrollcommand=scrollbar.set)
    task_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=task_list.yview)
    
    # 保存任务列表引用
    root.task_list = task_list
    
    # 添加删除按钮
    delete_btn = tk.Button(timer_frame,
                          text="删除选中的提醒", 
                          command=delete_selected_timer,
                          bg="#f44336", fg="white",
                          font=("微软雅黑", 9),
                          width=15)
    delete_btn.pack(pady=5)
    
    # 错误信息存储变量
    root.error_log = []  # 存储错误信息的列表
    
    # 添加文本显示区域
    result_text = scrolledtext.ScrolledText(root, 
                                          width=40, 
                                          height=10,
                                          font=("微软雅黑", 10),
                                          bg="white")
    result_text.pack(pady=10)
    
    # 将文本框保存为root的属性，以便其他函数访问
    root.result_display = result_text
    
    # 在后台线程中预加载模型
    threading.Thread(target=preload_model, args=(root,), daemon=True).start()
    
    # 启动按钮状态检查线程
    threading.Thread(target=check_model_status, args=(root,), daemon=True).start()
    
    # 启动定时器更新线程
    threading.Thread(target=update_timer_display, args=(root,), daemon=True).start()
    
    # 窗口关闭时清理资源
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    return root

def check_model_status(root):
    """检查模型加载状态并更新按钮"""
    while True:
        if recognition.is_model_loaded():
            # 模型加载完成，启用按钮
            root.start_button.config(state=tk.NORMAL)
            break
        elif recognition.is_model_loading():
            # 模型正在加载，继续等待
            time.sleep(0.5)
        else:
            # 模型加载失败，也启用按钮（用户可以重试）
            root.start_button.config(state=tk.NORMAL)
            break

def preload_model(root):
    """预加载模型到内存"""
    try:
        if hasattr(root, 'result_display'):
            root.result_display.delete(1.0, tk.END)
            root.result_display.insert(tk.END, "正在加载语音识别模型...\n请稍候...")
            root.update_idletasks()
        
        # 预加载模型
        model = recognition.load_model_only()
        
        if hasattr(root, 'result_display'):
            if model is not None:
                root.result_display.delete(1.0, tk.END)
                root.result_display.insert(tk.END, "模型加载完成，可以开始使用了！")
            else:
                root.result_display.delete(1.0, tk.END)
                root.result_display.insert(tk.END, "模型加载失败，请检查配置或重启程序。")
    except Exception as e:
        log_manager = LogManager()
        log_manager.log_error(f"模型预加载失败: {str(e)}")
        if hasattr(root, 'result_display'):
            root.result_display.delete(1.0, tk.END)
            root.result_display.insert(tk.END, f"模型加载失败: {str(e)}")

def delete_selected_timer():
    """删除选中的定时任务"""
    try:
        root = tk._default_root
        if not hasattr(root, 'task_list'):
            return
            
        # 获取选中的索引
        selected_indices = root.task_list.curselection()
        if not selected_indices:
            messagebox.showinfo("提示", "请先选择要删除的定时任务")
            return
            
        # 获取定时器处理器
        from timer_handler import get_timer_handler
        timer_handler = get_timer_handler()
        
        # 获取活动定时器
        active_timers = timer_handler.get_active_timers()
        
        # 确保索引有效
        if selected_indices[0] < len(active_timers):
            # 删除选中的定时器
            timer_id = active_timers[selected_indices[0]]['id']
            result = timer_handler.delete_timer(timer_id)
            
            if result['status'] == 'success':
                messagebox.showinfo("成功", result['message'])
                # 更新列表显示
                update_timer_list(root)
            else:
                messagebox.showerror("错误", result['message'])
    except Exception as e:
        log_manager = LogManager()
        log_manager.log_error(f"删除定时任务失败: {str(e)}")
        messagebox.showerror("错误", f"删除定时任务失败: {str(e)}")

def update_timer_list(root):
    """更新定时器任务列表"""
    if not hasattr(root, 'task_list'):
        return
        
    # 清空列表
    root.task_list.delete(0, tk.END)
    
    # 获取活动的定时器
    from timer_handler import get_timer_handler
    timer_handler = get_timer_handler()
    active_timers = timer_handler.get_active_timers()
    
    if not active_timers:
        root.task_list.insert(tk.END, "当前没有定时任务")
        return
        
    # 按剩余时间排序
    active_timers.sort(key=lambda x: x['remaining'])
    
    # 添加到列表
    for timer in active_timers:
        remaining_time = timer['remaining']
        hours, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        time_str = ""
        if hours > 0:
            time_str += f"{int(hours)}小时"
        if minutes > 0:
            time_str += f"{int(minutes)}分钟"
        if seconds > 0 and hours == 0:  # 只有在小时为0时才显示秒
            time_str += f"{int(seconds)}秒"
            
        display_text = f"{timer['display_time']} - {timer['message']} (剩余: {time_str})"
        root.task_list.insert(tk.END, display_text)

def update_timer_display(root):
    """更新定时器显示"""
    from timer_handler import get_timer_handler
    
    while True:
        try:
            # 更新任务列表
            update_timer_list(root)
        except Exception as e:
            ErrorHandler.handle_error(e, root)
        
        # 每秒更新一次
        time.sleep(1)

def start_action():
    """启动语音识别"""
    try:
        # 检查模型是否已加载
        if not recognition.is_model_loaded():
            root = tk._default_root
            if hasattr(root, 'result_display'):
                root.result_display.delete(1.0, tk.END)
                root.result_display.insert(tk.END, "模型尚未加载完成，请稍候...")
            return
            
        root = tk._default_root
        if hasattr(root, 'result_display'):
            root.result_display.delete(1.0, tk.END)
            root.result_display.insert(tk.END, "正在处理语音...\n请说话...")
            root.update_idletasks()
        
        # 使用已加载的模型进行识别
        text = recognition.voice_recognize()
        
        if text:
            if hasattr(root, 'result_display'):
                root.result_display.delete(1.0, tk.END)
                root.result_display.insert(tk.END, "正在处理命令...\n请稍候...")
                root.update_idletasks()
                
            from handle import process_voice_command
            command_type = process_voice_command(text)
            # 搜索命令已在process_voice_command中处理完成，不需要额外处理
        else:
            if hasattr(root, 'result_display'):
                root.result_display.delete(1.0, tk.END)
                root.result_display.insert(tk.END, "未能识别语音，请重试")
    except Exception as e:
        log_manager = LogManager()
        log_manager.log_error(f"命令处理失败: {str(e)}")
        if hasattr(root, 'result_display'):
            root.result_display.delete(1.0, tk.END)
            root.result_display.insert(tk.END, f"错误: {str(e)}")

def on_closing():
    """窗口关闭时清理资源"""
    try:
        # 释放模型资源
        recognition.release_model()
    finally:
        # 关闭窗口
        tk._default_root.destroy()

def show_error():
    """显示错误日志"""
    log_manager = LogManager()
    error_list = log_manager.get_recent_errors()
    message = "\n".join(error_list)
    messagebox.showerror("错误日志", f"最近错误记录：\n\n{message}")


