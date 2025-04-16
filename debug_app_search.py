import paper_downloader_fixed
import traceback

class MockAIAssistant:
    """模拟AI Assistant中的搜索功能"""
    
    def __init__(self):
        self.paper_downloader = paper_downloader_fixed.PaperDownloader()
        self.paper_results = []
        self.selected_paper = None
        
    def _execute_search(self, query, source):
        """模拟_execute_search方法"""
        print(f"执行搜索: {query} (来源: {source})")
        
        try:
            # 进行搜索
            results, message = self.paper_downloader.search_papers(query, source)
            
            if isinstance(results, str):  # 如果返回的是错误信息
                print(f"搜索错误: {results}")
                return
                
            if not results:
                print(f"未找到与 '{query}' 相关的论文")
                return
                
            # 更新搜索结果
            self._update_search_results(results, query, source)
        except Exception as e:
            print(f"搜索出错: {str(e)}")
            traceback.print_exc()
    
    def _update_search_results(self, results, query, source):
        """模拟_update_search_results方法"""
        # 存储搜索结果
        self.paper_results = results
        
        # 显示结果
        print(f"找到 {len(results)} 篇与 '{query}' 相关的论文 (来源: {source})")
        
        # 显示前3个结果
        for i, paper in enumerate(results[:3]):
            print(f"\n结果 {i+1}:")
            try:
                title = paper.get('title', '未知标题')
                authors = paper.get('authors', '未知作者')
                year = paper.get('year', '未知年份')
                source_info = paper.get('source', '未知来源')
                
                print(f"  标题: {title}")
                print(f"  作者: {authors}")
                print(f"  年份: {year}")
                print(f"  来源: {source_info}")
            except Exception as e:
                print(f"  显示结果时出错: {str(e)}")
                print(f"  结果类型: {type(paper)}")
                print(f"  结果内容: {paper}")
        
        # 重置选中的论文
        self.selected_paper = None
    
    def on_result_select(self, index):
        """模拟on_result_select方法"""
        if 0 <= index < len(self.paper_results):
            self.selected_paper = self.paper_results[index]
            
            # 显示选中的论文
            title = self.selected_paper.get('title', '未知标题')
            print(f"\n已选择: {title}")
            
            # 显示论文详情
            self.show_paper_details(self.selected_paper)
        else:
            self.selected_paper = None
            print("无效的选择")
    
    def show_paper_details(self, paper):
        """模拟show_paper_details方法"""
        print("\n论文详情:")
        
        try:
            # 显示基本信息
            print(f"标题: {paper.get('title', '未知标题')}")
            print(f"作者: {paper.get('authors', '未知作者')}")
            print(f"年份: {paper.get('year', '未知年份')}")
            print(f"来源: {paper.get('source', '未知来源')}")
            
            # 显示摘要
            abstract = paper.get('abstract', '无摘要')
            if abstract and len(abstract) > 200:
                abstract = abstract[:200] + "..."
            print(f"摘要: {abstract}")
            
            # 显示链接
            print(f"链接: {paper.get('url', '无链接')}")
        except Exception as e:
            print(f"显示论文详情时出错: {str(e)}")
            traceback.print_exc()

def test_app_search():
    """测试模拟的应用搜索功能"""
    app = MockAIAssistant()
    
    # 测试各种来源的搜索
    sources = ["Arxiv", "Google Scholar", "IEEE Xplore", "PubMed", "Semantic Scholar"]
    
    for source in sources:
        print("\n" + "="*50)
        print(f"测试 {source} 搜索:")
        print("="*50)
        
        try:
            # 执行搜索
            app._execute_search("机器学习", source)
            
            # 测试选择第一个结果
            if app.paper_results:
                print("\n测试选择第一个结果:")
                app.on_result_select(0)
        except Exception as e:
            print(f"测试 {source} 搜索时出错: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    test_app_search() 