# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

import PyInstaller.config
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

pg_datas, pg_binaries, pg_hiddenimports = collect_all("pygame")
hiddenimports = collect_submodules("pygame") + list(pg_hiddenimports)

# Try to centralize all build outputs under ./build
# NOTE: PyInstaller still allows overriding these via CLI flags.
# NOTE: Depending on how PyInstaller executes this spec, __file__ may be undefined.
# Use current working directory (project root) as the base.
_root = Path.cwd().resolve()
_dist = (_root / "build").resolve()
_work = (_dist / "temp").resolve()

_dist.mkdir(parents=True, exist_ok=True)
_work.mkdir(parents=True, exist_ok=True)

PyInstaller.config.CONF["distpath"] = str(_dist)
PyInstaller.config.CONF["workpath"] = str(_work)


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[] + list(pg_binaries),
    datas=[("assets", "assets"), ("scripts", "scripts")] + list(pg_datas),
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="main",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
