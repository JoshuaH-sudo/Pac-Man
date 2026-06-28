# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

project_root = Path.cwd()

block_cipher = None


a = Analysis(
    [str(project_root / "packaged_launcher.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(project_root / "src" / "assets" / "sprites"), "assets/sprites"),
        (str(project_root / "config.example.json"), "."),
        (str(project_root / "PACKAGED-INSTRUCTIONS.txt"), "."),
    ],
    hiddenimports=["arcade.gui"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Arcade's PyInstaller hook can emit arcade/VERSION/VERSION, which creates a
# directory named VERSION and triggers an import-time warning in arcade.version.
# Normalize it to arcade/VERSION so the file is loaded correctly.
normalized_datas = []
for entry in a.datas:
    if entry[0] == "arcade/VERSION/VERSION":
        normalized_datas.append(("arcade/VERSION", entry[1], entry[2]))
    else:
        normalized_datas.append(entry)
a.datas = normalized_datas

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pac-man",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="pac-man",
)
