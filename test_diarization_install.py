#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier l'installation de la diarisation
"""

import sys

def test_imports():
    """Teste les imports nécessaires"""
    print("🔍 Test des imports...")
    
    errors = []
    
    # Test PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
        print("  ✅ PyQt6 installé")
    except ImportError as e:
        errors.append(f"PyQt6: {e}")
        print("  ❌ PyQt6 manquant")
    
    # Test Whisper
    try:
        import whisper
        print("  ✅ Whisper installé")
    except ImportError as e:
        errors.append(f"Whisper: {e}")
        print("  ❌ Whisper manquant")
    
    # Test PyTorch
    try:
        import torch
        print(f"  ✅ PyTorch installé (version {torch.__version__})")
        if torch.cuda.is_available():
            print(f"     🚀 CUDA disponible (GPU: {torch.cuda.get_device_name(0)})")
        else:
            print("     💻 Mode CPU uniquement")
    except ImportError as e:
        errors.append(f"PyTorch: {e}")
        print("  ❌ PyTorch manquant")
    
    # Test pyannote.audio
    try:
        import pyannote.audio
        print("  ✅ pyannote.audio installé")
    except ImportError as e:
        errors.append(f"pyannote.audio: {e}")
        print("  ❌ pyannote.audio manquant")
        print("     Installez avec: pip install pyannote.audio")
    
    # Test pyannote.core
    try:
        import pyannote.core
        print("  ✅ pyannote.core installé")
    except ImportError as e:
        errors.append(f"pyannote.core: {e}")
        print("  ❌ pyannote.core manquant")
        print("     Installez avec: pip install pyannote.core")
    
    return len(errors) == 0, errors


def test_diarization_module():
    """Teste le module de diarisation"""
    print("\n🔍 Test du module de diarisation...")
    
    try:
        from diarization import SpeakerDiarization
        print("  ✅ Module diarization.py importé avec succès")
        
        # Créer une instance
        diarizer = SpeakerDiarization()
        print("  ✅ Instance SpeakerDiarization créée")
        
        return True
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False


def test_main_module():
    """Teste le module principal"""
    print("\n🔍 Test du module principal...")
    
    try:
        # Importer sans lancer l'application
        import main
        print("  ✅ Module main.py importé avec succès")
        return True
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False


def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("  Test d'installation - VocaNote avec Diarisation")
    print("=" * 60)
    print()
    
    # Test des imports
    imports_ok, errors = test_imports()
    
    if not imports_ok:
        print("\n❌ Certaines dépendances sont manquantes:")
        for error in errors:
            print(f"   - {error}")
        print("\n💡 Installez les dépendances manquantes avec:")
        print("   pip install -r requirements.txt")
        return False
    
    # Test du module de diarisation
    diarization_ok = test_diarization_module()
    
    # Test du module principal
    main_ok = test_main_module()
    
    # Résumé
    print("\n" + "=" * 60)
    print("  Résumé des tests")
    print("=" * 60)
    
    if imports_ok and diarization_ok and main_ok:
        print("\n✅ Tous les tests sont passés avec succès!")
        print("\n🎉 VocaNote est prêt à être utilisé avec la diarisation!")
        print("\n📚 Prochaines étapes:")
        print("   1. Configurez votre token HuggingFace (voir CONFIG_DIARISATION.md)")
        print("   2. Lancez VocaNote: python main.py")
        print("   3. Cochez 'Détecter les locuteurs' pour utiliser la diarisation")
        return True
    else:
        print("\n⚠️ Certains tests ont échoué")
        if not diarization_ok:
            print("   - Module de diarisation: ÉCHEC")
        if not main_ok:
            print("   - Module principal: ÉCHEC")
        print("\n💡 Vérifiez les erreurs ci-dessus et corrigez-les")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
