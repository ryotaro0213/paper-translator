@echo off
REM Paper Translator (Codex) — Windows wrapper for install.sh

setlocal

where bash >nul 2>&1
if %errorlevel%==0 (
    bash "%~dp0install.sh" %*
    exit /b %errorlevel%
)

echo [error] bash not found.
echo    Install Git for Windows (https://git-scm.com/) or use WSL.
exit /b 1
