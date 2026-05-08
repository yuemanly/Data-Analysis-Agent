@echo off
setlocal enabledelayedexpansion

REM ========================================
REM Chart Generate Pro - Test Suite
REM 功能：不闪退 + 自动记录日志 + 出错停住
REM ========================================

cd /d "%~dp0"

REM ---- 日志文件（按时间戳命名）----
set "LOG_DIR=%~dp0logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM 生成时间戳（兼容常见中文/英文系统）
for /f "tokens=1-3 delims=/-. " %%a in ("%date%") do (
    set "D1=%%a"
    set "D2=%%b"
    set "D3=%%c"
)
for /f "tokens=1-3 delims=:., " %%a in ("%time%") do (
    set "T1=%%a"
    set "T2=%%b"
    set "T3=%%c"
)

REM 处理可能的前导空格（例如  9:05:01）
set "T1=%T1: =0%"

REM 尝试拼 YYYYMMDD_HHMMSS（不同地区日期格式可能略有差异）
set "STAMP=%D1%%D2%%D3%_%T1%%T2%%T3%"
set "LOG_FILE=%LOG_DIR%\run_%STAMP%.log"

echo.
echo ========================================
echo Chart Generate Pro - Test Suite
echo ========================================
echo Log file: "%LOG_FILE%"
echo.

echo [INFO] Script started at %date% %time% > "%LOG_FILE%"
echo [INFO] Working dir: %cd% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM ---- 检查 Python ----
python --version >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    echo [ERROR] Python not found. Please install Python 3.8+ >> "%LOG_FILE%"
    echo.
    echo 详情请查看日志: "%LOG_FILE%"
    pause
    exit /b 1
)

REM ---- [1/3] Smoke tests ----
echo [1/3] Running smoke tests...
echo [1/3] Running smoke tests... >> "%LOG_FILE%"
python Test\test_smoke_all.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [FAIL] Smoke tests failed!
    echo [FAIL] Smoke tests failed! >> "%LOG_FILE%"
    echo.
    echo 详情请查看日志: "%LOG_FILE%"
    pause
    exit /b 1
)
echo [OK] Smoke tests passed
echo [OK] Smoke tests passed >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM ---- [2/3] Diagnostics ----
echo.
echo [2/3] Running diagnostics...
echo [2/3] Running diagnostics... >> "%LOG_FILE%"
python Test\diagnose.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [FAIL] Diagnostics failed!
    echo [FAIL] Diagnostics failed! >> "%LOG_FILE%"
    echo.
    echo 详情请查看日志: "%LOG_FILE%"
    pause
    exit /b 1
)
echo [OK] Diagnostics passed
echo [OK] Diagnostics passed >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM ---- [3/3] Start app ----
echo.
echo [3/3] Starting application...
echo Starting Flask server on http://localhost:5015
echo Press Ctrl+C to stop
echo.
echo [3/3] Starting application... >> "%LOG_FILE%"
echo [INFO] Starting Flask server on http://localhost:5015 >> "%LOG_FILE%"
echo [INFO] Press Ctrl+C to stop >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

python app_pro.py >> "%LOG_FILE%" 2>&1
set "APP_EXIT=%ERRORLEVEL%"

echo. >> "%LOG_FILE%"
echo [INFO] app_pro.py exited with code %APP_EXIT% at %date% %time% >> "%LOG_FILE%"

if not "%APP_EXIT%"=="0" (
    echo [WARN] Application exited with code %APP_EXIT%
    echo [WARN] Application exited with code %APP_EXIT% >> "%LOG_FILE%"
) else (
    echo [OK] Application exited normally
    echo [OK] Application exited normally >> "%LOG_FILE%"
)

echo.
echo 脚本执行结束。日志文件：
echo "%LOG_FILE%"
echo.
pause
endlocal
exit /b %APP_EXIT%