# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files
import os

# Collecter toutes les dépendances complexes
datas = []
binaries = []
hiddenimports = []

# === TRANSCRIPTION (Whisper) ===
try:
    tmp_ret = collect_all('whisper')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except: pass

# === DIARISATION (Pyannote + SpeechBrain) ===
for pkg in ['pyannote.audio', 'pyannote.core', 'pyannote.database', 'pyannote.pipeline', 'pyannote.metrics']:
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except: pass

# SpeechBrain nécessite une collecte spéciale (lazy imports)
try:
    tmp_ret = collect_all('speechbrain')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
    
    # Collecter explicitement les fichiers data de speechbrain
    sb_data = collect_data_files('speechbrain', include_py_files=True)
    datas += sb_data
except: pass

# === RÉSUMÉ (Transformers/BART) ===
for pkg in ['transformers', 'tokenizers', 'sentencepiece', 'safetensors']:
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except: pass

# === TORCH / ML ===
for pkg in ['torch', 'torchaudio', 'torchvision', 'pytorch_lightning', 'lightning_fabric', 'lightning']:
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except: pass

# === AUDIO ===
try:
    tmp_ret = collect_all('av')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except: pass

# === HUGGINGFACE ===
try:
    tmp_ret = collect_all('huggingface_hub')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except: pass

# === CRYPTOGRAPHIE (Licence) ===
try:
    tmp_ret = collect_all('cryptography')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except: pass

# === SCIPY ===
try:
    tmp_ret = collect_all('scipy')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except: pass

# Ajouts manuels souvent manquants
hiddenimports += [
    # Scipy
    'scipy.special.cython_special',
    'scipy.io.wavfile',
    'scipy.signal',
    # Sklearn
    'sklearn.utils._typedefs',
    'sklearn.neighbors._typedefs',
    'sklearn.neighbors._quad_tree',
    'sklearn.tree._utils',
    'sklearn.utils._cython_blas',
    # Pyannote / SpeechBrain
    'speechbrain',
    'speechbrain.inference',
    'speechbrain.dataio',
    'speechbrain.dataio.dataio',
    'speechbrain.dataio.batch',
    'speechbrain.dataio.dataset',
    'speechbrain.dataio.dataloader',
    'speechbrain.dataio.encoder',
    'speechbrain.dataio.iterators',
    'speechbrain.dataio.legacy',
    'speechbrain.dataio.sampler',
    'speechbrain.dataio.wer',
    'speechbrain.utils',
    'speechbrain.utils.importutils',
    'speechbrain.utils.data_utils',
    'speechbrain.utils.logger',
    'speechbrain.core',
    'speechbrain.nnet',
    'speechbrain.lobes',
    'speechbrain.processing',
    'speechbrain.pretrained',
    'asteroid_filterbanks',
    # Lightning
    'lightning',
    'pytorch_lightning',
    # Config
    'einops',
    'omegaconf',
    'semver',
    'hydra',
    'hydra._internal',
    'hydra._internal.core_plugins',
    'antlr4',
    # Audio
    'soundfile',
    'ffmpeg',
    'imageio_ffmpeg',
    'imageio',
    # Transformers
    'transformers.models.bart',
    'transformers.models.mbart',
    'transformers.models.auto',
    'transformers.generation',
    'transformers.tokenization_utils_base',
    # Utils
    'tabulate',
    'tqdm',
    'regex',
    'safetensors',
    'accelerate',
    # Modules locaux VocaNote
    'summarizer',
    'diarization',
    'license',
    # Requis par PyTorch
    'unittest',
    'unittest.mock',
    # Requis par Transformers
    'torchcodec',
    'importlib.metadata',
]

# Inclure ffmpeg local s'il existe
if os.path.exists('ffmpeg'):
    datas += [('ffmpeg', 'ffmpeg')]

# Inclure les modules Python locaux
local_modules = ['summarizer.py', 'diarization.py', 'license.py']
for mod in local_modules:
    if os.path.exists(mod):
        datas += [(mod, '.')]

# Inclure les fichiers de configuration
config_files = ['config.ini', 'hf_token.txt']
for cfg in config_files:
    if os.path.exists(cfg):
        datas += [(cfg, '.')]

# Inclure les fichiers de documentation
doc_files = ['README_FR.md', 'LICENSE.txt', 'START_HERE.txt', 'DEMARRAGE_RAPIDE.md']
for doc in doc_files:
    if os.path.exists(doc):
        datas += [(doc, '.')]

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'IPython', 'jupyter', 'notebook', 'tkinter', 
        'pytest'
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
    console=False,
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
