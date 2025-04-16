#!/bin/bash

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}        AI论文助手 - 依赖安装工具 (Linux)        ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# 检查Python是否安装
echo -e "${BLUE}[检查]${NC} 正在检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误]${NC} 未找到Python3。请安装Python 3.8或更高版本。"
    echo "您可以使用系统包管理器安装，例如："
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Fedora/RHEL: sudo dnf install python3 python3-pip"
    echo "  Arch Linux: sudo pacman -S python python-pip"
    exit 1
fi

# 显示Python版本
python3 --version

# 检查pip是否可用
echo -e "${BLUE}[检查]${NC} 正在检查pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}[警告]${NC} 未找到pip3，尝试安装pip..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -S python-pip
    else
        echo -e "${RED}[错误]${NC} 无法自动安装pip，请手动安装。"
        exit 1
    fi
fi

# 检查网络连接
echo -e "${BLUE}[检查]${NC} 正在检查网络连接..."
if ! ping -c 1 pypi.org &> /dev/null; then
    echo -e "${YELLOW}[警告]${NC} 无法连接到PyPI仓库，可能会影响安装进程。"
    echo "请检查您的网络连接并确保能够访问 pypi.org"
    read -p "是否仍要继续安装？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 更新pip
echo -e "${BLUE}[更新]${NC} 正在更新pip..."
pip3 install --upgrade pip

# 备份requirements文件
echo -e "${BLUE}[备份]${NC} 备份当前的requirements.txt..."
cp requirements.txt requirements.backup.txt 2>/dev/null || :

# 安装依赖
echo ""
echo -e "${BLUE}[安装]${NC} 开始安装所有必要依赖..."
echo "这可能需要几分钟时间，请耐心等待..."
echo ""

pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[警告]${NC} 安装依赖时遇到问题。"
    echo "尝试使用镜像源进行安装..."
    pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}[警告]${NC} 使用镜像源安装依赖仍然失败。"
        echo "尝试逐个安装依赖..."
        
        while read line; do
            # 跳过空行和注释
            [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
            
            # 提取包名
            package=$(echo "$line" | cut -d'>' -f1)
            echo "正在安装 $package..."
            pip3 install "$package"
        done < requirements.txt
    fi
fi

# 验证安装结果
echo ""
echo -e "${BLUE}[验证]${NC} 正在验证关键依赖是否已正确安装..."
if python3 -c "import requests, chardet, bs4, PyPDF2, lxml; print('验证成功')" &> /dev/null; then
    echo -e "${GREEN}[成功]${NC} 所有关键依赖已正确安装!"
else
    echo -e "${YELLOW}[警告]${NC} 部分关键依赖可能未正确安装。"
    echo "请检查上面的输出信息，或者尝试手动安装缺少的模块。"
fi

echo ""
echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}依赖安装程序执行完成。${NC}"
echo "如果遇到导入错误，请尝试手动安装缺少的模块:"
echo "  pip3 install 模块名"
echo -e "${BLUE}=================================================${NC}"
echo "" 