@echo off
echo ===================================================
echo     AI论文助手 - 设置Linux脚本执行权限
echo ===================================================
echo.

echo 此脚本用于在Windows环境下设置Linux脚本的执行权限
echo 仅适用于Git Bash或WSL（Windows Subsystem for Linux）环境

REM 检查是否有Git Bash
where bash >nul 2>&1
if %errorlevel% equ 0 (
    echo 检测到Git Bash，使用bash设置权限...
    bash -c "chmod +x install_dependencies.sh"
    bash -c "chmod +x install_missing_libs.sh"
    bash -c "chmod +x start_assistant.sh"
    echo 权限设置完成！
) else (
    REM 检查是否有WSL
    where wsl >nul 2>&1
    if %errorlevel% equ 0 (
        echo 检测到WSL，使用WSL设置权限...
        wsl chmod +x install_dependencies.sh
        wsl chmod +x install_missing_libs.sh
        wsl chmod +x start_assistant.sh
        echo 权限设置完成！
    ) else (
        echo 未检测到Git Bash或WSL。
        echo 如果您需要在Linux环境中运行这些脚本，请手动设置执行权限：
        echo   chmod +x install_dependencies.sh install_missing_libs.sh start_assistant.sh
    )
)

echo.
pause 