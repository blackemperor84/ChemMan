# ChemMan Demo Package - START HERE! 🚀

**Welcome!** This folder contains everything you need to create a **standalone demo version** of ChemMan that runs without any installation.

---

## 🎯 What is This?

This is a **portable demo package system** that converts your ChemMan application into:

- ✅ **Standalone .exe** (Windows) or binary (Linux/Mac)
- ✅ **No installation required** - just double-click and run
- ✅ **Pre-loaded with data** - 4400+ CLP + 492 SVHC substances
- ✅ **Portable** - can run from USB stick
- ✅ **Perfect for demos/presentations**

---

## 📁 Files in This Folder

| File | Purpose |
|------|---------|
| `00_START_HERE.md` | This file - read first! |
| `QUICK_START.md` | Fast build guide |
| `README_DEMO.md` | Full demo documentation |
| `build_demo_package.bat` | **Build script (Windows)** ⭐ |
| `build_demo_package.sh` | Build script (Linux/Mac) |
| `test_demo.bat` | Test configuration before building |
| `build_demo.py` | Creates demo database |
| `config_demo.py` | Demo configuration (SQLite) |
| `run_demo.py` | Demo application entry point |
| `chemman_demo.spec` | PyInstaller configuration |

---

## 🚀 Quick Start (3 Steps)

### Step 1: Test Configuration (Optional but Recommended)

```bash
# Windows
test_demo.bat

# This checks:
# - Python is installed
# - All dependencies present
# - Excel files exist
# - Database can be created
```

### Step 2: Build Demo Package

```bash
# Windows
build_demo_package.bat

# Linux/Mac
chmod +x build_demo_package.sh
./build_demo_package.sh

# Wait 3-5 minutes while it builds...
```

### Step 3: Test the Demo

```bash
# Go to built package
cd dist\ChemMan_Demo

# Windows: Double-click
START_CHEMMAN_DEMO.bat

# Linux/Mac: Run
./START_CHEMMAN_DEMO.sh

# Browser opens automatically
# Login: admin / Demo1234
```

**That's it!** 🎉

---

## 📦 What You'll Get

After building, you'll have a `dist/ChemMan_Demo/` folder (~150 MB) containing:

- ✅ Executable application
- ✅ Pre-loaded database (4400 CLP + 492 SVHC)
- ✅ Admin user (admin/Demo1234)
- ✅ All templates and static files
- ✅ Easy startup script

**Just ZIP this folder and send to anyone!**

---

## 📤 Distribution Options

### For Internal Demo (Colleagues)

```bash
# Zip the folder
# Windows PowerShell:
Compress-Archive -Path dist\ChemMan_Demo -DestinationPath ChemMan_Demo_v2.0.0.zip

# Send via:
# - Email (if < 25 MB after compression)
# - Network share
# - Cloud storage
```

### For External Demo (Clients/Partners)

1. Zip `ChemMan_Demo/` folder
2. Include `README_DEMO.md` with instructions
3. Optionally add presentation materials
4. Send with clear instructions

### For Presentation

1. Copy to presentation laptop
2. Test before meeting
3. Have backup on USB stick
4. Demo login: admin / Demo1234

---

## ⏱️ Time Estimates

| Task | Time |
|------|------|
| First-time setup | 5-7 min |
| Subsequent builds | 3-5 min |
| Distribution (ZIP) | 1 min |
| **Total** | **6-8 min** |

---

## 🎬 Use Cases

### ✅ Perfect For:

- **Management presentations** - "Here's what the system can do"
- **Client demos** - Show before deployment
- **Training sessions** - Let users practice
- **Trade shows** - Portable demo on laptop
- **Remote evaluation** - Send to decision-makers
- **Offline demos** - No internet needed

### ❌ Not For:

- Production use
- Real data storage
- Multi-user environments
- Network deployments

**For production:** Use `DEPLOYMENT_GUIDE.md` instead!

---

## 🛠️ Troubleshooting

### "PyInstaller not found"

```bash
pip install pyinstaller
```

### "Excel files not found"

Make sure these files are in the **parent directory**:
- `substancje_baza.xlsx`
- `svhc.xlsx`

### "Antivirus blocks demo"

- This is normal for PyInstaller executables
- Add exception for `ChemMan_Demo` folder
- Or run `test_demo.bat` first to verify everything works

### "Build fails"

1. Run `test_demo.bat` to check configuration
2. Make sure all dependencies are installed:
   ```bash
   cd ..
   pip install -r requirements.txt
   ```
3. Check error message in console

---

## 📚 Documentation

- **`QUICK_START.md`** - Fast building guide
- **`README_DEMO.md`** - Complete demo documentation
- **Parent `DEPLOYMENT_GUIDE.md`** - Production deployment

---

## 🔄 Updating Demo

When main application is updated:

```bash
# 1. Pull latest changes (if using git)
git pull origin master

# 2. Rebuild demo
cd DEMO
build_demo_package.bat

# 3. New package in dist/
```

---

## ✅ Pre-Distribution Checklist

Before sending demo to others:

- [ ] Built package successfully
- [ ] Tested startup (double-click works)
- [ ] Logged in (admin/Demo1234)
- [ ] Tested main features:
  - [ ] Add location
  - [ ] Search substance
  - [ ] View CMR detection
  - [ ] Export to CSV
- [ ] Checked data is present (4400+ substances)
- [ ] Created ZIP file
- [ ] Tested ZIP extraction
- [ ] Included README

---

## 💡 Pro Tips

1. **Build once, distribute many times** - No need to rebuild for each recipient

2. **Test on clean machine** - If possible, test on computer without Python/development tools

3. **Prepare demo script** - Know what features to show (see README_DEMO.md for scenarios)

4. **Keep original** - Save one copy as reference

5. **Version your demos** - Add date to ZIP filename:
   ```
   ChemMan_Demo_v2.0.0_2025-10-23.zip
   ```

---

## 🎯 Next Steps

1. **Now:** Run `build_demo_package.bat`
2. **Test:** Try the demo yourself
3. **Distribute:** ZIP and send to stakeholders
4. **Present:** Use demo for your meeting
5. **Deploy:** When approved, use `DEPLOYMENT_GUIDE.md` for production

---

## 📞 Need Help?

- Check `QUICK_START.md` for detailed instructions
- Review `README_DEMO.md` for full documentation
- Run `test_demo.bat` to diagnose issues
- Check parent directory `DEPLOYMENT_GUIDE.md` for production setup

---

## 🎉 Ready to Build?

```bash
# Windows
build_demo_package.bat

# Linux/Mac
./build_demo_package.sh
```

**Good luck with your demo!** 🚀

---

**ChemMan v2.0.0 - Demo Package System**
© 2025 NITROERG
