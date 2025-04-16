@echo off
echo ===================================================
echo      AI论文助手 - 快速安装缺失库工具
echo ===================================================
echo.

REM 设置控制台编码为UTF-8
chcp 65001 >nul
echo 控制台编码已设置为UTF-8

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python。请先安装Python 3.8或更高版本。
    pause
    exit /b 1
)

echo [安装] 正在安装chardet库...
python -m pip install chardet

echo [安装] 正在安装requests库...
python -m pip install requests

echo [安装] 正在安装beautifulsoup4库...
python -m pip install beautifulsoup4

echo [安装] 正在安装lxml库...
python -m pip install lxml

echo [安装] 正在安装urllib3库...
python -m pip install urllib3

echo [安装] 正在安装PyPDF2库...
python -m pip install PyPDF2

echo.
echo 正在验证关键依赖是否已正确安装...
python -c "import requests, chardet, bs4, lxml; print('验证成功')"
if %errorlevel% equ 0 (
    echo.
    echo [成功] 所有关键依赖已正确安装!
) else (
    echo.
    echo [警告] 部分库可能未正确安装，请检查上面的输出信息。
)

echo.
echo ===================================================
echo 如果还有其他缺失的库，请使用以下命令手动安装:
echo python -m pip install 库名
echo ===================================================
echo.
pause 