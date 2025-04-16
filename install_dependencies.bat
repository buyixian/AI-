@echo off
echo ===================================================
echo           AI论文助手 - 依赖安装工具
echo ===================================================
echo.

REM 设置控制台编码为UTF-8
chcp 65001 >nul
echo 控制台编码已设置为UTF-8

REM 检查Python是否安装
echo 正在检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8或更高版本。
    echo 您可以从 https://www.python.org/downloads/ 下载安装Python
    pause
    exit /b 1
)

REM 显示Python版本
python --version

REM 检查pip是否可用
echo 正在检查pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未找到pip，尝试安装pip...
    python -m ensurepip
    if %errorlevel% neq 0 (
        echo [错误] 无法安装pip，请手动安装。
        pause
        exit /b 1
    )
)

REM 检查网络连接
echo 正在检查网络连接...
ping -n 1 pypi.org >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 无法连接到PyPI仓库，可能会影响安装进程。
    echo 请检查您的网络连接并确保能够访问 pypi.org
    choice /C YN /M "是否仍要继续安装？(Y/N)"
    if %errorlevel% equ 2 exit /b 1
)

REM 更新pip
echo 正在更新pip...
python -m pip install --upgrade pip

REM 创建备份
echo 备份当前的requirements.txt...
copy requirements.txt requirements.backup.txt >nul 2>&1

REM 安装依赖
echo.
echo 开始安装所有必要依赖...
echo 这可能需要几分钟时间，请耐心等待...
echo.

python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 安装依赖时遇到问题。
    echo 尝试使用镜像源进行安装...
    python -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    if %errorlevel% neq 0 (
        echo [错误] 使用镜像源安装依赖仍然失败。
        echo 尝试逐个安装依赖...
        
        for /F "tokens=1,2 delims=>=" %%a in (requirements.txt) do (
            echo 正在安装 %%a...
            python -m pip install %%a
        )
    )
)

REM 最后检查安装是否成功
echo.
echo 正在验证关键依赖是否已正确安装...
python -c "import requests, chardet, bs4, PyPDF2, lxml; print('关键依赖验证成功!')" >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 部分关键依赖可能未正确安装。请检查上面的输出信息。
) else (
    echo [成功] 所有关键依赖已正确安装!
)

echo.
echo ===================================================
echo 依赖安装程序执行完成。
echo 如果遇到导入错误，请尝试手动安装缺少的模块: 
echo pip install 模块名
echo ===================================================
echo.
pause 