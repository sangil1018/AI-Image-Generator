# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# --- Add custom data files ---
# ('source_path_on_disk', 'destination_path_in_package')
custom_datas = [
]

# Collect hidden imports
hiddenimports = [
    'encodings.*', # Critical fix for ModuleNotFoundError: No module named 'encodings'
    'uvicorn', 'fastapi', 'sdnq',
    'diffusers', 'transformers', 'accelerate',
    'safetensors', 'scipy', 'numpy', 'PIL',
    'torch', 'torchvision'
]
hiddenimports += collect_submodules('sdnq')
hiddenimports += collect_submodules('diffusers')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=custom_datas,
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
    [],
    exclude_binaries=True,
    name='Z-Image-Turbo',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Z-Image-Turbo',
)
