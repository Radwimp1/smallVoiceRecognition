import json
import os
import difflib
from pypinyin import lazy_pinyin

#关键字模糊匹配模块
def levenshtein_distance(s1, s2):
    """
    计算两个字符串之间的Levenshtein距离
    """
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)
    
    # 创建矩阵
    matrix = [[0 for x in range(len(s2) + 1)] for x in range(len(s1) + 1)]
    
    # 初始化第一行和第一列
    for i in range(len(s1) + 1):
        matrix[i][0] = i
    for j in range(len(s2) + 1):
        matrix[0][j] = j
    
    # 填充矩阵
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # 删除
                matrix[i][j-1] + 1,      # 插入
                matrix[i-1][j-1] + cost   # 替换
            )
    
    return matrix[len(s1)][len(s2)]


def similarity_ratio(s1, s2):
    """
    计算两个字符串的相似度比率
    返回值范围：0.0 (完全不同) 到 1.0 (完全相同)
    """
    if not s1 or not s2:  # 处理空字符串情况
        return 0.0 if (s1 or s2) else 1.0  # 如果两者都为空则相似度为1，否则为0
    
    # 使用difflib的SequenceMatcher计算相似度
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def pinyin_similarity(s1, s2):
    """
    计算两个中文字符串的拼音相似度
    返回值范围：0.0 (完全不同) 到 1.0 (完全相同)
    """
    if not s1 or not s2:  # 处理空字符串情况
        return 0.0 if (s1 or s2) else 1.0  # 如果两者都为空则相似度为1，否则为0
    
    # 转换为拼音
    pinyin_s1 = ''.join(lazy_pinyin(s1))
    pinyin_s2 = ''.join(lazy_pinyin(s2))
    
    # 使用difflib的SequenceMatcher计算拼音相似度
    return difflib.SequenceMatcher(None, pinyin_s1, pinyin_s2).ratio()


def fuzzy_match_remark(who, json_file_path=None, pinyin_weight=0.6):
    """
    将输入的who参数与friends_info.json中的remark字段进行模糊匹配
    返回匹配度最高的remark值
    
    参数:
        who (str): 要匹配的名称
        json_file_path (str, optional): friends_info.json的路径，默认为当前目录
        pinyin_weight (float, optional): 拼音相似度的权重，默认为0.6
        
    返回:
        tuple: (最佳匹配的remark值, 相似度分数)
    """
    if not who:  # 如果输入为空，直接返回
        return None, 0.0
        
    # 导入正则表达式模块
    import re
    
    # 如果未指定json文件路径，使用默认路径
    if not json_file_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(current_dir, 'data', 'friends_info.json')
    
    try:
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            friends_data = json.load(f)
        
        best_match = None
        highest_score = 0.5  # 初始相似度阈值
        
        # 遍历所有联系人，寻找最佳匹配
        for friend in friends_data:
            remark = friend.get('remark')
            if not remark:  # 跳过没有remark的条目
                continue
                
            # 保存原始remark值用于返回
            original_remark = remark
            
            # 使用正则表达式过滤掉非汉字字符
            filtered_remark = re.sub(r'[^\u4e00-\u9fa5]', '', remark)
            
            # 如果过滤后为空，则使用原始值
            if not filtered_remark:
                filtered_remark = remark
            
            # 计算字符相似度（使用过滤后的remark）
            char_score = similarity_ratio(who, filtered_remark)
            
            # 计算拼音相似度（使用过滤后的remark）
            py_score = pinyin_similarity(who, filtered_remark)
            
            # 综合得分 (加权平均)
            score = py_score * pinyin_weight + char_score * (1 - pinyin_weight)
            
            # 打印每个联系人的匹配得分
            print(f"联系人: {original_remark} | 过滤后: {filtered_remark} | 字符相似度: {char_score:.2f} | 拼音相似度: {py_score:.2f} | 综合得分: {score:.2f}")
            
            # 更新最佳匹配
            if score > highest_score:
                highest_score = score
                best_match = original_remark
        
        return best_match, highest_score
    
    except Exception as e:
        print(f"匹配过程中出错: {str(e)}")
        return None, 0.0


# 示例用法
if __name__ == "__main__":
    test_name = input("请输入要匹配的名称: ")
    match, score = fuzzy_match_remark(test_name)
    if match:
        print(f"最佳匹配: {match} (相似度: {score:.2f})")
    else:
        print("未找到匹配")