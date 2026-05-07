# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/codex/cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/codex/**/*.py', 'codex'),
        ('config/*.json', 'config'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'codex.services',
        'codex.connectors',
        'codex.browser',
        'codex.classifiers',
        'codex.interaction_core',
        'codex.jobs',
        'codex.models',
        'codex.utils',
        'pypdf',
        'requests',
        'playwright',
        'curl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Codex-macOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.icns' if os.path.exists('assets/icon.icns') else None,
)
