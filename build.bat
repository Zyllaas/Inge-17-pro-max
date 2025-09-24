@echo off
echo Building Clipboard-AI...

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade pip and dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM Build the executable
echo Building executable...
pyinstaller ^
    --name ClipboardAI ^
    --onefile ^
    --noconsole ^
    --add-data "templates;templates" ^
    --add-data "config.toml;." ^
    --add-data ".env.example;." ^
    --distpath dist ^
    --workpath build ^
    app/main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build completed successfully!
    echo Executable: dist\ClipboardAI.exe
    echo.
    if exist dist\ClipboardAI.exe (
        echo File size: 
        dir dist\ClipboardAI.exe | findstr ClipboardAI.exe
    )
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
    echo Check the output above for errors.
)

pause