@echo off
echo 正在启动AI对话助手...
python src\ai_assistant.py
if errorlevel 1 (
    echo 启动失败。请确保已安装所有依赖。
    echo 运行 scripts\install_dependencies.bat 安装依赖。
    pause
) else (
    echo AI对话助手已关闭。
    pause
) 