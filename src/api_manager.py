import os
import json
import requests
import importlib.util

class APIManager:
    def __init__(self):
        self.settings = self.load_settings()
        self.other_apis = {}
        self.load_other_apis()
    
    def load_settings(self):
        """加载API设置"""
        settings = {
            "openai": {"api_key": "", "model": "gpt-4"},
            "azure": {"api_key": "", "endpoint": "", "deployment": ""},
            "local": {"api": "http://localhost:8000/v1"},
            "deepseek": {"api_key": "", "model": "deepseek-chat", "base_url": "https://api.deepseek.com/v1"},
            "other": {},
            "general": {
                "max_context": 10,  # 默认最大上下文数量
                "stream_output": True,  # 默认启用流式输出
                "temperature": 0.7,  # 默认温度
                "max_tokens": 2000   # 默认最大生成token数
            }
        }
        
        try:
            if os.path.exists("config/settings.json"):
                with open("config/settings.json", "r") as f:
                    loaded_settings = json.load(f)
                    # 更新默认设置
                    for key in loaded_settings:
                        if key in settings:
                            settings[key].update(loaded_settings[key])
        except Exception as e:
            print(f"加载设置时出错: {e}")
        
        return settings
    
    def save_settings(self):
        """保存API设置"""
        os.makedirs("config", exist_ok=True)
        with open("config/settings.json", "w") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)
    
    def load_other_apis(self):
        """加载自定义API插件"""
        plugins_dir = "api_plugins"
        os.makedirs(plugins_dir, exist_ok=True)
        
        # 创建示例插件文件
        self.create_example_plugin()
        
        # 加载所有插件
        for file in os.listdir(plugins_dir):
            if file.endswith(".py"):
                try:
                    module_path = os.path.join(plugins_dir, file)
                    module_name = os.path.splitext(file)[0]
                    
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, "API_NAME") and hasattr(module, "call_api"):
                        self.other_apis[module.API_NAME] = module.call_api
                except Exception as e:
                    print(f"加载API插件 {file} 时出错: {e}")
    
    def create_example_plugin(self):
        """创建示例API插件"""
        plugins_dir = "api_plugins"
        example_file = os.path.join(plugins_dir, "example_api.py")
        
        if not os.path.exists(example_file):
            with open(example_file, "w", encoding="utf-8") as f:
                f.write('''"""
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
''')
    
    def _prepare_messages(self, message, history):
        """准备消息格式，并应用上下文限制"""
        if history is None:
            history = []
            
        # 应用上下文数量限制
        max_context = self.settings.get("general", {}).get("max_context", 10)
        if max_context > 0 and len(history) > max_context * 2:  # 每轮对话包含用户和助手两条消息
            # 保留system消息(如果有)和最近的max_context轮对话
            history = history[-(max_context * 2):]
            
        messages = []
        for h in history:
            if "user" in h:
                messages.append({"role": "user", "content": h["user"]})
            if "assistant" in h:
                messages.append({"role": "assistant", "content": h["assistant"]})
        
        messages.append({"role": "user", "content": message})
        return messages
    
    def call_openai_api(self, message, history=None, stream_callback=None):
        """调用OpenAI API"""
        if not self.settings["openai"]["api_key"]:
            return "错误: 未设置OpenAI API密钥，请在设置中配置"
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.settings["openai"]["api_key"])
            
            messages = self._prepare_messages(message, history)
            
            # 确定是否使用流式输出
            stream = self.settings.get("general", {}).get("stream_output", True) and stream_callback is not None
            
            # 获取其他参数
            temperature = self.settings.get("general", {}).get("temperature", 0.7)
            max_tokens = self.settings.get("general", {}).get("max_tokens", 2000)
            
            if stream:
                # 流式输出
                response_text = ""
                response_stream = client.chat.completions.create(
                    model=self.settings["openai"]["model"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
                
                for chunk in response_stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        response_text += content
                        stream_callback(content)
                
                return response_text
            else:
                # 非流式输出
                response = client.chat.completions.create(
                    model=self.settings["openai"]["model"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                return response.choices[0].message.content
        except Exception as e:
            return f"调用OpenAI API时出错: {str(e)}"
    
    def call_azure_openai_api(self, message, history=None, stream_callback=None):
        """调用Azure OpenAI API"""
        if not all([self.settings["azure"]["api_key"], 
                   self.settings["azure"]["endpoint"], 
                   self.settings["azure"]["deployment"]]):
            return "错误: 未完全设置Azure OpenAI API参数，请在设置中配置"
        
        try:
            import openai
            client = openai.AzureOpenAI(
                api_key=self.settings["azure"]["api_key"],
                api_version="2023-05-15",
                azure_endpoint=self.settings["azure"]["endpoint"]
            )
            
            messages = self._prepare_messages(message, history)
            
            # 确定是否使用流式输出
            stream = self.settings.get("general", {}).get("stream_output", True) and stream_callback is not None
            
            # 获取其他参数
            temperature = self.settings.get("general", {}).get("temperature", 0.7)
            max_tokens = self.settings.get("general", {}).get("max_tokens", 2000)
            
            if stream:
                # 流式输出
                response_text = ""
                response_stream = client.chat.completions.create(
                    deployment_name=self.settings["azure"]["deployment"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
                
                for chunk in response_stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        response_text += content
                        stream_callback(content)
                
                return response_text
            else:
                # 非流式输出
                response = client.chat.completions.create(
                    deployment_name=self.settings["azure"]["deployment"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                return response.choices[0].message.content
        except Exception as e:
            return f"调用Azure OpenAI API时出错: {str(e)}"
    
    def call_local_api(self, message, history=None, stream_callback=None):
        """调用本地模型API"""
        api_url = self.settings["local"]["api"]
        if not api_url:
            return "错误: 未设置本地API地址，请在设置中配置"
        
        try:
            messages = self._prepare_messages(message, history)
            
            # 确定是否使用流式输出
            stream = self.settings.get("general", {}).get("stream_output", True) and stream_callback is not None
            
            # 获取其他参数
            temperature = self.settings.get("general", {}).get("temperature", 0.7)
            max_tokens = self.settings.get("general", {}).get("max_tokens", 2000)
            
            # API请求
            headers = {"Content-Type": "application/json"}
            data = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            }
            
            if stream:
                # 流式输出
                response = requests.post(
                    f"{api_url}/chat/completions",
                    headers=headers,
                    json=data,
                    stream=True,
                    timeout=60
                )
                
                if response.status_code == 200:
                    response_text = ""
                    for line in response.iter_lines():
                        if line:
                            try:
                                line = line.decode('utf-8')
                                if line.startswith('data: '):
                                    line = line[6:]  # 移除 "data: " 前缀
                                if line and line != "[DONE]":
                                    chunk = json.loads(line)
                                    if 'choices' in chunk and chunk['choices'] and 'delta' in chunk['choices'][0]:
                                        content = chunk['choices'][0]['delta'].get('content', '')
                                        if content:
                                            response_text += content
                                            stream_callback(content)
                            except Exception as e:
                                print(f"处理流式响应时出错: {str(e)}")
                                continue
                    return response_text
                else:
                    return f"API请求失败，状态码: {response.status_code}, 错误: {response.text}"
            else:
                # 非流式输出
                response = requests.post(
                    f"{api_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    return f"API请求失败，状态码: {response.status_code}, 错误: {response.text}"
        except Exception as e:
            return f"调用本地API时出错: {str(e)}"
    
    def call_deepseek_api(self, message, history=None, stream_callback=None):
        """调用DeepSeek API"""
        if not self.settings["deepseek"]["api_key"]:
            return "错误: 未设置DeepSeek API密钥，请在设置中配置"

        try:
            import openai
            print(f"使用OpenAI库版本: {openai.__version__}")
            print(f"DeepSeek API配置: URL={self.settings['deepseek']['base_url']}, 模型={self.settings['deepseek']['model']}")

            # 使用OpenAI客户端连接DeepSeek API
            client = openai.OpenAI(
                api_key=self.settings["deepseek"]["api_key"],
                base_url=self.settings["deepseek"]["base_url"]
            )

            # 准备消息
            messages = self._prepare_messages(message, history)
            
            # 确定是否使用流式输出
            stream = self.settings.get("general", {}).get("stream_output", True) and stream_callback is not None
            
            # 获取其他参数
            temperature = self.settings.get("general", {}).get("temperature", 0.7)
            max_tokens = self.settings.get("general", {}).get("max_tokens", 2000)

            try:
                if stream:
                    # 流式输出
                    response_text = ""
                    response_stream = client.chat.completions.create(
                        model=self.settings["deepseek"]["model"],
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True
                    )
                    
                    for chunk in response_stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            response_text += content
                            stream_callback(content)
                    
                    return response_text
                else:
                    # 非流式输出
                    response = client.chat.completions.create(
                        model=self.settings["deepseek"]["model"],
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content
            except Exception as api_error:
                print(f"调用DeepSeek API出错: {str(api_error)}")
                
                # 尝试使用示例API作为备用方案
                if "示例API" in self.other_apis:
                    print("使用示例API插件作为替代...")
                    api_function = self.other_apis["示例API"]
                    return api_function(message, self.settings.get("other", {}), history)
                else:
                    return f"""
DeepSeek API调用失败: {str(api_error)}

可能的原因包括:
1. API密钥不正确或已过期
2. 网络连接问题
3. API服务不可用

建议:
1. 检查API密钥是否正确
2. 检查网络连接
3. 尝试使用其他API服务
"""

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"DeepSeek API调用错误: {str(e)}")
            print(f"错误详情: {error_trace}")
            return f"调用DeepSeek API时出错: {str(e)}"
    
    def call_other_api(self, api_name, message, history=None, stream_callback=None):
        """调用其他自定义API"""
        if api_name not in self.other_apis:
            return f"错误: 找不到API: {api_name}"
        
        try:
            api_function = self.other_apis[api_name]
            # 注意：自定义API可能不支持流式输出
            return api_function(message, self.settings.get("other", {}), history)
        except Exception as e:
            return f"调用API {api_name} 时出错: {str(e)}"
    
    def call_api(self, api_type, message, history=None, stream_callback=None):
        """根据选择的API类型调用不同的API"""
        api_type = api_type.lower() if api_type else ""
        
        if api_type == "openai":
            return self.call_openai_api(message, history, stream_callback)
        elif api_type == "azure":
            return self.call_azure_openai_api(message, history, stream_callback)
        elif api_type == "local":
            return self.call_local_api(message, history, stream_callback)
        elif api_type == "deepseek":
            return self.call_deepseek_api(message, history, stream_callback)
        elif api_type in [k.lower() for k in self.other_apis.keys()]:
            # 查找匹配的API名称（不区分大小写）
            for k in self.other_apis.keys():
                if k.lower() == api_type:
                    return self.call_other_api(k, message, history, stream_callback)
        else:
            return f"错误: 未知的API类型: {api_type}"
    
    def get_available_apis(self):
        """获取所有可用的API列表"""
        apis = ["OpenAI", "Azure", "Local", "DeepSeek"]
        apis.extend(list(self.other_apis.keys()))
        return apis
    
    def register_api(self, name, callback):
        """注册新的API"""
        self.other_apis[name] = callback
        return True 