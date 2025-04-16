import paper_downloader_fixed
import traceback
import os
import sys

def debug_google_scholar():
    """详细调试谷歌学术搜索功能"""
    print("=== 开始调试谷歌学术搜索功能 ===")
    
    try:
        # 初始化下载器
        print("1. 初始化PaperDownloader...")
        pd = paper_downloader_fixed.PaperDownloader()
        
        # 搜索参数
        query = "机器学习"
        source = "Google Scholar"
        print(f"2. 准备搜索: 查询='{query}', 来源='{source}'")
        
        try:
            print("3. 开始执行搜索...")
            
            # 直接调用_search_google_scholar方法
            print("3.1 直接调用_search_google_scholar方法...")
            try:
                results, message = pd._search_google_scholar(query)
                print(f"3.2 _search_google_scholar返回: 状态='{message}', 结果数量={len(results) if results else 0}")
                
                # 检查结果类型
                print(f"3.3 结果类型: {type(results)}")
                if results:
                    if isinstance(results, list):
                        print(f"3.4 第一个结果类型: {type(results[0])}")
                        if isinstance(results[0], dict):
                            print(f"3.5 第一个结果键: {list(results[0].keys())}")
                    else:
                        print(f"3.4 结果不是列表类型")
            except Exception as inner_err:
                print(f"3.X 直接调用方法出错: {str(inner_err)}")
                traceback.print_exc()
            
            # 通过search_papers方法调用
            print("\n4. 通过search_papers方法调用...")
            try:
                full_results, full_message = pd.search_papers(query, source)
                print(f"4.1 search_papers返回: 状态='{full_message}', 结果数量={len(full_results) if full_results else 0}")
                
                # 检查结果类型
                print(f"4.2 结果类型: {type(full_results)}")
                if full_results:
                    if isinstance(full_results, list):
                        print(f"4.3 第一个结果类型: {type(full_results[0])}")
                        if isinstance(full_results[0], dict):
                            print(f"4.4 第一个结果键: {list(full_results[0].keys())}")
                    else:
                        print(f"4.3 结果不是列表类型")
                
                print("\n5. 尝试访问搜索结果的属性...")
                try:
                    for i, item in enumerate(full_results[:1]):  # 只检查第一个结果
                        print(f"5.1 结果 {i+1}:")
                        print(f"  - 类型: {type(item)}")
                        
                        if hasattr(item, 'keys'):
                            keys = list(item.keys())
                            print(f"  - 键: {keys}")
                            
                            # 尝试访问每个属性
                            for key in keys:
                                value = item.get(key, '未设置')
                                print(f"  - {key}: {type(value)}")
                                
                                # 如果是字符串，检查其长度
                                if isinstance(value, str):
                                    print(f"    长度: {len(value)}")
                                    if len(value) > 100:
                                        print(f"    预览: {value[:100]}...")
                                    else:
                                        print(f"    完整值: {value}")
                        else:
                            print(f"  - 不是字典类型")
                except Exception as attr_err:
                    print(f"5.X 访问属性时出错: {str(attr_err)}")
                    traceback.print_exc()
            except Exception as outer_err:
                print(f"4.X search_papers调用出错: {str(outer_err)}")
                traceback.print_exc()
            
        except Exception as e:
            print(f"搜索过程中出错: {str(e)}")
            traceback.print_exc()
        
        # 检查调试文件
        print("\n6. 检查调试文件...")
        debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug")
        debug_file = os.path.join(debug_dir, "google_scholar_response.html")
        
        if os.path.exists(debug_file):
            try:
                file_size = os.path.getsize(debug_file)
                print(f"6.1 找到调试文件: {debug_file} (大小: {file_size:,} 字节)")
                
                # 分析文件内容
                with open(debug_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(100)
                    print(f"6.2 文件开头: {content}...")
                    
                with open(debug_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "请证明您不是机器人" in content:
                        print("6.3 警告: Google要求验证码验证!")
                    elif "robot" in content.lower():
                        print("6.3 警告: 可能存在反爬虫检测!")
            except Exception as file_err:
                print(f"6.X 读取调试文件时出错: {str(file_err)}")
        else:
            print(f"6.0 未找到调试文件: {debug_file}")
    
    except Exception as e:
        print(f"调试过程中出错: {str(e)}")
        traceback.print_exc()
    
    print("\n=== 调试谷歌学术搜索功能完成 ===")

if __name__ == "__main__":
    debug_google_scholar() 