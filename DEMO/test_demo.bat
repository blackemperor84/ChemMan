@echo off
REM Test ChemMan Demo Configuration
REM This script tests if demo will work before building

echo ============================================================
echo   ChemMan Demo - Configuration Test
echo ============================================================
echo.

echo [1/4] Testing Python installation...
python --version
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python not found
    pause
    exit /b 1
)
echo ✅ Python OK
echo.

echo [2/4] Testing dependencies...
python -c "import flask; import pandas; import sqlalchemy; print('✅ All imports OK')"
if %errorlevel% neq 0 (
    echo ❌ ERROR: Missing dependencies
    echo Please run: pip install -r ../requirements.txt
    pause
    exit /b 1
)
echo.

echo [3/4] Checking Excel files...
if not exist "..\substancje_baza.xlsx" (
    echo ❌ ERROR: substancje_baza.xlsx not found in parent directory
    pause
    exit /b 1
)
if not exist "..\svhc.xlsx" (
    echo ❌ ERROR: svhc.xlsx not found in parent directory
    pause
    exit /b 1
)
echo ✅ Excel files OK
echo.

echo [4/4] Testing demo database creation...
python build_demo.py
if %errorlevel% neq 0 (
    echo ❌ ERROR: Failed to build demo database
    pause
    exit /b 1
)
echo.

echo ============================================================
echo   ✅ All Tests Passed!
echo ============================================================
echo.
echo You can now build the demo package:
echo    build_demo_package.bat
echo.
pause
