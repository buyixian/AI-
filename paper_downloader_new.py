import os
import re
import json
import time
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

class PaperDownloader:
    def __init__(self, papers_dir="papers"):
        # 创建论文下载目录
        self.papers_dir = papers_dir
        os.makedirs(papers_dir, exist_ok=True)
        
        # 存储搜索结果
        self.search_results = []
        
        # 支持的来源
        self.sources = ["Arxiv", "Sci-Hub", "Google Scholar", "IEEE Xplore", "PubMed"]
        
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
            else:
                return [], "不支持的来源"
                
            self.search_results = results
            return results, message
            
        except Exception as e:
            return [], f"搜索出错: {str(e)}"
    
    def _search_arxiv(self, query, max_results=20):
        """搜索Arxiv论文，使用REST API而不是arxiv模块"""
        try:
            # 使用Arxiv API
            encoded_query = quote_plus(query)
            url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}"
            
            response = self.session.get(url)
            if response.status_code != 200:
                return [], f"API请求失败，状态码: {response.status_code}"
            
            # 解析XML响应
            content = response.text
            
            # 提取论文条目
            entries = content.split("<entry>")[1:]
            
            results = []
            for entry in entries:
                # 提取标题
                title_match = re.search(r"<title>(.*?)</title>", entry)
                title = title_match.group(1).strip() if title_match else "未知标题"
                
                # 提取作者 - 使用<name>标签
                authors = []
                for author_match in re.finditer(r"<name>(.*?)</name>", entry):
                    authors.append(author_match.group(1).strip())
                author_text = ", ".join(authors) if authors else "未知作者"
                
                # 提取发布日期
                date_match = re.search(r"<published>(.*?)</published>", entry)
                pub_date = date_match.group(1).strip()[:4] if date_match else "未知日期"
                
                # 提取PDF链接
                pdf_match = re.search(r'<link title="pdf" href="(.*?)"', entry)
                pdf_url = pdf_match.group(1) if pdf_match else ""
                
                # 提取摘要
                abstract_match = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                abstract = abstract_match.group(1).strip() if abstract_match else "无摘要"
                
                # 提取ID
                id_match = re.search(r"<id>(.*?)</id>", entry)
                arxiv_id = id_match.group(1) if id_match else ""
                
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
    
    def _search_google_scholar(self, query, max_results=10):
        """搜索Google Scholar论文"""
        try:
            # 简化实现，直接返回搜索链接
            results = [{
                'title': f"Google Scholar 搜索: {query}",
                'authors': "未知作者",
                'year': "未知年份",
                'url': f"https://scholar.google.com/scholar?q={quote_plus(query)}",
                'abstract': "Google Scholar搜索结果",
                'source': 'Google Scholar',
                'id': query
            }]
            return results, "通过Google Scholar搜索"
            
        except Exception as e:
            return [], f"Google Scholar搜索出错: {str(e)}"
    
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