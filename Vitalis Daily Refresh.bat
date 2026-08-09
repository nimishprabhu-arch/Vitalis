@echo off
cd /d C:\Projects\Vitalis

echo ========================================
echo   Vitalis daily refresh started
echo ========================================
echo.

python run_daily_import.py

echo.
echo ========================================
echo   Vitalis refresh finished
echo ========================================
pause