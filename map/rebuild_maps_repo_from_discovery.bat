@echo off
chcp 65001 >nul
setlocal
cd /d D:\map
set MAP_VLLM_URL=https://vllm-a5000.iii-ei-stack.com/v1/chat/completions
set MAP_MODEL_NAME=cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit
set MAP_SEARCH_MODE=search_augmented
set MAP_SEARCH_BACKEND=whitelist_rss
set MAP_SEARCH_MIN_DELAY=3.5
set MAP_SEARCH_MAX_DELAY=7.5
set MAP_SEARCH_FETCH_ENABLED=1

python build_ticker_registry.py
if errorlevel 1 goto :fail
python evidence_builder.py
if errorlevel 1 goto :fail
python rebuild_maps_repo_from_discovery.py
if errorlevel 1 goto :fail
python publish_site.py
if errorlevel 1 goto :fail

echo.
echo Rebuild and publish completed successfully.
pause
exit /b 0
:fail
echo.
echo Rebuild and publish failed.
pause
exit /b 1
