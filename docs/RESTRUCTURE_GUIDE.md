# 项目重构指南

为了提高项目的可读性和可维护性，建议将目录结构按以下方式重新组织：

## 推荐的目录结构

```
AI-/
├── src/                      # 核心源代码
│   ├── __init__.py           # 使src成为Python模块
│   ├── ai_assistant.py       # 主助手代码
│   ├── api_manager.py        # API管理
│   ├── knowledge_manager.py  # 知识库管理
│   ├── paper_downloader.py   # 论文下载器
│   └── paper_downloader_fixed.py
│ 
├── scripts/                  # 辅助脚本
│   ├── install_dependencies.bat
│   ├── install_dependencies.sh
│   ├── install_missing_libs.bat
│   ├── install_missing_libs.sh
│   ├── setup_permissions.bat
│   └── test_download.bat
│
├── tests/                    # 测试代码
│   ├── debug_app_search.py
│   ├── debug_google_scholar.py
│   ├── debug_specific_source.py
│   ├── search_test.py
│   ├── test_gsapp.py
│   └── test_search_direct.py
│
├── backup/                   # 备份文件
│   ├── ai_assistant.bak
│   └── ai_assistant_backup.py
│
├── docs/                     # 文档
│   └── DEPENDENCIES.md
│
├── api_plugins/              # API插件(保持原位置)
├── config/                   # 配置文件(保持原位置)
├── knowledge_base/           # 知识库(保持原位置)
├── downloaded_papers/        # 下载的论文(保持原位置)
│
├── README.md                # 留在根目录
├── requirements.txt         # 留在根目录
├── start_assistant.bat      # 留在根目录
└── start_assistant.sh       # 留在根目录
```

## 移动文件的步骤

请按照以下步骤手动移动文件：

1. 创建所有需要的目录：`src`, `scripts`, `tests`, `backup`, `docs`
2. 移动核心代码文件到 `src` 目录：
   - `ai_assistant.py`
   - `api_manager.py`
   - `knowledge_manager.py`
   - `paper_downloader.py`
   - `paper_downloader_fixed.py`
   - `paper_downloader_new.py`

3. 移动脚本文件到 `scripts` 目录：
   - `install_dependencies.bat`
   - `install_dependencies.sh`
   - `install_missing_libs.bat`
   - `install_missing_libs.sh`
   - `setup_permissions.bat`
   - `test_download.bat`

4. 移动测试文件到 `tests` 目录：
   - `debug_app_search.py`
   - `debug_google_scholar.py`
   - `debug_specific_source.py`
   - `search_test.py`
   - `test.py`
   - `test_gsapp.py`
   - `test_search_direct.py`

5. 移动备份文件到 `backup` 目录：
   - `ai_assistant.bak`
   - `ai_assistant_backup.py`

6. 移动文档文件到 `docs` 目录：
   - `DEPENDENCIES.md`

7. 留在根目录的文件：
   - `README.md`
   - `requirements.txt`
   - `requirements.backup.txt`
   - `start_assistant.bat`
   - `start_assistant.sh`
   - `.gitattributes`

## 更新导入路径

移动文件后，需要更新Python文件中的导入路径，确保模块之间的引用正确。

在 `src` 目录中创建 `__init__.py` 文件，使其成为一个正式的Python包，便于导入。

## 更新启动脚本

移动文件后，需要更新 `start_assistant.bat` 和 `start_assistant.sh` 脚本中的路径，确保它们能正确找到 `ai_assistant.py` 文件。

例如，修改为：
```bash
# start_assistant.sh
python src/ai_assistant.py
```

```batch
:: start_assistant.bat
python src\ai_assistant.py
```

## 建议的后续优化

1. 添加单元测试
2. 创建更详细的文档
3. 统一命名约定
4. 创建更明确的模块分层 