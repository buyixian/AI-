@echo off
echo 正在启动下载测试...
echo 这将启动AI助手并自动执行下载测试

REM 启动Python程序并传递测试标志
python ai_assistant.py --test-download

echo 测试完成
pause
