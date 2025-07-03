import requests
import base64
import json
import subprocess
import re

def search_music(keyword):
    # 搜索API地址（通过浏览器开发者工具获取的真实API）
    url = "https://music.163.com/api/cloudsearch/pc"

    # 构造请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://music.163.com/",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # 构造请求参数
    data = {
        "s": keyword,
        "type": 1,  # 1: 单曲
        "limit": 30,  # 每页结果数量
        "offset": 0  # 页数偏移
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()

        # 解析返回的JSON数据
        result = response.json()
        if result["code"] == 200:
            return result["result"]["songs"]
        else:
            print("搜索失败，错误代码:", result["code"])
            return None

    except Exception as e:
        print("请求出错:", e)
        return None


def display_results(songs):
    if not songs:
        print("未找到相关歌曲")
        return

    print(f"找到 {len(songs)} 首相关歌曲：\n")
    play_music(songs[0])
    for index, song in enumerate(songs, 1):
        name = song["name"]
        artists = "/".join([ar["name"] for ar in song["ar"]])
        album = song["al"]["name"]
        song_id = song["id"]
        print(f"{index}. {name} - {artists} | 专辑: {album} (ID: {song_id})")

def play_music(song):
    json_str = {}
    json_str["type"] = "song"
    json_str["id"] = song["id"]
    json_str["cmd"] = "play"
    json_str=json.dumps(json_str)
    encoded_bytes = base64.b64encode(json_str.encode("utf-8"))
    encoded_json = encoded_bytes.decode("utf-8")
    print(f"orpheus://{encoded_json}")
    subprocess.run(["start"," ",f"orpheus://{encoded_json}"], shell=True)

class MusicHandler:
    def __init__(self):
        pass
        
    def extract_song_name(self, text):
        """从语音命令中提取歌曲名称"""
        patterns = [
            r'(?:播放|来首|放首)(.+?)的(.+?)(?=$|[，。])',  # 新增处理'的'的格式
            r'(?:我想听)(.+?)(?=$|[，。])',
            r'(?:播放一?首|来首|放首)(.+?)(?=$|[，。])',
            r'(\S+?)歌(?=$|[，。])'
        ]

        # 更新关键词列表
        music_keywords = ["播放", "首", "歌", "我想听"]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 处理含'的'的格式
                if pattern == patterns[0]:
                    return f"{matches[0]} {matches[1]}".strip()
                return matches[0].strip()

        # 检查是否包含特定的音乐关键词
        music_keywords = ["播放", "首", "歌"]
        
        for keyword in music_keywords:
            if keyword in text:
                # 提取关键词后面的内容作为歌曲名
                parts = text.split(keyword, 1)
                if len(parts) > 1 and parts[1].strip():
                    # 去除可能的标点符号
                    song_name = re.sub(r'[，。！？].*$', '', parts[1].strip())
                    return song_name
        
        # 如果上述方法都没提取到，尝试直接分割文本
        words = text.split()
        if len(words) > 1:
            return ''.join(words[1:])
        
        return ""
    
    def play_music(self, text):
        """处理音乐播放命令"""
        song_name = self.extract_song_name(text)
        if not song_name:
            return {"status": "error", "message": "未能识别歌曲名称"}
            
        results = search_music(song_name)
        if results:
            display_results(results)
            return {"status": "success", "message": f"正在播放: {song_name}"}
        else:
            return {"status": "error", "message": "未找到相关歌曲，请重试"}

if __name__ == "__main__":
    keyword = input("请输入要搜索的歌曲名称或歌手：")
    results = search_music(keyword)

    if results:
        display_results(results)
    else:
        print("搜索失败，请稍后重试")