@echo off
cd /d C:\Projects\Vitalis

echo ========================================
echo Vitalis Repo Clean Check
echo ========================================
echo.

git status --short > "%TEMP%\vitalis_git_status.txt"

for %%A in ("%TEMP%\vitalis_git_status.txt") do (
  if %%~zA==0 (
    echo Repo is clean. Dragon asleep.
  ) else (
    echo Repo has pending changes:
    echo.
    type "%TEMP%\vitalis_git_status.txt"
  )
)

echo.
pause