# ChemMan Demo - Quick Start Guide

## 🎯 Goal

Create a **standalone demo package** that runs without any installation.

---

## 🚀 Building the Demo Package

### Prerequisites

You only need:
- Python 3.11+ (already installed if you're running the dev version)
- All dependencies from `requirements.txt` (already installed)

### Step-by-Step Build Process

#### Windows

```powershell
# 1. Go to DEMO folder
cd DEMO

# 2. Run the build script
build_demo_package.bat

# 3. Wait for build to complete (3-5 minutes)

# 4. Package is ready in: dist\ChemMan_Demo\
```

#### Linux/Mac

```bash
# 1. Go to DEMO folder
cd DEMO

# 2. Make script executable
chmod +x build_demo_package.sh

# 3. Run the build script
./build_demo_package.sh

# 4. Wait for build to complete (3-5 minutes)

# 5. Package is ready in: dist/ChemMan_Demo/
```

---

## 📦 What Gets Created

After building, you'll have:

```
dist/ChemMan_Demo/
├── START_CHEMMAN_DEMO.bat     # ← Double-click this to run (Windows)
├── START_CHEMMAN_DEMO.sh      # ← Run this on Linux/Mac
├── chemman_demo.exe           # Main executable (Windows)
├── chemman_demo               # Main executable (Linux/Mac)
├── demo_chemman.db            # Database with all data
├── static/                    # Web assets
├── templates/                 # HTML templates
├── substancje_baza.xlsx       # CLP data (backup)
├── svhc.xlsx                  # SVHC data (backup)
├── README.txt                 # Instructions
└── [many DLL/SO files]        # Dependencies

Total size: ~150 MB
```

---

## ✅ Testing the Demo

### On Your Machine (Before Distribution)

```bash
# 1. Go to the built package
cd dist/ChemMan_Demo

# 2. Windows: Double-click START_CHEMMAN_DEMO.bat
#    Linux/Mac: ./START_CHEMMAN_DEMO.sh

# 3. Browser opens automatically to http://127.0.0.1:5000

# 4. Login:
#    Username: admin
#    Password: Demo1234

# 5. Test all features!
```

---

## 📤 Distributing the Demo

### Option 1: ZIP File (Recommended)

```powershell
# Windows
Compress-Archive -Path dist\ChemMan_Demo -DestinationPath ChemMan_Demo_v2.0.0.zip

# Linux/Mac
tar -czf ChemMan_Demo_v2.0.0.tar.gz -C dist ChemMan_Demo
```

Send this ZIP file to anyone:
- ✅ No installation needed
- ✅ Works offline
- ✅ Portable (can run from USB)

### Option 2: Network Share

Copy `ChemMan_Demo/` folder to:
- Company network drive
- SharePoint
- USB stick

### Option 3: Cloud Storage

Upload ZIP to:
- Google Drive
- OneDrive
- Company file server

---

## 🎬 Demo Scenarios

### Quick Demo (5 min)

1. Start application
2. Login as admin
3. Show dashboard
4. Add a location
5. Search for "Benzene" and add to location
6. Show CMR automatic detection
7. Export data to CSV

### Full Demo (15 min)

1. All of above, plus:
2. Show all 4400+ substances
3. Demonstrate advanced filters
4. Upload SDS file
5. Show user management
6. Show audit log
7. Demonstrate bilingual interface

---

## 🛠️ Troubleshooting Build Issues

### Issue: "PyInstaller not found"

**Solution:**
```bash
pip install pyinstaller
```

### Issue: "ModuleNotFoundError during build"

**Solution:**
```bash
# Reinstall all dependencies
cd ..
pip install -r requirements.txt
cd DEMO
```

### Issue: "substancje_baza.xlsx not found"

**Solution:**
- Make sure Excel files are in parent directory
- Check file names are exactly:
  - `substancje_baza.xlsx`
  - `svhc.xlsx`

### Issue: "Build takes too long (>10 min)"

**Solution:**
- This is normal on first build
- Subsequent builds are faster
- Close antivirus temporarily (it slows down PyInstaller)

### Issue: "Executable doesn't run"

**Solution:**
1. Check antivirus - add exception for ChemMan_Demo folder
2. Run from command line to see error messages
3. Check `demo_chemman.log` file

---

## 🔄 Updating the Demo

When you update the main application:

```bash
# 1. Pull latest changes
git pull origin master

# 2. Rebuild demo
cd DEMO
build_demo_package.bat  # or .sh

# 3. New package ready in dist/
```

---

## ⚠️ Important Notes

### Demo Limitations

- ❌ **Not for production use!**
- ✅ Demo/presentation purposes only
- ⚠️ Data persists (unless you delete database)
- ⚠️ No network access (runs locally only)

### Security

- Demo password is **simple by design** (Demo1234 - meets 8-char requirement)
- Don't use demo package for real data
- For production, use full deployment (DEPLOYMENT_GUIDE.md)

### Performance

- First startup may be slow (2-3 seconds)
- Subsequent starts are faster
- SQLite is slower than PostgreSQL (expected)

---

## 📊 Build Time Estimates

| Task | Time |
|------|------|
| Install PyInstaller | 30 sec |
| Build demo database | 1 min |
| PyInstaller build | 2-5 min |
| **Total** | **3-7 min** |

### File Sizes

| Item | Size |
|------|------|
| Executable + DLLs | ~100 MB |
| Database | ~40 MB |
| Static files | ~5 MB |
| **Total Package** | **~150 MB** |
| **ZIP file** | **~50 MB** |

---

## ✅ Checklist Before Distribution

- [ ] Built package successfully
- [ ] Tested startup script
- [ ] Logged in with admin/Demo1234
- [ ] Tested key features (add location, search, export)
- [ ] Checked database has data (4400+ CLP, 492 SVHC)
- [ ] Zipped package
- [ ] Included README_DEMO.md
- [ ] Prepared presentation/demo script

---

## 🎉 You're Ready!

Your standalone demo package is ready to:
- Show to management
- Present to clients
- Demonstrate at meetings
- Send to remote users

**Good luck with your presentation!** 🚀
