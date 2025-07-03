import re
import tkinter as tk
from weather_handler import get_search_results
from music_handler import MusicHandler
from timer_handler import get_timer_handler
from search_handler import SearchHandler

#处理语音命令模块
class CommandHandler:
    def __init__(self):
        # 定义不同类型的关键词
        self.search_keywords = ["搜索", "查找", "查询", "了解"]
        self.music_keywords = ["我想听", "播放", "首", "听", "歌", "的歌", "音乐"]
        self.weather_keywords = ["天气", "气温", "温度"]  # 添加天气关键词
        self.wechat_keywords = ["给", "发送", "发消息", "发信息"]  # 添加微信消息关键词
        # 初始化音乐处理器
        self.music_handler = MusicHandler()
        self.timer_handler = get_timer_handler()
        self.search_handler = SearchHandler()
    
    def handle_qa(self, text):
        """处理智能问答命令"""
        query = re.sub(r'(问答|提问|问题)', '', text).strip()
        result = self.search_handler.generate_answer(query)
        return result  # 直接返回完整结果对象

    def classify_command(self, text):
        """分类命令类型"""
        # 预处理文本，将中文数字转换为阿拉伯数字
        processed_text = self._preprocess_chinese_numbers(text)
        print(f"预处理后的文本: {processed_text}")
        
        # 按优先级检查各类命令
        
        # 1. 检查智能问答命令（最高优先级）
        if re.search(r'^(问答|提问|问题)', text):
            return {
                "type": 4, 
                "handler": self.handle_qa,
                "text": text
            }
        
        # 2. 检查音乐播放命令
        if any(keyword in text for keyword in self.music_keywords):
            return 2, {'type': 2, 'text': text}
        
        # 2. 检查定时器命令
        timer_patterns = [
            r'(\d+)\s*(?:个)?\s*(小时|分钟|秒钟|秒)后(?:提醒我|叫我|告诉我)?',
            r'半(?:个)?(小时|分钟)后(?:提醒我|叫我|告诉我)?'
        ]
        
        for pattern in timer_patterns:
            if re.search(pattern, processed_text):
                return 3, {'type': 'timer', 'text': text}
        
        # 3. 检查微信消息命令
        wechat_pattern = r'给(.+?)(?:发送|发)(?:消息|信息)?(.+)'
        wechat_match = re.search(wechat_pattern, text)
        if wechat_match or ("给" in text and any(keyword in text for keyword in self.wechat_keywords)):
            return self.handle_wechat_message(text)
        
        # 4. 检查天气查询命令
        if any(keyword in text for keyword in self.weather_keywords) and "天气" in text:
            return self.handle_weather(text)
        
        # 5. 检查搜索命令
        if any(keyword in text for keyword in self.search_keywords):
            return self.handle_search(text)
        
        # 6. 默认为普通搜索
        return self.handle_search(text)

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

    def handle_search(self, text):
        """处理搜索相关命令"""
        # 使用预处理后的文本作为查询内容
        processed_text = self._preprocess_chinese_numbers(text)
        query = self._extract_query(processed_text)
        
        # 调用search_handler的generate_answer方法而不是get_search_results
        result = self.search_handler.generate_answer(query)
        
        return "search", {
            "type": 1,
            "query": query,
            "results": result,
            "original_text": text
        }

    def handle_weather(self, text):
        """处理天气相关命令"""
        location = self._extract_location(text)
        search_results = get_search_results(location, is_weather=True)  # 添加is_weather参数
        return "search", {
            "type": 1,
            "query": f"{location}天气",
            "results": search_results,
            "original_text": text
        }

    def _extract_location(self, text):
        """提取地点信息"""
        patterns = [
            r'(.+?)的天气',
            r'(.+?)天气怎么样',
            r'(.+?)气温',
            r'(.+?)天气预报',
            r'查询(.+?)的天气',
            r'(.+?)今天天气',
            r'(.+?)现在天气'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                location = matches[0].strip()
                # 处理一些特殊情况
                if location in ['今天', '现在', '当前']:
                    return "当前位置"
                return location
        
        return "当前位置"

    def handle_music(self, text):
        """处理音乐相关命令"""
        song_name = self.music_handler.extract_song_name(text)
        if not song_name:
            return "music", {
                "type": 2,
                "original_text": text,
                "song_name": ""
            }
        
        return "music", {
            "type": 2,
            "original_text": text,
            "song_name": song_name
        }

    def _extract_query(self, text):
        """提取搜索查询内容"""
        # 优化正则表达式以更好地匹配查询内容
        patterns = [
            r'[查询搜索](.+?)(?=$|[，。])',  # 匹配"查询"或"搜索"后的内容
            r'[帮我找找看看](.+?)(?=$|[，。])',  # 匹配"帮我找"等后的内容
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].strip()
        
        # 如果上述模式都没匹配到，尝试直接提取关键信息
        words = text.split()
        if len(words) > 1:
            return ''.join(words[1:])
        
        return text
        
    def handle_wechat_message(self, text):
        """处理微信消息命令
        
        参数:
            text (str): 用户输入的命令文本
            
        返回:
            tuple: (命令类型, 命令数据)
        """
        # 提取接收者和消息内容
        wechat_pattern = r'给(.+?)(?:发送|发)(?:消息|信息)?(.+)'
        match = re.search(wechat_pattern, text)
        
        if match:
            recipient = match.group(1).strip()
            content = match.group(2).strip()
        else:
            # 如果正则表达式没有匹配成功，尝试其他方式提取
            parts = text.split('发送')
            if len(parts) >= 2:
                recipient_part = parts[0]
                if '给' in recipient_part:
                    recipient = recipient_part.split('给')[1].strip()
                    content = parts[1].strip()
                else:
                    recipient = ''
                    content = ''
            else:
                recipient = ''
                content = ''
        
        print(f"微信消息命令解析: 接收者={recipient}, 内容={content}")
        
        # 如果没有提取到接收者或内容，返回错误信息
        if not recipient or not content:
            return 4, {
                "type": 4,
                "status": "error",
                "message": "无法解析微信消息命令，请确保包含接收者和消息内容"
            }
        
        # 导入微信处理模块并发送消息
        from wechat_handler import send_wechat_message
        result = send_wechat_message(recipient, content)
        
        return 4, {
            "type": 4,
            "status": result["status"],
            "message": result["message"],
            "recipient": result["recipient"],
            "content": result["content"]
        }

def process_voice_command(text):
    handler = CommandHandler()
    command_type, command_data = handler.classify_command(text)
    
    # 新增问答命令处理
    if isinstance(command_type, dict) and command_type.get("type") == 4:
        result = command_type["handler"](command_type["text"])
        from display_manager import display_search_results
        display_search_results(result)
        return

    if command_type == 2:  # 音乐播放命令
        result = handler.music_handler.play_music(text)
        # 显示播放结果信息
        root = tk._default_root
        if hasattr(root, 'result_display'):
            root.result_display.delete(1.0, tk.END)
            root.result_display.insert(tk.END, result['message'])
        
    # 处理定时器命令
    elif command_type == 3:  # 定时器命令
        timer_handler = get_timer_handler()
        timer_info = timer_handler.parse_timer_command(text)
        
        if timer_info:
            result = timer_handler.set_timer(
                timer_info['seconds'], 
                timer_info['message'],
                timer_info['display']
            )
            
            # 显示设置成功信息
            root = tk._default_root
            if hasattr(root, 'result_display'):
                root.result_display.delete(1.0, tk.END)
                root.result_display.insert(tk.END, result['message'])
                
            # 打印识别记录
            print(f"定时命令识别记录: {text}")
            print(f"解析结果: {timer_info}")
            
            # 更新任务列表
            if hasattr(root, 'task_list'):
                from programBox import update_timer_list
                update_timer_list(root)
        else:
            # 显示无法解析的信息
            root = tk._default_root
            if hasattr(root, 'result_display'):
                root.result_display.delete(1.0, tk.END)
                root.result_display.insert(tk.END, "无法解析定时命令，请重试")
    elif command_type == 4:  # 微信消息命令
        # 显示发送结果信息
        root = tk._default_root
        if hasattr(root, 'result_display'):
            root.result_display.delete(1.0, tk.END)
            root.result_display.insert(tk.END, command_data['message'])
    elif command_type == "search":  
        # 处理搜索命令
        from display_manager import display_search_results
        display_search_results(command_data["results"])
        return command_data["type"]  
    elif command_type == "music":   
        return 2
    else:
        return 0
        
    return command_type