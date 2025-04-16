import paper_downloader_fixed
import traceback

def test_search(query="机器学习", source="Semantic Scholar"):
    """测试论文搜索功能"""
    print(f"测试论文搜索: {query} (来源: {source})")
    
    try:
        # 初始化下载器
        pd = paper_downloader_fixed.PaperDownloader()
        print("初始化下载器成功")
        
        # 确保是支持的来源
        if source not in pd.sources:
            print(f"不支持的来源: {source}")
            print(f"支持的来源: {pd.sources}")
            return
            
        # 搜索
        print(f"\n搜索中...")
        try:
            results, msg = pd.search_papers(query, source)
            print(f"搜索结果消息: {msg}")
            print(f"搜索结果数量: {len(results)}")
            
            # 检查结果
            if not results:
                print("没有找到匹配的论文")
                return
                
            # 打印前3个结果
            print("\n搜索结果:")
            for i, paper in enumerate(results[:3], 1):
                print(f"\n结果 {i}:")
                if not isinstance(paper, dict):
                    print(f"  注意: 结果不是字典类型，而是 {type(paper)}")
                    print(f"  内容: {paper}")
                    continue
                    
                print(f"  标题: {paper.get('title', '无标题')}")
                print(f"  作者: {paper.get('authors', '未知作者')}")
                print(f"  年份: {paper.get('year', '未知年份')}")
                abstract = paper.get('abstract', '无摘要')
                if abstract and len(abstract) > 100:
                    abstract = abstract[:100] + "..."
                print(f"  摘要: {abstract}")
                print(f"  链接: {paper.get('url', '无链接')}")
            
        except Exception as e:
            print(f"搜索过程中出错: {str(e)}")
            print(traceback.format_exc())
            
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    # 测试默认搜索
    test_search()
    
    # 测试谷歌学术搜索
    print("\n" + "="*50)
    print("测试Google Scholar搜索")
    print("="*50)
    test_search("机器学习", "Google Scholar")
    
    # 用户可以修改这里指定查询关键词和来源
    # test_search("深度学习", "Arxiv") 