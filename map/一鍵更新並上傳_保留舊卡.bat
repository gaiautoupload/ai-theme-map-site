@echo off
chcp 65001 >nul
setlocal
cd /d D:\map

REM === AI Theme Map one-click pipeline ===
REM 文章主體由地端/遠端 vLLM 模型撰寫；搜尋採白名單 RSS；發布到 GitHub Pages repo。
set MAP_VLLM_URL=https://vllm-a5000.iii-ei-stack.com/v1/chat/completions
set MAP_MODEL_NAME=cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit
set MAP_SEARCH_MODE=search_augmented
set MAP_SEARCH_BACKEND=whitelist_rss
set MAP_SEARCH_MIN_DELAY=3.5
set MAP_SEARCH_MAX_DELAY=7.5
set MAP_SEARCH_FETCH_ENABLED=1
set MAP_DISCOVERY_RUN_TOP=5
set MAP_SITE_REPO_DIR=D:\ai-theme-map-site
set MAP_SITE_URL=https://gaiautoupload.github.io/ai-theme-map-site/

echo.
echo [AI Theme Map] 一鍵更新並上傳
echo - 使用 vLLM 撰寫新主題文章
echo - 保留舊卡並把新卡放最上面
echo - 補齊資金流向/火勢推演與產業結構分層
echo - 發布並 push 到 GitHub Pages
echo.

python -X utf8 run_one_click_update_and_publish.py
if errorlevel 1 goto :fail

echo.
echo 完成。網站：%MAP_SITE_URL%
pause
exit /b 0

:fail
echo.
echo 更新或上傳失敗，請看上方錯誤訊息。
pause
exit /b 1
