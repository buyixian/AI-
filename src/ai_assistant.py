# -*- coding: utf-8 -*-
import os
import sys
import json
import webbrowser
import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from threading import Thread
import re
import threading
import platform
import subprocess
import datetime
import time
from urllib.parse import quote_plus
import logging

# 导入自定义模块
from api_manager import APIManager
from knowledge_manager import KnowledgeManager
from paper_downloader import PaperDownloader

# 创建测试下载批处理文件
def create_test_batch_file():
    """创建测试下载的批处理文件"""
    try:
        # 批处理文件路径
        batch_file = "test_download.bat"
        
        # 检查是否已存在
        if os.path.exists(batch_file):
            # 查看文件修改时间，如果不是今天创建的，则重新创建
            mod_time = os.path.getmtime(batch_file)
            mod_date = datetime.datetime.fromtimestamp(mod_time).date()
            today = datetime.datetime.now().date()
            
            if mod_date == today:
                return  # 今天已经创建过，不需要重新创建
        
        # 创建批处理文件内容
        content = """@echo off
echo 正在启动下载测试...
echo 这将启动AI助手并自动执行下载测试

REM 启动Python程序并传递测试标志
python ai_assistant.py --test-download

echo 测试完成
pause
"""
        
        # 写入文件
        with open(batch_file, "w") as f:
            f.write(content)
        
        print(f"已创建测试下载批处理文件: {batch_file}")
    except Exception as e:
        print(f"创建批处理文件失败: {str(e)}")

def check_encoding_issues():
    """检查并修复可能的编码问题"""
    try:
        import chardet
        
        # 检测当前文件的编码
        with open(__file__, 'rb') as f:
            result = chardet.detect(f.read())
        
        file_encoding = result['encoding']
        confidence = result['confidence']
        
        # 打印编码信息
        print(f"文件编码检测: {file_encoding}, 可信度: {confidence:.2f}")
        
        # 如果不是UTF-8编码，尝试转换
        if file_encoding and file_encoding.lower() != 'utf-8' and confidence > 0.7:
            try:
                # 读取当前文件
                with open(__file__, 'rb') as f:
                    content = f.read()
                
                # 解码并重新编码为UTF-8
                decoded = content.decode(file_encoding, errors='replace')
                utf8_content = decoded.encode('utf-8')
                
                # 创建备份
                backup_file = __file__ + '.backup'
                with open(backup_file, 'wb') as f:
                    f.write(content)
                
                # 重写文件为UTF-8
                with open(__file__, 'wb') as f:
                    f.write(utf8_content)
                
                print(f"已将文件从 {file_encoding} 转换为 UTF-8，原文件已备份为 {backup_file}")
            except Exception as e:
                print(f"转换文件编码时出错: {str(e)}")
    except ImportError:
        print("缺少chardet库，无法检测文件编码。请安装: pip install chardet")
    except Exception as e:
        print(f"检查编码时发生错误: {str(e)}")

