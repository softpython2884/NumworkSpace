@echo off
REM Build a single-file NOVA.exe on Windows.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Setting up first ...
    call play.cmd --help >nul 2>&1
)
set "VPY=%~dp0.venv\Scripts\python.exe"
if not exist "%VPY%" set "VPY=python"

"%VPY%" -m pip install --quiet --upgrade pyinstaller
if errorlevel 1 (
    echo Could not install PyInstaller.
    pause
    exit /b 1
)

"%VPY%" tools\make_icon.py
"%VPY%" -m PyInstaller --noconfirm --clean nova.spec
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Built: %~dp0dist\NOVA.exe
pause
endlocal
