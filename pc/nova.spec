# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for NOVA.

Run it from the pc/ directory:

    pyinstaller nova.spec

The game has no data files -- sprites are text in data.py and every sound is
synthesised at startup -- so this is a plain one-file build with an icon.
"""

import os

block_cipher = None
HERE = os.path.abspath(os.getcwd())
ICON = os.path.join(HERE, "assets", "nova.ico")

a = Analysis(
    ["nova.py"],
    pathex=[HERE],
    binaries=[],
    datas=[],
    hiddenimports=["numpy"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Trim the parts of the toolchain a game never touches. Without this the
    # one-file build drags in matplotlib and friends if they happen to be
    # installed alongside.
    excludes=["tkinter", "matplotlib", "PIL", "scipy", "pandas",
              "setuptools", "pytest", "IPython"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="NOVA",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # No console window on Windows; on Linux this flag is ignored.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON if os.path.exists(ICON) else None,
)
