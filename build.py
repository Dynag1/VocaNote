#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de build pour créer l'exécutable VocaNote avec PyInstaller
Inclut FFmpeg automatiquement dans le build.
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
                print(f"   ⚠️ Impossible de supprimer {dir_name} (peut-être ouvert ?) : {e}")
    
    for file_name in files_to_clean:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                print(f"   ✓ Supprimé: {file_name}")
            except Exception as e:
                print(f"   ⚠️ Impossible de supprimer {file_name} : {e}")


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
    """Créer le fichier .spec pour PyInstaller avec inclusion de FFmpeg"""
    print("\n📝 Création du fichier .spec...")
    
    # Vérifier si le dossier ffmpeg existe
    ffmpeg_data = ""
    if os.path.exists("ffmpeg"):
        print("   ✅ Dossier FFmpeg trouvé, il sera inclus dans l'exécutable")
        # Inclure tout le dossier ffmpeg dans le dossier racine de l'app
        ffmpeg_data = "('ffmpeg', 'ffmpeg'),"
    else:
        print("   ⚠️ Dossier FFmpeg NON trouvé ! L'exécutable nécessitera une installation manuelle de FFmpeg.")
    
    # Trouver le dossier des assets Whisper
    whisper_assets = ""
    try:
        import whisper
        whisper_path = os.path.dirname(whisper.__file__)
        assets_path = os.path.join(whisper_path, "assets")
        if os.path.exists(assets_path):
            print(f"   ✅ Assets Whisper trouvés: {assets_path}")
            whisper_assets = f"(r'{assets_path}', 'whisper/assets'),"
        else:
            print("   ⚠️ Assets Whisper NON trouvés")
    except Exception as e:
        print(f"   ⚠️ Impossible de localiser Whisper: {e}")
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        {ffmpeg_data}
        {whisper_assets}
        ('config.ini', '.'),
        ('README_FR.md', '.'),
        ('LICENSE.txt', '.'),
    ],
    hiddenimports=[
        'whisper',
        'torch',
        'torchaudio',
        'numpy',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'imageio_ffmpeg',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        '*.pt', 
        '*.pth',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'PIL.ImageQt',
        'tkinter',
        'test',
        'tests',
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
    upx_exclude=['torch*.dll', 'mkl*.dll', 'libiomp*.dll'],
    name='VocaNote',
)
"""
    
    with open('VocaNote.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("   ✓ Fichier VocaNote.spec créé")


def build_executable():
    """Construire l'exécutable avec PyInstaller"""
    print("\n🔨 Construction de l'exécutable...")
    print("   ⚠ Cela peut prendre plusieurs minutes...\n")
    
    try:
        subprocess.check_call([
            'pyinstaller',
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
    
    # Chemins possibles pour ISCC.exe
    iscc_paths = [
        r"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
        r"C:\\Program Files\\Inno Setup 6\\ISCC.exe",
        os.environ.get("ISCC_PATH", "ISCC.exe")
    ]
    
    iscc_exe = None
    for path in iscc_paths:
        if os.path.exists(path) or shutil.which(path):
            iscc_exe = path
            break
            
    if not iscc_exe:
        print("   ⚠️ Inno Setup (ISCC.exe) n'a pas été trouvé.")
        print("   👉 Veuillez installer Inno Setup 6+ pour créer l'installateur.")
        print("   ℹ️ Vous pouvez toujours utiliser l'exécutable portable dans dist/VocaNote")
        return False
        
    print(f"   ✓ Compilateur trouvé: {iscc_exe}")
    
    try:
        subprocess.check_call([iscc_exe, "setup.iss"])
        print("\n" + "=" * 60)
        print("  ✅ INSTALLATEUR CRÉÉ AVEC SUCCÈS!")
        print("=" * 60)
        print(f"\n📦 L'installateur se trouve dans le dossier 'installer/'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n   ❌ Erreur lors de la création de l'installateur: {e}")
        return False


def create_readme():
    """Créer les fichiers de documentation"""
    if not os.path.exists('LICENSE.txt'):
        with open('LICENSE.txt', 'w', encoding='utf-8') as f:
            f.write("MIT License - Copyright (c) 2025 VocaNote Team")


def main():
    """Fonction principale du script de build"""
    print("=" * 60)
    print("  VocaNote - Script de Build Complet")
    print("=" * 60)
    
    if not os.path.exists('main.py'):
        print("\n❌ Erreur: main.py introuvable!")
        sys.exit(1)
    
    clean_build()
    install_pyinstaller()
    create_readme()
    create_spec_file()
    
    if build_executable():
        create_installer()
        
        print("\n📋 RÉCAPITULATIF:")
        print("   1. Exécutable portable : dist/VocaNote/VocaNote.exe")
        if os.path.exists("installer"):
            print("   2. Installateur : installer/VocaNote_Setup_1.0.0.exe")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
