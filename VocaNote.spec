# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

# Collecter toutes les dépendances complexes
datas = []
binaries = []
hiddenimports = []

# Collecter pour pyannote.audio et ses dépendances
tmp_ret = collect_all('pyannote.audio')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('pyannote.core')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('pyannote.database')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('pyannote.pipeline')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collecter pour torch
tmp_ret = collect_all('torch')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collecter pour whisper
tmp_ret = collect_all('whisper')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collecter pour av (AudioDecoder)
tmp_ret = collect_all('av')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collecter pour huggingface_hub
tmp_ret = collect_all('huggingface_hub')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collecter pour lightning_fabric (Source de l'erreur version.info)
tmp_ret = collect_all('lightning_fabric')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collecter pour torchvision (Fix pour RuntimeError: operator torchvision::nms does not exist)
tmp_ret = collect_all('torchvision')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collecter pour pytorch_lightning
tmp_ret = collect_all('pytorch_lightning')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Ajouts manuels souvent manquants
hiddenimports += [
    'scipy.special.cython_special',
    'sklearn.utils._typedefs',
    'sklearn.neighbors._typedefs',
    'sklearn.neighbors._quad_tree',
    'sklearn.tree._utils',
    'sklearn.utils._cython_blas',
    'speechbrain',
    'lightning',
    'pytorch_lightning',
    'asteroid_filterbanks',
    'einops',
    'omegaconf',
    'semver',
    'soundfile',
    'tabulate',
    'ffmpeg_python',
    'imageio_ffmpeg',
    'hydra',
    'hydra._internal',
    'hydra._internal.core_plugins',
    'omegaconf',
    'antlr4',
    'shutil',
    'modulefinder',
]

# Inclure ffmpeg local s'il existe dans le dossier source
if os.path.exists('ffmpeg'):
    datas += [('ffmpeg', 'ffmpeg')]

# Inclure les fichiers de config et docs
datas += [
    ('config.ini', '.'),
    ('README_FR.md', '.'),
    ('LICENSE.txt', '.'),
    ('START_HERE.txt', '.'),
    ('MODELES_A_ACCEPTER.md', '.'),
    ('DEPANNAGE_*.md', '.'),
    ('GUIDE_*.md', '.'),
]

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'IPython', 'jupyter', 'notebook', 'tkinter', 'test', 'tests'
    ],
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
    name='VocaNote',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Console désactivée pour la version de production (voir vocanote.log pour les erreurs)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logoVN.ico' if os.path.exists('logoVN.ico') else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VocaNote',
)
