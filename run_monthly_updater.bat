@echo off
cd /d "%~dp0"
echo ==================================================
echo  Starting Monthly LLM Wiki Stock Update Pipeline
echo  Time: %date% %time%
echo ==================================================
python monthly_stock_updater.py
echo ==================================================
echo  Pipeline Completed.
echo ==================================================
pause
