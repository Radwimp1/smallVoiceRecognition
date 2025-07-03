import re
import time
import threading
import datetime
import winsound
import tkinter as tk
from tkinter import messagebox
from log_manager import LogManager
import uuid  # 导入uuid模块生成唯一ID

#定时模块
class TimerHandler:
    def __init__(self):
        self.log_manager = LogManager()
        self.timers = []  # 存储所有定时器
        self.timer_thread = None
        self.is_running = False
    
    def parse_timer_command(self, text):
        """解析定时命令"""
        # 打印输入的文本，便于调试
        print(f"正在解析定时命令: {text}")
        
        # 预处理文本，将中文数字转换为阿拉伯数字
        processed_text = self._preprocess_chinese_numbers(text)
        print(f"预处理后的文本: {processed_text}")
        
        # 相对时间模式
        relative_pattern = r'(\d+)\s*(?:个)?\s*(小时|分钟|秒钟|秒)后(?:提醒我|叫我|告诉我)?(.+)?'
        
        # 半小时特殊模式
        half_pattern = r'半(?:个)?(小时|分钟)后(?:提醒我|叫我|告诉我)?(.+)?'
        
        relative_match = re.search(relative_pattern, processed_text)
        half_match = re.search(half_pattern, processed_text)
        
        # 打印匹配结果，便于调试
        if relative_match:
            print(f"相对时间匹配成功: {relative_match.groups()}")
        if half_match:
            print(f"半小时匹配成功: {half_match.groups()}")
        
        # 处理半小时特殊情况
        if half_match:
            unit = half_match.group(1)
            message = half_match.group(2) or "时间到了"
            
            # 设置为30分钟或0.5小时
            amount = 30 if unit == "分钟" else 0.5
            
            # 转换为秒
            seconds = 0
            if unit == "小时":
                seconds = int(amount * 3600)
            elif unit == "分钟":
                seconds = int(amount * 60)
            
            print(f"半{unit}转换为秒数: {seconds}")
                
            return {
                'type': 'relative',
                'seconds': seconds,
                'message': message.strip(),
                'display': f"半{unit}后"
            }
        
        # 处理相对时间
        if relative_match:
            amount_str = relative_match.group(1)
            unit = relative_match.group(2)
            message = relative_match.group(3) or "时间到了"
            
            print(f"解析数量: {amount_str}, 单位: {unit}")
            
            # 直接转换阿拉伯数字
            amount = int(amount_str)
            print(f"数字: {amount}")
            
            # 转换为秒
            seconds = 0
            if unit == "小时":
                seconds = amount * 3600
            elif unit == "分钟":
                seconds = amount * 60
            elif unit in ["秒", "秒钟"]:
                seconds = amount
            
            print(f"转换为秒数: {seconds}")
                
            return {
                'type': 'relative',
                'seconds': seconds,
                'message': message.strip(),
                'display': f"{amount}{unit}后"
            }
        
        print("未能匹配任何定时命令模式")
        return None
        
    def _preprocess_chinese_numbers(self, text):
        """预处理文本中的中文数字，转换为阿拉伯数字"""
        # 中文数字映射
        cn_num = {
            '零': '0', '一': '1', '二': '2', '两': '2', '三': '3', '四': '4', '五': '5',
            '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
            '十一': '11', '十二': '12', '十三': '13', '十四': '14', '十五': '15',
            '十六': '16', '十七': '17', '十八': '18', '十九': '19', '二十': '20'
        }
        
        # 先替换两个字符的中文数字
        for cn, arabic in sorted(cn_num.items(), key=lambda x: len(x[0]), reverse=True):
            text = text.replace(cn, arabic)
            
        return text
    
    def set_timer(self, seconds, message, display_time):
        """设置定时器"""
        try:
            # 计算目标时间
            target_time = time.time() + seconds
            
            # 生成唯一ID
            timer_id = str(uuid.uuid4())
            
            # 添加到定时器列表
            timer_info = {
                'id': timer_id,
                'target_time': target_time,
                'message': message,
                'display_time': display_time,
                'set_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.timers.append(timer_info)
            
            # 确保定时器线程在运行
            self._ensure_timer_thread()
            
            # 打印识别记录
            print(f"设置定时器: {display_time} - {message}")
            
            return {
                'status': 'success',
                'message': f'已设置{display_time}的提醒: {message}',
                'details': timer_info
            }
        except Exception as e:
            error_msg = f'设置定时器失败: {str(e)}'
            self.log_manager.log_error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def delete_timer(self, timer_id):
        """删除指定ID的定时器"""
        try:
            for i, timer in enumerate(self.timers):
                if timer['id'] == timer_id:
                    removed_timer = self.timers.pop(i)
                    print(f"删除定时器: {removed_timer['display_time']} - {removed_timer['message']}")
                    return {
                        'status': 'success',
                        'message': f'已删除定时提醒: {removed_timer["message"]}'
                    }
            
            return {
                'status': 'error',
                'message': '未找到指定的定时任务'
            }
        except Exception as e:
            error_msg = f'删除定时器失败: {str(e)}'
            self.log_manager.log_error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def _ensure_timer_thread(self):
        """确保定时器线程在运行"""
        if self.timer_thread is None or not self.timer_thread.is_alive():
            self.is_running = True
            self.timer_thread = threading.Thread(target=self._timer_monitor, daemon=True)
            self.timer_thread.start()
    
    def _timer_monitor(self):
        """定时器监控线程"""
        while self.is_running:
            current_time = time.time()
            triggered_timers = []
            
            # 检查是否有定时器到期
            for timer in self.timers:
                if current_time >= timer['target_time']:
                    triggered_timers.append(timer)
            
            # 触发提醒
            for timer in triggered_timers:
                self._trigger_alarm(timer)
                self.timers.remove(timer)
            
            # 如果没有更多定时器，退出线程
            if not self.timers:
                self.is_running = False
                break
                
            # 每秒检查一次
            time.sleep(1)
    
    def _trigger_alarm(self, timer):
        """触发闹钟提醒"""
        try:
            # 播放提示音
            winsound.PlaySound("SystemExclamation", winsound.SND_ASYNC)
            
            # 显示提醒对话框
            def show_reminder():
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口
                messagebox.showinfo("提醒", f"{timer['message']}\n\n设置时间: {timer['set_time']}")
                root.destroy()
            
            # 在主线程中显示对话框
            threading.Thread(target=show_reminder).start()
            
            print(f"提醒触发: {timer['message']}")
        except Exception as e:
            self.log_manager.log_error(f"触发提醒失败: {str(e)}")
    
    def get_active_timers(self):
        """获取当前活动的定时器"""
        return [
            {
                'id': timer['id'],
                'message': timer['message'],
                'display_time': timer['display_time'],
                'remaining': int(timer['target_time'] - time.time()),
                'set_time': timer['set_time']
            }
            for timer in self.timers
        ]
    
    def clear_timers(self):
        """清除所有定时器"""
        self.timers = []
        return {
            'status': 'success',
            'message': '已清除所有定时器'
        }

# 单例模式
_timer_handler_instance = None

def get_timer_handler():
    global _timer_handler_instance
    if _timer_handler_instance is None:
        _timer_handler_instance = TimerHandler()
    return _timer_handler_instance