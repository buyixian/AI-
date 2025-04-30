import paper_downloader_fixed
import ai_assistant
import traceback
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread, Lock
import time
import webbrowser
from urllib.parse import quote_plus
import queue

def test_app_search():
    """在简化的应用程序环境中测试学术搜索功能"""
    try:
        print("正在初始化简化的应用程序...")
        
        # 创建主窗口
        root = tk.Tk()
        root.title("测试应用 - 学术搜索")
        root.geometry("850x650")
        
        # 创建消息队列用于线程间通信
        message_queue = queue.Queue()
        
        # 创建搜索框和按钮
        frame = ttk.Frame(root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加标题
        title_label = ttk.Label(frame, text="论文搜索系统", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, padx=5, pady=10, sticky="w")
        
        ttk.Label(frame, text="搜索关键词:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        search_entry = ttk.Entry(frame, width=40)
        search_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        search_entry.insert(0, "机器学习")
        
        # 状态标签和进度条
        status_frame = ttk.Frame(frame)
        status_frame.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        status_var = tk.StringVar()
        status_var.set("就绪")
        status_label = ttk.Label(status_frame, textvariable=status_var)
        status_label.pack(side=tk.LEFT)
        
        progress = ttk.Progressbar(status_frame, orient="horizontal", length=100, mode="indeterminate")
        progress.pack(side=tk.LEFT, padx=(10, 0))
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(frame, text="搜索结果", padding="10")
        result_frame.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        result_text = tk.Text(result_frame, wrap=tk.WORD, width=90, height=28, yscrollcommand=scrollbar.set)
        result_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=result_text.yview)
        
        # 使结果区域可以点击打开链接
        result_text.tag_configure("link", foreground="blue", underline=1)
        result_text.tag_configure("title", font=("Arial", 10, "bold"))
        result_text.bind("<Button-1>", lambda e: open_link(e, result_text))
        
        # 初始化下载器和状态变量
        downloader = paper_downloader_fixed.PaperDownloader()
        search_thread = None
        thread_lock = Lock()
        cancel_search = False
        
        # 打开链接的函数
        def open_link(event, text_widget):
            index = text_widget.index(f"@{event.x},{event.y}")
            for tag in text_widget.tag_names(index):
                if tag.startswith("link-"):
                    url = tag.split("-", 1)[1]
                    webbrowser.open(url)
                    break
        
        # 处理消息队列的函数
        def process_queue():
            try:
                while not message_queue.empty():
                    message_type, data = message_queue.get_nowait()
                    
                    if message_type == "status":
                        status_var.set(data)
                    elif message_type == "progress_start":
                        progress.start(10)
                    elif message_type == "progress_stop":
                        progress.stop()
                    elif message_type == "enable_search":
                        search_button.config(state="normal")
                    elif message_type == "disable_search":
                        search_button.config(state="disabled")
                    elif message_type == "enable_cancel":
                        cancel_button.config(state="normal")
                    elif message_type == "disable_cancel":
                        cancel_button.config(state="disabled")
                    elif message_type == "clear_results":
                        result_text.delete(1.0, tk.END)
                    elif message_type == "append_result":
                        result_text.insert(tk.END, data)
                    elif message_type == "append_link":
                        url, text = data
                        url_tag = f"link-{url}"
                        result_text.insert(tk.END, text, (url_tag, "link"))
                        result_text.tag_bind(url_tag, "<Button-1>", lambda e: webbrowser.open(url))
                    elif message_type == "append_title":
                        result_text.insert(tk.END, data, "title")
                    elif message_type == "error":
                        messagebox.showerror("搜索错误", data)
                    elif message_type == "browser_open":
                        webbrowser.open(data)
            except Exception as e:
                print(f"处理消息队列出错: {str(e)}")
            
            # 安排下一次处理（100毫秒）
            root.after(100, process_queue)
        
        # 异步搜索函数
        def search_async():
            nonlocal search_thread, cancel_search
            
            query = search_entry.get().strip()
            selected_source = source_var.get()
            
            if not query:
                message_queue.put(("status", "请输入搜索关键词"))
                return
            
            # 如果有正在运行的搜索，先停止它
            with thread_lock:
                if search_thread and search_thread.is_alive():
                    cancel_search = True
                    message_queue.put(("status", "正在取消先前的搜索..."))
                    return
                
                cancel_search = False
            
            # 更新UI状态
            message_queue.put(("disable_search", None))
            message_queue.put(("enable_cancel", None))
            message_queue.put(("status", "搜索中..."))
            message_queue.put(("progress_start", None))
            message_queue.put(("clear_results", None))
            message_queue.put(("append_result", f"正在搜索: {query}\n来源: {selected_source}\n\n"))
            
            # 特殊处理百度学术和中国知网
            if selected_source == "百度学术":
                def direct_baidu_search():
                    try:
                        url = f"https://xueshu.baidu.com/s?wd={quote_plus(query)}"
                        message_queue.put(("clear_results", None))
                        message_queue.put(("append_title", f"百度学术搜索: {query}\n\n"))
                        message_queue.put(("append_result", "由于API限制，将在浏览器中打开百度学术搜索结果。\n\n"))
                        message_queue.put(("append_result", "点击打开: "))
                        message_queue.put(("append_link", (url, url)))
                        message_queue.put(("browser_open", url))
                        message_queue.put(("enable_search", None))
                        message_queue.put(("disable_cancel", None))
                        message_queue.put(("status", "已在浏览器中打开"))
                        message_queue.put(("progress_stop", None))
                    except Exception as e:
                        message_queue.put(("error", f"打开百度学术时出错: {str(e)}"))
                
                # 在线程中执行以避免UI阻塞
                Thread(target=direct_baidu_search, daemon=True).start()
                return
            
            elif selected_source == "中国知网":
                def direct_cnki_search():
                    try:
                        url = f"https://kns.cnki.net/kns8/defaultresult/index?kw={quote_plus(query)}"
                        message_queue.put(("clear_results", None))
                        message_queue.put(("append_title", f"中国知网搜索: {query}\n\n"))
                        message_queue.put(("append_result", "由于API限制，将在浏览器中打开中国知网搜索结果。\n\n"))
                        message_queue.put(("append_result", "点击打开: "))
                        message_queue.put(("append_link", (url, url)))
                        message_queue.put(("browser_open", url))
                        message_queue.put(("enable_search", None))
                        message_queue.put(("disable_cancel", None))
                        message_queue.put(("status", "已在浏览器中打开"))
                        message_queue.put(("progress_stop", None))
                    except Exception as e:
                        message_queue.put(("error", f"打开中国知网时出错: {str(e)}"))
                
                # 在线程中执行以避免UI阻塞
                Thread(target=direct_cnki_search, daemon=True).start()
                return
            
            # 创建异步线程
            def search_thread_func():
                nonlocal cancel_search
                
                try:
                    # 延迟减少资源冲突
                    time.sleep(0.1)
                    
                    # 执行搜索
                    results, message = downloader.search_papers(query, selected_source)
                    
                    # 检查是否取消
                    with thread_lock:
                        if cancel_search:
                            message_queue.put(("clear_results", None))
                            message_queue.put(("append_result", "搜索已取消\n"))
                            message_queue.put(("enable_search", None))
                            message_queue.put(("disable_cancel", None))
                            message_queue.put(("status", "已取消"))
                            message_queue.put(("progress_stop", None))
                            return
                    
                    # 结果数据分批次处理，防止UI阻塞
                    message_queue.put(("clear_results", None))
                    message_queue.put(("append_title", f"搜索状态: {message}\n"))
                    message_queue.put(("append_result", f"找到 {len(results)} 个结果\n\n"))
                    
                    # 分批处理结果，每次最多处理5个结果
                    for i, paper in enumerate(results[:10], 1):
                        # 检查是否取消
                        with thread_lock:
                            if cancel_search:
                                message_queue.put(("append_result", "\n搜索过程被取消\n"))
                                break
                        
                        message_queue.put(("append_title", f"结果 {i}:\n"))
                        message_queue.put(("append_result", f"  标题: {paper.get('title', '无标题')}\n"))
                        message_queue.put(("append_result", f"  作者: {paper.get('authors', '未知作者')}\n"))
                        message_queue.put(("append_result", f"  年份: {paper.get('year', '未知年份')}\n"))
                        
                        # 显示引用次数和期刊信息（如果有）
                        if 'citations' in paper and paper['citations'] != 'N/A':
                            message_queue.put(("append_result", f"  引用次数: {paper.get('citations', '未知')}\n"))
                        if 'venue' in paper and paper['venue']:
                            message_queue.put(("append_result", f"  发表于: {paper.get('venue', '未知')}\n"))
                        
                        # 显示摘要
                        abstract = paper.get('abstract', '无摘要')
                        if abstract and len(abstract) > 150:
                            abstract = abstract[:150] + "..."
                        message_queue.put(("append_result", f"  摘要: {abstract}\n"))
                        
                        # 显示链接
                        url = paper.get('url', '')
                        if url:
                            message_queue.put(("append_result", f"  链接: "))
                            message_queue.put(("append_link", (url, url)))
                            message_queue.put(("append_result", "\n"))
                        else:
                            message_queue.put(("append_result", f"  链接: 无链接\n"))
                        
                        message_queue.put(("append_result", "-" * 80 + "\n\n"))
                        
                        # 适当延迟，让UI有时间更新
                        time.sleep(0.01)
                    
                    if len(results) > 10:
                        message_queue.put(("append_result", f"（仅显示前10个结果，共找到 {len(results)} 个结果）\n\n"))
                    
                    # 更新UI状态
                    message_queue.put(("enable_search", None))
                    message_queue.put(("disable_cancel", None))
                    message_queue.put(("status", "搜索完成"))
                    message_queue.put(("progress_stop", None))
                    
                except Exception as e:
                    message_queue.put(("append_result", f"搜索过程中出错: {str(e)}\n"))
                    message_queue.put(("enable_search", None))
                    message_queue.put(("disable_cancel", None))
                    message_queue.put(("status", "搜索出错"))
                    message_queue.put(("progress_stop", None))
                    message_queue.put(("error", f"搜索过程中出错:\n{str(e)}"))
                    traceback.print_exc()
            
            # 启动搜索线程
            search_thread = Thread(target=search_thread_func, daemon=True)
            search_thread.start()
        
        # 取消搜索
        def cancel_search_func():
            nonlocal cancel_search
            with thread_lock:
                cancel_search = True
            message_queue.put(("status", "正在取消搜索..."))
            message_queue.put(("disable_cancel", None))
        
        # 按钮框架
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=2, padx=5, pady=5)
        
        # 搜索按钮
        search_button = ttk.Button(button_frame, text="搜索", command=search_async, width=8)
        search_button.pack(side=tk.LEFT, padx=2)
        
        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=cancel_search_func, width=8, state="disabled")
        cancel_button.pack(side=tk.LEFT, padx=2)
        
        # 添加搜索源选择
        source_frame = ttk.LabelFrame(frame, text="搜索源", padding="5")
        source_frame.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        
        sources = ["Google Scholar", "百度学术", "中国知网", "Arxiv", "Semantic Scholar", "IEEE Xplore", "PubMed"]
        source_var = tk.StringVar(value=sources[0])
        
        # 单选按钮组
        for i, source in enumerate(sources):
            ttk.Radiobutton(source_frame, text=source, variable=source_var, value=source).grid(
                row=0, column=i, padx=10, pady=5, sticky="w")
        
        # 添加搜索提示
        tip_frame = ttk.Frame(frame)
        tip_frame.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        
        ttk.Label(tip_frame, text="提示:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(tip_frame, text="1. 使用引号可以进行精确搜索，例如 \"深度学习\"", font=("Arial", 9)).pack(side=tk.LEFT)
        ttk.Label(tip_frame, text="2. 百度学术和中国知网将在浏览器中打开", font=("Arial", 9)).pack(side=tk.LEFT, padx=(15,0))
        
        # 设置框架比例
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)
        
        # 执行初始搜索（延迟执行，等界面完全加载）
        def delayed_search():
            message_queue.put(("status", "准备初始搜索..."))
            # 进一步延迟初始搜索以确保UI完全加载
            root.after(800, search_async)
        
        # 绑定回车键搜索
        def on_enter(event):
            search_async()
        
        search_entry.bind("<Return>", on_enter)
        
        # 启动消息队列处理器
        process_queue()
        
        # 延迟开始初始搜索
        root.after(1000, delayed_search)
        
        # 设置关闭窗口的处理
        def on_closing():
            nonlocal cancel_search
            # 确保停止所有线程
            with thread_lock:
                cancel_search = True
            root.destroy()
            sys.exit(0)
            
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 绑定鼠标滚轮事件，让文本区域可以滚动
        def on_mousewheel(event):
            # 处理Windows上的鼠标滚轮事件
            result_text.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # 绑定鼠标滚轮事件
        result_text.bind("<MouseWheel>", on_mousewheel)
        
        print("应用程序初始化完成，启动主循环...")
        root.mainloop()
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        traceback.print_exc()
        messagebox.showerror("程序错误", f"程序初始化失败:\n{str(e)}")

if __name__ == "__main__":
    test_app_search() 