@echo off
cd /d C:\Projects\Vitalis

echo ========================================
echo Vitalis Daily Health Sync
echo ========================================

echo Running Health Connect sync...
python cloud\run_health_connect_sync.py

if errorlevel 1 (
  echo Health Connect sync failed.
  pause
  exit /b 1
)

echo.
echo Vitalis daily health sync complete.
pause