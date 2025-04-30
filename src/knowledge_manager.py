# -*- coding: utf-8 -*-
import os
import re
import json
import shutil
from datetime import datetime

class KnowledgeManager:
    def __init__(self):
        """初始化知识库管理器"""
        self.knowledge_base_dir = "knowledge_base"
        self.index_file = os.path.join(self.knowledge_base_dir, "index.json")
        
        # 确保知识库目录存在
        os.makedirs(self.knowledge_base_dir, exist_ok=True)
        
        # 知识库分区
        self.categories = ["论文", "学习笔记", "参考资料", "其他"]
        
        # 确保各个分区目录都存在
        for category in self.categories:
            category_dir = os.path.join(self.knowledge_base_dir, category)
            os.makedirs(category_dir, exist_ok=True)
        
        # 初始化索引
        self.index = self.load_index()
    
    def load_index(self):
        """加载知识库索引"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载索引时出错: {e}")
                return self._create_default_index()
        else:
            return self._create_default_index()
    
    def _create_default_index(self):
        """创建默认索引结构"""
        return {
            "files": {},
            "categories": {category: [] for category in self.categories},
            "last_updated": datetime.now().isoformat()
        }
    
    def save_index(self):
        """保存知识库索引"""
        self.index["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.index, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存索引时出错: {e}")
    
    def add_file(self, file_path, category="其他"):
        """添加文件到知识库指定分区

        Args:
            file_path: 文件路径
            category: 分区名称，默认为"其他"

        Returns:
            bool: 是否成功添加
        """
        try:
            # 验证分区是否存在
            if category not in self.categories:
                print(f"分区 '{category}' 不存在，将使用'其他'分区")
                category = "其他"
            
            # 获取文件名和扩展名
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # 确保分区目录存在
            category_dir = os.path.join(self.knowledge_base_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            
            # 复制文件到分区目录
            dest_path = os.path.join(category_dir, filename)
            shutil.copy2(file_path, dest_path)
            
            # 提取文本内容
            content = self.extract_text(dest_path, file_ext)
            
            # 更新索引
            file_id = f"{category}/{filename}"
            self.index["files"][file_id] = {
                "path": dest_path,
                "category": category,
                "added_time": datetime.now().isoformat(),
                "type": file_ext[1:] if file_ext else "unknown",
                "size": os.path.getsize(dest_path),
                "tokens": len(content.split()),
                "content": content,  # 保存内容到索引
                "summary": self.generate_summary(content)
            }
            
            # 更新分区文件列表
            if file_id not in self.index["categories"][category]:
                self.index["categories"][category].append(file_id)
            
            # 保存索引
            self.save_index()
            return True
        except Exception as e:
            print(f"添加文件时出错: {e}")
            return False
    
    def add_paper_to_knowledge_base(self, paper_filepath, paper_data=None, category="论文"):
        """添加论文到知识库

        Args:
            paper_filepath: 论文文件路径
            paper_data: 论文元数据，包含标题、作者等信息
            category: 添加到的分类，默认为"论文"

        Returns:
            tuple: (bool, str) 是否成功添加和新文件名
        """
        try:
            # 确保分类存在
            if category not in self.categories:
                # 如果分类不存在，添加到categories列表
                self.categories.append(category)
                # 更新索引中的categories
                if category not in self.index["categories"]:
                    self.index["categories"][category] = []
            
            # 确保分类目录存在
            category_dir = os.path.join(self.knowledge_base_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            
            # 获取文件名和扩展名
            filename = os.path.basename(paper_filepath)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # 如果有论文元数据，使用更有意义的文件名
            if paper_data and isinstance(paper_data, dict):
                # 提取标题和作者
                title = paper_data.get('title', '').strip()
                authors = paper_data.get('authors', '').strip()
                year = paper_data.get('year', '')
                
                # 构建有意义的文件名
                if title:
                    # 清理标题，去除不合法的文件名字符
                    clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
                    clean_title = clean_title.strip()
                    
                    # 截断过长的标题
                    if len(clean_title) > 100:
                        clean_title = clean_title[:100]
                    
                    # 添加作者和年份信息
                    if authors:
                        # 提取第一作者姓氏
                        first_author = authors.split(',')[0].strip().split()[-1]
                        new_filename = f"{clean_title}_{first_author}"
                        if year:
                            new_filename += f"_{year}"
                    else:
                        new_filename = clean_title
                        if year:
                            new_filename += f"_{year}"
                    
                    # 添加扩展名
                    new_filename += file_ext
                    
                    # 检查文件名长度，如果太长则缩短
                    if len(new_filename) > 200:
                        new_filename = new_filename[:195] + file_ext
                else:
                    new_filename = filename
            else:
                new_filename = filename
            
            # 目标路径
            dest_path = os.path.join(category_dir, new_filename)
            
            # 如果文件已存在，添加序号
            if os.path.exists(dest_path):
                name_base, ext = os.path.splitext(new_filename)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(category_dir, f"{name_base}_{counter}{ext}")
                    counter += 1
                new_filename = os.path.basename(dest_path)
            
            # 复制文件到指定分类
            shutil.copy2(paper_filepath, dest_path)
            
            # 提取文本内容
            content = self.extract_text(dest_path, file_ext)
            
            # 更新索引
            file_id = f"{category}/{new_filename}"
            
            # 基本索引信息
            file_info = {
                "path": dest_path,
                "category": category,
                "added_time": datetime.now().isoformat(),
                "type": file_ext[1:] if file_ext else "unknown",
                "size": os.path.getsize(dest_path),
                "tokens": len(content.split()),
                "content": content,  # 保存内容到索引
                "summary": self.generate_summary(content)
            }
            
            # 如果有论文元数据，添加到索引
            if paper_data and isinstance(paper_data, dict):
                # 添加元数据字段
                for key, value in paper_data.items():
                    if key not in file_info and value:
                        file_info[key] = value
            
            # 更新索引
            self.index["files"][file_id] = file_info
            
            # 更新分区文件列表
            if file_id not in self.index["categories"][category]:
                self.index["categories"][category].append(file_id)
            
            # 保存索引
            self.save_index()
            
            return True, new_filename
        except Exception as e:
            print(f"添加论文到知识库时出错: {e}")
            return False, None
    
    def remove_file(self, file_id):
        """从知识库中删除文件
        
        Args:
            file_id: 文件ID，格式为"分区/文件名"
            
        Returns:
            bool: 是否成功删除
        """
        try:
            # 检查文件是否存在于索引中
            if file_id not in self.index["files"]:
                return False
            
            # 获取文件信息
            file_info = self.index["files"][file_id]
            file_path = file_info["path"]
            category = file_info["category"]
            
            # 删除文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 从索引中移除
            del self.index["files"][file_id]
            
            # 从分区列表中移除
            if category in self.index["categories"] and file_id in self.index["categories"][category]:
                self.index["categories"][category].remove(file_id)
            
            # 保存索引
            self.save_index()
            return True
        except Exception as e:
            print(f"删除文件时出错: {e}")
            return False
    
    def extract_text(self, file_path, file_ext):
        """从不同类型的文件中提取文本"""
        try:
            # 纯文本文件
            if file_ext in [".txt", ".md", ".csv"]:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            
            # PDF文件
            elif file_ext == ".pdf":
                try:
                    import PyPDF2
                    with open(file_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                        return text
                except ImportError:
                    return "无法提取PDF文本，请安装PyPDF2库"
            
            # Word文档
            elif file_ext in [".docx", ".doc"]:
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = ""
                    for para in doc.paragraphs:
                        text += para.text + "\n"
                    return text
                except ImportError:
                    return "无法提取Word文档文本，请安装python-docx库"
            
            # 其他文件类型
            else:
                return f"不支持的文件类型: {file_ext}"
        except Exception as e:
            return f"提取文本时出错: {str(e)}"
    
    def generate_summary(self, text, max_length=200):
        """生成文本摘要（简单实现）"""
        if len(text) <= max_length:
            return text
            
        # 简单实现：取开头部分文本
        return text[:max_length] + "..."
    
    def _tokenize(self, text):
        """将文本分词为列表
        
        Args:
            text: 要分词的文本
            
        Returns:
            list: 分词后的标记列表
        """
        if not text:
            return []
        
        # 转换为小写
        text = text.lower()
        
        # 移除标点符号，替换为空格
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 按空格分词
        tokens = text.split()
        
        # 移除过短的词
        tokens = [token for token in tokens if len(token) > 1]
        
        # 去重
        return list(set(tokens))
    
    def _calculate_similarity(self, query_tokens, text_tokens):
        """计算查询与文本之间的相似度
        
        Args:
            query_tokens: 查询关键词的标记列表
            text_tokens: 文本的标记列表
            
        Returns:
            float: 相似度分数，取值范围 0~1
        """
        if not query_tokens or not text_tokens:
            return 0
        
        # 计算共有词数量
        common_tokens = set(query_tokens) & set(text_tokens)
        
        # 简单的相似度计算：共有词数量除以查询词数量
        similarity = len(common_tokens) / len(query_tokens)
        return similarity
    
    def refresh_index(self):
        """刷新索引，确保所有文件都在索引中，并移除不存在的文件"""
        try:
            # 检查索引中的文件是否都存在，移除不存在的文件
            files_to_remove = []
            
            for file_id, file_info in self.index["files"].items():
                file_path = file_info.get("path", "")
                if not file_path or not os.path.exists(file_path):
                    files_to_remove.append(file_id)
            
            # 从索引中移除不存在的文件
            for file_id in files_to_remove:
                category = self.index["files"][file_id].get("category", "")
                
                # 从文件索引中移除
                del self.index["files"][file_id]
                
                # 从分区列表中移除
                if category and category in self.index["categories"] and file_id in self.index["categories"][category]:
                    self.index["categories"][category].remove(file_id)
            
            # 扫描知识库目录，添加新文件
            for category in self.categories:
                category_dir = os.path.join(self.knowledge_base_dir, category)
                
                if os.path.exists(category_dir) and os.path.isdir(category_dir):
                    for filename in os.listdir(category_dir):
                        file_path = os.path.join(category_dir, filename)
                        
                        # 跳过目录
                        if os.path.isdir(file_path):
                            continue
                        
                        # 检查文件是否已在索引中
                        file_id = f"{category}/{filename}"
                        if file_id not in self.index["files"]:
                            # 添加到索引
                            file_ext = os.path.splitext(filename)[1].lower()
                            content = self.extract_text(file_path, file_ext)
                            
                            self.index["files"][file_id] = {
                                "path": file_path,
                                "category": category,
                                "added_time": datetime.now().isoformat(),
                                "type": file_ext[1:] if file_ext else "unknown",
                                "size": os.path.getsize(file_path),
                                "tokens": len(content.split()),
                                "content": content,  # 添加内容字段用于搜索
                                "summary": self.generate_summary(content)
                            }
                            
                            # 更新分区文件列表
                            if file_id not in self.index["categories"][category]:
                                self.index["categories"][category].append(file_id)
            
            # 保存更新后的索引
            self.save_index()
            return True
        except Exception as e:
            print(f"刷新索引时出错: {e}")
            return False
    
    def search(self, query, categories=None, max_results=5):
        """搜索知识库内的内容
        
        Args:
            query: 查询关键词
            categories: 要搜索的知识库分区，默认为全部
            max_results: 最大结果数量
            
        Returns:
            list: 含有匹配结果的列表
        """
        if not self.index or not self.index.get("files"):
            return []
        
        # 确保索引是最新的
        self.refresh_index()
        
        # 处理分区筛选
        file_ids_to_search = []
        if categories:
            if isinstance(categories, str):
                categories = [categories]
            # 只获取指定分区的文件ID列表
            for category in categories:
                if category in self.index["categories"]:
                    file_ids_to_search.extend(self.index["categories"][category])
        else:
            # 获取所有文件ID
            for category_files in self.index["categories"].values():
                file_ids_to_search.extend(category_files)
        
        # 执行搜索
        results = []
        query_tokens = self._tokenize(query)
        
        for file_id in file_ids_to_search:
            if file_id not in self.index["files"]:
                continue
                
            file_info = self.index["files"][file_id]
            filename = file_id.split("/", 1)[1] if "/" in file_id else file_id
            
            # 获取文件内容或摘要
            content = file_info.get('content', '')
            if not content and os.path.exists(file_info.get('path', '')):
                # 如果索引中没有内容，尝试读取文件
                file_ext = os.path.splitext(filename)[1].lower()
                content = self.extract_text(file_info['path'], file_ext)
            
            title = file_info.get('title', filename)
            abstract = file_info.get('summary', '')
            
            # 计算相关度分数
            score = 0
            matches = []
            
            # 分段搜索
            if content:
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if not para.strip():
                        continue
                    para_score = self._calculate_similarity(query_tokens, self._tokenize(para))
                    if para_score > 0.2:  # 相关度阈值
                        score += para_score
                        matches.append(para)
            
            # 标题和摘要匹配加权
            if title:
                title_score = self._calculate_similarity(query_tokens, self._tokenize(title)) * 2
                score += title_score
            
            if abstract:
                abstract_score = self._calculate_similarity(query_tokens, self._tokenize(abstract)) * 1.5
                score += abstract_score
            
            if score > 0:
                result = {
                    "file_id": file_id,
                    "filename": filename,
                    "path": file_info.get("path", ""),
                    "category": file_info.get("category", "其他"),
                    "score": score,
                    "contexts": matches[:3],  # 最多返回3个匹配段落
                    "summary": abstract
                }
                
                # 添加其他有用的元数据
                for key in ["title", "authors", "year", "source", "added_time"]:
                    if key in file_info:
                        result[key] = file_info[key]
                        
                results.append(result)
        
        # 按相关度排序并限制结果数
        results = sorted(results, key=lambda x: x['score'], reverse=True)[:max_results]
        return results
    
    def get_files_by_category(self, category=None):
        """获取指定分区的文件列表
        
        Args:
            category: 分区名称，如不指定则返回所有文件
            
        Returns:
            list: 文件信息列表
        """
        files = []
        
        try:
            if category and category in self.categories:
                # 获取特定分区的文件
                file_ids = self.index["categories"].get(category, [])
            else:
                # 获取所有文件
                file_ids = []
                for cat_files in self.index["categories"].values():
                    file_ids.extend(cat_files)
            
            # 收集文件信息
            for file_id in file_ids:
                if file_id in self.index["files"]:
                    file_info = self.index["files"][file_id]
                    filename = file_id.split("/", 1)[1] if "/" in file_id else file_id
                    
                    # 基本信息
                    file_data = {
                        "file_id": file_id,
                        "filename": filename,
                        "category": file_info.get("category", "其他"),
                        "type": file_info.get("type", "unknown"),
                        "size": file_info.get("size", 0),
                        "added_time": file_info.get("added_time", ""),
                        "path": file_info.get("path", ""),
                        "summary": file_info.get("summary", "")
                    }
                    
                    # 添加其他有用元数据
                    for key in ["title", "authors", "year", "source"]:
                        if key in file_info:
                            file_data[key] = file_info[key]
                        
                    files.append(file_data)
            
            return files
        
        except Exception as e:
            print(f"获取文件列表时出错: {e}")
            return []
    
    def get_all_files(self):
        """获取知识库中的所有文件信息"""
        files = []
        for filename, info in self.index["files"].items():
            file_path = os.path.join(self.knowledge_base_dir, filename)
            if os.path.exists(file_path):
                files.append({
                    "filename": filename,
                    "type": info.get("type", "unknown"),
                    "size": info.get("size", 0),
                    "added_time": info.get("added_time", ""),
                    "summary": info.get("summary", "")
                })
        return files
    
    def get_knowledge_context(self, query, categories=None, max_results=3):
        """获取与查询相关的知识库上下文，用于增强AI回答
        
        Args:
            query: 查询关键词
            categories: 要搜索的知识库分区，默认为全部
            max_results: 最大结果数量
            
        Returns:
            str: 格式化后的知识库上下文
        """
        # 从指定分区或所有分区搜索
        search_results = self.search(query, categories=categories, max_results=max_results)
        
        if not search_results:
            return ""
        
        context = "以下是来自知识库的相关信息：\n\n"
        
        for i, result in enumerate(search_results, 1):
            # 显示分区信息
            category = result.get('category', '未分类')
            context += f"{i}. 【{category}】{result.get('filename', '')}\n"
            
            # 添加标题和作者信息（如果有）
            if 'title' in result:
                context += f"标题: {result['title']}\n"
            if 'authors' in result:
                context += f"作者: {result['authors']}\n"
            if 'year' in result:
                context += f"年份: {result['year']}\n"
            
            # 相关内容片段
            if result.get('contexts') and len(result['contexts']) > 0:
                context += "相关内容：\n"
                for ctx in result['contexts']:
                    # 截断过长的内容
                    if len(ctx) > 300:
                        ctx = ctx[:300] + "..."
                    context += f"  {ctx}\n"
            elif 'abstract' in result:
                context += f"摘要: {result['abstract']}\n"
            elif 'summary' in result:
                context += f"摘要: {result['summary']}\n"
            
            context += "\n"
        
        return context
    
    def get_file_info(self, file_id):
        """获取指定文件的详细信息
        
        Args:
            file_id: 文件ID，格式为"分区/文件名"
            
        Returns:
            dict: 文件信息字典或None（如果文件不存在）
        """
        try:
            if file_id in self.index["files"]:
                return self.index["files"][file_id]
            return None
        except Exception as e:
            print(f"获取文件信息时出错: {str(e)}")
            return None 