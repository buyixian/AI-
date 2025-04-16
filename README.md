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
pip install requests tkinter
```

### 启动方式

1. 双击 `start_assistant.bat` 文件启动程序
2. 或者在命令行中运行 `python ai_assistant.py`

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

## 开发者信息

如需二次开发或贡献代码，请查看源代码中的注释说明。主要文件结构：

- `ai_assistant.py` - 主程序文件
- `start_assistant.bat` - Windows启动脚本
- `config/` - 配置文件目录
- `knowledge_base/` - 知识库文件目录 