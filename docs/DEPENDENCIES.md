# AI论文助手依赖安装指南

## 所需依赖

AI论文助手运行需要以下主要依赖库：

- **requests**: 用于HTTP请求和下载文件
- **chardet**: 用于文件编码检测
- **beautifulsoup4 (bs4)**: 用于HTML/XML解析
- **lxml**: XML解析器
- **PyPDF2**: PDF文件操作
- **python-docx**: Word文档处理
- **其他支持库**: urllib3, certifi, idna等

## 安装方法

### 方法1：使用安装脚本（推荐）

#### Windows系统
1. 确保已安装Python 3.8或更高版本
2. 右键点击`install_dependencies.bat`，选择"以管理员身份运行"
3. 等待安装完成

#### Linux/macOS系统
1. 确保已安装Python 3.8或更高版本和pip3
2. 打开终端，进入项目目录
3. 执行以下命令：
   ```
   chmod +x install_dependencies.sh
   ./install_dependencies.sh
   ```
4. 等待安装完成

### 方法2：快速安装缺失库

如果只是缺少个别库，可以使用快速安装脚本：

#### Windows系统
1. 右键点击`install_missing_libs.bat`，选择"以管理员身份运行"

#### Linux/macOS系统
1. 打开终端，进入项目目录
2. 执行以下命令：
   ```
   chmod +x install_missing_libs.sh
   ./install_missing_libs.sh
   ```

### 方法3：手动安装

使用pip命令手动安装依赖：

```
pip install requests chardet beautifulsoup4 lxml PyPDF2 python-docx urllib3 certifi idna python-dateutil tqdm Pillow
```

或者一次性安装所有依赖：

```
pip install -r requirements.txt
```

## 常见问题

### 无法安装lxml

lxml库通常需要编译，可能在某些系统上安装失败。可以尝试：

#### Windows
```
pip install lxml-4.9.2-cp39-cp39-win_amd64.whl
```
(根据您的Python版本和系统架构选择合适的wheel文件)

#### Linux
```
sudo apt-get install python3-lxml
```
或
```
sudo apt-get install libxml2-dev libxslt-dev
pip install lxml
```

### pip命令未找到

如果系统未识别pip命令，请尝试使用：
- `python -m pip install ...`
- `python3 -m pip install ...`

### 安装缓慢或超时

可以使用国内镜像源加速：
```
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## 验证安装

运行以下命令验证是否所有依赖都已成功安装：

```python
python -c "import requests, chardet, bs4, PyPDF2, lxml; print('所有依赖已安装')"
```

如果没有显示错误信息，则表明依赖已正确安装。 