@echo off
REM Development helper script for Clipboard-AI

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="setup" goto setup
if "%1"=="test" goto test
if "%1"=="lint" goto lint
if "%1"=="build" goto build
if "%1"=="clean" goto clean
if "%1"=="run" goto run
goto invalid

:help
echo Clipboard-AI Development Helper
echo.
echo Usage: dev.bat [command]
echo.
echo Commands:
echo   setup    - Set up development environment
echo   test     - Run all tests
echo   lint     - Run code linting and formatting
echo   build    - Build the executable
echo   clean    - Clean build artifacts
echo   run      - Run the app in development mode
echo   help     - Show this help
echo.
goto end

:setup
echo Setting up development environment...
python setup.py
goto end

:test
echo Running tests...
if not exist venv (
    echo Virtual environment not found. Run 'dev setup' first.
    goto end
)
call venv\Scripts\activate.bat
python -m pytest tests\ -v
goto end

:lint
echo Running code linting and formatting...
if not exist venv (
    echo Virtual environment not found. Run 'dev setup' first.
    goto end
)
call venv\Scripts\activate.bat
echo.
echo Running black...
black app/ tests/ --check --diff
echo.
echo Running ruff...
ruff check app/ tests/
echo.
echo Running mypy...
mypy app/ --ignore-missing-imports
goto end

:build
echo Building executable...
if not exist venv (
    echo Virtual environment not found. Run 'dev setup' first.
    goto end
)
call build.bat
goto end

:clean
echo Cleaning build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist out rmdir /s /q out
if exist *.spec del *.spec
echo Cleaned build artifacts.
goto end

:run
echo Running in development mode...
if not exist venv (
    echo Virtual environment not found. Run 'dev setup' first.
    goto end
)
call venv\Scripts\activate.bat
python app/main.py
goto end

:invalid
echo Invalid command: %1
echo Run 'dev help' for available commands.
goto end

:end