@echo off
chcp 65001 >nul
setlocal
cd /d D:\ai-theme-map-site

set "MAP_VLLM_URL=https://vllm-a5000.iii-ei-stack.com/v1/chat/completions"
set "MAP_MODEL_NAME=cyankiwi/gemma-4-31B-it-AWQ-4bit"
set "MAP_MODEL_AUTO_DISCOVER=1"
set "MAP_SEARCH_MODE=search_augmented"
set "MAP_SEARCH_BACKEND=whitelist_rss"
set "MAP_SEARCH_MIN_DELAY=3.5"
set "MAP_SEARCH_MAX_DELAY=7.5"
set "MAP_SEARCH_FETCH_ENABLED=1"
set "PYTHONPATH=%CD%\.python-packages;%PYTHONPATH%"

set "PYTHON_EXE=python"
where python >nul 2>nul
if errorlevel 1 (
    if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
        set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    ) else if exist "C:\Users\pioterlee\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
        set "PYTHON_EXE=C:\Users\pioterlee\AppData\Local\Python\pythoncore-3.14-64\python.exe"
    ) else (
        for /d %%d in ("%USERPROFILE%\AppData\Local\Programs\Python\Python*") do (
            if exist "%%d\python.exe" set "PYTHON_EXE=%%d\python.exe"
        )
    )
)

echo Starting daily pipeline...
echo Python executable: %PYTHON_EXE%
"%PYTHON_EXE%" run_daily_pipeline.py
if errorlevel 1 goto :fail

echo.
echo Daily pipeline completed successfully.
timeout /t 10
exit /b 0

:fail
echo.
echo Daily pipeline failed.
timeout /t 10
exit /b 1
