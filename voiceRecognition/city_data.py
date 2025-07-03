import os
import json
import requests
import configparser

def generate_city_data():
    """
    从高德API获取城市数据并保存为JSON文件
    """
    # 读取配置文件
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    # 获取API密钥和URL
    amap_key = config.get('api', 'amap_key')
    city_list_url = config.get('search', 'district_url')
    
    # 确保data目录存在
    os.makedirs('data', exist_ok=True)
    json_file_path = os.path.join('data', 'city_data.json')
    
    try:
        # 从高德API获取城市数据
        params = {
            'key': amap_key,
            'subdistrict': '3',
            'extensions': 'base'
        }
        response = requests.get(city_list_url, params=params)
        data = response.json()
        
        if data['status'] == '1' and data.get('districts'):
            # 解析城市数据
            city_data = {}
            _parse_districts(data['districts'][0]['districts'], city_data)
            
            # 保存为JSON文件
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(city_data, f, ensure_ascii=False, indent=4)
            
            print(f"城市数据已保存到 {json_file_path}")
            print(f"共收集了 {len(city_data)} 个城市")
            return True
        else:
            print("获取城市数据失败")
            return False
    except Exception as e:
        print(f"生成城市数据失败: {str(e)}")
        return False

def _parse_districts(districts, city_data):
    """
    递归解析行政区划
    """
    for district in districts:
        # 只缓存城市级别（省、市、区）
        if district['level'] in ['province', 'city', 'district']:
            city_data[district['name']] = district['adcode']
        # 递归处理子区域
        if 'districts' in district and district['districts']:
            _parse_districts(district['districts'], city_data)

def load_city_data():
    """
    加载城市数据，如果JSON文件不存在则生成
    """
    json_file_path = os.path.join('data', 'city_data.json')
    
    # 检查文件是否存在
    if not os.path.exists(json_file_path):
        print("城市数据文件不存在，正在生成...")
        if not generate_city_data():
            print("生成城市数据失败，返回空字典")
            return {}
    
    try:
        # 从JSON文件加载城市数据
        with open(json_file_path, 'r', encoding='utf-8') as f:
            city_data = json.load(f)
        print(f"已从文件加载 {len(city_data)} 个城市数据")
        return city_data
    except Exception as e:
        print(f"加载城市数据失败: {str(e)}")
        return {}

if __name__ == "__main__":
    # 当直接运行此脚本时，生成城市数据
    generate_city_data()