# novasphere.spec
block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=['.', 'frontend'],
    binaries=[],
    datas=[
        ('frontend/nova_style.py', 'frontend'),
        ('frontend/novasphere.ico', '.'),
        ('frontend/novasphere.png', '.'),
        ('config', 'config'),
        ('auth/app_paths.py', 'auth'),
    ],
    hiddenimports=[
        'qtawesome',
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'flask',
        'auth.app_paths',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5'],
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
    name='NovaSphere',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='frontend/novasphere.ico',
)