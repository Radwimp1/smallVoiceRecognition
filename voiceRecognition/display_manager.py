import tkinter as tk

# 显示搜索结果的函数
def display_search_results(results):
    """显示搜索结果"""
    # 获取根窗口和文本控件
    root = tk._default_root
    if not root or not hasattr(root, 'result_display'):
        print("错误: 无法获取显示控件")
        return
        
    result_text = root.result_display
    
    # 清空现有内容
    result_text.delete(1.0, tk.END)
    
    # 配置标签样式
    if not hasattr(result_text, 'tag_configured_flag'):
        result_text.tag_configure('title', font=('微软雅黑', 11, 'bold'))
        result_text.tag_configure('content', font=('微软雅黑', 10))
        result_text.tag_configure('error', foreground='red', font=('微软雅黑', 10, 'bold'))
        result_text.tag_configure('weather', foreground='blue', font=('微软雅黑', 10))
        result_text.tag_configure('temperature', foreground='#FF6600', font=('微软雅黑', 10, 'bold'))
        result_text.tag_configure('highlight', background='#FFFFCC', font=('微软雅黑', 10))
        result_text.tag_configured_flag = True
    
    # 检查是否为天气查询结果
    is_weather_query = 'query' in results and '天气' in results.get('query', '')
    
    if results['status'] == 'success':
        if is_weather_query and 'results' in results:
            # 显示天气查询结果
            weather_result = results['results'][0] if results['results'] else None
            if weather_result:
                location = results.get('query', '').replace('天气', '').strip()
                
                result_text.insert(tk.END, f"📍 {location}天气信息\n", 'title')
                result_text.insert(tk.END, "="*40 + "\n", 'content')
                
                # 显示天气内容
                weather_content = weather_result.get('content', '')
                
                # 解析天气内容的各个部分
                lines = weather_content.split('\n')
                for line in lines:
                    if '天气：' in line:
                        result_text.insert(tk.END, "🌡️ ", 'weather')
                        result_text.insert(tk.END, f"{line}\n", 'content')
                    elif '温度：' in line:
                        result_text.insert(tk.END, "🌡️ ", 'weather')
                        result_text.insert(tk.END, f"{line}\n", 'temperature')
                    elif '湿度：' in line:
                        result_text.insert(tk.END, "💧 ", 'weather')
                        result_text.insert(tk.END, f"{line}\n", 'content')
                    elif '风向：' in line:
                        result_text.insert(tk.END, "💨 ", 'weather')
                        result_text.insert(tk.END, f"{line}\n", 'content')
                    elif '发布时间：' in line:
                        result_text.insert(tk.END, "🕒 ", 'weather')
                        result_text.insert(tk.END, f"{line}\n", 'content')
                    else:
                        result_text.insert(tk.END, f"{line}\n", 'content')
                
        elif 'answer' in results:
            # 显示 DeepSeek AI 回答
            result_text.insert(tk.END, "🤖 DeepSeek AI回答\n", 'title')
            result_text.insert(tk.END, "="*40 + "\n", 'content')
            result_text.insert(tk.END, f"{results['answer']}\n", 'content')
            result_text.insert(tk.END, "="*40 + "\n", 'content')
            
            # 显示查询信息
            if 'query' in results:
                result_text.insert(tk.END, f"🔍 搜索关键词: ", 'title')
                result_text.insert(tk.END, f"{results['query']}\n\n", 'content')
            
            # 显示模型信息（如果有）
            if 'model' in results:
                result_text.insert(tk.END, f"📊 使用模型: ", 'title')
                result_text.insert(tk.END, f"{results['model']}\n", 'content')
            
            # 显示令牌信息（如果有）
            if 'tokens' in results:
                result_text.insert(tk.END, f"🔢 使用令牌数: ", 'title')
                result_text.insert(tk.END, f"{results['tokens']}\n", 'content')
        elif 'results' in results:
            # 显示普通搜索结果
            result_text.insert(tk.END, f"🔍 搜索结果: {results.get('query', '')}\n", 'title')
            result_text.insert(tk.END, "="*40 + "\n", 'content')
            
            for i, result in enumerate(results['results'], 1):
                result_text.insert(tk.END, f"【结果 {i}】\n", 'title')
                result_text.insert(tk.END, f"标题: {result.get('title', '')}\n", 'content')
                result_text.insert(tk.END, f"内容: {result.get('content', '')}\n\n", 'content')
    else:
        # 显示错误信息
        result_text.insert(tk.END, "❌ 错误提示 ❌\n", 'error')
        error_msg = results.get('message', '未知错误')
        result_text.insert(tk.END, f"{error_msg}\n", 'error')
    
    # 滚动到顶部
    result_text.see("1.0")
    
    # 更新界面
    root.update()