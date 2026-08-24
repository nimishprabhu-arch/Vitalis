@echo off
cd /d C:\Projects\Vitalis

echo ========================================
echo Vitalis API Deploy
echo ========================================

echo Deploying vitalis-api to Supabase...
npx supabase@latest functions deploy vitalis-api --project-ref ltnlhxsdmcsjpcpxvvxl

if errorlevel 1 (
  echo.
  echo Deploy failed.
  pause
  exit /b 1
)

echo.
echo Vitalis API deployed successfully.
pause