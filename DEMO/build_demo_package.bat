@echo off
REM Build ChemMan Demo Package for Windows
REM This script creates a standalone executable package

echo ============================================================
echo   ChemMan v2.0.0 - Building Demo Package
echo ============================================================
echo.

REM Step 1: Check if PyInstaller is installed
echo [1/5] Checking PyInstaller...
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)
echo ✅ PyInstaller ready
echo.

REM Step 2: Build demo database
echo [2/5] Building demo database...
python build_demo.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to build demo database
    pause
    exit /b 1
)
echo ✅ Demo database created
echo.

REM Step 3: Clean previous builds
echo [3/5] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo ✅ Cleaned
echo.

REM Step 4: Build executable with PyInstaller
echo [4/5] Building executable (this may take several minutes)...
pyinstaller chemman_demo.spec --clean
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)
echo ✅ Executable built
echo.

REM Step 5: Copy startup script
echo [5/5] Creating startup script...
(
echo @echo off
echo echo ============================================================
echo echo   ChemMan v2.0.0 - Demo Version
echo echo ============================================================
echo echo.
echo echo Starting ChemMan Demo...
echo echo.
echo echo Browser will open automatically in a few seconds.
echo echo.
echo chemman_demo.exe
echo pause
) > dist\ChemMan_Demo\START_CHEMMAN_DEMO.bat
echo ✅ Startup script created
echo.

REM Step 6: Copy README
copy README_DEMO.md dist\ChemMan_Demo\README.txt >nul

echo ============================================================
echo   ✅ Build Complete!
echo ============================================================
echo.
echo 📦 Package location: dist\ChemMan_Demo\
echo.
echo 🚀 To test the demo:
echo    1. Go to: dist\ChemMan_Demo\
echo    2. Double-click: START_CHEMMAN_DEMO.bat
echo    3. Login: admin / Demo1234
echo.
echo 📤 To distribute:
echo    - Zip the entire ChemMan_Demo folder
echo    - Send to colleagues/clients
echo.
pause
