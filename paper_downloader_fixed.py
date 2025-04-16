import os
import re
import json
import time
import requests
import hashlib
import logging
import traceback
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PaperDownloader')

class PaperDownloader:
    def __init__(self, papers_dir="papers"):
        # 创建论文下载目录
        self.papers_dir = papers_dir
        os.makedirs(papers_dir, exist_ok=True)
        
        # 存储搜索结果
        self.search_results = []
        
        # 支持的来源
        self.sources = ["Arxiv", "Sci-Hub", "Google Scholar", "IEEE Xplore", "PubMed", "Semantic Scholar"]
        
        # 初始化会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_papers(self, query, source="Arxiv"):
        """搜索论文"""
        self.search_results = []
        message = ""
        
        try:
            logging.info(f"开始搜索: {query}, 来源: {source}")
            
            if source == "Arxiv":
                results, message = self._search_arxiv(query)
            elif source == "Sci-Hub":
                results, message = self._search_scihub(query)
            elif source == "Google Scholar":
                results, message = self._search_google_scholar(query)
            elif source == "IEEE Xplore":
                results, message = self._search_ieee(query)
            elif source == "PubMed":
                results, message = self._search_pubmed(query)
            elif source == "Semantic Scholar":
                try:
                    # 为Semantic Scholar搜索添加额外的超时保护
                    import threading
                    import time
                    
                    result_container = []
                    error_container = []
                    
                    def search_with_timeout():
                        try:
                            res, msg = self._search_semantic_scholar(query)
                            result_container.append((res, msg))
                        except Exception as e:
                            error_container.append(str(e))
                    
                    # 创建线程并设置超时
                    thread = threading.Thread(target=search_with_timeout)
                    thread.daemon = True
                    thread.start()
                    
                    # 等待最多3秒
                    thread.join(3)
                    
                    if thread.is_alive():
                        # 如果线程还在运行，说明超时了
                        logging.warning("Semantic Scholar搜索请求超时")
                        results, message = self._semantic_scholar_fallback(query, "搜索请求超时")
                    elif result_container:
                        results, message = result_container[0]
                    elif error_container:
                        logging.error(f"Semantic Scholar搜索错误: {error_container[0]}")
                        results, message = self._semantic_scholar_fallback(query, error_container[0])
                    else:
                        logging.error("Semantic Scholar搜索未知错误")
                        results, message = self._semantic_scholar_fallback(query, "未知错误")
                except Exception as e:
                    logging.error(f"Semantic Scholar搜索线程错误: {str(e)}")
                    results, message = self._semantic_scholar_fallback(query, str(e))
            else:
                logging.warning(f"不支持的搜索源: {source}")
                return [], "不支持的来源"
            
            # 确保结果是列表类型
            if not isinstance(results, list):
                if isinstance(results, dict) and "error" in results:
                    # 返回错误信息
                    logging.error(f"搜索返回错误: {results['error']}")
                    return results, message
                else:
                    results = [results] if results else []
                
            self.search_results = results
            logging.info(f"搜索完成, 找到 {len(results)} 个结果, 消息: {message}")
            return results, message
            
        except Exception as e:
            error_msg = f"搜索出错: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            # 返回一个空列表和错误消息
            return [], error_msg
    
    def _search_arxiv(self, query, max_results=20):
        """搜索Arxiv论文，使用REST API并用BeautifulSoup解析XML"""
        try:
            # 使用Arxiv API
            encoded_query = quote_plus(query)
            url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}"
            
            response = self.session.get(url)
            if response.status_code != 200:
                return [], f"API请求失败，状态码: {response.status_code}"
            
            # 使用BeautifulSoup解析XML
            soup = BeautifulSoup(response.text, 'xml')
            if soup is None:
                # 如果xml解析器不可用，尝试html解析器
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取所有entry标签
            entries = soup.find_all('entry')
            if not entries:
                return [], "未找到匹配的论文"
            
            results = []
            for entry in entries:
                # 提取标题
                title_tag = entry.find('title')
                title = title_tag.text.strip() if title_tag else "未知标题"
                
                # 提取作者
                authors = []
                author_tags = entry.find_all('author')
                for author_tag in author_tags:
                    name_tag = author_tag.find('name')
                    if name_tag:
                        authors.append(name_tag.text.strip())
                author_text = ", ".join(authors) if authors else "未知作者"
                
                # 提取发布日期
                published_tag = entry.find('published')
                pub_date = published_tag.text.strip()[:4] if published_tag else "未知日期"
                
                # 提取PDF链接
                pdf_url = ""
                for link in entry.find_all('link'):
                    if link.get('title') == 'pdf':
                        pdf_url = link.get('href', '')
                        break
                
                # 提取摘要
                summary_tag = entry.find('summary')
                abstract = summary_tag.text.strip() if summary_tag else "无摘要"
                
                # 提取ID
                id_tag = entry.find('id')
                arxiv_id = id_tag.text if id_tag else ""
                
                results.append({
                    'title': title,
                    'authors': author_text,
                    'year': pub_date,
                    'url': pdf_url,
                    'abstract': abstract,
                    'source': 'Arxiv',
                    'id': arxiv_id,
                    'arxiv_id': arxiv_id.split('/')[-1] if arxiv_id else ""
                })
            
            return results, f"在Arxiv上找到 {len(results)} 篇相关论文"
            
        except Exception as e:
            return [], f"Arxiv搜索出错: {str(e)}"
    
    def _search_scihub(self, query, max_results=10):
        """搜索Sci-Hub论文（通过DOI或标题）"""
        # 简化实现，仅返回一个包含查询的结果
        try:
            results = [{
                'title': f"搜索: {query}",
                'authors': "未知作者",
                'year': "未知年份",
                'url': f"https://sci-hub.se/{query}",
                'abstract': "Sci-Hub搜索结果",
                'source': 'Sci-Hub',
                'id': query
            }]
            return results, "通过Sci-Hub搜索"
                
        except Exception as e:
            return [], f"Sci-Hub搜索出错: {str(e)}"
    
    def _search_google_scholar(self, query):
        """从Google Scholar搜索论文（优先在线搜索，提供明确提示）"""
        logging.info(f"尝试从Google Scholar搜索: {query}")
        
        try:
            # 设置UserAgent列表，模拟正常浏览器
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
            ]
            
            # 随机选择UA并设置请求头
            import random
            selected_ua = random.choice(user_agents)
            self.session.headers.update({'User-Agent': selected_ua})
            
            # 构建搜索URL（增加随机参数避免模式识别）
            timestamp = int(time.time())
            search_url = f"https://scholar.google.com/scholar?q={quote_plus(query)}&hl=zh-CN&as_sdt=0,5&as_vis=1&gs_t={timestamp}"
            
            # 设置超时和重试参数
            max_retries = 2
            timeout = 10
            
            # 记录连接尝试
            for attempt in range(max_retries):
                try:
                    logging.info(f"Google Scholar在线搜索尝试 {attempt+1}/{max_retries}")
                    
                    # 添加延迟以模拟人类行为
                    if attempt > 0:
                        delay = 2 + random.random() * 2  # 2-4秒随机延迟
                        logging.info(f"添加{delay:.1f}秒延迟后重试")
                        time.sleep(delay)
                    
                    # 进行请求
                    response = self.session.get(search_url, timeout=timeout)
                    
                    # 检查是否被重定向到验证页面
                    if "检查您的网络安全" in response.text or "verify you're a human" in response.text:
                        logging.warning("Google Scholar 请求被重定向到验证页面")
                        # 不立即切换到离线模式，而是告知用户需要验证
                        return self._return_captcha_message(query)
                    
                    if response.status_code == 200:
                        # 尝试解析结果
                        soup = BeautifulSoup(response.text, 'html.parser')
                        results = []
                        
                        # 查找所有论文条目
                        articles = soup.select("div.gs_r.gs_or.gs_scl")
                        if not articles:
                            articles = soup.select("div.gs_ri")  # 尝试替代选择器
                        
                        if not articles:
                            logging.warning("无法解析Google Scholar页面结构")
                            return self._return_no_parse_message(query)
                        
                        # 提取论文信息
                        for article in articles:
                            result = {}
                            
                            # 提取标题
                            title_tag = article.select_one("h3.gs_rt a")
                            if title_tag:
                                result["title"] = title_tag.text
                                result["url"] = title_tag.get("href", "")
                            else:
                                continue  # 如果没有标题，跳过这个条目
                            
                            # 提取作者和年份信息
                            author_info = article.select_one("div.gs_a")
                            if author_info:
                                author_text = author_info.text
                                # 提取作者（在第一个 - 之前）
                                if " - " in author_text:
                                    result["authors"] = author_text.split(" - ")[0].strip()
                                # 提取年份（通常在括号中）
                                year_match = re.search(r"(\d{4})", author_text)
                                if year_match:
                                    result["year"] = year_match.group(1)
                            
                            # 提取摘要
                            abstract_tag = article.select_one("div.gs_rs")
                            if abstract_tag:
                                result["abstract"] = abstract_tag.text.strip()
                            
                            # 提取PDF链接
                            pdf_link = None
                            links = article.select("div.gs_or_ggsm a")
                            for link in links:
                                if link.text == "[PDF]" or "pdf" in link.get("href", "").lower():
                                    pdf_link = link.get("href")
                                    break
                            
                            if pdf_link:
                                result["pdf_link"] = pdf_link
                            
                            results.append(result)
                        
                        # 只有当实际找到结果时才添加备用搜索源
                        if results:
                            # 添加备用搜索源
                            self._add_alternative_sources(results, query)
                            
                            return results, f"在Google Scholar上找到 {len(results)} 篇相关论文"
                        else:
                            # 没有解析到结果，可能页面结构变化
                            return self._return_no_results_message(query)
                    
                    elif response.status_code == 429 or response.status_code == 403:
                        logging.warning(f"Google Scholar请求被限制，状态码: {response.status_code}")
                        # 如果被限制访问，直接告知用户
                        if attempt == max_retries - 1:
                            return self._return_rate_limited_message(query, response.status_code)
                        # 否则等待一段时间后重试
                        time.sleep(2)
                    
                    else:
                        logging.warning(f"Google Scholar返回非正常状态码: {response.status_code}")
                        # 如果是最后一次尝试，告知状态码
                        if attempt == max_retries - 1:
                            return self._return_error_status_message(query, response.status_code)
                        # 否则等待一段时间后重试
                        time.sleep(1)
                
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    logging.warning(f"Google Scholar请求超时或连接错误: {str(e)}")
                    # 如果是最后一次尝试，清晰告知连接问题
                    if attempt == max_retries - 1:
                        return self._return_connection_error_message(query, str(e))
                    # 否则等待一段时间后重试
                    time.sleep(1)
            
            # 如果所有尝试都失败，提供明确的错误信息
            return self._return_all_attempts_failed_message(query)
            
        except Exception as e:
            error_msg = f"Google Scholar搜索错误: {str(e)}"
            logging.error(error_msg)
            # 提供具体的错误信息，而不是默认切换到离线模式
            return self._return_exception_message(query, str(e))

    def _return_captcha_message(self, query):
        """返回人机验证提示消息"""
        message = "Google Scholar需要完成人机验证"
        results = [{
            'title': "Google Scholar需要人机验证",
            'authors': "系统提示",
            'year': str(datetime.now().year),
            'url': f"https://scholar.google.com/scholar?q={quote_plus(query)}",
            'abstract': "Google Scholar检测到自动访问并要求完成人机验证。建议：\n1. 在浏览器中手动访问Google Scholar\n2. 完成验证后再尝试搜索\n3. 或使用百度学术/中国知网等其他学术搜索引擎",
            'source': 'Google Scholar',
            'id': hashlib.md5(f"captcha_{query}".encode()).hexdigest(),
            'citations': "N/A",
            'venue': "系统提示"
        }]
        # 添加其他可用的搜索引擎
        self._add_alternative_sources(results, query)
        return results, message

    def _return_no_parse_message(self, query):
        """返回无法解析页面提示消息"""
        message = "无法解析Google Scholar页面结构"
        results = [{
            'title': "Google Scholar页面解析失败",
            'authors': "系统提示",
            'year': str(datetime.now().year),
            'url': f"https://scholar.google.com/scholar?q={quote_plus(query)}",
            'abstract': "系统无法解析Google Scholar返回的页面结构，可能是Google修改了页面格式。建议：\n1. 在浏览器中手动访问链接\n2. 使用其他学术搜索引擎查找相关论文",
            'source': 'Google Scholar',
            'id': hashlib.md5(f"no_parse_{query}".encode()).hexdigest(),
            'citations': "N/A",
            'venue': "系统提示"
        }]
        # 添加其他可用的搜索引擎
        self._add_alternative_sources(results, query)
        return results, message

    def _return_no_results_message(self, query):
        """返回未找到结果的提示消息"""
        message = "Google Scholar未找到相关结果"
        results = [{
            'title': "Google Scholar未找到相关结果",
            'authors': "系统提示",
            'year': str(datetime.now().year),
            'url': f"https://scholar.google.com/scholar?q={quote_plus(query)}",
            'abstract': f"Google Scholar未找到与'{query}'相关的结果。建议：\n1. 尝试使用不同的关键词\n2. 使用更简短或更准确的搜索词\n3. 尝试其他学术搜索引擎",
            'source': 'Google Scholar',
            'id': hashlib.md5(f"no_results_{query}".encode()).hexdigest(),
            'citations': "N/A", 
            'venue': "系统提示"
        }]
        # 添加其他可用的搜索引擎
        self._add_alternative_sources(results, query)
        return results, message

    def _return_rate_limited_message(self, query, status_code):
        """返回访问限制提示消息"""
        message = f"Google Scholar访问受限 (状态码: {status_code})"
        results = [{
            'title': "Google Scholar访问频率受限",
            'authors': "系统提示",
            'year': str(datetime.now().year),
            'url': f"https://scholar.google.com/scholar?q={quote_plus(query)}",
            'abstract': f"Google Scholar限制了搜索频率 (HTTP状态码: {status_code})。建议：\n1. 等待一段时间后再试\n2. 使用VPN或更换IP地址\n3. 使用百度学术等其他学术搜索引擎",
            'source': 'Google Scholar',
            'id': hashlib.md5(f"rate_limited_{query}".encode()).hexdigest(),
            'citations': "N/A",
            'venue': "系统提示"
        }]
        # 添加其他可用的搜索引擎
        self._add_alternative_sources(results, query)
        return results, message

    def _return_error_status_message(self, query, status_code):
        """返回HTTP错误状态码提示消息"""
        message = f"Google Scholar服务器返回错误: {status_code}"
        results = [{
            'title': f"Google Scholar服务器错误 (状态码: {status_code})",
            'authors': "系统提示",
            'year': str(datetime.now().year),
            'url': f"https://scholar.google.com/scholar?q={quote_plus(query)}",
            'abstract': f"Google Scholar服务器返回了错误状态码 {status_code}。这可能是暂时的服务器问题。建议：\n1. 稍后再试\n2. 使用其他搜索引擎",
            'source': 'Google Scholar',
            'id': hashlib.md5(f"error_status_{query}_{status_code}".encode()).hexdigest(),
            'citations': "N/A",
            'venue': "系统提示" 
        }]
        # 添加其他可用的搜索引擎
        self._add_alternative_sources(results, query)
        return results, message

    def _return_connection_error_message(self, query, error_details):
        """返回连接错误提示消息"""
        message = "连接到Google Scholar失败"
        results = [{
            'title': "连接Google Scholar失败",
            'authors': "系统提示",
            'year': str(datetime.now().year),
            'url': f"https://scholar.google.com/scholar?q={quote_plus(query)}",
            'abstract': f"连接到Google Scholar时出现网络错误。错误信息：{error_details}\n可能原因：\n1. 网络连接问题\n2. Google Scholar在您的地区可能无法访问\n3. 防火墙或网络设置限制",
            'source': 'Google Scholar',
            'id': hashlib.md5(f"connection_error_{query}".encode()).hexdigest(),
            'citations': "N/A",
            'venue': "系统提示"
        }]
        # 添加其他可用的搜索引擎
        self._add_alternative_sources(results, query)
        return results, message

    def _return_all_attempts_failed_message(self, query):
        """返回所有尝试都失败的提示消息"""
        message = "多次尝试连接Google Scholar均失败"
        results = [{
            'title': "无法访问Google Scholar",
            'authors': "系统提示",
            'year': str(datetime.now().year),
            'url': f"https://scholar.google.com/scholar?q={quote_plus(query)}",
            'abstract': "多次尝试访问Google Scholar均失败。建议：\n1. 检查网络连接\n2. 使用VPN或代理服务\n3. 使用百度学术、中国知网等国内学术资源",
            'source': 'Google Scholar',
            'id': hashlib.md5(f"all_attempts_failed_{query}".encode()).hexdigest(),
            'citations': "N/A",
            'venue': "系统提示"
        }]
        # 添加其他可用的搜索引擎
        self._add_alternative_sources(results, query)
        return results, message

    def _return_exception_message(self, query, error_details):
        """返回异常错误提示消息"""
        message = f"搜索过程发生异常: {error_details}"
        results = [{
            'title': "搜索过程中发生错误",
            'authors': "系统提示",
            'year': str(datetime.now().year), 
            'url': f"https://scholar.google.com/scholar?q={quote_plus(query)}",
            'abstract': f"搜索过程中发生程序错误。错误详情：{error_details}\n建议：\n1. 检查网络连接\n2. 尝试其他搜索引擎",
            'source': 'Google Scholar',
            'id': hashlib.md5(f"exception_{query}".encode()).hexdigest(),
            'citations': "N/A",
            'venue': "系统提示"
        }]
        # 添加其他可用的搜索引擎
        self._add_alternative_sources(results, query)
        return results, message

    def _add_alternative_sources(self, results, query):
        """添加备用学术搜索源（中文学术网站）"""
        current_year = datetime.now().year
        
        # 添加百度学术链接
        results.append({
            'title': f"百度学术搜索: {query}",
            'authors': "百度学术",
            'year': str(current_year),
            'url': f"https://xueshu.baidu.com/s?wd={quote_plus(query)}",
            'abstract': "百度学术是中文学术搜索引擎，提供海量中英文文献检索，包括期刊、会议论文、学位论文等多种学术资源。点击链接可在浏览器中打开百度学术搜索结果。",
            'source': 'Google Scholar',
            'id': hashlib.md5(f"baidu_xueshu_{query}".encode()).hexdigest(),
            'citations': "N/A",
            'venue': "搜索引擎"
        })
        
        # 添加中国知网链接
        results.append({
            'title': f"CNKI 中国知网: {query}",
            'authors': "中国知网",
            'year': str(current_year),
            'url': f"https://kns.cnki.net/kns8/defaultresult/index?kw={quote_plus(query)}",
            'abstract': "中国知网(CNKI)是中国知识基础设施工程的核心组成部分，收录了中国学术期刊、博士论文、硕士论文、会议论文、报纸等多种学术资源。点击链接可在浏览器中打开中国知网搜索结果。",
            'source': 'Google Scholar',
            'id': hashlib.md5(f"cnki_{query}".encode()).hexdigest(),
            'citations': "N/A",
            'venue': "搜索引擎"
        })
    
    def _search_ieee(self, query, max_results=10):
        """搜索IEEE Xplore论文"""
        try:
            # 简化实现，直接返回搜索链接
            results = [{
                'title': f"IEEE Xplore 搜索: {query}",
                'authors': "未知作者",
                'year': "未知年份",
                'url': f"https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={quote_plus(query)}",
                'abstract': "IEEE Xplore搜索结果",
                'source': 'IEEE Xplore',
                'id': query
            }]
            return results, "通过IEEE Xplore搜索"
            
        except Exception as e:
            return [], f"IEEE Xplore搜索出错: {str(e)}"
    
    def _search_pubmed(self, query, max_results=10):
        """搜索PubMed论文"""
        encoded_query = quote_plus(query)
        url = f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_query}"
        
        return [{
            'title': f"PubMed 搜索: {query}",
            'authors': "PubMed搜索",
            'year': "N/A",
            'url': url,
            'abstract': "PubMed搜索功能尚未完全实现。请点击链接在浏览器中查看搜索结果。",
            'source': 'PubMed',
            'id': hashlib.md5(query.encode()).hexdigest()
        }], f"已生成PubMed搜索链接"
    
    def _search_semantic_scholar(self, query, max_results=10):
        """搜索Semantic Scholar论文"""
        try:
            # 构建搜索URL - 使用最新API格式
            encoded_query = quote_plus(query)
            search_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={max_results}&fields=title,authors,year,abstract,url,citationCount,venue,publicationDate"
            
            print(f"[DEBUG] 尝试访问Semantic Scholar API: {search_url}")
            
            # 发送请求
            try:
                print(f"[DEBUG] 发送请求...")
                # 设置更短的超时时间
                response = self.session.get(search_url, timeout=5)
                print(f"[DEBUG] 收到响应，状态码: {response.status_code}")
                
                # 检查是否成功
                if response.status_code != 200:
                    print(f"[DEBUG] API请求失败，状态码: {response.status_code}")
                    return self._semantic_scholar_fallback(query, f"API请求失败，状态码: {response.status_code}")
                
                # 解析JSON响应
                print(f"[DEBUG] 解析JSON响应")
                data = response.json()
                papers = data.get('data', [])
                print(f"[DEBUG] 找到 {len(papers)} 篇论文")
                
                if not papers:
                    print(f"[DEBUG] 未找到结果")
                    return self._semantic_scholar_fallback(query, "未找到结果")
                
                # 处理搜索结果
                results = []
                for i, paper in enumerate(papers):
                    print(f"[DEBUG] 处理第 {i+1} 篇论文")
                    # 提取标题
                    title = paper.get('title', '未知标题')
                    
                    # 提取作者
                    authors = []
                    for author in paper.get('authors', []):
                        authors.append(author.get('name', ''))
                    author_text = ", ".join(authors) if authors else "未知作者"
                    
                    # 提取年份
                    year = str(paper.get('year', '未知年份'))
                    
                    # 提取摘要
                    abstract = paper.get('abstract', '无摘要')
                    
                    # 提取URL
                    url = paper.get('url', '')
                    if not url:
                        paper_id = paper.get('paperId', '')
                        url = f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else ""
                    
                    # 提取引用次数
                    citations = str(paper.get('citationCount', 0))
                    
                    # 提取发表期刊/会议
                    venue = paper.get('venue', '')
                    
                    # 生成ID
                    paper_id = paper.get('paperId', hashlib.md5(title.encode()).hexdigest())
                    
                    # 创建结果条目
                    results.append({
                        'title': title,
                        'authors': author_text,
                        'year': year,
                        'url': url,
                        'abstract': abstract,
                        'source': 'Semantic Scholar',
                        'id': paper_id,
                        'citations': citations,
                        'venue': venue
                    })
                
                if not results:
                    print(f"[DEBUG] 处理后没有结果")
                    return self._semantic_scholar_fallback(query, "无法解析结果")
                
                print(f"[DEBUG] 成功获取 {len(results)} 篇论文")
                return results, f"在Semantic Scholar上找到 {len(results)} 篇相关论文"
                
            except requests.exceptions.Timeout:
                print("[DEBUG] 请求超时")
                return self._semantic_scholar_fallback(query, "API请求超时")
            except requests.exceptions.ConnectionError:
                print("[DEBUG] 连接错误")
                return self._semantic_scholar_fallback(query, "API连接错误")
            except json.JSONDecodeError:
                print("[DEBUG] 无效的JSON响应")
                return self._semantic_scholar_fallback(query, "无效的JSON响应")
            except Exception as e:
                print(f"[DEBUG] API请求出错: {str(e)}")
                return self._semantic_scholar_fallback(query, f"API请求出错: {str(e)}")
                
        except Exception as e:
            print(f"[DEBUG] 搜索整体出错: {str(e)}")
            return self._semantic_scholar_fallback(query, f"搜索整体出错: {str(e)}")
            
    def _semantic_scholar_fallback(self, query, error_message=None):
        """Semantic Scholar搜索的备用方法，返回直接链接"""
        print(f"[DEBUG] 使用备用方法, 错误: {error_message}")
        error_info = f"访问Semantic Scholar API出错: {error_message}" if error_message else "无法访问Semantic Scholar API"
        return [{
            'title': f"Semantic Scholar 搜索: {query}",
            'authors': "未知作者",
            'year': "未知年份",
            'url': f"https://www.semanticscholar.org/search?q={quote_plus(query)}",
            'abstract': f"{error_info}。请直接点击链接在浏览器中查看。",
            'source': 'Semantic Scholar',
            'id': hashlib.md5(f"semantic_scholar_{query}".encode()).hexdigest()
        }], f"Semantic Scholar搜索出错，已提供直接链接"
    
    def download_paper(self, paper_index, save_path, progress_callback=None):
        """
        下载指定索引的论文
        
        Args:
            paper_index: 论文在搜索结果中的索引
            save_path: 保存路径
            progress_callback: 进度回调函数，接受一个0-100的整数参数
        
        Returns:
            success: 布尔值，表示下载是否成功
        """
        try:
            # 验证索引
            if not self.search_results:
                print("没有可用的搜索结果")
                return False
            
            if paper_index < 0 or paper_index >= len(self.search_results):
                print(f"无效的论文索引: {paper_index}")
                return False
            
            # 获取论文信息
            paper = self.search_results[paper_index]
            paper_url = paper.get("url", "")
            
            if not paper_url:
                print("文献URL不可用")
                return False
            
            # 初始化进度
            if progress_callback:
                progress_callback(0)
            
            try:
                # 实际下载文件
                response = requests.get(paper_url, stream=True, timeout=30)
                
                if response.status_code == 200:
                    # 检查响应类型
                    content_type = response.headers.get('Content-Type', '')
                    if 'pdf' in content_type.lower() or paper_url.lower().endswith('.pdf'):
                        # 直接写入二进制流
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        with open(save_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # 更新进度
                                if progress_callback and total_size > 0:
                                    progress = int((downloaded / total_size) * 100)
                                    progress_callback(min(progress, 99))
                        
                        print(f"论文 '{paper.get('title', '未知')}' 已成功下载")
                        return True
                    else:
                        # 如果不是PDF，尝试使用浏览器打开
                        try:
                            import webbrowser
                            webbrowser.open(paper_url)
                            
                            # 创建一个信息文件
                            with open(save_path, "w", encoding="utf-8") as f:
                                f.write(f"标题: {paper.get('title', '未知标题')}\n")
                                f.write(f"作者: {paper.get('authors', '未知作者')}\n")
                                f.write(f"年份: {paper.get('year', '未知年份')}\n")
                                f.write(f"URL: {paper_url}\n\n")
                                if "abstract" in paper:
                                    f.write(f"摘要: {paper['abstract']}\n")
                                f.write("\n注意：已在浏览器中打开原始链接。")
                            
                            print("已在浏览器中打开文献链接，并保存了文献信息")
                            return True
                        except Exception as e:
                            print(f"无法打开浏览器: {str(e)}")
                            return False
                else:
                    print(f"下载失败，服务器返回状态码: {response.status_code}")
                    return False
            except Exception as e:
                print(f"下载过程中出错: {str(e)}")
                return False
                
        except Exception as e:
            print(f"下载准备过程中出错: {str(e)}")
            return False 