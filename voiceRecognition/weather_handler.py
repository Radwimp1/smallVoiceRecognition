import requests
from bs4 import BeautifulSoup
import re
from display_manager import display_search_results
from pypinyin import lazy_pinyin, Style
import jieba
import Levenshtein
import configparser
import os
import json
from log_manager import LogManager
from city_data import load_city_data

class SearchProcessor:
    def __init__(self):
        # 读取配置文件
        self.config = configparser.ConfigParser()
        self.config.read('config.ini', encoding='utf-8')
        
        # 从配置文件获取设置
        self.headers = {
            'User-Agent': self.config.get('api', 'user_agent')
        }
        self.search_url = self.config.get('search', 'baidu_url')
        self.amap_key = self.config.get('api', 'amap_key')
        self.weather_url = self.config.get('search', 'weather_url')
        self.geocode_url = self.config.get('search', 'geocode_url')
        self.city_list_url = self.config.get('search', 'district_url')
        self.similarity_threshold = self.config.getfloat('search', 'similarity_threshold')
        self.max_results = self.config.getint('search', 'max_results')
        self.default_city = self.config.get('weather', 'default_city', fallback='默认城市')
        
        self.city_cache = {}
        self.pinyin_cache = {}
        self.log_manager = LogManager()
        
        # 添加城市列表加载
        self._load_city_list()  # 新增的初始化调用

    def _fuzzy_match(self, location):
        """模糊匹配城市名称"""
        best_match = None
        max_score = 0
        location_pinyin = ''.join(lazy_pinyin(location))
        
        print(f"\n正在进行模糊匹配: {location}")
        
        for city_name in self.city_cache.keys():
            # 计算综合相似度得分
            score = self._calculate_similarity_score(
                location, city_name,
                location_pinyin, ''.join(lazy_pinyin(city_name))
            )
            
            # 总是记录最高得分项，无论是否达到阈值
            if score > max_score:
                max_score = score
                best_match = city_name
                
            # 保留调试信息
            if score > 0.4:
                print(f"候选城市: {city_name}, 相似度: {score:.2f}")
        
        if best_match:
            print(f"最佳匹配: {best_match}, 相似度: {max_score:.2f}")
            return best_match
        else:
            print("未找到任何匹配城市")
            return location  # 返回原始输入作为保底

    def _calculate_similarity_score(self, text1, text2, pinyin1, pinyin2):
        """计算综合相似度得分"""
        # 字符相似度（考虑部分匹配）
        char_ratio = max(
            Levenshtein.ratio(text1, text2),
            Levenshtein.ratio(text1, text2[:len(text1)]) if len(text1) <= len(text2) else 0,
            Levenshtein.ratio(text2, text1[:len(text2)]) if len(text2) <= len(text1) else 0
        )
        
        # 拼音相似度（考虑声调）
        pinyin_detail1 = lazy_pinyin(text1, style=Style.TONE3)
        pinyin_detail2 = lazy_pinyin(text2, style=Style.TONE3)
        pinyin_ratio = Levenshtein.ratio(''.join(pinyin_detail1), ''.join(pinyin_detail2))
        
        # 长度相似度
        len_ratio = min(len(text1), len(text2)) / max(len(text1), len(text2))
        
        # 调整权重
        return char_ratio * 0.6 + pinyin_ratio * 0.3 + len_ratio * 0.1

    def string_similarity(self, s1, s2):
        """计算字符串相似度（保留原方法以兼容）"""
        return Levenshtein.ratio(s1, s2)

    def get_city_code(self, location):
        """获取城市编码"""
        try:
            params = {
                'key': self.amap_key,
                'address': location
            }
            response = requests.get(self.geocode_url, params=params)
            data = response.json()
            
            if data['status'] == '1' and data['geocodes']:
                return data['geocodes'][0]['adcode']
            return None
        except Exception as e:
            print(f"获取城市编码失败: {str(e)}")
            return None

    def extract_location(self, query):
        """从查询中提取城市名称
        
        使用jieba分词和正则表达式识别可能的城市名称，并与城市列表进行匹配
        """
        # 使用jieba进行分词
        words = jieba.cut(query)
        words_list = list(words)
        print(f"分词结果: {'/'.join(words_list)}")
        
        # 定义可能表示城市的关键词模式
        city_patterns = [
            r'(.+?)[市县区]',  # 匹配以"市"、"县"、"区"结尾的词
            r'(.+?)[自治区]'  # 匹配以"自治区"结尾的词
        ]
        
        # 从分词结果中查找可能的城市名称
        potential_locations = []
        
        # 首先检查完整的词是否匹配城市名称
        for word in words_list:
            if word in self.city_cache:
                print(f"直接匹配到城市: {word}")
                return word
        
        # 然后检查是否有带有城市标识的词
        for word in words_list:
            for pattern in city_patterns:
                match = re.search(pattern, word)
                if match:
                    potential_city = match.group(1)
                    if len(potential_city) >= 2:  # 避免单字城市造成的误判
                        potential_locations.append(potential_city)
        
        # 如果找到潜在城市名称，尝试与城市列表匹配
        if potential_locations:
            for loc in potential_locations:
                # 尝试直接匹配
                if loc in self.city_cache:
                    print(f"模式匹配到城市: {loc}")
                    return loc
                # 尝试模糊匹配
                similar_city = self.get_similar_city(loc)
                if similar_city != loc:
                    print(f"模糊匹配到城市: {similar_city}")
                    return similar_city
        
        # 如果没有找到明确的城市名称，尝试对整个查询进行模糊匹配
        # 提取2-4个字的连续片段进行匹配
        for i in range(len(query) - 1):
            for j in range(2, min(5, len(query) - i + 1)):
                potential_city = query[i:i+j]
                if potential_city in self.city_cache:
                    print(f"子串匹配到城市: {potential_city}")
                    return potential_city
                
                # 对潜在城市名进行模糊匹配
                similar_city = self.get_similar_city(potential_city)
                if similar_city != potential_city and len(similar_city) >= 2:
                    print(f"子串模糊匹配到城市: {similar_city}")
                    return similar_city
        
        # 如果所有方法都失败，返回None
        print("未能从查询中提取到城市名称")
        return None
        
    def process_weather_query(self, location=None, is_forecast=False, query=None):
        """处理天气查询
        
        Args:
            location: 直接指定的城市名称
            is_forecast: 是否查询天气预报
            query: 原始查询文本，如果提供则尝试从中提取城市名称
        """
        try:
            # 如果提供了原始查询，尝试从中提取城市名称
            if query and not location:
                print(f"\n从查询中提取城市名称: {query}")
                extracted_location = self.extract_location(query)
                if extracted_location:
                    location = extracted_location
                    print(f"成功提取到城市名称: {location}")
                else:
                    print("无法从查询中提取城市名称，使用默认位置")
                    location = self.default_city  # 使用配置文件中的默认城市
            
            # 确保location不为空
            if not location:
                raise Exception("未提供城市名称")
                
            # 尝试纠正城市名称
            corrected_location = self.get_similar_city(location)
            if corrected_location != location:
                print(f"\n已将 {location} 纠正为 {corrected_location}")
                location = corrected_location

            print(f"\n开始查询{location}天气")
            # 获取城市编码
            city_code = self.get_city_code(location)
            if not city_code:
                raise Exception(f"无法获取{location}的城市编码")
                
            params = {
                'key': self.amap_key,
                'city': city_code,  # 使用城市编码
                'extensions': 'all' if is_forecast else 'base'
            }
            response = requests.get(self.weather_url, params=params)
            weather_data = response.json()
            
            if weather_data['status'] == '1':
                if is_forecast and weather_data.get('forecasts'):
                    # 处理预报天气
                    forecast = weather_data['forecasts'][0]
                    today = forecast['casts'][0]
                    weather_info = (
                        f"{location}天气预报：\n"
                        f"日期：{today['date']}（{today['week']}）\n"
                        f"白天：{today['dayweather']}，{today['daytemp']}℃，{today['daywind']}风{today['daypower']}级\n"
                        f"夜间：{today['nightweather']}，{today['nighttemp']}℃，{today['nightwind']}风{today['nightpower']}级"
                    )
                elif not is_forecast and weather_data.get('lives'):
                    # 处理实况天气
                    live = weather_data['lives'][0]
                    weather_info = (
                        f"{location}实时天气：\n"
                        f"天气：{live['weather']}\n"
                        f"温度：{live['temperature']}℃\n"
                        f"湿度：{live['humidity']}%\n"
                        f"风向：{live['winddirection']}风 {live['windpower']}级\n"
                        f"发布时间：{live['reporttime']}"
                    )
                else:
                    raise Exception("未获取到天气数据")
                
                results = {
                    'status': 'success',
                    'results': [{
                        'title': f"{location}天气信息",
                        'content': weather_info
                    }],
                    'query': f"{location}天气"
                }
            else:
                results = {
                    'status': 'error',
                    'message': f'天气查询失败：{weather_data.get("info", "未知错误")}',
                    'query': f"{location}天气"
                }
            
            display_search_results(results)
            return results
            
        except Exception as e:
            error_msg = f'天气查询失败: {str(e)}'
            self.log_manager.log_error(error_msg)
            print(f"\n错误: {error_msg}")
            results = {
                'status': 'error',
                'message': error_msg,
                'query': f"{location}天气"
            }
            display_search_results(results)
            return results

    def process_search_query(self, query):
        """处理搜索查询"""
        try:
            print(f"\n开始搜索: {query}")
            # 构建搜索参数
            params = {'wd': query}
            # 发送请求
            response = requests.get(self.search_url, params=params, headers=self.headers)
            response.encoding = 'utf-8'
            
            # 解析结果
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = []
            
            # 更新选择器以匹配百度搜索结果
            for result in soup.select('div.c-container'):
                title = result.select_one('h3.t')
                content = result.select_one('.c-abstract')
                if title:
                    title_text = title.get_text().strip()
                    content_text = content.get_text().strip() if content else ""
                    search_results.append({
                        'title': title_text,
                        'content': content_text
                    })
                    # 打印每条搜索结果
                    print("\n=== 搜索结果 ===")
                    print(f"标题: {title_text}")
                    print(f"内容: {content_text}")
                    print("===============")
            
            print(f"\n共找到 {len(search_results)} 条结果")
            
            results = {
                'status': 'success',
                'results': search_results[:self.max_results],  # 使用配置的最大结果数
                'query': query
            }
            
            # 直接调用显示函数
            display_search_results(results)
            return results
            
        except Exception as e:
            error_msg = f'搜索失败: {str(e)}'
            self.log_manager.log_error(error_msg)
            print(f"\n错误: {error_msg}")
            results = {
                'status': 'error',
                'message': error_msg,
                'query': query
            }
            display_search_results(results)
            return results

    def clean_query(self, query):
        """清理搜索关键词"""
        # 移除特殊字符
        query = re.sub(r'[^\w\s]', '', query)
        # 移除多余空格
        query = ' '.join(query.split())
        return query

    def get_similar_city(self, location):
        """获取相似的城市名称"""
        # 如果已经是标准城市名，直接返回
        if location in self.city_cache:
            return location
            
        # 尝试模糊匹配
        best_match = self._fuzzy_match(location)
        if best_match:
            print(f"模糊匹配结果: {location} -> {best_match}")
            return best_match
            
        # 如果没有匹配结果，返回原始输入
        return location

    def _fuzzy_match(self, location):
        """模糊匹配城市名称"""
        if not location or len(location) < 2:
            return None
            
        best_match = None
        max_score = 0
        location_pinyin = ''.join(lazy_pinyin(location))
        
        # 使用拼音和编辑距离进行匹配
        for city in self.city_cache.keys():
            # 获取城市拼音
            if city in self.pinyin_cache:
                city_pinyin = self.pinyin_cache[city]
            else:
                city_pinyin = ''.join(lazy_pinyin(city))
                self.pinyin_cache[city] = city_pinyin
                
            # 计算相似度
            score = 1 - Levenshtein.distance(location_pinyin, city_pinyin) / max(len(location_pinyin), len(city_pinyin))
            
            # 如果相似度超过阈值且高于当前最佳匹配，更新最佳匹配
            if score > self.similarity_threshold and score > max_score:
                max_score = score
                best_match = city
        
        return best_match

    def _load_city_list(self):
        """从本地JSON文件加载城市列表，如果文件不存在则从高德API获取"""
        try:
            # 从本地JSON文件加载城市数据
            self.city_cache = load_city_data()
            
            if not self.city_cache:
                print("从本地加载城市数据失败，尝试从API获取")
                # 如果本地加载失败，尝试从API获取
                params = {
                    'key': self.amap_key,
                    'subdistrict': '3',
                    'extensions': 'base'
                }
                response = requests.get(self.city_list_url, params=params)
                data = response.json()
                
                if data['status'] == '1' and data.get('districts'):
                    # 清空缓存
                    self.city_cache = {}
                    # 递归解析城市列表
                    self._parse_districts(data['districts'][0]['districts'])
            else:
                print(f"已从本地文件加载 {len(self.city_cache)} 个城市数据")
        except Exception as e:
            print(f"加载城市列表失败: {str(e)}")

    def _parse_districts(self, districts):
        """递归解析行政区划"""
        for district in districts:
            # 只缓存城市级别（省、市、区）
            if district['level'] in ['province', 'city', 'district']:
                self.city_cache[district['name']] = district['adcode']
            # 递归处理子区域
            if 'districts' in district and district['districts']:
                self._parse_districts(district['districts'])

def get_search_results(query, is_weather=False, is_forecast=False):
    """获取搜索结果的主函数"""
    processor = SearchProcessor()
    if is_weather:
        # 使用新的提取城市功能，将原始查询传入process_weather_query
        return processor.process_weather_query(query=query, is_forecast=is_forecast)
    else:
        cleaned_query = processor.clean_query(query)
        return processor.process_search_query(cleaned_query)