@echo off
title Vitalis Daily Import

echo.
echo ========================================
echo   Vitalis Daily Import
echo ========================================
echo.
echo Starting Vitalis refresh...
echo.

cd /d C:\Projects\Vitalis

python run_daily_import.py

echo.
echo ========================================
echo   Vitalis refresh finished
echo ========================================
echo.
echo If you see no errors above, Vitalis is updated.
echo.
pause