class AIAssistant:
    def __init__(self, root):
        """初始化AI助手"""
        self.root = root
        root.title("AI论文助手")
        
        # 设置最小窗口大小
        root.minsize(900, 700)
        
        # 初始化关键管理器
        self.api_manager = APIManager()
        self.paper_downloader = PaperDownloader("downloaded_papers")
        self.knowledge_manager = KnowledgeManager()
        
        # 创建Tab控件
        self.tab_control = ttk.Notebook(root)
        
        # 创建各个选项卡
        self.chat_tab = ttk.Frame(self.tab_control)
        self.paper_tab = ttk.Frame(self.tab_control)
        self.knowledge_tab = ttk.Frame(self.tab_control)
        self.settings_tab = ttk.Frame(self.tab_control)
        
        # 添加选项卡到Tab控件
        self.tab_control.add(self.chat_tab, text="AI聊天")
        self.tab_control.add(self.paper_tab, text="文献下载")
        self.tab_control.add(self.knowledge_tab, text="知识库")
        self.tab_control.add(self.settings_tab, text="设置")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # 存储下载状态和结果
        self.selected_paper = None
        self.last_download_path = None
        self.paper_results = []
        
        # 初始化提示
        self.prompt_template = ""
        
        # 存储聊天历史
        self.chat_history = []
        self.chat_history_data = []  # 添加这一行，初始化聊天历史数据
        
        # 初始化组件
        self.setup_chat_tab()
        self.setup_paper_tab()
        self.setup_knowledge_tab()
        self.setup_settings_tab()
        
        # 加载设置
        self.load_settings()
    
    def setup_chat_tab(self):
        # 对话历史
        chat_frame = ttk.Frame(self.chat_tab)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.chat_history = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, font=("Arial", 10))
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_history.config(state=tk.DISABLED)
        
        # 输入区域
        input_frame = ttk.Frame(self.chat_tab)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.user_input = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=4, font=("Arial", 10))
        self.user_input.pack(fill=tk.X, padx=5, pady=5, side=tk.LEFT, expand=True)
        self.user_input.bind("<Control-Return>", self.send_message)
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT, padx=5)
        
        self.send_button = ttk.Button(button_frame, text="发送", command=self.send_message)
        self.send_button.pack(pady=2)
        
        self.clear_button = ttk.Button(button_frame, text="清除", command=self.clear_chat)
        self.clear_button.pack(pady=2)
        
        # API选择
        api_frame = ttk.Frame(self.chat_tab)
        api_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(api_frame, text="选择API:").pack(side=tk.LEFT, padx=5)
        
        self.api_var = tk.StringVar()
        # 获取所有可用的API
        self.api_choices = self.api_manager.get_available_apis()
        self.api_dropdown = ttk.Combobox(api_frame, textvariable=self.api_var, values=self.api_choices, state="readonly")
        self.api_dropdown.pack(side=tk.LEFT, padx=5)
        if self.api_choices:
            # 默认选择示例API，如果存在
            if "示例API" in self.api_choices:
                self.api_var.set("示例API")
            else:
                self.api_dropdown.current(0)
        
        # 添加使用知识库选项
        self.use_knowledge_var = tk.BooleanVar()
        self.use_knowledge_var.set(False)
        ttk.Checkbutton(api_frame, text="使用知识库增强", variable=self.use_knowledge_var).pack(side=tk.LEFT, padx=15)
    
    def setup_knowledge_tab(self):
        """设置知识库选项卡"""
        # 分为左右两部分布局
        main_frame = ttk.Frame(self.knowledge_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 左侧：分区选择和文件列表
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # 分区选择框架
        category_frame = ttk.LabelFrame(left_frame, text="知识库分区")
        category_frame.pack(fill="x", padx=5, pady=5)
        
        # 分区选择变量
        self.selected_category = tk.StringVar(value="全部")
        
        # 添加分区选择单选按钮
        categories = ["全部"] + self.knowledge_manager.categories
        for category in categories:
            rb = ttk.Radiobutton(
                category_frame, 
                text=category, 
                value=category, 
                variable=self.selected_category,
                command=self.refresh_knowledge_list
            )
            rb.pack(anchor="w", padx=10, pady=2)
        
        # 文件列表框架
        files_frame = ttk.LabelFrame(left_frame, text="文件列表")
        files_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建列表和滚动条
        self.knowledge_list = tk.Listbox(files_frame, height=15)
        scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.knowledge_list.yview)
        self.knowledge_list.configure(yscrollcommand=scrollbar.set)
        
        self.knowledge_list.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", padx=5, pady=5)
        
        # 绑定选择事件
        self.knowledge_list.bind("<<ListboxSelect>>", self.on_knowledge_file_select)
        self.knowledge_list.bind("<Double-1>", self.open_knowledge_file)
        
        # 操作按钮
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.pack(fill="x", padx=5, pady=5)
        
        # 添加文件按钮
        add_button = ttk.Button(buttons_frame, text="添加文件", command=self.upload_to_knowledge_base)
        add_button.pack(side="left", padx=5, pady=5)
        
        # 删除文件按钮
        self.delete_button = ttk.Button(buttons_frame, text="删除文件", command=self.delete_from_knowledge_base, state="disabled")
        self.delete_button.pack(side="left", padx=5, pady=5)
        
        # 刷新按钮
        refresh_button = ttk.Button(buttons_frame, text="刷新列表", command=self.refresh_knowledge_list)
        refresh_button.pack(side="right", padx=5, pady=5)
        
        # 右侧：文件详情和预览
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # 文件详情框架
        details_frame = ttk.LabelFrame(right_frame, text="文件详情")
        details_frame.pack(fill="x", padx=5, pady=5)
        
        # 详情标签
        self.file_title_label = ttk.Label(details_frame, text="标题: ")
        self.file_title_label.pack(anchor="w", padx=10, pady=2)
        
        self.file_authors_label = ttk.Label(details_frame, text="作者: ")
        self.file_authors_label.pack(anchor="w", padx=10, pady=2)
        
        self.file_year_label = ttk.Label(details_frame, text="年份: ")
        self.file_year_label.pack(anchor="w", padx=10, pady=2)
        
        self.file_category_label = ttk.Label(details_frame, text="分区: ")
        self.file_category_label.pack(anchor="w", padx=10, pady=2)
        
        self.file_path_label = ttk.Label(details_frame, text="路径: ")
        self.file_path_label.pack(anchor="w", padx=10, pady=2)
        
        # 文件预览框架
        preview_frame = ttk.LabelFrame(right_frame, text="文件预览")
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建文本框和滚动条
        self.preview_text = tk.Text(preview_frame, wrap="word")
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        self.preview_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        preview_scrollbar.pack(side="right", fill="y", padx=5, pady=5)
        
        # 初始化时加载文件列表
        self.refresh_knowledge_list()
    
    def setup_settings_tab(self):
        """设置API配置选项卡"""
        # 初始化API管理器，如果尚未初始化
        if not hasattr(self, 'api_manager'):
            self.api_manager = APIManager()
            
        # 创建API类型选择下拉框
        ttk.Label(self.settings_tab, text="选择API类型:").pack(anchor="w", padx=10, pady=5)
        
        settings_frame = ttk.Frame(self.settings_tab)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建一个带滚动条的Canvas，用于容纳所有设置
        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # OpenAI设置
        openai_frame = ttk.LabelFrame(scrollable_frame, text="OpenAI设置")
        openai_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(openai_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.openai_key = ttk.Entry(openai_frame, width=50, show="*")
        self.openai_key.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(openai_frame, text="模型:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.openai_model = ttk.Entry(openai_frame, width=30)
        self.openai_model.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.openai_model.insert(0, "gpt-4")
        
        # Azure OpenAI设置
        azure_frame = ttk.LabelFrame(scrollable_frame, text="Azure OpenAI设置")
        azure_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(azure_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.azure_key = ttk.Entry(azure_frame, width=50, show="*")
        self.azure_key.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(azure_frame, text="Endpoint:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.azure_endpoint = ttk.Entry(azure_frame, width=50)
        self.azure_endpoint.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(azure_frame, text="部署名称:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.azure_deployment = ttk.Entry(azure_frame, width=30)
        self.azure_deployment.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # DeepSeek设置
        deepseek_frame = ttk.LabelFrame(scrollable_frame, text="DeepSeek设置")
        deepseek_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(deepseek_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.deepseek_key = ttk.Entry(deepseek_frame, width=50, show="*")
        self.deepseek_key.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(deepseek_frame, text="模型:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.deepseek_model = ttk.Entry(deepseek_frame, width=30)
        self.deepseek_model.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.deepseek_model.insert(0, "deepseek-chat")
        
        ttk.Label(deepseek_frame, text="API地址:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.deepseek_url = ttk.Entry(deepseek_frame, width=50)
        self.deepseek_url.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.deepseek_url.insert(0, "https://api.deepseek.com/v1")
        
        # 本地模型设置
        local_frame = ttk.LabelFrame(scrollable_frame, text="本地模型设置")
        local_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(local_frame, text="API地址:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.local_api = ttk.Entry(local_frame, width=50)
        self.local_api.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.local_api.insert(0, "http://localhost:8000/v1")
        
        # 其他API设置
        other_frame = ttk.LabelFrame(scrollable_frame, text="其他API设置")
        other_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(other_frame, text="API插件目录:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        plugin_path = os.path.abspath("api_plugins")
        ttk.Label(other_frame, text=plugin_path).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Button(other_frame, text="打开插件目录", 
                   command=lambda: self.open_directory(plugin_path)).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(other_frame, text="刷新API列表", 
                   command=self.refresh_api_list).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 保存设置按钮
        save_frame = ttk.Frame(scrollable_frame)
        save_frame.pack(pady=10)
        
        ttk.Button(save_frame, text="保存设置", command=self.save_settings).pack(pady=5)
    
    def setup_paper_tab(self):
        """设置文献下载选项卡"""
        # 初始化论文下载器，如果尚未初始化
        if not hasattr(self, 'paper_downloader'):
            self.paper_downloader = PaperDownloader("downloaded_papers")
            
        # 初始化知识库管理器，如果尚未初始化
        if not hasattr(self, 'knowledge_manager'):
            self.knowledge_manager = KnowledgeManager()
            
        # 搜索框和按钮
        search_frame = ttk.Frame(self.paper_tab)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(search_frame, text="论文搜索:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.search_entry = ttk.Entry(search_frame, width=50)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.search_entry.bind("<Return>", lambda e: self.search_papers())
        
        self.search_button = ttk.Button(search_frame, text="搜索", command=self.search_papers)
        self.search_button.grid(row=0, column=2, padx=5, pady=5)
        
        # 添加取消搜索按钮（默认禁用）
        self.cancel_search_button = ttk.Button(search_frame, text="停止搜索", command=self.cancel_search, state="disabled")
        self.cancel_search_button.grid(row=0, column=3, padx=5, pady=5)
        
        # 创建下载源选择
        ttk.Label(search_frame, text="来源:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # 添加百度学术和中国知网到来源列表
        sources = self.paper_downloader.sources + ["百度学术", "中国知网"]
        self.source_var = tk.StringVar(value="Google Scholar")  # 默认选择Google Scholar
        source_combo = ttk.Combobox(search_frame, textvariable=self.source_var,
                                   values=sources,
                                   state="readonly", width=20)
        source_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 测试下载按钮
        self.test_download_button = ttk.Button(
            search_frame, text="测试下载功能", 
            command=self.test_download_function)
        self.test_download_button.grid(row=1, column=2, padx=5, pady=5)
        
        # 添加搜索状态标签
        self.search_status_var = tk.StringVar(value="就绪")
        search_status_label = ttk.Label(search_frame, textvariable=self.search_status_var)
        search_status_label.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        # 快速DOI/ArXiv ID下载
        doi_frame = ttk.LabelFrame(self.paper_tab, text="快速DOI/ArXiv ID下载")
        doi_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(doi_frame, text="输入DOI或ArXiv ID:").pack(side="left", padx=5, pady=5)
        self.doi_entry = ttk.Entry(doi_frame, width=50)
        self.doi_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.doi_entry.bind("<Return>", lambda e: self.quick_access())
        
        self.doi_button = ttk.Button(doi_frame, text="下载", command=self.quick_access)
        self.doi_button.pack(side="left", padx=5, pady=5)
        
        # 正确设置quick_access_button变量
        self.quick_access_button = ttk.Button(doi_frame, text="检查", command=self.quick_access)
        self.quick_access_button.pack(side="left", padx=5, pady=5)
        
        # 创建下载进度条
        progress_frame = ttk.Frame(self.paper_tab)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.download_progress = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="determinate")
        self.download_progress.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        
        self.paper_status_label = ttk.Label(progress_frame, text="准备就绪")
        self.paper_status_label.pack(side="left", padx=5, pady=5)
        
        # 创建搜索进度指示器
        self.search_progress = ttk.Progressbar(progress_frame, orient="horizontal", length=100, mode="indeterminate")
        self.search_progress.pack(side="right", padx=5, pady=5)
        
        # 创建主框架：左侧结果列表，右侧详细信息
        paper_main_frame = ttk.Frame(self.paper_tab)
        paper_main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左侧：搜索结果
        left_frame = ttk.Frame(paper_main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # 搜索结果框架
        results_frame = ttk.LabelFrame(left_frame, text="搜索结果")
        results_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # 使用Treeview显示搜索结果
        columns = ("title", "authors", "year", "source")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", selectmode="browse", height=10)
        
        # 定义列
        self.results_tree.heading("title", text="标题")
        self.results_tree.heading("authors", text="作者")
        self.results_tree.heading("year", text="年份")
        self.results_tree.heading("source", text="来源")
        
        # 设置列宽
        self.results_tree.column("title", width=300)
        self.results_tree.column("authors", width=150)
        self.results_tree.column("year", width=50)
        self.results_tree.column("source", width=80)
        
        # 添加滚动条
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        # 布局
        self.results_tree.pack(side="left", fill="both", expand=True)
        results_scrollbar.pack(side="right", fill="y")
        
        # 绑定选择事件
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_select)
        
        # 右侧：论文详情
        right_frame = ttk.Frame(paper_main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # 详情框架
        details_frame = ttk.LabelFrame(right_frame, text="论文详情")
        details_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # 创建文本框用于显示详情
        self.paper_details_text = tk.Text(details_frame, wrap="word", width=40, height=15)
        details_scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.paper_details_text.yview)
        self.paper_details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.paper_details_text.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")
        
        # 配置样式
        self.paper_details_text.tag_configure("title", font=("Arial", 12, "bold"))
        self.paper_details_text.tag_configure("heading", font=("Arial", 10, "bold"))
        self.paper_details_text.tag_configure("link", foreground="blue", underline=1)
        self.paper_details_text.bind("<Button-1>", self.open_url)
        
        # 添加按钮区域
        buttons_frame = ttk.Frame(self.paper_tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        self.download_button = ttk.Button(buttons_frame, text="下载选中论文", command=self.download_selected_paper, state="disabled")
        self.download_button.pack(side="left", padx=5, pady=5)
        
        self.open_browser_button = ttk.Button(buttons_frame, text="在浏览器中打开", command=self.open_url_in_browser, state="disabled")
        self.open_browser_button.pack(side="left", padx=5, pady=5)
        
        # 添加知识库导入按钮
        self.add_to_kb_button = ttk.Button(buttons_frame, text="导入到知识库", command=self.add_paper_to_kb, state="disabled")
        self.add_to_kb_button.pack(side="left", padx=5, pady=5)
        
        # 添加刷新按钮
        refresh_button = ttk.Button(buttons_frame, text="刷新下载列表", command=self.refresh_downloaded_files)
        refresh_button.pack(side="right", padx=5, pady=5)
        
        # 创建已下载文件列表
        downloads_frame = ttk.LabelFrame(self.paper_tab, text="已下载论文")
        downloads_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建下载文件列表
        self.downloaded_files_list = tk.Listbox(downloads_frame, height=8)
        self.downloaded_files_list.pack(side="left", fill="both", expand=True)
        
        # 添加滚动条
        downloads_scrollbar = ttk.Scrollbar(downloads_frame, orient="vertical", command=self.downloaded_files_list.yview)
        self.downloaded_files_list.configure(yscrollcommand=downloads_scrollbar.set)
        downloads_scrollbar.pack(side="right", fill="y")
        
        # 绑定双击事件
        self.downloaded_files_list.bind("<Double-1>", self.on_file_double_click)
        self.downloaded_files_list.bind("<<ListboxSelect>>", self.on_file_select)
        
        # 文件操作按钮
        file_buttons_frame = ttk.Frame(self.paper_tab)
        file_buttons_frame.pack(fill="x", padx=10, pady=5)
        
        open_file_button = ttk.Button(file_buttons_frame, text="打开文件", command=self.open_selected_file)
        open_file_button.pack(side="left", padx=5, pady=5)
        
        self.add_file_to_kb_button = ttk.Button(file_buttons_frame, text="添加到知识库", command=self.add_downloaded_to_kb)
        self.add_file_to_kb_button.pack(side="left", padx=5, pady=5)
        
        open_folder_button = ttk.Button(file_buttons_frame, text="打开下载文件夹", command=self.open_papers_folder)
        open_folder_button.pack(side="right", padx=5, pady=5)
        
        # 初始化下载目录
        self.papers_dir = "downloaded_papers"
        if not os.path.exists(self.papers_dir):
            os.makedirs(self.papers_dir)
            
        # 刷新已下载文件列表
        self.refresh_downloaded_files()
        
        # 初始化搜索控制变量
        self.search_thread = None
        self.cancel_search_flag = False
        
        # 更新状态
        self.paper_status_label.config(text="准备就绪")
    
    def cancel_search(self):
        """取消正在进行的搜索"""
        if self.search_thread and self.search_thread.is_alive():
            self.cancel_search_flag = True
            self.search_status_var.set("正在取消...")
            self.cancel_search_button.config(state="disabled")
            
    def search_papers(self):
        """搜索论文"""
        query = self.search_entry.get().strip()
        if not query:
            self.paper_status_label.config(text="请输入搜索关键词")
            return
        
        source = self.source_var.get()
        
        # 重置取消标志
        self.cancel_search_flag = False
        
        # 更新UI状态
        self.search_button.config(state="disabled")
        self.cancel_search_button.config(state="normal")
        self.search_status_var.set("搜索中...")
        self.search_progress.start(10)
        
        # 清空之前的结果
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 清空当前论文详情
        self.clear_paper_details()
        
        # 使用线程异步执行搜索
        self.search_thread = threading.Thread(target=self._execute_search, args=(query, source))
        self.search_thread.daemon = True
        self.search_thread.start()
    
    def _execute_search(self, query, source):
        """执行搜索操作"""
        # 当源为百度学术或中国知网时，直接在浏览器中打开
        if source == "百度学术":
            url = f"https://xueshu.baidu.com/s?wd={quote_plus(query)}"
            self.root.after(0, lambda: self.paper_status_label.config(text="百度学术搜索将在浏览器中打开"))
            self.root.after(0, lambda: self.search_button.config(state="normal"))
            self.root.after(0, lambda: self.cancel_search_button.config(state="disabled"))
            self.root.after(0, lambda: self.search_progress.stop())
            webbrowser.open(url)
            return
        
        elif source == "中国知网":
            url = f"https://kns.cnki.net/kns8/defaultresult/index?kw={quote_plus(query)}"
            self.root.after(0, lambda: self.paper_status_label.config(text="中国知网搜索将在浏览器中打开"))
            self.root.after(0, lambda: self.search_button.config(state="normal"))
            self.root.after(0, lambda: self.cancel_search_button.config(state="disabled"))
            self.root.after(0, lambda: self.search_progress.stop())
            webbrowser.open(url)
            return
        
        try:
            # 循环检查是否应该取消搜索
            def is_search_cancelled():
                return hasattr(self, 'cancel_search_flag') and self.cancel_search_flag

            # 延迟减少资源冲突
            time.sleep(0.1)
            
            # 检查是否需要取消
            if is_search_cancelled():
                self.root.after(0, lambda: self._handle_search_cancelled())
                return
                
            # 进行搜索
            try:
                results, message = self.paper_downloader.search_papers(query, source)
            except Exception as e:
                self.root.after(0, lambda: self._handle_search_error(f"搜索出错: {str(e)}"))
                return
                
            # 再次检查是否需要取消
            if is_search_cancelled():
                self.root.after(0, lambda: self._handle_search_cancelled())
                return
                
            # 处理搜索返回结果
            if isinstance(results, dict) and "error" in results:
                # 处理返回错误信息的情况
                error_message = results["error"]
                self.root.after(0, lambda: self._handle_search_error(error_message))
                return
                    
            elif isinstance(results, str):  
                # 如果返回的是错误信息字符串
                self.root.after(0, lambda: self._handle_search_error(results))
                return
                    
            if not results:
                self.root.after(0, lambda: self.paper_status_label.config(text=f"未找到与 '{query}' 相关的论文"))
                self.root.after(0, lambda: self.search_button.config(state="normal"))
                self.root.after(0, lambda: self.cancel_search_button.config(state="disabled"))
                self.root.after(0, lambda: self.search_progress.stop())
                return
                
            # 更新UI显示搜索结果
            self.root.after(0, lambda: self._update_search_results(results, query, source))
            
        except Exception as e:
            import traceback
            logging.error(f"搜索执行错误: {str(e)}")
            logging.error(traceback.format_exc())
            self.root.after(0, lambda: self._handle_search_error(f"搜索出错: {str(e)}"))

    def _handle_search_cancelled(self):
        """处理搜索被取消的情况"""
        self.paper_status_label.config(text="搜索已取消")
        self.search_button.config(state="normal")
        self.cancel_search_button.config(state="disabled")
        self.search_progress.stop()
        self.search_status_var.set("就绪")
        
    def _handle_search_error(self, error_msg):
        """处理搜索过程中的错误"""
        logging.error(f"搜索错误: {error_msg}")
        self.search_button.config(state="normal")
        self.cancel_search_button.config(state="disabled")
        self.paper_status_label.config(text=f"搜索出错: {error_msg}")
        self.search_progress.stop()
        self.search_status_var.set("出错")
        
        # 如果错误消息过长，截断显示并在详情区域显示完整信息
        if len(error_msg) > 60:
            self.paper_status_label.config(text=f"搜索出错: {error_msg[:60]}...")
            self.paper_details_text.delete(1.0, tk.END)
            self.paper_details_text.insert(tk.END, "搜索出错\n\n", "title")
            self.paper_details_text.insert(tk.END, f"错误详情: {error_msg}\n\n")
            self.paper_details_text.insert(tk.END, "建议:\n1. 检查网络连接\n2. 尝试使用其他搜索源\n3. 如使用Google Scholar，可能需要科学上网\n4. 尝试使用百度学术或中国知网")
        
        # 显示错误提示对话框
        self.root.after(100, lambda: messagebox.showerror("搜索错误", 
                                                       f"搜索过程中出错:\n{error_msg}\n\n建议尝试使用百度学术或中国知网搜索"))
    
    def _update_search_results(self, results, query, source):
        """更新搜索结果显示（UI线程安全）"""
        # 清空当前结果列表
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 存储搜索结果
        self.paper_results = results
        
        # 添加搜索结果到树形列表（分批处理以避免界面卡顿）
        def add_batch(start_idx, batch_size=5):
            end_idx = min(start_idx + batch_size, len(results))
            for i in range(start_idx, end_idx):
                paper = results[i]
                title = paper.get('title', 'Unknown Title')
                authors = paper.get('authors', 'Unknown Authors')
                year = paper.get('year', '')
                source_info = paper.get('source', 'Unknown Source')
                
                # 插入到树形列表
                self.results_tree.insert("", "end", values=(title, authors, year, source_info))
            
            # 如果还有更多结果，安排下一批处理
            if end_idx < len(results):
                self.root.after(10, lambda: add_batch(end_idx, batch_size))
            else:
                # 所有结果都处理完毕
                self.search_button.config(state="normal")
        
        # 开始分批处理
        add_batch(0)
        
        # 更新状态
        self.paper_status_label.config(text=f"找到 {len(results)} 篇与 '{query}' 相关的论文 (来源: {source})")
        
        # 重置选中的论文
        self.selected_paper = None
        
        # 禁用下载按钮
        self.download_button.config(state="disabled")
        self.open_browser_button.config(state="disabled")
        self.add_to_kb_button.config(state="disabled")
    
    def on_result_select(self, event):
        """处理搜索结果选择事件"""
        selection = self.results_tree.selection()
        if selection:
            item_id = selection[0]
            item_index = self.results_tree.index(item_id)
            
            if 0 <= item_index < len(self.paper_results):
                self.selected_paper = self.paper_results[item_index]
                
                # 更新状态标签
                title = self.selected_paper.get('title', 'Unknown Title')
                self.paper_status_label.config(text=f"已选择: {title}")
                
                # 启用下载按钮
                self.download_button.config(state="normal")
                self.open_browser_button.config(state="normal")
                self.add_to_kb_button.config(state="normal")
                
                # 显示论文摘要
                self.show_paper_details(self.selected_paper)
            else:
                self.selected_paper = None
                self.paper_status_label.config(text="无效的选择")
                
                # 禁用按钮
                self.download_button.config(state="disabled")
                self.open_browser_button.config(state="disabled")
                self.add_to_kb_button.config(state="disabled")
                
                # 清空摘要
                self.clear_paper_details()
        else:
            self.selected_paper = None
            
            # 禁用按钮
            self.download_button.config(state="disabled")
            self.open_browser_button.config(state="disabled")
            self.add_to_kb_button.config(state="disabled")
            
            # 清空摘要
            self.clear_paper_details()
    
    def download_selected_paper(self):
        """下载选中的论文"""
        if not self.selected_paper:
            self.paper_status_label.config(text="请先选择一篇论文")
            return
        
        # 获取PDF链接
        pdf_link = None
        direct_pdf_url = self.selected_paper.get('direct_pdf_url', '')
        arxiv_id = self.selected_paper.get('arxiv_id', '')
        doi = self.selected_paper.get('doi', '')
        
        # 如果是DOI，使用专门的DOI下载逻辑
        if doi:
            if self.selected_paper.get('source') == 'Sci-Hub' or 'doi.org' in self.selected_paper.get('url', ''):
                self.download_by_doi(doi)
                return
        
        # 如果是ArXiv，优先使用direct_pdf_url
        if arxiv_id:
            if direct_pdf_url:
                pdf_link = direct_pdf_url
            else:
                pdf_link = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        elif direct_pdf_url:
            pdf_link = direct_pdf_url
        else:
            # 查找其他可能的PDF链接
            pdf_link = self.selected_paper.get('pdf_link', '')
            if not pdf_link:
                url = self.selected_paper.get('url', '')
                if url and url.lower().endswith('.pdf'):
                    pdf_link = url
        
        # 如果没有找到PDF链接，提示用户
        if not pdf_link:
            self.paper_status_label.config(text="无法找到PDF下载链接，请尝试在浏览器中打开")
            return
        
        # 设置PDF链接
        self.selected_paper['pdf_link'] = pdf_link
        
        # 在单独的线程中执行下载，避免UI冻结
        download_thread = threading.Thread(target=self._execute_download)
        download_thread.daemon = True
        download_thread.start()
    
    def download_by_doi(self, doi):
        """通过DOI直接下载论文"""
        if not doi:
            self.paper_status_label.config(text="无效的DOI")
            return
            
        # 确保下载目录存在
        download_dir = "downloaded_papers"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # 更新UI状态
        self.paper_status_label.config(text=f"正在通过DOI下载: {doi}...")
        self.doi_button.config(state="disabled", text="正在下载...")
        
        # 创建论文数据用于展示
        mirrors = [
            "https://sci-hub.se",
            "https://sci-hub.ru",
            "https://sci-hub.st",
            "https://sci-hub.ren"
        ]
        
        # 更新详情显示
        self.paper_details_text.delete(1.0, tk.END)
        self.paper_details_text.insert(tk.END, f"正在下载 DOI: {doi}\n\n", "bold")
        self.paper_details_text.insert(tk.END, "来源: Sci-Hub\n\n")
        
        # 添加备用镜像链接
        self.paper_details_text.insert(tk.END, "备用Sci-Hub镜像链接 (如果自动下载失败，可点击手动打开):\n")
        for i, mirror in enumerate(mirrors):
            url = f"{mirror}/{doi}"
            tag_name = f"url={url}"
            self.paper_details_text.insert(tk.END, f"镜像 {i+1}: ")
            self.paper_details_text.insert(tk.END, url, ("link", tag_name))
            self.paper_details_text.insert(tk.END, "\n")
        
        # 使用线程进行下载
        download_thread = threading.Thread(target=lambda: self._execute_doi_download(doi))
        download_thread.daemon = True
        download_thread.start()
    
    def _execute_doi_download(self, doi):
        """执行DOI下载"""
        # 重置进度条
        self.root.after(0, lambda: self.download_progress.config(value=0))
        self.root.after(0, lambda: self.download_status.config(text="准备通过DOI下载..."))
        
        # Sci-Hub镜像列表 - 更新镜像列表
        success = False
        mirrors = ["sci-hub.se", "sci-hub.ru", "sci-hub.st", "sci-hub.ren", "sci-hub.ee", "sci-hub.wf"]
        
        # 准备文件名和路径
        filename = f"DOI_{doi.replace('/', '_')}.pdf"
        filepath = os.path.join("downloaded_papers", filename)
        
        # 如果文件已存在，添加序号
        if os.path.exists(filepath):
            counter = 1
            while os.path.exists(filepath):
                filepath = os.path.join("downloaded_papers", f"DOI_{doi.replace('/', '_')}_{counter}.pdf")
                counter += 1
        
        # 更完整的请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        # 尝试每个镜像
        error_message = ""
        found_html_no_pdf = False
        
        for i, mirror in enumerate(mirrors):
            if success:
                break
                
            # 计算基础进度值（基于当前镜像索引）
            base_progress = i * (100 // len(mirrors))  # 将总进度均匀分配到各个镜像
            self.root.after(0, lambda p=base_progress: self.download_progress.config(value=p))
            self.root.after(0, lambda m=mirror: self.download_status.config(
                text=f"尝试镜像 {m}..."))
                
            # 构建URL并尝试多种格式
            url_formats = [
                f"https://{mirror}/{doi}",  # 标准格式
                f"https://{mirror}/doi/{doi}"  # 某些镜像使用的格式
            ]
            
            for url_format in url_formats:
                if success:
                    break
                    
                try:
                    # 更新状态
                    self.root.after(0, lambda u=url_format: 
                        self.download_status.config(text=f"连接到 {u}..."))
                    
                    # 获取页面，使用更长的超时时间
                    response = requests.get(url_format, headers=headers, timeout=30, allow_redirects=True)
                    
                    if response.status_code == 200:
                        # 更新进度
                        progress_step = (100 // len(mirrors)) // 3  # 每个镜像进度的三分之一
                        self.root.after(0, lambda p=base_progress+progress_step: 
                            self.download_progress.config(value=p))
                        self.root.after(0, lambda: 
                            self.download_status.config(text=f"解析页面内容..."))
                        
                        # 解析页面寻找PDF
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 查找PDF内容的多种方式
                        pdf_src = None
                        
                        # 1. 查找标准PDF iframe
                        iframe = soup.find('iframe', id='pdf')
                        if iframe and iframe.has_attr('src'):
                            pdf_src = iframe['src']
                        
                        # 2. 如果没找到iframe，查找embed标签
                        if not pdf_src:
                            embed = soup.find('embed', attrs={'type': 'application/pdf'})
                            if embed and embed.has_attr('src'):
                                pdf_src = embed['src']
                        
                        # 3. 如果还没找到，查找链接到PDF的a标签
                        if not pdf_src:
                            pdf_links = soup.select('a[href$=".pdf"]')
                            if pdf_links:
                                pdf_src = pdf_links[0]['href']
                        
                        # 4. 查找包含"下载"或"download"的按钮/链接
                        if not pdf_src:
                            download_links = []
                            for a in soup.find_all('a'):
                                if a.get_text() and ('下载' in a.get_text() or 'download' in a.get_text().lower()):
                                    if a.has_attr('href'):
                                        download_links.append(a['href'])
                            
                            if download_links:
                                pdf_src = download_links[0]
                        
                        # 如果找到了PDF链接
                        if pdf_src:
                            # 格式化PDF URL
                            if pdf_src.startswith('//'):
                                pdf_src = 'https:' + pdf_src
                            elif not pdf_src.startswith(('http://', 'https://')):
                                # 确保链接格式正确
                                base_url = url_format
                                if '/' in base_url[8:]:  # 跳过 http(s)://
                                    base_url = '/'.join(base_url.split('/')[:-1]) + '/'
                                pdf_src = base_url + pdf_src.lstrip('/')
                            
                            # 更新进度
                            self.root.after(0, lambda p=base_progress+2*progress_step: 
                                self.download_progress.config(value=p))
                            self.root.after(0, lambda src=pdf_src: 
                                self.download_status.config(text=f"找到PDF链接，开始下载: {src[:50]}..."))
                            
                            # 设置重试机制下载PDF
                            pdf_retry_count = 0
                            max_pdf_retries = 2
                            
                            while pdf_retry_count < max_pdf_retries and not success:
                                try:
                                    # 下载PDF
                                    with requests.get(pdf_src, headers=headers, stream=True, timeout=40) as pdf_response:
                                        if pdf_response.status_code == 200:
                                            content_type = pdf_response.headers.get('Content-Type', '').lower()
                                            
                                            # 验证是否为PDF内容
                                            if 'application/pdf' in content_type or pdf_src.lower().endswith('.pdf'):
                                                # 获取文件大小
                                                total_size = int(pdf_response.headers.get('content-length', 0))
                                                
                                                # 保存文件
                                                with open(filepath, 'wb') as f:
                                                    downloaded = 0
                                                    for i, chunk in enumerate(pdf_response.iter_content(chunk_size=8192)):
                                                        if chunk:
                                                            f.write(chunk)
                                                            downloaded += len(chunk)
                                                            
                                                            # 更新进度条，但不要太频繁
                                                            if i % 10 == 0 and total_size > 0:
                                                                download_progress = base_progress + 2*progress_step + int((downloaded / total_size) * progress_step)
                                                                self.root.after(0, lambda p=download_progress: 
                                                                    self.download_progress.config(value=p))
                                                                self.root.after(0, lambda d=downloaded, t=total_size: 
                                                                    self.download_status.config(
                                                                        text=f"下载中: {d/1024/1024:.1f}MB / {t/1024/1024:.1f}MB"))
                                                
                                                # 验证文件
                                                if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:  # 确保至少10KB
                                                    success = True
                                                    
                                                    # 更新UI状态
                                                    self.root.after(0, lambda: self.download_progress.config(value=100))
                                                    self.root.after(0, lambda: self.download_status.config(
                                                        text=f"下载完成!"))
                                                    self.root.after(0, lambda: self.paper_status_label.config(
                                                        text=f"论文下载成功！DOI: {doi}, 已保存为: {os.path.basename(filepath)}"))
                                                    self.root.after(0, lambda: self.doi_button.config(
                                                        state="normal", text="通过DOI下载"))
                                                        
                                                    # 刷新文件列表并高亮显示下载文件
                                                    self.root.after(100, self.refresh_downloaded_files)
                                                    self.root.after(500, lambda: self._highlight_file(os.path.basename(filepath)))
                                                    
                                                    # 下载成功，返回结果
                                                    return {
                                                        "success": True,
                                                        "message": f"论文 DOI:{doi} 下载成功",
                                                        "file_path": filepath
                                                    }
                                                else:
                                                    # 文件下载失败或损坏
                                                    if os.path.exists(filepath):
                                                        os.remove(filepath)
                                                    error_message = f"从 {mirror} 下载的文件可能已损坏或过小"
                                            else:
                                                # 不是PDF内容
                                                error_message = f"从 {mirror} 获取的内容不是PDF (类型: {content_type})"
                                        else:
                                            error_message = f"从 {mirror} 下载PDF失败，状态码: {pdf_response.status_code}"
                                except Exception as e:
                                    error_message = f"从 {mirror} 下载PDF出错: {str(e)}"
                                
                                pdf_retry_count += 1
                                if pdf_retry_count < max_pdf_retries and not success:
                                    time.sleep(2)  # 重试前等待
                        else:
                            # 没有找到PDF iframe
                            found_html_no_pdf = True
                            error_message = f"{mirror} 返回了页面，但未找到PDF下载链接"
                    else:
                        # 请求失败
                        error_message = f"连接 {mirror} 失败，状态码: {response.status_code}"
                except requests.exceptions.SSLError:
                    error_message = f"{mirror} SSL证书验证失败"
                except requests.exceptions.ConnectionError:
                    error_message = f"连接 {mirror} 失败，请检查网络连接"
                except requests.exceptions.Timeout:
                    error_message = f"连接 {mirror} 超时，请稍后再试"
                except Exception as e:
                    # 捕获异常
                    error_message = f"从 {mirror} 下载时出错: {str(e)}"
        
        # 所有镜像都尝试失败
        self.root.after(0, lambda: self.download_progress.config(value=0))
        self.root.after(0, lambda: self.download_status.config(text="下载失败"))
        self.root.after(0, lambda: self.paper_status_label.config(
            text=f"无法通过DOI下载论文: {error_message}"))
        self.root.after(0, lambda: self.doi_button.config(
            state="normal", text="通过DOI下载"))
            
        # 构建替代链接
        alternative_mirrors = []
        for mirror in mirrors:
            alternative_mirrors.append(f"https://{mirror}/{doi}")
            
        # 添加其他可能的来源链接
        alternative_mirrors.append(f"https://doi.org/{doi}")  # 官方DOI解析器
        alternative_mirrors.append(f"https://www.crossref.org/openurl?pid=youremail@example.com&id=doi:{doi}")
        
        # 返回失败结果
        return {
            "success": False, 
            "message": f"无法通过DOI下载论文: {error_message}",
            "alternative_links": alternative_mirrors
        }
    
    def _execute_download(self):
        """在单独线程中执行下载，避免UI冻结"""
        try:
            # 清除进度条和更新状态
            self.download_progress["value"] = 0
            self.download_button.config(state="disabled")
            self.paper_status_label.config(text="准备下载...")
            
            # 检查PDF链接是否存在
            pdf_link = self.selected_paper.get('pdf_link', '')
            if not pdf_link:
                self.paper_status_label.config(text="无法找到PDF链接，下载失败")
                self.download_button.config(state="normal")
                return
                
            # 清理文件名中的非法字符
            def clean_filename(name):
                name = re.sub(r'[\\/*?:"<>|]', "_", name)
                return name.strip()
            
            # 根据选中的论文设置文件名
            title = self.selected_paper.get('title', 'unknown_paper')
            # 移除文件名中不合法的字符
            clean_title = clean_filename(title)
            # 如果文件名过长，截断它
            if len(clean_title) > 100:
                clean_title = clean_title[:100]
            
            # 设置保存目录
            if not os.path.exists(self.papers_dir):
                os.makedirs(self.papers_dir)
                
            # 构建文件路径
            file_path = os.path.join(self.papers_dir, f"{clean_title}.pdf")
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                counter = 1
                while os.path.exists(file_path):
                    file_path = os.path.join(self.papers_dir, f"{clean_title}_{counter}.pdf")
                    counter += 1
            
            # 更新UI状态
            self.paper_status_label.config(text=f"正在从 {pdf_link} 下载...")
            self.download_progress.start(10)  # 动画效果
            
            # 配置请求头 - 更全面的请求头配置
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'DNT': '1'
            }
            
            # 执行下载 - 改进错误处理和重试逻辑
            max_retries = 3
            retry_count = 0
            success = False
            error_message = ""
            
            while retry_count < max_retries and not success:
                try:
                    # 允许重定向
                    response = requests.get(
                        pdf_link, 
                        headers=headers, 
                        stream=True, 
                        timeout=45,  # 增加超时时间
                        allow_redirects=True  # 确保跟随重定向
                    )
                    
                    # 记录最终URL（处理重定向后）
                    final_url = response.url
                    
                    if response.status_code == 200:
                        # 检查内容类型
                        content_type = response.headers.get('Content-Type', '').lower()
                        
                        # 处理PDF内容
                        if 'application/pdf' in content_type or pdf_link.lower().endswith('.pdf') or final_url.lower().endswith('.pdf'):
                            # 获取总文件大小
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded = 0
                            
                            # 保存PDF文件
                            with open(file_path, 'wb') as f:
                                self.download_progress.stop()  # 停止不确定进度动画
                                
                                for i, chunk in enumerate(response.iter_content(chunk_size=8192)):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        
                                        # 更新进度条
                                        if i % 5 == 0 and total_size > 0:
                                            progress = int((downloaded / total_size) * 100)
                                            self.download_progress["value"] = progress
                                            self.download_status.config(
                                                text=f"下载中: {downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB"
                                            )
                                            # 允许UI更新
                                            self.root.update_idletasks()
                            
                            # 验证下载的文件
                            if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:  # 至少1KB
                                success = True
                                
                                # 更新状态
                                self.download_progress["value"] = 100
                                self.paper_status_label.config(text=f"下载完成: {os.path.basename(file_path)}")
                                self.download_status.config(text="下载成功!")
                                
                                # 记录下载路径以供后续使用
                                self.last_download_path = file_path
                                
                                # 刷新下载列表
                                self.refresh_downloaded_files()
                                self._highlight_file(os.path.basename(file_path))
                            else:
                                # 文件损坏或太小
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                error_message = "下载的文件可能已损坏或不完整"
                        else:
                            # 处理HTML响应 - 尝试从中提取PDF链接
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # 尝试寻找页面上的PDF链接
                            pdf_links = soup.select('a[href$=".pdf"]')
                            if pdf_links:
                                new_pdf_link = pdf_links[0]['href']
                                # 如果是相对链接，转为绝对链接
                                if not new_pdf_link.startswith(('http://', 'https://')):
                                    base_url = response.url
                                    if '/' in base_url[8:]:  # 跳过 http(s)://
                                        base_url = '/'.join(base_url.split('/')[:-1]) + '/'
                                    new_pdf_link = base_url + new_pdf_link.lstrip('/')
                                
                                # 更新链接并重试
                                pdf_link = new_pdf_link
                                retry_count += 1
                                self.paper_status_label.config(text=f"找到新的PDF链接，尝试下载: {pdf_link}")
                                continue
                            
                            # 没有找到PDF链接
                            error_message = f"响应内容不是PDF文件 (类型: {content_type})"
                            
                            # 如果看起来是学术网站的登录页面，提示用户
                            if '登录' in response.text or 'login' in response.text.lower() or 'sign in' in response.text.lower():
                                error_message = "需要登录才能访问此内容，请尝试在浏览器中手动打开"
                    else:
                        # 处理HTTP错误
                        if response.status_code == 403:
                            error_message = "访问被拒绝 (403 Forbidden)，可能需要登录或访问权限"
                        elif response.status_code == 404:
                            error_message = "未找到资源 (404 Not Found)，链接可能已失效"
                        elif response.status_code == 429:
                            error_message = "请求过多 (429 Too Many Requests)，请稍后再试"
                        elif 500 <= response.status_code < 600:
                            error_message = f"服务器错误 ({response.status_code})，请稍后再试"
                        else:
                            error_message = f"HTTP错误: {response.status_code}"
                
                except requests.exceptions.SSLError:
                    error_message = "SSL证书验证失败，请检查网络设置"
                except requests.exceptions.ConnectionError:
                    error_message = "连接错误，请检查网络连接"
                except requests.exceptions.Timeout:
                    error_message = "请求超时，请检查网络连接或稍后再试"
                except requests.exceptions.TooManyRedirects:
                    error_message = "重定向过多，请稍后再试"
                except requests.exceptions.RequestException as e:
                    error_message = f"请求错误: {str(e)}"
                except Exception as e:
                    error_message = f"下载过程中出错: {str(e)}"
                
                retry_count += 1
                if retry_count < max_retries and not success:
                    self.paper_status_label.config(text=f"下载失败，正在重试 ({retry_count}/{max_retries})...")
                    time.sleep(2)  # 重试前等待2秒
            
            # 如果所有尝试都失败
            if not success:
                self.download_progress.stop()
                self.paper_status_label.config(text=f"下载失败: {error_message}")
                
                # 尝试在浏览器中打开
                try:
                    import webbrowser
                    # 如果是PDF链接，直接打开
                    url_to_open = pdf_link
                    # 如果不是PDF，尝试找到更合适的URL打开
                    if not pdf_link.lower().endswith('.pdf'):
                        url_to_open = self.selected_paper.get('url', '') or pdf_link
                    
                    # 确认打开浏览器
                    if messagebox.askyesno("下载失败", 
                                         f"下载失败: {error_message}\n\n是否在浏览器中打开链接尝试手动下载?"):
                        webbrowser.open(url_to_open)
                        self.paper_status_label.config(text="已在浏览器中打开链接")
                except Exception as e:
                    self.paper_status_label.config(text=f"无法打开浏览器: {str(e)}")
            
            # 恢复按钮状态
            self.download_button.config(state="normal")
            
        except Exception as e:
            # 处理任何其他异常
            self.paper_status_label.config(text=f"下载过程中出现意外错误: {str(e)}")
            self.download_progress.stop()
            self.download_button.config(state="normal")
    
    def refresh_downloaded_files(self):
        """刷新已下载文件列表"""
        try:
            # 清空当前列表
            self.downloaded_files_list.delete(0, tk.END)
            
            # 检查下载目录是否存在
            if not os.path.exists(self.papers_dir):
                os.makedirs(self.papers_dir)
                return
            
            # 获取所有PDF文件
            pdf_files = [f for f in os.listdir(self.papers_dir) 
                        if f.lower().endswith('.pdf')]
            
            # 按修改时间排序（最新的在前）
            pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.papers_dir, x)), 
                          reverse=True)
            
            # 添加到列表
            for pdf_file in pdf_files:
                self.downloaded_files_list.insert(tk.END, pdf_file)
                
            # 更新状态
            self.paper_status_label.config(text=f"找到 {len(pdf_files)} 个已下载的PDF文件")
            
        except Exception as e:
            self.paper_status_label.config(text=f"刷新文件列表时出错: {str(e)}")

    def _handle_download_result(self, result):
        """处理下载结果，更新UI"""
        # 恢复UI状态
        self.download_progress.stop()
        self.download_button.config(state="normal")
        
        if result["success"]:
            # 下载成功
            self.paper_status_label.config(text=result["message"])
            
            # 保存最后下载的文件路径
            self.last_download_path = result.get("file_path", "")
            
            # 刷新文件列表并高亮新下载的文件
            self.refresh_downloaded_files()
            if "file_path" in result:
                self._highlight_file(os.path.basename(result["file_path"]))
        else:
            # 下载失败
            self.paper_status_label.config(text=result["message"])
            
            # 如果有替代链接建议，显示它们
            alternative_links = result.get("alternative_links", [])
            if alternative_links:
                links_text = "\n".join(alternative_links)
                message = f"下载失败。请尝试以下链接:\n{links_text}"
                self.show_message("下载失败", message)
    
    def on_file_select(self, event):
        """处理文件选择事件"""
        try:
            # 获取选中项
            selection = self.downloaded_files_list.curselection()
            if not selection:
                return
                
            # 获取文件名
            index = selection[0]
            filename = self.downloaded_files_list.get(index)
            
            # 更新状态标签
            file_path = os.path.join(self.papers_dir, filename)
            file_size = os.path.getsize(file_path) / 1024  # KB
            
            # 显示文件信息
            if file_size > 1024:
                size_str = f"{file_size/1024:.2f} MB"
            else:
                size_str = f"{file_size:.2f} KB"
                
            # 显示文件信息
            self.paper_status_label.config(text=f"已选择: {filename} ({size_str})")
            
        except Exception as e:
            self.paper_status_label.config(text=f"无法获取文件信息: {str(e)}")

    def on_file_double_click(self, event):
        """双击文件时的处理"""
        try:
            self.open_selected_file()
        except Exception as e:
            self.paper_status_label.config(text=f"打开文件时出错: {str(e)}")
    
    def open_selected_file(self):
        """打开当前选中的文件"""
        # 获取选中的文件
        selection = self.downloaded_files_list.curselection()
        if not selection:
            self.paper_status_label.config(text="请先选择一个文件")
            return
            
        # 获取文件路径
        index = selection[0]
        filename = self.downloaded_files_list.get(index)
        file_path = os.path.join(self.papers_dir, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.paper_status_label.config(text="文件不存在，请刷新列表")
            return
            
        # 调用打开文件方法
        self.open_file(file_path)
    
    def open_file(self, file_path):
        """根据操作系统打开文件"""
        try:
            if sys.platform.startswith('win'):
                os.startfile(file_path)
            elif sys.platform.startswith('darwin'):  # macOS
                subprocess.call(['open', file_path])
            else:  # Linux
                subprocess.call(['xdg-open', file_path])
        except Exception as e:
            self.paper_status_label.config(text=f"无法打开文件: {str(e)}")
    
    def open_papers_folder(self):
        """打开论文下载文件夹"""
        try:
            papers_dir = self.paper_downloader.papers_dir
            
            if not os.path.exists(papers_dir):
                os.makedirs(papers_dir)
            
            self.open_file(papers_dir)
            self.paper_status_label.config(text=f"已打开下载文件夹")
        except Exception as e:
            self.paper_status_label.config(text=f"打开文件夹出错: {str(e)}")
    
    def send_message(self, event=None):
        message = self.user_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        # 清空输入
        self.user_input.delete("1.0", tk.END)
        
        # 更新对话历史
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, "用户: " + message + "\n\n")
        
        # 添加到历史数据
        self.chat_history_data.append({"user": message})
        
        # 调用AI API
        self.chat_history.insert(tk.END, "AI助手: 正在思考...\n\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)
        
        # 启动线程处理API请求
        Thread(target=self.process_api_request, args=(message,)).start()
    
    def process_api_request(self, message):
        # 获取选择的API类型
        api_type = self.api_var.get()
        
        # 检查是否需要使用知识库增强
        use_knowledge = hasattr(self, 'use_knowledge_var') and self.use_knowledge_var.get()
        knowledge_context = ""
        
        if use_knowledge:
            # 从知识库获取相关上下文
            knowledge_context = self.knowledge_manager.get_knowledge_context(message)
            if knowledge_context:
                # 将知识库上下文加入到提示中
                message = knowledge_context + "\n\n基于以上知识库信息，请回答: " + message
        
        # 调用API
        response = self.api_manager.call_api(api_type, message, self.chat_history_data)
        
        # 添加到历史数据
        self.chat_history_data.append({"assistant": response})
        
        # 更新对话历史
        self.chat_history.config(state=tk.NORMAL)
        # 删除"正在思考..."
        self.chat_history.delete(float(self.chat_history.index(tk.END)) - 3.0, tk.END)
        # 添加回复
        self.chat_history.insert(tk.END, "AI助手: " + response + "\n\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)
    
    def clear_chat(self):
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.config(state=tk.DISABLED)
    
    def upload_to_knowledge_base(self):
        files = filedialog.askopenfilenames(title="选择文件上传到知识库", 
                                          filetypes=[("文本文件", "*.txt"), 
                                                     ("PDF文件", "*.pdf"),
                                                     ("Word文件", "*.docx"),
                                                     ("所有文件", "*.*")])
        if files:
            # 创建知识库目录
            os.makedirs("knowledge_base", exist_ok=True)
            
            for file in files:
                # 拷贝文件到知识库
                import shutil
                filename = os.path.basename(file)
                destination = os.path.join("knowledge_base", filename)
                shutil.copy2(file, destination)
            
            messagebox.showinfo("上传成功", f"已上传 {len(files)} 个文件到知识库")
            self.refresh_knowledge_list()
    
    def manage_knowledge_base(self):
        if not os.path.exists("knowledge_base"):
            messagebox.showinfo("提示", "知识库为空")
            return
            
        selected = self.knowledge_list.curselection()
        if not selected:
            messagebox.showinfo("提示", "请先选择文件")
            return
            
        file = self.knowledge_list.get(selected[0])
        answer = messagebox.askyesno("确认", f"是否删除文件 {file}?")
        if answer:
            os.remove(os.path.join("knowledge_base", file))
            self.refresh_knowledge_list()
    
    def refresh_knowledge_list(self):
        """刷新知识库文件列表"""
        # 清空当前列表
        self.knowledge_list.delete(0, tk.END)
        
        # 获取选中的分区
        category = self.selected_category.get()
        
        # 获取文件列表
        if category == "全部":
            files = self.knowledge_manager.get_files_by_category()
        else:
            files = self.knowledge_manager.get_files_by_category(category)
        
        # 用于保存文件ID映射
        self.knowledge_files_map = {}
        
        # 添加文件到列表中
        if files:
            for i, file_info in enumerate(files):
                display_name = file_info.get('title', file_info.get('filename', '未知文件'))
                # 存储文件ID到映射中
                self.knowledge_list.insert(tk.END, display_name)
                # 存储文件ID到字典中，以索引为键
                self.knowledge_files_map[i] = file_info.get('file_id')
        else:
            self.knowledge_list.insert(tk.END, f"{'当前分区为空' if category != '全部' else '知识库为空'}")
        
        # 清空详情和预览
        self.clear_file_details()
        
        # 禁用删除按钮
        self.delete_button.config(state="disabled")
    
    def on_knowledge_file_select(self, event):
        """处理知识库文件选择事件"""
        # 获取选中的索引
        selection = self.knowledge_list.curselection()
        if not selection:
            return
        
        index = selection[0]
        # 获取文件ID
        try:
            # 从字典中获取文件ID
            file_id = self.knowledge_files_map.get(index)
            if not file_id:
                # 如果没有文件ID，可能是空提示信息
                self.clear_file_details()
                return
                
            # 获取文件信息
            file_info = self.knowledge_manager.get_file_info(file_id)
            if not file_info:
                self.clear_file_details()
                return
                
            # 更新详情显示
            self.file_title_label.config(text=f"标题: {file_info.get('title', '未知')}")
            self.file_authors_label.config(text=f"作者: {file_info.get('authors', '未知')}")
            self.file_year_label.config(text=f"年份: {file_info.get('year', '未知')}")
            self.file_category_label.config(text=f"分区: {file_info.get('category', '其他')}")
            self.file_path_label.config(text=f"路径: {file_info.get('path', '未知')}")
            
            # 尝试显示预览
            self.load_file_preview(file_info)
            
            # 启用删除按钮
            self.delete_button.config(state="normal")
        except Exception as e:
            print(f"文件选择出错: {str(e)}")
            self.clear_file_details()
    
    def clear_file_details(self):
        """清空文件详情和预览"""
        self.file_title_label.config(text="标题: ")
        self.file_authors_label.config(text="作者: ")
        self.file_year_label.config(text="年份: ")
        self.file_category_label.config(text="分区: ")
        self.file_path_label.config(text="路径: ")
        self.preview_text.delete(1.0, tk.END)
    
    def load_file_preview(self, file_info):
        """加载文件预览"""
        self.preview_text.delete(1.0, tk.END)
        
        # 尝试加载文件摘要或内容
        if 'abstract' in file_info and file_info['abstract']:
            self.preview_text.insert(tk.END, "摘要:\n", "heading")
            self.preview_text.insert(tk.END, file_info['abstract'] + "\n\n")
        
        if 'summary' in file_info and file_info['summary']:
            self.preview_text.insert(tk.END, "概要:\n", "heading")
            self.preview_text.insert(tk.END, file_info['summary'] + "\n\n")
        
        # 配置样式
        self.preview_text.tag_configure("heading", font=("Arial", 10, "bold"))
    
    def open_knowledge_file(self, event):
        """打开选中的知识库文件"""
        # 获取选中的索引
        selection = self.knowledge_list.curselection()
        if not selection:
            return
        
        index = selection[0]
        # 获取文件ID
        try:
            # 从字典中获取文件ID
            file_id = self.knowledge_files_map.get(index)
            if not file_id:
                return
                
            # 获取文件信息
            file_info = self.knowledge_manager.get_file_info(file_id)
            if not file_info or 'path' not in file_info:
                return
                
            # 打开文件
            self.open_file(file_info['path'])
        except Exception as e:
            print(f"打开文件出错: {str(e)}")
    
    def delete_from_knowledge_base(self):
        """从知识库中删除选中文件"""
        # 获取选中的索引
        selection = self.knowledge_list.curselection()
        if not selection:
            return
        
        index = selection[0]
        # 获取文件ID
        try:
            # 从字典中获取文件ID
            file_id = self.knowledge_files_map.get(index)
            if not file_id:
                return
                
            # 确认删除
            if not messagebox.askyesno("确认删除", "确定要从知识库中删除此文件吗？"):
                return
                
            # 删除文件
            success = self.knowledge_manager.remove_file(file_id)
            if success:
                messagebox.showinfo("删除成功", "文件已从知识库中删除")
                # 刷新列表
                self.refresh_knowledge_list()
            else:
                messagebox.showerror("删除失败", "无法删除文件，请检查文件是否被占用")
        except Exception as e:
            messagebox.showerror("删除错误", f"删除过程中出错: {str(e)}")

    def open_directory(self, path):
        """打开目录"""
        if os.path.exists(path):
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':  # macOS
                os.system(f'open "{path}"')
            else:  # Linux
                os.system(f'xdg-open "{path}"')
        else:
            messagebox.showinfo("提示", "目录不存在")
    
    def refresh_api_list(self):
        """刷新API列表"""
        self.api_manager.load_other_apis()
        self.api_choices = self.api_manager.get_available_apis()
        self.api_dropdown['values'] = self.api_choices
        messagebox.showinfo("成功", "API列表已刷新")
    
    def save_settings(self):
        settings = {
            "openai": {
                "api_key": self.openai_key.get(),
                "model": self.openai_model.get()
            },
            "azure": {
                "api_key": self.azure_key.get(),
                "endpoint": self.azure_endpoint.get(),
                "deployment": self.azure_deployment.get()
            },
            "deepseek": {
                "api_key": self.deepseek_key.get(),
                "model": self.deepseek_model.get(),
                "base_url": self.deepseek_url.get()
            },
            "local": {
                "api": self.local_api.get()
            }
        }
        
        # 更新API管理器中的设置
        self.api_manager.settings.update(settings)
        self.api_manager.save_settings()
        
        messagebox.showinfo("成功", "设置已保存")
    
    def load_settings(self):
        try:
            if os.path.exists("config/settings.json"):
                with open("config/settings.json", "r") as f:
                    settings = json.load(f)
                
                if "openai" in settings:
                    self.openai_key.delete(0, tk.END)
                    self.openai_key.insert(0, settings["openai"].get("api_key", ""))
                    
                    self.openai_model.delete(0, tk.END)
                    self.openai_model.insert(0, settings["openai"].get("model", "gpt-4"))
                
                if "azure" in settings:
                    self.azure_key.delete(0, tk.END)
                    self.azure_key.insert(0, settings["azure"].get("api_key", ""))
                    
                    self.azure_endpoint.delete(0, tk.END)
                    self.azure_endpoint.insert(0, settings["azure"].get("endpoint", ""))
                    
                    self.azure_deployment.delete(0, tk.END)
                    self.azure_deployment.insert(0, settings["azure"].get("deployment", ""))

                if "deepseek" in settings:
                    self.deepseek_key.delete(0, tk.END)
                    self.deepseek_key.insert(0, settings["deepseek"].get("api_key", ""))
                    
                    self.deepseek_model.delete(0, tk.END)
                    self.deepseek_model.insert(0, settings["deepseek"].get("model", "deepseek-chat"))
                    
                    self.deepseek_url.delete(0, tk.END)
                    self.deepseek_url.insert(0, settings["deepseek"].get("base_url", "https://api.deepseek.com/v1"))
                
                if "local" in settings:
                    self.local_api.delete(0, tk.END)
                    self.local_api.insert(0, settings["local"].get("api", "http://localhost:8000/v1"))
        except Exception as e:
            print(f"加载设置时出错: {e}")

    def open_url(self, event):
        """打开链接URL"""
        try:
            index = self.paper_details_text.index(f"@{event.x},{event.y}")
            # 获取点击位置的标签
            tags = self.paper_details_text.tag_names(index)
            
            # 查找链接URL
            for tag in tags:
                if tag.startswith("url="):
                    url = tag[4:]  # 移除 "url=" 前缀
                    webbrowser.open(url)
                    self.paper_status_label.config(text=f"已在浏览器中打开链接")
                    break
            
            # 检查是否点击了带有"link"标签的文本，但没有url=前缀
            if "link" in tags and not any(tag.startswith("url=") for tag in tags):
                # 尝试获取当前选中的文本
                try:
                    start = self.paper_details_text.index(f"{index} linestart")
                    end = self.paper_details_text.index(f"{index} lineend")
                    line_text = self.paper_details_text.get(start, end)
                    
                    # 尝试提取URL样式的文本
                    url_match = re.search(r'https?://\S+', line_text)
                    if url_match:
                        url = url_match.group(0)
                        webbrowser.open(url)
                        self.paper_status_label.config(text=f"已在浏览器中打开链接")
                except:
                    pass
        except Exception as e:
            self.paper_status_label.config(text=f"打开链接出错: {str(e)}")

    def quick_access(self, event=None):
        """快速下载DOI或ArXiv ID"""
        input_text = self.doi_entry.get().strip()
        if not input_text:
            self.paper_status_label.config(text="请输入DOI、ArXiv ID或URL")
            return

        # 检查是否是ArXiv ID
        arxiv_id = None
        # 常见的ArXiv ID格式: 2201.08239 或 arxiv:2201.08239
        arxiv_pattern = r'(?:arxiv:)?(\d{4}\.\d{5}|\d{4}\.\d{4,5}v\d+)'
        arxiv_match = re.search(arxiv_pattern, input_text, re.IGNORECASE)
        
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            # 调用ArXiv下载处理
            self.paper_status_label.config(text=f"检测到ArXiv ID: {arxiv_id}，正在准备下载...")
            # 创建测试论文数据
            test_paper = {
                'title': f'ArXiv Paper: {arxiv_id}',
                'authors': 'Unknown',
                'pdf_link': f'https://arxiv.org/pdf/{arxiv_id}.pdf',
                'url': f'https://arxiv.org/abs/{arxiv_id}',
                'abstract': 'Abstract not available',
                'source': 'ArXiv'
            }
            self.selected_paper = test_paper
            self.download_selected_paper()
            return
        
        # 提取DOI - 首先尝试直接匹配
        doi_match = re.search(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", input_text, re.IGNORECASE)
        
        # 如果没有直接匹配到DOI，尝试解析URL中的DOI
        if not doi_match:
            # 尝试从URL路径中提取
            url_match = re.search(r"https?://[^\s]+", input_text)
            if url_match:
                url = url_match.group(0)
                try:
                    from urllib.parse import urlparse, unquote
                    parsed_url = urlparse(url)
                    # 检查路径中的DOI
                    path = unquote(parsed_url.path)
                    doi_in_path = re.search(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", path, re.IGNORECASE)
                    if doi_in_path:
                        doi_match = doi_in_path
                    else:
                        # 检查查询参数中的DOI
                        query = unquote(parsed_url.query)
                        doi_in_query = re.search(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", query, re.IGNORECASE)
                        if doi_in_query:
                            doi_match = doi_in_query
                except:
                    pass
        
        # 如果仍然没有找到DOI
        if not doi_match:
            self.paper_status_label.config(text="无法识别DOI或ArXiv ID，请确认输入格式正确")
            return
            
        # 提取匹配的DOI
        doi = doi_match.group(1)
        
        # 清理DOI（删除末尾的标点符号）
        doi = re.sub(r'[.,;]$', '', doi)
        
        # 创建测试论文数据
        test_paper = {
            'title': f'DOI: {doi}',
            'authors': 'Unknown',
            'doi': doi,
            'url': f'https://doi.org/{doi}',
            'abstract': 'Abstract not available',
            'source': 'DOI'
        }
        self.selected_paper = test_paper
        self.paper_status_label.config(text=f"检测到DOI: {doi}，正在准备下载...")
        # 尝试通过DOI下载
        self.download_selected_paper()

    def test_download_function(self):
        """测试下载功能是否工作正常"""
        # 创建一个确定能正常下载的测试数据
        test_paper = {
            'title': 'Test Paper From ArXiv',
            'authors': 'Test Author',
            'pdf_link': 'https://arxiv.org/pdf/2201.08239.pdf',  # 一个确定有效的ArXiv论文
            'url': 'https://arxiv.org/abs/2201.08239',
            'abstract': 'Test abstract',
            'source': 'Test'
        }
        
        # 设置为当前选中的论文
        self.selected_paper = test_paper
        
        # 手动确认下载目录存在
        download_dir = "downloaded_papers"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # 更新UI状态
        self.paper_status_label.config(text="正在测试下载功能，下载ArXiv上的测试论文...")
        
        # 确认PaperDownloader使用正确的目录
        self.paper_downloader.papers_dir = download_dir
        
        # 禁用按钮避免重复点击
        self.test_download_button.config(state="disabled", text="正在测试下载...")
        
        # 使用线程来执行下载
        download_thread = threading.Thread(target=self._test_download_execute)
        download_thread.daemon = True
        download_thread.start()
        
        # 切换到文献下载标签页
        self.tabs.select(self.paper_tab)

    def _test_download_execute(self):
        """执行测试下载"""
        try:
            # 重置进度条
            self.root.after(0, lambda: self.download_progress.config(value=0))
            self.root.after(0, lambda: self.download_status.config(text="准备下载测试文件..."))
            
            # 直接使用requests下载文件，绕过可能的问题
            # 使用更可靠的arxiv论文ID
            arxiv_id = "2201.08239"
            url = f'https://arxiv.org/pdf/{arxiv_id}.pdf'
            
            # 更全面的请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            # 设置文件名和路径
            filename = "Test_Download_Success.pdf"
            filepath = os.path.join("downloaded_papers", filename)
            
            # 如果文件已存在，先删除
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
                
            # 直接下载
            self.root.after(0, lambda: self.download_progress.config(value=20))
            self.root.after(0, lambda: self.download_status.config(
                text="连接到 ArXiv 服务器..."))
            
            # 设置重试机制
            max_retries = 3
            retry_count = 0
            success = False
            error_message = ""
            
            while retry_count < max_retries and not success:
                try:
                    response = requests.get(
                        url, 
                        headers=headers, 
                        stream=True, 
                        timeout=45,  # 增加超时时间
                        allow_redirects=True
                    )
                    
                    if response.status_code == 200:
                        # 验证内容类型
                        content_type = response.headers.get('Content-Type', '').lower()
                        if 'application/pdf' not in content_type and not url.lower().endswith('.pdf'):
                            self.root.after(0, lambda: self.download_status.config(
                                text=f"内容类型不是PDF: {content_type}"))
                            retry_count += 1
                            continue
                            
                        # 获取文件大小
                        total_size = int(response.headers.get('content-length', 0))
                        
                        with open(filepath, 'wb') as f:
                            downloaded = 0
                            for i, chunk in enumerate(response.iter_content(chunk_size=8192)):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    
                                    # 更新进度条，但不要太频繁
                                    if i % 10 == 0 and total_size > 0:
                                        progress = 20 + int((downloaded / total_size) * 80)
                                        self.root.after(0, lambda p=progress: self.download_progress.config(value=p))
                                        self.root.after(0, lambda d=downloaded, t=total_size: self.download_status.config(
                                            text=f"下载中: {d/1024/1024:.1f}MB / {t/1024/1024:.1f}MB"))
                        
                        # 验证文件
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:  # 确保文件至少有10KB
                            # 下载成功，更新UI
                            success = True
                            self.root.after(0, lambda: self.download_progress.config(value=100))
                            self.root.after(0, lambda: self.download_status.config(
                                text=f"测试下载成功!"))
                            self.root.after(0, lambda: self.paper_status_label.config(
                                text=f"测试下载成功！文件已保存为：{filename} ({os.path.getsize(filepath)/1024:.1f} KB)"))
                            self.root.after(0, lambda: self.test_download_button.config(
                                state="normal", text="测试下载功能"))
                        else:
                            # 文件下载但可能损坏
                            if os.path.exists(filepath):
                                os.remove(filepath)
                            self.root.after(0, lambda: self.download_status.config(text="下载的文件可能已损坏"))
                            error_message = "下载的文件可能已损坏或不完整"
                            retry_count += 1
                    else:
                        # 下载失败，尝试备用链接
                        if retry_count == 0:
                            # 第一次失败，尝试备用链接
                            url = f"https://arxiv.org/pdf/{arxiv_id}" # 无.pdf后缀，让服务器处理
                            retry_count += 1
                            self.root.after(0, lambda: self.download_status.config(
                                text=f"第一次尝试失败 ({response.status_code})，使用备用链接..."))
                            continue
                        
                        # 下载失败
                        self.root.after(0, lambda: self.download_status.config(
                            text=f"下载失败: {response.status_code}"))
                        error_message = f"HTTP状态码：{response.status_code}"
                        retry_count += 1
                
                except (requests.RequestException, IOError) as e:
                    # 网络错误或文件错误
                    error_message = str(e)
                    self.root.after(0, lambda err=error_message: self.download_status.config(
                        text=f"下载错误: {err}"))
                    retry_count += 1
                    time.sleep(2)  # 等待后重试
            
            # 处理最终结果
            if not success:
                self.root.after(0, lambda: self.download_progress.config(value=0))
                self.root.after(0, lambda err=error_message: self.download_status.config(
                    text=f"下载失败: {err}"))
                self.root.after(0, lambda err=error_message: self.paper_status_label.config(
                    text=f"测试下载失败：{err}"))
                self.root.after(0, lambda: self.test_download_button.config(
                    state="normal", text="测试下载功能"))
            
            # 刷新文件列表
            self.root.after(100, self.refresh_downloaded_files)
            
            # 如果成功，高亮显示下载的文件
            if success:
                self.root.after(500, lambda: self._highlight_file(filename))
                
        except Exception as e:
            # 发生错误
            error_details = f"{type(e).__name__}: {str(e)}"
            self.root.after(0, lambda: self.download_progress.config(value=0))
            self.root.after(0, lambda: self.download_status.config(text="下载出错"))
            self.root.after(0, lambda err=error_details: self.paper_status_label.config(
                text=f"测试下载出错: {err}"))
            self.root.after(0, lambda: self.test_download_button.config(
                state="normal", text="测试下载功能"))
    
    def _highlight_file(self, filename):
        """高亮显示文件列表中的特定文件"""
        try:
            # 查找文件在列表中的位置
            for i in range(self.downloaded_files_list.size()):
                if self.downloaded_files_list.get(i) == filename:
                    # 清除所有选择
                    self.downloaded_files_list.selection_clear(0, tk.END)
                    # 选中目标文件
                    self.downloaded_files_list.selection_set(i)
                    # 滚动使其可见
                    self.downloaded_files_list.see(i)
                    # 高亮显示（不是所有平台支持）
                    try:
                        self.downloaded_files_list.itemconfig(i, {'bg': '#e0f0ff'})
                        # 3秒后恢复正常背景
                        self.root.after(3000, lambda idx=i: 
                                       self.downloaded_files_list.itemconfig(idx, {'bg': ''}))
                    except:
                        pass  # 如果不支持背景色更改，忽略错误
                    break
        except Exception as e:
            print(f"高亮文件时出错: {str(e)}")

    def open_url_in_browser(self, event=None):
        """在浏览器中打开论文链接"""
        if not self.selected_paper:
            self.paper_status_label.config(text="请先选择一篇论文")
            return
        
        url = self.selected_paper.get('browser_url', '') or self.selected_paper.get('url', '') or self.selected_paper.get('pdf_link', '')
        
        if not url:
            self.paper_status_label.config(text="没有可用的链接")
            return
        
        # 更新状态
        self.paper_status_label.config(text=f"正在尝试在浏览器中打开链接...")
        
        # 使用线程打开浏览器，避免阻塞UI
        def open_browser_thread():
            try:
                # 设置超时时间
                timer = threading.Timer(15, lambda: self.root.after(0, lambda: self.paper_status_label.config(text="打开链接超时，请手动复制链接: " + url)))
                timer.start()
                
                # 尝试打开浏览器
                webbrowser.open(url)
                
                # 如果成功打开，取消超时计时器
                timer.cancel()
                self.root.after(0, lambda: self.paper_status_label.config(text=f"已在浏览器中打开链接"))
                
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.paper_status_label.config(text=f"打开链接出错: {error_msg}"))
        
        # 创建并启动线程
        browser_thread = threading.Thread(target=open_browser_thread)
        browser_thread.daemon = True
        browser_thread.start()

    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.paper_status_label.config(text="已复制到剪贴板")

    def show_message(self, title, message):
        """显示消息对话框"""
        messagebox.showinfo(title, message)

    def show_paper_details(self, paper):
        """显示论文详细信息"""
        if not hasattr(self, 'paper_details_text'):
            return
            
        # 清空当前内容
        self.paper_details_text.delete(1.0, tk.END)
        
        # 添加标题
        title = paper.get('title', '未知标题')
        self.paper_details_text.insert(tk.END, f"{title}\n\n", "title")
        
        # 添加作者
        authors = paper.get('authors', '未知作者')
        self.paper_details_text.insert(tk.END, "作者: ", "heading")
        self.paper_details_text.insert(tk.END, f"{authors}\n\n")
        
        # 添加年份
        year = paper.get('year', '未知年份')
        self.paper_details_text.insert(tk.END, "年份: ", "heading")
        self.paper_details_text.insert(tk.END, f"{year}\n\n")
        
        # 添加来源
        source = paper.get('source', '未知来源')
        self.paper_details_text.insert(tk.END, "来源: ", "heading")
        self.paper_details_text.insert(tk.END, f"{source}\n\n")
        
        # 添加摘要
        abstract = paper.get('abstract', '')
        if abstract:
            self.paper_details_text.insert(tk.END, "摘要: \n", "heading")
            self.paper_details_text.insert(tk.END, f"{abstract}\n\n")
        
        # 添加链接
        url = paper.get('url', '')
        if url:
            self.paper_details_text.insert(tk.END, "链接: \n", "heading")
            # 创建带有URL标签的链接文本
            tag_name = f"url={url}"
            self.paper_details_text.tag_configure(tag_name, foreground="blue", underline=1)
            self.paper_details_text.insert(tk.END, f"{url}\n\n", ("link", tag_name))
        
        # 添加PDF链接（如果有）
        pdf_link = paper.get('pdf_link', '')
        if pdf_link and pdf_link != url:
            self.paper_details_text.insert(tk.END, "PDF链接: \n", "heading")
            # 创建带有URL标签的PDF链接文本
            tag_name = f"url={pdf_link}"
            self.paper_details_text.tag_configure(tag_name, foreground="blue", underline=1)
            self.paper_details_text.insert(tk.END, f"{pdf_link}\n\n", ("link", tag_name))
        
        # 添加DOI
        doi = paper.get('doi', '')
        if doi:
            self.paper_details_text.insert(tk.END, "DOI: ", "heading")
            doi_url = f"https://doi.org/{doi}"
            tag_name = f"url={doi_url}"
            self.paper_details_text.tag_configure(tag_name, foreground="blue", underline=1)
            self.paper_details_text.insert(tk.END, f"{doi}\n\n", ("link", tag_name))
        
        # 添加ArXiv ID
        arxiv_id = paper.get('arxiv_id', '')
        if arxiv_id:
            self.paper_details_text.insert(tk.END, "ArXiv ID: ", "heading")
            arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
            tag_name = f"url={arxiv_url}"
            self.paper_details_text.tag_configure(tag_name, foreground="blue", underline=1)
            self.paper_details_text.insert(tk.END, f"{arxiv_id}\n\n", ("link", tag_name))
        
        # 其他元数据
        if 'citations' in paper:
            self.paper_details_text.insert(tk.END, "引用数: ", "heading")
            self.paper_details_text.insert(tk.END, f"{paper['citations']}\n\n")
        
        if 'categories' in paper:
            self.paper_details_text.insert(tk.END, "分类: ", "heading")
            self.paper_details_text.insert(tk.END, f"{paper['categories']}\n\n")

    def clear_paper_details(self):
        """清空论文详情显示"""
        if hasattr(self, 'paper_details_text'):
            self.paper_details_text.delete(1.0, tk.END)

    def add_paper_to_kb(self):
        """将当前选中的论文添加到知识库"""
        if not self.selected_paper:
            self.paper_status_label.config(text="请先选择一篇论文")
            return
        
        # 检查是否已下载
        if not hasattr(self, "last_download_path") or not self.last_download_path:
            # 如果没有下载记录，尝试先下载
            self.paper_status_label.config(text="正在尝试下载论文...")
            self.download_selected_paper()
            
            # 添加延时，等待下载完成
            def delayed_add():
                if hasattr(self, "last_download_path") and self.last_download_path and os.path.exists(self.last_download_path):
                    self.select_category_for_paper(self.last_download_path, self.selected_paper)
                else:
                    self.paper_status_label.config(text="请先下载论文，然后再添加到知识库")
            
            self.root.after(3000, delayed_add)  # 等待3秒
            return
        
        if not os.path.exists(self.last_download_path):
            self.paper_status_label.config(text="下载文件不存在，请重新下载")
            return
        
        # 打开分区选择对话框
        self.select_category_for_paper(self.last_download_path, self.selected_paper)

    def add_downloaded_to_kb(self):
        """将已下载的论文添加到知识库"""
        # 获取选中的文件
        selection = self.downloaded_files_list.curselection()
        if not selection:
            self.paper_status_label.config(text="请先选择已下载的论文")
            return
        
        # 获取文件路径
        index = selection[0]
        filename = self.downloaded_files_list.get(index)
        file_path = os.path.join(self.papers_dir, filename)
        
        if not os.path.exists(file_path):
            self.paper_status_label.config(text="文件不存在，请刷新列表")
            return
        
        # 尝试提取论文元数据（简单实现）
        paper_data = self.extract_paper_metadata(filename)
        
        # 打开分区选择对话框
        self.select_category_for_paper(file_path, paper_data)

    def extract_paper_metadata(self, filename):
        """从文件名尝试提取论文元数据"""
        paper_data = {
            'title': filename,
            'authors': '未知作者',
            'year': '',
            'source': '本地文件'
        }
        
        # 尝试从文件名提取更多信息
        # 例如： Title_Author_2022.pdf 格式
        parts = os.path.splitext(filename)[0].split('_')
        if len(parts) >= 3:
            year_match = re.search(r'(19|20)\d{2}', parts[-1])
            if year_match:
                paper_data['year'] = year_match.group(0)
                paper_data['authors'] = parts[-2]
                paper_data['title'] = '_'.join(parts[:-2])
        elif len(parts) == 2:
            # Title_Author.pdf
            paper_data['title'] = parts[0]
            paper_data['authors'] = parts[1]
        
        return paper_data

    def select_category_for_paper(self, file_path, paper_data):
        """显示分区选择对话框"""
        try:
            # 确保知识库管理器已初始化
            if not hasattr(self, 'knowledge_manager'):
                self.knowledge_manager = KnowledgeManager()
                
            # 创建对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("选择知识库分区")
            dialog.geometry("450x350")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 设置最小尺寸
            dialog.minsize(450, 350)
            
            # 添加对话框内容
            main_frame = ttk.Frame(dialog, padding="10")
            main_frame.pack(fill="both", expand=True)
            
            # 显示论文信息
            info_frame = ttk.LabelFrame(main_frame, text="论文信息")
            info_frame.pack(fill="x", padx=5, pady=5)
            
            title = paper_data.get('title', os.path.basename(file_path))
            authors = paper_data.get('authors', '未知作者')
            
            title_label = ttk.Label(info_frame, text=f"标题: {title}", wraplength=400)
            title_label.pack(anchor="w", padx=5, pady=2)
            
            authors_label = ttk.Label(info_frame, text=f"作者: {authors}", wraplength=400)
            authors_label.pack(anchor="w", padx=5, pady=2)
            
            if 'year' in paper_data and paper_data['year']:
                year_label = ttk.Label(info_frame, text=f"年份: {paper_data['year']}")
                year_label.pack(anchor="w", padx=5, pady=2)
            
            # 文件路径信息
            path_label = ttk.Label(info_frame, text=f"文件: {os.path.basename(file_path)}", wraplength=400)
            path_label.pack(anchor="w", padx=5, pady=2)
            
            # 分区选择
            category_frame = ttk.LabelFrame(main_frame, text="选择分区")
            category_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # 创建滚动区域以适应大量分类
            canvas = tk.Canvas(category_frame)
            scrollbar = ttk.Scrollbar(category_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # 获取分类列表，如果categories属性不存在，创建一个默认列表
            if not hasattr(self.knowledge_manager, 'categories') or not self.knowledge_manager.categories:
                self.knowledge_manager.categories = ["论文", "学习笔记", "教程", "书籍", "其他"]
            
            # 默认选择"论文"分类
            category_var = tk.StringVar(value="论文")
            
            # 添加分类选项
            for category in self.knowledge_manager.categories:
                rb = ttk.Radiobutton(scrollable_frame, text=category, value=category, variable=category_var)
                rb.pack(anchor="w", padx=5, pady=3)
            
            # 添加"新建分类"选项
            new_category_frame = ttk.Frame(main_frame)
            new_category_frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(new_category_frame, text="新建分类:").pack(side="left", padx=2)
            new_category_entry = ttk.Entry(new_category_frame, width=20)
            new_category_entry.pack(side="left", padx=2, fill="x", expand=True)
            
            def add_new_category():
                new_cat = new_category_entry.get().strip()
                if new_cat and new_cat not in self.knowledge_manager.categories:
                    self.knowledge_manager.categories.append(new_cat)
                    rb = ttk.Radiobutton(scrollable_frame, text=new_cat, value=new_cat, variable=category_var)
                    rb.pack(anchor="w", padx=5, pady=3)
                    category_var.set(new_cat)
                    new_category_entry.delete(0, tk.END)
            
            ttk.Button(new_category_frame, text="添加", command=add_new_category).pack(side="left", padx=2)
            
            # 按钮区域
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x", padx=5, pady=10)
            
            # 确定按钮
            def confirm():
                try:
                    selected_category = category_var.get()
                    
                    # 检查知识库路径
                    kb_path = self.knowledge_manager.knowledge_base_dir
                    if not os.path.exists(kb_path):
                        os.makedirs(kb_path, exist_ok=True)
                    
                    # 显示进度信息
                    self.paper_status_label.config(text=f"正在添加到知识库: {selected_category}...")
                    
                    # 添加到知识库
                    success, new_filename = self.knowledge_manager.add_paper_to_knowledge_base(
                        file_path, paper_data, selected_category)
                    
                    if success:
                        self.paper_status_label.config(text=f"已成功添加到知识库: {selected_category}")
                        
                        # 刷新知识库列表（如果在知识库选项卡中）
                        if hasattr(self, 'knowledge_list') and self.knowledge_list:
                            self.refresh_knowledge_list()
                            
                        dialog.destroy()
                        self.show_message("添加成功", f"论文已成功添加到知识库\n分类: {selected_category}\n文件: {new_filename}")
                    else:
                        self.paper_status_label.config(text="添加到知识库失败")
                        messagebox.showerror("添加失败", "无法添加文件到知识库，请检查文件和权限。")
                except Exception as e:
                    self.paper_status_label.config(text=f"添加到知识库时出错: {str(e)}")
                    messagebox.showerror("错误", f"添加到知识库时出错:\n{str(e)}")
                    dialog.destroy()
            
            ttk.Button(button_frame, text="确定", command=confirm).pack(side="right", padx=5, pady=5)
            ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="right", padx=5, pady=5)
            
            # 显示对话框
            dialog.wait_window()
        except Exception as e:
            self.paper_status_label.config(text=f"打开分区选择对话框时出错: {str(e)}")
            messagebox.showerror("错误", f"无法打开分区选择对话框:\n{str(e)}")

    def _handle_download_exception(self, e, url, filepath=None):
        """处理下载过程中可能出现的各种异常情况，提供更详细的错误信息和建议
        
        Args:
            e: 异常对象
            url: 正在下载的URL
            filepath: 可能已部分下载的文件路径
            
        Returns:
            tuple: (错误消息, 错误标题, 是否可能为权限问题)
        """
        error_type = type(e).__name__
        error_message = str(e)
        error_title = "下载错误"
        permission_issue = False
        
        # 清理可能已部分下载的文件
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
                
        # 根据异常类型处理不同的错误情况
        if isinstance(e, requests.exceptions.SSLError):
            error_message = f"SSL证书验证失败。可能原因：\n1. 网络连接不安全\n2. 系统日期时间设置错误\n3. SSL证书已过期"
            error_title = "SSL证书错误"
            
        elif isinstance(e, requests.exceptions.ConnectionError):
            error_message = f"连接错误。可能原因：\n1. 网络连接不稳定\n2. 目标服务器无法访问\n3. 防火墙阻止了连接"
            error_title = "连接错误"
            
        elif isinstance(e, requests.exceptions.Timeout):
            error_message = f"请求超时。可能原因：\n1. 网络速度较慢\n2. 服务器响应时间过长\n3. 文件太大，下载超时"
            error_title = "请求超时"
            
        elif isinstance(e, requests.exceptions.TooManyRedirects):
            error_message = f"重定向过多。可能原因：\n1. URL重定向循环\n2. 服务器配置错误"
            error_title = "重定向错误"
            
        elif isinstance(e, requests.exceptions.HTTPError):
            status_code = e.response.status_code if hasattr(e, 'response') and hasattr(e.response, 'status_code') else "未知"
            
            if status_code == 403:
                error_message = f"访问被拒绝 (403 Forbidden)。可能原因：\n1. 需要登录凭证\n2. IP被禁止\n3. 地理位置限制"
                error_title = "访问被拒绝"
                permission_issue = True
                
            elif status_code == 404:
                error_message = f"资源未找到 (404 Not Found)。可能原因：\n1. URL错误\n2. 文件已被移除\n3. 资源不存在"
                error_title = "资源未找到"
                
            elif status_code == 429:
                error_message = f"请求过多 (429 Too Many Requests)。可能原因：\n1. 短时间内发送了太多请求\n2. IP被限流\n3. 需要等待一段时间再试"
                error_title = "请求频率限制"
                
            elif 500 <= status_code < 600:
                error_message = f"服务器错误 ({status_code})。可能原因：\n1. 服务器内部错误\n2. 服务器过载\n3. 服务器维护中"
                error_title = "服务器错误"
                
            else:
                error_message = f"HTTP错误: {status_code}。URL: {url}"
                error_title = "HTTP错误"
        
        elif isinstance(e, IOError) and ("Permission" in str(e) or "拒绝访问" in str(e)):
            error_message = f"文件系统权限错误。可能原因：\n1. 没有写入权限\n2. 文件被其他程序占用\n3. 系统限制"
            error_title = "权限错误"
            permission_issue = True
            
        elif "Memory" in error_type or "内存" in error_message:
            error_message = f"内存不足。可能原因：\n1. 文件太大\n2. 系统资源不足\n3. 其他程序占用内存"
            error_title = "内存错误"
            
        # 提供建议解决方案
        suggestions = [
            "1. 检查网络连接是否稳定",
            "2. 尝试使用VPN或代理服务",
            "3. 直接通过浏览器手动下载",
            "4. 尝试其他文献来源",
            "5. 检查系统时间设置是否正确"
        ]
        
        if permission_issue:
            suggestions.extend([
                "6. 确保应用有足够的文件访问权限",
                "7. 以管理员身份运行程序",
                "8. 关闭可能占用文件的程序"
            ])
            
        full_message = f"{error_message}\n\n建议解决方案:\n" + "\n".join(suggestions)
        
        # 记录异常
        logging.error(f"下载异常: {error_title} - {error_type}: {error_message}")
        logging.error(f"URL: {url}")
        
        return full_message, error_title, permission_issue

def set_console_encoding():
    """设置控制台编码，确保正确显示中文"""
    try:
        if sys.platform == 'win32':
            # Windows平台下设置控制台编码
            import ctypes
            # 设置控制台代码页为UTF-8
            ctypes.windll.kernel32.SetConsoleCP(65001)  # 设置控制台输入代码页为UTF-8
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)  # 设置控制台输出代码页为UTF-8
            
            # 确保sys.stdout使用UTF-8编码
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            
            print("控制台编码已设置为UTF-8")
    except Exception as e:
        print(f"设置控制台编码时出错: {str(e)}")

def main():
    """主程序入口点"""
    # 检查命令行参数
    import sys
    test_mode = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-download":
            test_mode = True

    # 创建主窗口
    root = tk.Tk()
    root.title("AI对话助手 - 论文下载工具")
    
    # 调整初始窗口大小
    root.geometry("1000x800")
    
    # 初始化应用
    app = AIAssistant(root)
    
    # 如果指定了测试下载，则在加载后自动执行测试
    if test_mode:
        root.after(1000, app.test_download_function)
        # 切换到文献下载标签页
        app.tabs.select(app.paper_tab)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    # 设置控制台编码
    set_console_encoding()
    
    # 检查并修复可能的编码问题
    check_encoding_issues()
    
    # 确保下载目录存在
    if not os.path.exists("downloaded_papers"):
        os.makedirs("downloaded_papers", exist_ok=True)
    
    # 创建测试下载批处理文件
    create_test_batch_file()
    
    # 运行主程序
    main() 