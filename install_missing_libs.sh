#!/bin/bash

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}     AI论文助手 - 快速安装缺失库工具 (Linux)     ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误]${NC} 未找到Python3。请安装Python 3.8或更高版本。"
    exit 1
fi

# 检查pip是否可用
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}[警告]${NC} 未找到pip3，请先安装pip。"
    echo "例如: sudo apt install python3-pip"
    exit 1
fi

# 安装关键库
echo -e "${BLUE}[安装]${NC} 正在安装chardet库..."
pip3 install chardet

echo -e "${BLUE}[安装]${NC} 正在安装requests库..."
pip3 install requests

echo -e "${BLUE}[安装]${NC} 正在安装beautifulsoup4库..."
pip3 install beautifulsoup4

echo -e "${BLUE}[安装]${NC} 正在安装lxml库..."
pip3 install lxml

echo -e "${BLUE}[安装]${NC} 正在安装urllib3库..."
pip3 install urllib3

echo -e "${BLUE}[安装]${NC} 正在安装PyPDF2库..."
pip3 install PyPDF2

# 验证
echo ""
echo -e "${BLUE}[验证]${NC} 正在验证关键依赖是否已正确安装..."
if python3 -c "import requests, chardet, bs4, lxml; print('验证成功')" &> /dev/null; then
    echo -e "${GREEN}[成功]${NC} 所有关键依赖已正确安装!"
else
    echo -e "${YELLOW}[警告]${NC} 部分库可能未正确安装，请检查上面的输出信息。"
fi

echo ""
echo -e "${BLUE}=================================================${NC}"
echo "如果还有其他缺失的库，请使用以下命令手动安装:"
echo "  pip3 install 库名"
echo -e "${BLUE}=================================================${NC}"
echo "" 