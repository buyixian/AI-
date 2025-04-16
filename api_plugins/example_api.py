"""
示例API插件，展示如何实现自定义API
"""

API_NAME = "示例API"  # 此名称会出现在下拉菜单中

def call_api(message, settings, history=None):
    """
    调用API的函数
    
    参数:
        message (str): 用户消息
        settings (dict): API设置
        history (list): 历史对话记录
        
    返回:
        str: API响应
    """
    # 在这里实现实际的API调用
    return f"这是示例API的响应: 您发送了消息：{message}"
