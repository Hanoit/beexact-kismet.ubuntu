# main.spec

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

project_root = os.getcwd()

datas = [
    (os.path.join(project_root, 'kismet.db'), '.'),
    (os.path.join(project_root, 'icon/export-csv-32.png'), '.')
]

hiddenimports = (
    collect_submodules('torch') +
    collect_submodules('torch.cuda') +
    collect_submodules('transformers') +
    collect_submodules('sentence_transformers')
)

a = Analysis(
    ['kismet_export.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['./hooks'],
    runtime_hooks=[],
    excludes=[
        'torch.utils.tensorboard',
        'nvidia'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='kismet_to_csv',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='icon/export-csv-32.png'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='kismet_to_csv''
)