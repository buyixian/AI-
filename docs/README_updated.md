# AI对话助手

一个功能强大的AI对话工具，支持多种API调用、知识库管理和文献下载功能。

## 功能特点

- 支持多种AI API（OpenAI、Azure OpenAI、本地模型等）
- 知识库管理系统，支持上传和检索文档
- 文献搜索和下载功能，支持多个学术搜索引擎
- 简洁美观的图形用户界面
- 双击启动脚本，使用方便

## 使用说明

### 安装依赖

在使用前，请先安装必要的Python依赖包：

```
pip install -r requirements.txt
```

或使用提供的安装脚本：
- Windows: 运行 `scripts/install_dependencies.bat`
- Linux/Mac: 运行 `scripts/install_dependencies.sh`

### 启动方式

1. 双击 `start_assistant.bat` 文件启动程序
2. 或者在命令行中运行 `python src/ai_assistant.py`

### 配置API

1. 在"API设置"选项卡中配置您的API密钥和其他参数
2. 支持OpenAI、Azure OpenAI和本地模型等多种接口
3. 设置保存在 `config/settings.json` 文件中

### 知识库管理

1. 在"知识库"选项卡上传文档（支持PDF、TXT、DOCX等格式）
2. 上传的文档将保存在 `knowledge_base` 目录中
3. 可以在对话中引用知识库中的信息

### 文献下载

1. 在"文献下载"选项卡搜索学术论文
2. 支持从多个学术搜索引擎查找文献
3. 可以直接下载文献或打开原始链接

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
├── scripts/                  # 辅助脚本
│   ├── install_dependencies.bat
│   ├── install_dependencies.sh
│   └── 其他脚本文件
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