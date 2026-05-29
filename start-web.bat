@echo off
REM AI Learning Tutor - Web launch script (Windows)

echo Checking dependencies...
python -m pip install -q -r requirements.txt -r requirements-web.txt

if "%DEEPSEEK_API_KEY%"=="" (
    if "%ANTHROPIC_API_KEY%"=="" (
        echo.
        echo ERROR: No API key set.
        echo.
        echo Please set ONE of:
        echo   DeepSeek (recommended for Chinese):
        echo     set DEEPSEEK_API_KEY=sk-...
        echo     set AI_TUTOR_PROVIDER=deepseek
        echo.
        echo   Anthropic Claude:
        echo     set ANTHROPIC_API_KEY=sk-ant-...
        echo     set AI_TUTOR_PROVIDER=anthropic
        echo.
        exit /b 1
    )
)

echo Starting AI Learning Tutor Web...
echo.
python -m web.server
