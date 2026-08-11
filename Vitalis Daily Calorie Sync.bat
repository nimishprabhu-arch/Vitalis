@echo off
cd /d C:\Projects\Vitalis

echo ========================================
echo Vitalis Daily Calorie Sync
echo ========================================

echo Importing Samsung calorie export...
python importers\import_samsung_calories.py

if errorlevel 1 (
  echo Calorie import failed.
  pause
  exit /b 1
)

echo Uploading updated snapshots to Supabase...
python cloud\upload_all_snapshots.py

if errorlevel 1 (
  echo Supabase upload failed.
  pause
  exit /b 1
)

echo.
echo Vitalis daily calorie sync complete.
pause