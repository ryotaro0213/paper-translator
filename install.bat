@echo off
REM Paper Translator -- Windows installer (wraps install.sh via Git Bash or WSL)

setlocal

where bash >nul 2>&1
if %errorlevel%==0 (
    bash "%~dp0install.sh" %*
    exit /b %errorlevel%
)

echo [error] bash not found.
echo    Install Git for Windows (https://git-scm.com/) or use WSL.
exit /b 1
