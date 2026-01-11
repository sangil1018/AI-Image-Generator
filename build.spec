# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all Gradio data files (frontend assets)
gradio_datas = collect_data_files('gradio')
gradio_client_datas = collect_data_files('gradio_client')

# Collect hidden imports
hiddenimports = [
    'uvicorn', 'fastapi', 'gradio', 'sdnq',
    'diffusers', 'transformers', 'accelerate',
    'safetensors', 'scipy', 'numpy', 'PIL',
    'gradio_client', 'torch', 'torchvision'
]
hiddenimports += collect_submodules('sdnq')
hiddenimports += collect_submodules('diffusers')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=gradio_datas + gradio_client_datas,
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
