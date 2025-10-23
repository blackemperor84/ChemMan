# -*- mode: python ; coding: utf-8 -*-
# PyInstaller specification file for ChemMan Demo

import sys
import os
from pathlib import Path

block_cipher = None

# Get directories - SPECPATH is the path to this spec file
spec_dir = os.path.dirname(SPECPATH)  # This is DEMO folder
parent_dir = os.path.dirname(spec_dir)  # This is parent (chem-man app folder)

a = Analysis(
    ['run_demo.py'],
    pathex=[parent_dir],
    binaries=[],
    datas=[
        # Templates
        ('../templates', 'templates'),
        # Static files
        ('../static', 'static'),
        # Excel files (optional, for backup)
        ('../substancje_baza.xlsx', '.'),
        ('../svhc.xlsx', '.'),
        # Demo database
        ('demo_chemman.db', '.'),
        # Config
        ('config_demo.py', '.'),
        ('../config.py', '.'),
        # Main application files
        ('app_demo_wrapper.py', '.'),
        ('../app.py', '.'),
        ('../models.py', '.'),
        ('../limiter.py', '.'),
        ('../decorators.py', '.'),
        ('../utils', 'utils'),
        ('../routes', 'routes'),
    ],
    hiddenimports=[
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.ext.baked',
        'pandas',
        'openpyxl',
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_bcrypt',
        'flask_limiter',
        'flask_migrate',
        'flask_wtf',
        'flask_wtf.csrf',
        'wtforms',
        'werkzeug',
        'jinja2',
        'click',
        'itsdangerous',
        'markupsafe',
        'email.mime.text',
        'email.mime.multipart',
        'app',
        'models',
        'limiter',
        'config',
        'utils',
        'routes.auth',
        'routes.substances',
        'routes.locations',
        'routes.files',
        'routes.admin',
        'routes.export',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'unittest',
        'test',
        'tests',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='chemman_demo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Show console window for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChemMan_Demo',
)
