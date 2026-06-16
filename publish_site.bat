@echo off
chcp 65001 >nul
setlocal
cd /d D:\ai-theme-map-site

set MAP_VLLM_URL=https://vllm-a5000.iii-ei-stack.com/v1/chat/completions
set MAP_MODEL_NAME=cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit

:: 偵測 Python 路徑
set PYTHON_EXE=python
where python >nul 2>nul
if errorlevel 1 (
    if exist "C:\Users\pioterlee\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
        set PYTHON_EXE="C:\Users\pioterlee\AppData\Local\Python\pythoncore-3.14-64\python.exe"
    ) else (
        for /d %%d in ("%USERPROFILE%\AppData\Local\Programs\Python\Python*") do (
            if exist "%%d\python.exe" set PYTHON_EXE="%%d\python.exe"
        )
    )
)

%PYTHON_EXE% publish_site.py
timeout /t 10

