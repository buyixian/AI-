# AI对话助手

一个功能强大的AI对话工具，支持多种API调用、知识库管理和文献下载功能。

## 功能特点

- 支持多种AI API（OpenAI、Azure OpenAI、本地模型等）
- 知识库管理系统，支持上传和检索文档
- 文献搜索和下载功能，支持多个学术搜索引擎
- 简洁美观的图形用户界面
- 双击启动脚本，使用方便
- AI对话参数控制，支持上下文数量限制和流式传输调整

## 使用说明

### 安装依赖

在使用前，请先安装必要的Python依赖包：

```
pip install -r requirements.txt
```

或使用提供的安装脚本：
- Windows: 运行 `install_dependencies.bat`
- Linux/Mac: 运行 `install_dependencies.sh`

### 启动方式

1. 双击 `start_assistant.bat` 文件启动程序
2. 或者在命令行中运行 `python src/ai_assistant.py`

### 配置API

1. 在"API设置"选项卡中配置您的API密钥和其他参数
2. 支持OpenAI、Azure OpenAI和本地模型等多种接口
3. 设置保存在 `config/settings.json` 文件中
4. 可调整上下文窗口大小、流式输出、温度、最大生成长度等通用参数

### 知识库管理

1. 在"知识库"选项卡上传文档（支持PDF、TXT、DOCX等格式）
2. 上传的文档将保存在 `knowledge_base` 目录中
3. 可以在对话中引用知识库中的信息

### 文献下载

1. 在"文献下载"选项卡搜索学术论文
2. 支持从多个学术搜索引擎查找文献
3. 可以直接下载文献或打开原始链接

### AI对话参数调整

1. 在"设置"选项卡中找到"通用参数设置"部分
2. 调整上下文窗口大小控制AI记忆的对话轮数
3. 开启/关闭流式输出，控制AI回答的显示方式
4. 调整温度参数改变AI回答的创造性
5. 设置最大生成长度限制AI回答的长度
6. 详细说明请参阅 `docs/API参数说明.md`

## 系统要求

- Python 3.6+
- Windows/macOS/Linux操作系统

## 目录结构

项目采用以下目录结构组织文件：

```
AI-/
├── src/                      # 核心源代码
│   ├── ai_assistant.py       # 主助手代码
│   ├── api_manager.py        # API管理
│   ├── knowledge_manager.py  # 知识库管理
│   └── paper_downloader.py   # 论文下载器
│ 
├── scripts/                  # 其他辅助脚本
│   └── test_download.bat     # 测试下载脚本
│
├── tests/                    # 测试代码
│   ├── debug_app_search.py
│   ├── test_gsapp.py
│   └── 其他测试文件
│
├── api_plugins/              # API插件
├── config/                   # 配置文件
├── knowledge_base/           # 知识库
├── downloaded_papers/        # 下载的论文
│
├── README.md                 # 项目说明
├── requirements.txt          # 依赖列表
├── install_dependencies.bat  # Windows安装依赖脚本
├── install_dependencies.sh   # Linux/Mac安装依赖脚本
├── install_missing_libs.bat  # Windows安装缺失库脚本
├── install_missing_libs.sh   # Linux/Mac安装缺失库脚本
├── setup_permissions.bat     # 权限设置脚本
├── start_assistant.bat       # Windows启动脚本
└── start_assistant.sh        # Linux/Mac启动脚本
```

## 开发者信息

如需二次开发或贡献代码，请按照以下指南：

1. 核心代码位于 `src` 目录中
2. 使用 `tests` 目录中的脚本进行功能测试
3. 添加新功能时请保持目录结构的一致性
4. 配置文件统一放在 `config` 目录中

详细的依赖信息请参考 `docs/DEPENDENCIES.md` 文件。

## 故障排除

### AI对话功能不工作的常见问题

1. **API管理器功能问题**
   - 已添加缺失的`get_available_apis`方法，确保API选择下拉菜单正常工作
   - 改进了`call_deepseek_api`方法的错误处理和连接逻辑

2. **连接问题**
   - 如果无法连接到DeepSeek API服务器，检查网络连接和防火墙设置
   - 确认API密钥的有效性

3. **文件编码问题**
   - 所有文件应使用UTF-8编码，避免中文显示乱码
   - 控制台应设置为代码页65001（UTF-8）

4. **依赖项问题**
   - 确保安装了正确版本的OpenAI库（1.73.0或更高）
   - 如果遇到问题，运行`install_missing_libs.bat`安装缺失依赖

5. **流式输出问题**
   - 如果流式输出显示异常，尝试关闭流式输出功能
   - 某些API可能不支持流式输出，会自动退回到标准输出模式

### 最近更新
- 优化了温度参数调整界面，添加实时数值显示
- 改进了对话显示格式，使用彩色标签提高可读性
- 新增了参数测试按钮，便于快速测试不同参数设置
- 新增AI对话参数控制功能，可调整上下文窗口大小和流式输出
- 添加温度和最大生成长度控制，优化对话体验
- 修复了API管理器中的问题，使AI对话功能恢复正常
- 改进了错误处理，提供更有用的错误信息
- 优化了DeepSeek API的连接方式

如果仍然遇到问题，请检查日志或联系技术支持。 