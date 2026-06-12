@echo off
chcp 65001 >nul
setlocal

:: 設定工作目錄為此專案路徑
cd /d D:\ai-theme-map-site

:: 設定環境變數
set MAP_VLLM_URL=https://vllm-a5000.iii-ei-stack.com/v1/chat/completions
set MAP_MODEL_NAME=cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit
set MAP_SEARCH_MODE=search_augmented
set MAP_SEARCH_BACKEND=whitelist_rss
set MAP_SEARCH_MIN_DELAY=3.5
set MAP_SEARCH_MAX_DELAY=7.5
set MAP_SEARCH_FETCH_ENABLED=1

:: 設定日誌檔案路徑
set LOG_FILE=D:\ai-theme-map-site\daily_pipeline_auto.log

echo ========================================== >> "%LOG_FILE%"
echo 啟動每日自動排程更新: %date% %time% >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"

python run_daily_pipeline.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

echo 每日自動更新完成: %date% %time% >> "%LOG_FILE%"
echo SUCCESS >> "%LOG_FILE%"
exit /b 0

:fail
echo 每日自動更新失敗！請檢查此日誌以獲取錯誤詳情。: %date% %time% >> "%LOG_FILE%"
echo FAILED >> "%LOG_FILE%"
exit /b 1
