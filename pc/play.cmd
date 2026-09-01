@echo off
REM NOVA - install what is needed, then play. Windows.
REM
REM   play.cmd                  first run installs, later runs just launch
REM   play.cmd --fullscreen     any option is passed straight to the game
REM
REM Everything lands in pc\.venv; delete that folder to start over.
setlocal
cd /d "%~dp0"
set "VENV=%~dp0.venv"

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo NOVA needs Python 3.8 or newer.
    echo Install it from https://www.python.org/downloads/
    echo Tick "Add Python to PATH" in the installer, then run this again.
    pause
    exit /b 1
)

%PY% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if errorlevel 1 (
    echo Your Python is older than 3.8. Please update it.
    pause
    exit /b 1
)

if not exist "%VENV%\Scripts\python.exe" (
    echo Creating a virtual environment in pc\.venv ...
    %PY% -m venv "%VENV%"
    if errorlevel 1 (
        echo Could not create the virtual environment.
        pause
        exit /b 1
    )
)

set "VPY=%VENV%\Scripts\python.exe"
"%VPY%" -m pip install --quiet --upgrade pip >nul 2>&1

"%VPY%" -c "import pygame" >nul 2>&1
if errorlevel 1 (
    REM pygame-ce first: the community fork ships wheels for new Python
    REM releases months before upstream pygame does. Same "import pygame".
    echo Installing pygame-ce and numpy ...
    "%VPY%" -m pip install --quiet pygame-ce numpy
    if errorlevel 1 (
        echo pygame-ce did not install; falling back to pygame ...
        "%VPY%" -m pip install --quiet pygame numpy
        if errorlevel 1 (
            echo Could not install the dependencies.
            echo Try by hand:  "%VPY%" -m pip install pygame-ce numpy
            pause
            exit /b 1
        )
    )
)

echo Launching NOVA ...
"%VPY%" "%~dp0nova.py" %*
if errorlevel 1 pause
endlocal
