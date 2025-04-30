import os
import re
import json
import time
import requests
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup
import hashlib
import logging

class PaperDownloader:
    def __init__(self, papers_dir="papers"):
        # 创建论文下载目录
        self.papers_dir = papers_dir
        os.makedirs(papers_dir, exist_ok=True)
        
        # 存储搜索结果
        self.search_results = []
        
        # 支持的来源
        self.sources = ["Arxiv", "Sci-Hub", "Google Scholar", "IEEE Xplore", "PubMed", "Google", "Semantic Scholar"]
        
        # 初始化会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
        })
    
    def search_papers(self, query, source="Arxiv"):
        """搜索论文"""
        self.search_results = []
        message = ""
        
        try:
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
            elif source == "Google":
                results, message = self._search_google(query)
            elif source == "Semantic Scholar":
                results, message = self._search_semantic_scholar(query)
            else:
                return [], "不支持的来源"
                
            self.search_results = results
            return results, message
            
        except Exception as e:
            return [], f"搜索出错: {str(e)}"
    
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
                arxiv_id_short = arxiv_id.split('/')[-1] if arxiv_id else ""
                
                # 提取分类
                categories = []
                category_tags = entry.find_all('category')
                for cat_tag in category_tags:
                    if cat_tag.get('term'):
                        categories.append(cat_tag.get('term'))
                category_text = ", ".join(categories) if categories else "未分类"
                
                # 格式化摘要，压缩多余的空白
                abstract = re.sub(r'\s+', ' ', abstract).strip()
                
                # 创建直接下载的URL
                direct_pdf_url = pdf_url
                
                # 创建结果条目
                results.append({
                    'title': title,
                    'authors': author_text,
                    'year': pub_date,
                    'url': pdf_url,
                    'abstract': abstract,
                    'source': 'Arxiv',
                    'id': arxiv_id,
                    'arxiv_id': arxiv_id_short,
                    'categories': category_text,
                    'direct_pdf_url': direct_pdf_url
                })
            
            return results, f"在Arxiv上找到 {len(results)} 篇相关论文"
            
        except Exception as e:
            return [], f"Arxiv搜索出错: {str(e)}"
    
    def _extract_doi(self, text):
        """从文本中提取DOI"""
        # 标准DOI格式: 10.xxxx/yyyy
        doi_pattern = r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b"
        match = re.search(doi_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _search_scihub(self, query, max_results=10):
        """搜索Sci-Hub论文（通过DOI或标题）"""
        try:
            # Sci-Hub镜像站点列表
            mirrors = [
                "https://sci-hub.se",
                "https://sci-hub.ru",
                "https://sci-hub.st",
                "https://sci-hub.ren"
            ]
            
            # 尝试从查询中提取DOI
            doi = self._extract_doi(query)
            
            # 如果查询是URL，可能需要从URL中提取DOI
            if not doi and ('http://' in query or 'https://' in query):
                # 尝试从网址中提取DOI
                try:
                    # 从URL路径中获取可能的DOI
                    parsed_url = urlparse(query)
                    path = parsed_url.path
                    doi = self._extract_doi(path)
                    
                    # 如果路径中没有DOI，尝试查询参数
                    if not doi and parsed_url.query:
                        doi = self._extract_doi(parsed_url.query)
                except:
                    pass
            
            if doi:
                title = f"DOI: {doi}"
                query_param = doi  # 使用提取出的DOI
            else:
                title = f"搜索: {query}"
                query_param = query
            
            # 为每个镜像站点创建结果
            results = []
            for mirror in mirrors:
                url = f"{mirror}/{query_param}"
                
                results.append({
                    'title': f"{title} ({mirror.split('//')[1]})",
                    'authors': "通过Sci-Hub访问" + (" (已提取DOI)" if doi else ""),
                    'year': "N/A",
                    'url': url,
                    'abstract': "Sci-Hub提供免费访问学术论文的平台。\n\n使用方法：\n1. 点击下载按钮，系统将尝试直接下载PDF（如果可用）\n2. 如果直接下载失败，将在浏览器中打开Sci-Hub链接\n3. 在打开的网页中查找并点击PDF下载按钮\n4. 如果第一个镜像无法访问，请尝试列表中的其他镜像\n\n" + (f"已识别DOI: {doi}" if doi else ""),
                    'source': 'Sci-Hub',
                    'id': doi if doi else query,
                    'mirror': mirror,
                    'doi': doi
                })
            
            return results, f"通过Sci-Hub搜索: {len(results)}个镜像站点可用" + (" (已识别DOI)" if doi else "")
                
        except Exception as e:
            return [], f"Sci-Hub搜索出错: {str(e)}"
    
    def _search_google_scholar(self, query):
        """从Google Scholar搜索论文"""
        try:
            url = f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}&hl=zh-CN&as_sdt=0,5"
            
            # 更新用户代理为较新的Chrome版本
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive'
            }
            
            # 实现重试机制
            max_retries = 3
            retry_count = 0
            response = None
            
            while retry_count < max_retries:
                try:
                    response = self.session.get(url, headers=headers, timeout=8)
                    if response.status_code == 200:
                        break
                except (requests.RequestException, ConnectionError, TimeoutError) as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        raise e
                    time.sleep(1)  # 等待1秒再次尝试
            
            if not response or response.status_code != 200:
                return {"error": f"无法连接到Google Scholar，状态码: {response.status_code if response else '未知'}"}
            
            # 检查是否返回CAPTCHA页面
            if "请证明您不是机器人" in response.text or "Please show you're not a robot" in response.text:
                return {"error": "Google Scholar 要求验证码验证，请稍后重试或者尝试使用VPN"}
            
            # 保存HTML响应用于调试
            debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug")
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            with open(os.path.join(debug_dir, "google_scholar_response.html"), "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # 解析结果
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # 查找所有论文条目
            articles = soup.select("div.gs_r.gs_or.gs_scl")
            if not articles:
                articles = soup.select("div.gs_ri")  # 尝试替代选择器
            
            if not articles:
                # 如果仍找不到条目，尝试分析页面结构
                return {"error": "无法解析Google Scholar页面。页面结构可能已更改，请尝试其他来源或稍后再试。"}
            
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
            
            return results
        except Exception as e:
            error_msg = f"Google Scholar搜索错误: {str(e)}"
            logging.error(error_msg)
            return {"error": f"{error_msg}。Google Scholar可能需要使用VPN访问，请确保网络连接正常。"}
    
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
        try:
            # 简化实现，直接返回搜索链接
            results = [{
                'title': f"PubMed 搜索: {query}",
                'authors': "未知作者",
                'year': "未知年份",
                'url': f"https://pubmed.ncbi.nlm.nih.gov/?term={quote_plus(query)}",
                'abstract': "PubMed搜索结果",
                'source': 'PubMed',
                'id': query
            }]
            return results, "通过PubMed搜索"
            
        except Exception as e:
            return [], f"PubMed搜索出错: {str(e)}"
    
    def _search_google(self, query, max_results=10):
        """搜索Google获取学术相关结果"""
        try:
            # 构建搜索URL - 添加一些过滤器找学术相关内容
            encoded_query = quote_plus(f"{query} filetype:pdf")
            search_url = f"https://www.google.com/search?q={encoded_query}"
            
            # 提供直接链接
            results = [{
                'title': f"Google 搜索: {query} (PDF文件)",
                'authors': "Google搜索",
                'year': "N/A",
                'url': search_url,
                'abstract': f"Google搜索是访问Google Scholar的替代方案。\n\n可以尝试的搜索技巧:\n1. 添加 'filetype:pdf' 查找PDF文件\n2. 添加作者名、期刊名或机构名缩小范围\n3. 添加 'site:edu' 或 'site:ac.uk' 等限制在教育机构网站\n4. 使用引号(\"{query}\")进行精确匹配\n\n原始查询: {query}",
                'source': 'Google',
                'id': hashlib.md5(query.encode()).hexdigest()
            }]
            
            # 扩展搜索 - 添加专业内容搜索
            results.append({
                'title': f"Google 搜索: {query} (学术文献)",
                'authors': "Google学术搜索",
                'year': "N/A",
                'url': f"https://www.google.com/search?q={quote_plus(query + ' academic paper research')}",
                'abstract': "使用Google搜索学术文献，比Google Scholar更容易访问。",
                'source': 'Google',
                'id': hashlib.md5((query + "academic").encode()).hexdigest()
            })
            
            # ResearchGate搜索
            results.append({
                'title': f"ResearchGate 搜索: {query}",
                'authors': "ResearchGate",
                'year': "N/A",
                'url': f"https://www.researchgate.net/search/publication?q={quote_plus(query)}",
                'abstract': "ResearchGate是一个科研社交网络，包含大量免费论文和预印本。",
                'source': 'Google',
                'id': hashlib.md5((query + "researchgate").encode()).hexdigest()
            })
            
            return results, f"提供了Google搜索替代方案，可能更容易访问"
            
        except Exception as e:
            print(f"Google搜索出错: {str(e)}")
            return [{
                'title': f"Google 搜索: {query}",
                'authors': "Google搜索",
                'year': "N/A",
                'url': f"https://www.google.com/search?q={quote_plus(query)}",
                'abstract': f"访问Google搜索出错: {str(e)}。请直接点击链接在浏览器中查看。",
                'source': 'Google',
                'id': hashlib.md5(query.encode()).hexdigest()
            }], f"Google搜索出错，已提供直接链接"
    
    def _search_semantic_scholar(self, query, max_results=10):
        """搜索Semantic Scholar论文"""
        try:
            # 构建搜索URL
            encoded_query = quote_plus(query)
            search_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={max_results}&fields=title,authors,year,abstract,url,citationCount"
            
            print(f"尝试访问Semantic Scholar API: {search_url}")
            
            # 发送请求
            try:
                response = self.session.get(search_url, timeout=10)
                
                # 检查是否成功
                if response.status_code != 200:
                    print(f"Semantic Scholar API请求失败，状态码: {response.status_code}")
                    # 退回到简单实现
                    return self._semantic_scholar_fallback(query)
                
                # 解析JSON响应
                data = response.json()
                papers = data.get('data', [])
                
                if not papers:
                    print("未找到Semantic Scholar搜索结果")
                    return self._semantic_scholar_fallback(query, "未找到结果")
                
                # 处理搜索结果
                results = []
                for paper in papers:
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
                        'citations': citations
                    })
                
                if not results:
                    return self._semantic_scholar_fallback(query, "无法解析结果")
                
                return results, f"通过Semantic Scholar找到 {len(results)} 篇相关论文"
                
            except Exception as e:
                print(f"Semantic Scholar API请求出错: {str(e)}")
                return self._semantic_scholar_fallback(query, str(e))
                
        except Exception as e:
            print(f"Semantic Scholar搜索整体出错: {str(e)}")
            return self._semantic_scholar_fallback(query, str(e))
            
    def _semantic_scholar_fallback(self, query, error_message=None):
        """Semantic Scholar搜索的备用方法，返回直接链接"""
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
    
    def download_paper(self, paper_data):
        """下载论文并保存到本地

        Args:
            paper_data: 包含论文信息的字典，必须包含pdf_link键

        Returns:
            dict: 包含下载结果信息
        """
        if not paper_data or not isinstance(paper_data, dict):
            return {"success": False, "message": "无效的论文数据"}
        
        # 检查PDF链接是否存在
        pdf_link = paper_data.get("pdf_link")
        if not pdf_link:
            return {"success": False, "message": "没有找到PDF链接"}
        
        # 获取标题用作文件名
        title = paper_data.get("title", "unnamed_paper")
        
        # 清理标题，去除不合法的文件名字符
        title = re.sub(r'[\\/*?:"<>|]', "", title)
        title = title.strip()
        
        # 截断过长的标题
        if len(title) > 100:
            title = title[:100]
        
        # 如果是DOI直接访问，使用DOI作为文件名
        if paper_data.get("doi") and "DOI:" in title:
            title = f"DOI_{paper_data.get('doi').replace('/', '_')}"
        
        # 确保存储目录存在
        if not os.path.exists(self.papers_dir):
            os.makedirs(self.papers_dir)
        
        filename = f"{title}.pdf"
        filepath = os.path.join(self.papers_dir, filename)
        
        # 如果文件已存在，添加序号
        if os.path.exists(filepath):
            counter = 1
            while os.path.exists(filepath):
                filepath = os.path.join(self.papers_dir, f"{title}_{counter}.pdf")
                counter += 1
        
        # 检查是否是Sci-Hub链接
        is_scihub = False
        for mirror in ["sci-hub.se", "sci-hub.ru", "sci-hub.st", "sci-hub.ren"]:
            if mirror in pdf_link:
                is_scihub = True
                break
        
        # 设置下载头信息
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7"
        }
        
        # 尝试下载文件，最多重试3次
        max_retries = 3
        retry_count = 0
        success = False
        error_message = ""
        
        while retry_count < max_retries and not success:
            try:
                if is_scihub:
                    # 对于Sci-Hub，先请求页面，然后提取PDF下载链接
                    response = self.session.get(pdf_link, headers=headers, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 尝试查找Sci-Hub中的PDF嵌入iframe
                        iframe = soup.find('iframe', id='pdf')
                        if iframe and iframe.has_attr('src'):
                            pdf_src = iframe['src']
                            # 如果链接不是以http开头，加上https:
                            if pdf_src.startswith('//'):
                                pdf_src = 'https:' + pdf_src
                            elif not pdf_src.startswith(('http://', 'https://')):
                                pdf_src = 'https://' + pdf_src.lstrip('/')
                                
                            # 使用提取的PDF链接进行下载
                            pdf_response = self.session.get(pdf_src, headers=headers, stream=True, timeout=30)
                            if pdf_response.status_code == 200:
                                with open(filepath, 'wb') as f:
                                    for chunk in pdf_response.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                success = True
                            else:
                                error_message = f"无法下载PDF，状态码: {pdf_response.status_code}"
                        else:
                            # 尝试查找其他可能的PDF链接按钮
                            buttons = soup.select('button#save')
                            if buttons:
                                error_message = "找到下载按钮，但需要手动点击。请在浏览器中打开链接: " + pdf_link
                            else:
                                error_message = "在Sci-Hub页面中未找到PDF。请在浏览器中手动访问: " + pdf_link
                    else:
                        error_message = f"访问Sci-Hub失败，状态码: {response.status_code}"
                else:
                    # 普通链接的下载逻辑
                    response = self.session.get(pdf_link, headers=headers, stream=True, timeout=30)
                    
                    # 检查响应状态
                    if response.status_code == 200:
                        # 检查内容类型
                        content_type = response.headers.get('Content-Type', '').lower()
                        if 'application/pdf' in content_type:
                            # 保存PDF文件
                            with open(filepath, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            success = True
                        elif 'text/html' in content_type:
                            # 可能是重定向页面，尝试提取PDF链接
                            soup = BeautifulSoup(response.text, 'html.parser')
                            meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
                            if meta_refresh and 'content' in meta_refresh.attrs:
                                # 提取重定向URL
                                match = re.search(r'url=([^;]*)', meta_refresh['content'])
                                if match and match.group(1):
                                    pdf_link = match.group(1)
                                    retry_count += 1
                                    continue
                            
                            # 尝试寻找页面上的PDF链接
                            pdf_links = soup.select('a[href$=".pdf"]')
                            if pdf_links:
                                pdf_link = pdf_links[0]['href']
                                if not pdf_link.startswith('http'):
                                    # 构建完整URL
                                    base_url = response.url
                                    if not base_url.endswith('/'):
                                        base_url = '/'.join(base_url.split('/')[:-1]) + '/'
                                    pdf_link = base_url + pdf_link
                                retry_count += 1
                                continue
                            
                            error_message = "页面不包含有效的PDF内容"
                        else:
                            error_message = f"内容类型不是PDF: {content_type}"
                    else:
                        error_message = f"下载失败，HTTP状态码: {response.status_code}"
            
            except requests.RequestException as e:
                error_message = f"下载请求错误: {str(e)}"
            except Exception as e:
                error_message = f"下载过程中出错: {str(e)}"
            
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2)  # 等待2秒后重试
        
        # 返回下载结果
        if success:
            return {
                "success": True,
                "message": f"论文《{title}》下载成功",
                "file_path": filepath
            }
        else:
            # 对于Sci-Hub链接，返回更详细的错误信息和建议
            if is_scihub:
                alternative_mirrors = []
                for mirror in ["sci-hub.se", "sci-hub.ru", "sci-hub.st", "sci-hub.ren"]:
                    if mirror not in pdf_link:
                        doi = paper_data.get("doi", "")
                        if doi:
                            alternative_mirrors.append(f"https://{mirror}/{doi}")
                            
                message = f"通过Sci-Hub下载失败: {error_message}\n"
                if alternative_mirrors:
                    message += "请尝试在浏览器中手动访问以下链接:\n" + "\n".join(alternative_mirrors)
                return {
                    "success": False,
                    "message": message,
                    "paper_data": paper_data,
                    "alternative_links": alternative_mirrors
                }
            else:
                return {
                    "success": False,
                    "message": f"论文下载失败: {error_message}",
                    "paper_data": paper_data
                } 