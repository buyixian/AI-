import paper_downloader_fixed
import sys

def test_search_function(query="机器学习", source="Google Scholar"):
    """测试论文搜索功能（终端版本）"""
    print(f"开始搜索：{query}，来源：{source}")
    
    try:
        # 初始化PaperDownloader
        downloader = paper_downloader_fixed.PaperDownloader()
        
        # 检查搜索源是否有效
        if source not in downloader.sources and source not in ["百度学术", "中国知网"]:
            print(f"错误：不支持的搜索源 '{source}'")
            print(f"支持的搜索源: {', '.join(downloader.sources + ['百度学术', '中国知网'])}")
            return
        
        # 特殊处理百度学术和中国知网
        if source == "百度学术":
            print("\n百度学术搜索需要在浏览器中进行。")
            print(f"搜索链接: https://xueshu.baidu.com/s?wd={query}")
            return
        
        if source == "中国知网":
            print("\n中国知网搜索需要在浏览器中进行。")
            print(f"搜索链接: https://kns.cnki.net/kns8/defaultresult/index?kw={query}")
            return
        
        # 执行搜索
        print("搜索中，请稍候...")
        results, message = downloader.search_papers(query, source)
        
        # 显示结果数量和状态
        print(f"\n搜索结果: {message}")
        print(f"找到 {len(results)} 个结果\n")
        
        # 显示前5个结果
        max_display = min(5, len(results))
        for i, paper in enumerate(results[:max_display], 1):
            print(f"结果 {i}:")
            print(f"  标题: {paper.get('title', '无标题')}")
            print(f"  作者: {paper.get('authors', '未知作者')}")
            print(f"  年份: {paper.get('year', '未知年份')}")
            
            # 显示引用和期刊信息（如果有）
            if 'citations' in paper and paper['citations'] != 'N/A':
                print(f"  引用次数: {paper.get('citations', '未知')}")
            if 'venue' in paper and paper['venue']:
                print(f"  发表于: {paper.get('venue', '未知')}")
            
            # 显示摘要
            abstract = paper.get('abstract', '无摘要')
            if abstract and len(abstract) > 150:
                abstract = abstract[:150] + "..."
            print(f"  摘要: {abstract}")
            
            # 显示链接
            print(f"  链接: {paper.get('url', '无链接')}")
            print("-" * 80)
            
        if len(results) > max_display:
            print(f"\n还有 {len(results) - max_display} 个结果未显示。")
            
        return results
            
    except Exception as e:
        print(f"搜索过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 解析命令行参数
    query = "机器学习"  # 默认查询
    source = "Google Scholar"  # 默认来源
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    if len(sys.argv) > 2:
        source = sys.argv[2]
    
    # 执行搜索
    test_search_function(query, source)
    
    # 等待用户按键后退出
    input("\n按回车键退出...") 