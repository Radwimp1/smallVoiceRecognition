from wxauto import *
import os
import json
from fuzzy_match import fuzzy_match_remark

# 定义保存好友列表的文件路径
friends_file = os.path.join(os.path.dirname(__file__), 'data', 'friends_info.json')

# 初始化微信对象
wx = WeChat()

def init_friends_list():
    """初始化好友列表，如果文件不存在则获取并保存"""
    # 检查好友列表文件是否存在
    if os.path.exists(friends_file):
        # 如果文件存在，直接从文件加载好友列表
        print("好友列表文件已存在，直接加载文件数据")
        with open(friends_file, 'r', encoding='utf-8') as f:
            friend_infos = json.load(f)
    else:
        # 如果文件不存在，获取好友列表并保存到文件
        print("好友列表文件不存在，获取好友列表并保存")
        friend_infos = wx.GetAllFriends()
        
        # 保存好友列表到文件
        with open(friends_file, 'w', encoding='utf-8') as f:
            json.dump(friend_infos, f, ensure_ascii=False, indent=4)
    
    return friend_infos

def send_wechat_message(who, content):
    """发送微信消息给指定联系人
    
    参数:
        who (str): 联系人名称
        content (str): 要发送的消息内容
        
    返回:
        dict: 包含发送状态和消息的字典
    """
    try:
        # 初始化好友列表
        friend_infos = init_friends_list()
        
        # 模糊匹配联系人名称
        matched_name, score = fuzzy_match_remark(who)
        if matched_name and score > 0.5:  # 设置一个阈值，确保匹配质量
            print(f"模糊匹配到联系人: {matched_name} (相似度: {score:.2f})")
            who = matched_name
        else:
            print(f"未找到高匹配度的联系人，使用原始输入: {who}")
        
        # 发送消息
        wx.ChatWith(who=who)
        wx.SendMsg(msg=content, who=who)
        
        return {
            "status": "success",
            "message": f"已成功发送消息给 {who}",
            "recipient": who,
            "content": content
        }
    except Exception as e:
        print(f"发送消息时出错: {str(e)}")
        return {
            "status": "error",
            "message": f"发送消息失败: {str(e)}",
            "recipient": who,
            "content": content
        }

