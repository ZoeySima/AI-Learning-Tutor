@echo off
REM AI Learning Tutor - Web launch script (Windows)

echo Checking dependencies...
python -m pip install -q -r requirements.txt -r requirements-web.txt

if "%ANTHROPIC_API_KEY%"=="" (
    echo.
    echo ERROR: ANTHROPIC_API_KEY environment variable not set.
    echo.
    echo Please set it first:
    echo   set ANTHROPIC_API_KEY=sk-ant-...
    echo.
    exit /b 1
)

echo Starting AI Learning Tutor Web...
echo.
python -m web.server
