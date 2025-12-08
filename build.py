#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de build pour créer l'exécutable VocaNote avec PyInstaller
Inclut: Transcription (Whisper), Diarisation (Pyannote), Résumé (Transformers), Licence
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def clean_build():
    """Nettoyer les anciens fichiers de build"""
    print("🧹 Nettoyage des anciens fichiers de build...")
    
    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['VocaNote.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"   ✓ Supprimé: {dir_name}/")
            except Exception as e:
                print(f"   ⚠️ Impossible de supprimer {dir_name}: {e}")
    
    for file_name in files_to_clean:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                print(f"   ✓ Supprimé: {file_name}")
            except Exception as e:
                print(f"   ⚠️ Impossible de supprimer {file_name}: {e}")


def install_pyinstaller():
    """Installer PyInstaller si nécessaire"""
    print("\n📦 Vérification de PyInstaller...")
    
    try:
        import PyInstaller
        print("   ✓ PyInstaller est déjà installé")
    except ImportError:
        print("   ⚠ PyInstaller n'est pas installé. Installation en cours...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("   ✓ PyInstaller installé avec succès")


def create_spec_file():
    """Créer le fichier .spec optimisé pour VocaNote avec toutes les fonctionnalités"""
    print("\n📝 Création du fichier .spec complet...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
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

# === DIARISATION (Pyannote) ===
for pkg in ['pyannote.audio', 'pyannote.core', 'pyannote.database', 'pyannote.pipeline', 'pyannote.metrics']:
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
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
    # Pyannote
    'speechbrain',
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
    'ffmpeg_python',
    'imageio_ffmpeg',
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
]

# Inclure ffmpeg local s'il existe
if os.path.exists('ffmpeg'):
    datas += [('ffmpeg', 'ffmpeg')]

# Inclure les modules Python locaux
local_modules = ['summarizer.py', 'diarization.py', 'license.py']
for mod in local_modules:
    if os.path.exists(mod):
        datas += [(mod, '.')]

# Inclure config.ini s'il existe
if os.path.exists('config.ini'):
    datas += [('config.ini', '.')]

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
        'test', 'tests', 'unittest', 'pytest'
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
'''
    
    with open('VocaNote.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("   ✓ Fichier VocaNote.spec créé (avec toutes les fonctionnalités)")


def build_executable():
    """Construire l'exécutable avec PyInstaller"""
    print("\n🔨 Construction de l'exécutable...")
    print("   ⚠ Cela peut prendre 10-30 minutes (PyTorch/Transformers sont volumineux)...\n")
    
    try:
        subprocess.check_call([
            sys.executable,
            '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            'VocaNote.spec'
        ])
        print("\n" + "=" * 60)
        print("  ✅ BUILD DE L'EXÉCUTABLE RÉUSSI!")
        print("=" * 60)
        print(f"\n📁 L'exécutable se trouve dans: {os.path.abspath('dist/VocaNote')}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n   ❌ Erreur lors de la construction: {e}")
        return False


def create_installer():
    """Créer l'installateur avec Inno Setup"""
    print("\n💿 Création de l'installateur Windows...")
    
    # Créer le dossier installer s'il n'existe pas
    if not os.path.exists('installer'):
        os.makedirs('installer')
    
    # Chemins possibles pour ISCC.exe
    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        os.environ.get("ISCC_PATH", "ISCC.exe")
    ]
    
    iscc_exe = None
    for path in iscc_paths:
        if os.path.exists(path) or shutil.which(path):
            iscc_exe = path
            break
            
    if not iscc_exe:
        print("   ⚠️ Inno Setup (ISCC.exe) n'a pas été trouvé.")
        print("   👉 Téléchargez Inno Setup 6: https://jrsoftware.org/isdl.php")
        print("   ℹ️ L'exécutable portable est tout de même prêt dans dist/VocaNote")
        return False
        
    print(f"   ✓ Compilateur trouvé: {iscc_exe}")
    
    try:
        if not os.path.exists('setup.iss'):
            print("   ❌ Erreur: setup.iss introuvable!")
            return False
            
        subprocess.check_call([iscc_exe, "setup.iss"])
        print("\n" + "=" * 60)
        print("  ✅ INSTALLATEUR CRÉÉ AVEC SUCCÈS!")
        print("=" * 60)
        print(f"\n📦 L'installateur se trouve dans: {os.path.abspath('installer')}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n   ❌ Erreur lors de la création de l'installateur: {e}")
        return False


def create_license_file():
    """Créer le fichier LICENSE.txt s'il n'existe pas"""
    if not os.path.exists('LICENSE.txt'):
        with open('LICENSE.txt', 'w', encoding='utf-8') as f:
            f.write("""MIT License

Copyright (c) 2025 VocaNote

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""")
        print("   ✓ Fichier LICENSE.txt créé")


def check_requirements():
    """Vérifier que toutes les dépendances sont installées"""
    print("\n🔍 Vérification des dépendances...")
    
    required = ['PyQt6', 'whisper', 'torch', 'transformers', 'cryptography']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg.lower().replace('-', '_'))
            print(f"   ✓ {pkg}")
        except ImportError:
            print(f"   ❌ {pkg} manquant")
            missing.append(pkg)
    
    if missing:
        print(f"\n   ⚠️ Packages manquants: {', '.join(missing)}")
        print("   👉 Exécutez: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Fonction principale du script de build"""
    print("=" * 60)
    print("  🎤 VocaNote - Script de Build Complet")
    print("  Transcription | Diarisation | Résumé | Licence")
    print("=" * 60)
    
    if not os.path.exists('main.py'):
        print("\n❌ Erreur: main.py introuvable!")
        print("   Assurez-vous d'exécuter ce script depuis le dossier VocaNote")
        sys.exit(1)
    
    # Étapes de préparation
    check_requirements()
    clean_build()
    create_license_file()
    install_pyinstaller()
    create_spec_file()
    
    # Build
    if build_executable():
        # Tentative de création de l'installateur
        if create_installer():
            print("\n" + "=" * 60)
            print("  🎉 BUILD COMPLET TERMINÉ!")
            print("=" * 60)
            print("\n📋 RÉCAPITULATIF:")
            print("   1. Exécutable portable : dist/VocaNote/VocaNote.exe")
            print("   2. Installateur        : installer/VocaNote_Setup_1.0.0.exe")
            print("\n   🚀 Prêt à distribuer!")
        else:
            print("\n" + "=" * 60)
            print("  ⚠️ BUILD PARTIEL")
            print("=" * 60)
            print("\n   L'exécutable est prêt, mais pas l'installateur.")
            print("   👉 Installez Inno Setup pour créer l'installateur.")
    else:
        print("\n❌ Le build a échoué. Vérifiez les erreurs ci-dessus.")
        sys.exit(1)


if __name__ == "__main__":
    main()
