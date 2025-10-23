#!/bin/bash
# Build ChemMan Demo Package for Linux/Mac
# This script creates a standalone executable package

echo "============================================================"
echo "  ChemMan v2.0.0 - Building Demo Package"
echo "============================================================"
echo

# Step 1: Check if PyInstaller is installed
echo "[1/5] Checking PyInstaller..."
python3 -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "PyInstaller not found. Installing..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install PyInstaller"
        exit 1
    fi
fi
echo "✅ PyInstaller ready"
echo

# Step 2: Build demo database
echo "[2/5] Building demo database..."
python3 build_demo.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build demo database"
    exit 1
fi
echo "✅ Demo database created"
echo

# Step 3: Clean previous builds
echo "[3/5] Cleaning previous builds..."
rm -rf build dist
echo "✅ Cleaned"
echo

# Step 4: Build executable with PyInstaller
echo "[4/5] Building executable (this may take several minutes)..."
pyinstaller chemman_demo.spec --clean
if [ $? -ne 0 ]; then
    echo "ERROR: PyInstaller build failed"
    exit 1
fi
echo "✅ Executable built"
echo

# Step 5: Create startup script
echo "[5/5] Creating startup script..."
cat > dist/ChemMan_Demo/START_CHEMMAN_DEMO.sh << 'EOF'
#!/bin/bash
echo "============================================================"
echo "  ChemMan v2.0.0 - Demo Version"
echo "============================================================"
echo
echo "Starting ChemMan Demo..."
echo
echo "Browser will open automatically in a few seconds."
echo
./chemman_demo
EOF

chmod +x dist/ChemMan_Demo/START_CHEMMAN_DEMO.sh
echo "✅ Startup script created"
echo

# Step 6: Copy README
cp README_DEMO.md dist/ChemMan_Demo/README.txt

echo "============================================================"
echo "  ✅ Build Complete!"
echo "============================================================"
echo
echo "📦 Package location: dist/ChemMan_Demo/"
echo
echo "🚀 To test the demo:"
echo "   1. Go to: dist/ChemMan_Demo/"
echo "   2. Run: ./START_CHEMMAN_DEMO.sh"
echo "   3. Login: admin / Demo1234"
echo
echo "📤 To distribute:"
echo "   - Tar/zip the entire ChemMan_Demo folder"
echo "   - Send to colleagues/clients"
echo
