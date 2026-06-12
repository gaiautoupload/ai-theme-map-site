@echo off
chcp 65001 >nul
setlocal
cd /d D:\ai-theme-map-site

set MAP_VLLM_URL=https://vllm-a5000.iii-ei-stack.com/v1/chat/completions
set MAP_MODEL_NAME=cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit
set MAP_SEARCH_MODE=search_augmented
set MAP_SEARCH_BACKEND=whitelist_rss
set MAP_SEARCH_MIN_DELAY=3.5
set MAP_SEARCH_MAX_DELAY=7.5
set MAP_SEARCH_FETCH_ENABLED=1

echo 正在執行每日排程更新管線...
python run_daily_pipeline.py
if errorlevel 1 goto :fail

echo.
echo Daily pipeline completed successfully.
pause
exit /b 0

:fail
echo.
echo Daily pipeline failed.
pause
exit /b 1
