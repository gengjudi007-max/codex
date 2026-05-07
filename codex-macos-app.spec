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
        ('docs', 'docs'),
    ],
    hiddenimports=[
        'codex',
        'codex.interaction',
        'codex.services',
        'codex.connectors',
        'codex.connectors.beijing_land_connector',
        'codex.connectors.guangzhou_land_connector',
        'codex.connectors.hangzhou_land_connector',
        'codex.connectors.shanghai_land_connector',
        'codex.connectors.shenzhen_land_connector',
        'codex.connectors.simple_city_land_connector',
        'codex.connectors.wuxi_land_connector',
        'codex.connectors.kunming_land_connector',
        'codex.browser',
        'codex.classifiers',
        'codex.interaction_core',
        'codex.jobs',
        'codex.models',
        'codex.utils',
        'pypdf',
        'requests',
        'urllib.request',
        'urllib.parse',
        'subprocess',
        'json',
        'csv',
        're',
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
    [],
    exclude_binaries=True,
    name='Codex',
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
    icon='assets/icon.icns' if os.path.exists('assets/icon.icns') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Codex',
)

app = BUNDLE(
    coll,
    name='Codex.app',
    icon='assets/icon.icns' if os.path.exists('assets/icon.icns') else None,
    bundle_identifier='com.codex.app',
    version='0.2.0',
    shortversion='0.2.0',
    info_plist={
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15.0',
        'CFBundleDisplayName': 'Codex',
        'CFBundleGetInfoString': 'Codex - 房地产数据助手',
        'NSPrincipalClass': 'NSApplication',
    },
)
