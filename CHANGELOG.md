# 📝 Changelog - VocaNote

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

---

## [1.0.1] - 2025-12-01

### 🐛 Corrections
- Suppression de l'avertissement "FP16 is not supported on CPU" pour une meilleure expérience utilisateur
- Ajout d'un filtre de warnings pour masquer les messages techniques inutiles

### ✨ Améliorations
- Message de statut amélioré : affiche "💻 CPU" ou "🚀 GPU (CUDA)" de manière plus conviviale
- Meilleure indication visuelle du périphérique utilisé

### 📚 Documentation
- Ajout de NOTES_TECHNIQUES.md expliquant l'avertissement FP16 et l'utilisation CPU/GPU
- Documentation complète sur l'accélération GPU

---

## [1.0.0] - 2025-12-01

### 🎉 Version Initiale

#### ✨ Fonctionnalités
- Interface graphique moderne avec PyQt6
- Transcription audio avec OpenAI Whisper
- Support de 5 modèles (tiny, base, small, medium, large)
- Support multilingue avec auto-détection
- Support de multiples formats audio (WAV, MP3, M4A, FLAC, OGG)
- Accélération GPU (CUDA) si disponible
- Copie dans le presse-papiers
- Sauvegarde en fichier TXT
- Barre de progression et messages de statut
- Gestion complète des erreurs

#### 🔧 Build & Distribution
- Script PyInstaller (build.py)
- Script Inno Setup (setup.iss)
- Scripts batch Windows (lancer_vocanote.bat, build_executable.bat)
- Fichier de configuration (config.ini)

#### 📚 Documentation
- Documentation complète en français (11 fichiers)
- Guide de démarrage rapide
- Guide d'installation
- Guide visuel de l'interface
- Structure du projet
- Index de documentation

#### 🎨 Interface
- Design Material Design moderne
- Palette de couleurs harmonieuse
- Animations et transitions fluides
- Messages de statut clairs
- Indicateurs visuels intuitifs

---

## Format

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

### Types de changements
- **✨ Ajouté** pour les nouvelles fonctionnalités
- **🔄 Modifié** pour les changements dans les fonctionnalités existantes
- **⚠️ Déprécié** pour les fonctionnalités qui seront bientôt supprimées
- **🗑️ Supprimé** pour les fonctionnalités supprimées
- **🐛 Corrigé** pour les corrections de bugs
- **🔒 Sécurité** pour les vulnérabilités corrigées

---

*Dernière mise à jour : 2025-12-01*
