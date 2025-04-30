import paper_downloader_fixed
import traceback

def test_google_scholar_search():
    """特别测试Google Scholar搜索功能"""
    print("开始测试Google Scholar搜索...")
    
    # 初始化下载器
    pd = paper_downloader_fixed.PaperDownloader()
    source = "Google Scholar"
    query = "机器学习"
    
    try:
        print(f"执行搜索: {query} (来源: {source})")
        
        # 直接调用搜索方法
        results, message = pd.search_papers(query, source)
        
        print(f"搜索结果状态: {message}")
        print(f"结果类型: {type(results)}")
        print(f"结果数量: {len(results)}")
        
        if results:
            # 显示详细结果
            print("\n详细结果:")
            for i, item in enumerate(results):
                print(f"\n结果 {i+1}:")
                print(f"  类型: {type(item)}")
                if hasattr(item, 'keys'):
                    print(f"  键: {list(item.keys())}")
                    
                    # 安全获取属性并显示
                    try:
                        title = item.get('title', '未知标题')
                        url = item.get('url', '无链接')
                        print(f"  标题: {title}")
                        print(f"  链接: {url}")
                    except Exception as e:
                        print(f"  获取属性出错: {str(e)}")
                else:
                    print(f"  内容: {item}")
                    
            # 模拟选择第一个结果
            if len(results) > 0:
                print("\n选择第一个结果:")
                selected = results[0]
                
                try:
                    print(f"选中项类型: {type(selected)}")
                    
                    if hasattr(selected, 'get'):
                        title = selected.get('title', '未知标题')
                        abstract = selected.get('abstract', '无摘要')
                        print(f"标题: {title}")
                        print(f"摘要: {abstract}")
                    else:
                        print(f"选中项不是字典: {selected}")
                except Exception as e:
                    print(f"处理选中项时出错: {str(e)}")
                    traceback.print_exc()
                    
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_google_scholar_search() 