@echo off
chcp 65001 >nul
setlocal
cd /d D:\map
set MAP_VLLM_URL=https://vllm-a5000.iii-ei-stack.com/v1/chat/completions
set MAP_MODEL_NAME=cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit
python publish_site.py
pause

