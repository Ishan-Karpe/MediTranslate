# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/meditranslate/main.py'],
    pathex=['src/meditranslate'],
    binaries=[],
    datas=[('/home/ishan/Documents/MediTranslate/src/meditranslate/data', 'meditranslate/data'), ('/home/ishan/Documents/MediTranslate/src/meditranslate/resources', 'meditranslate/resources'), ('/home/ishan/Documents/MediTranslate/.env', '.')],
    hiddenimports=['pdf2image', 'reportlab', 'pyside6', 'cv2', 'numpy', 'ui', 'services', 'utils'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MediTranslate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MediTranslate',
)
