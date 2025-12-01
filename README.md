# 🎤 VocaNote - Transcription Audio vers Texte

VocaNote est une application de bureau moderne qui utilise l'intelligence artificielle pour transcrire vos fichiers audio en texte.

![VocaNote](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Fonctionnalités

- 🎯 **Transcription précise** utilisant Whisper d'OpenAI
- 🌍 **Support multilingue** avec détection automatique
- 🎨 **Interface moderne** et intuitive avec PyQt6
- ⚡ **Accélération GPU** (CUDA) pour des transcriptions rapides
- 📁 **Multiples formats** supportés (WAV, MP3, M4A, FLAC, OGG)
- 💾 **Sauvegarde facile** des transcriptions
- 📋 **Copie rapide** dans le presse-papiers

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- Windows 10/11 (64-bit)
- 4 GB RAM minimum (8 GB recommandé)
- Carte graphique NVIDIA avec CUDA (optionnel, pour accélération)

### Installation des dépendances

```bash
# Cloner ou télécharger le projet
cd VocaNote

# Installer les dépendances
pip install -r requirements.txt
```

### Exécution de l'application

```bash
python main.py
```

## 📦 Création de l'exécutable

### 1. Construire l'exécutable

```bash
python build.py
```

Ce script va:
- Nettoyer les anciens builds
- Installer PyInstaller si nécessaire
- Créer le fichier .spec
- Générer l'exécutable dans `dist/VocaNote/`

### 2. Créer l'installateur Windows

1. Installez [Inno Setup](https://jrsoftware.org/isdl.php)
2. Ouvrez `setup.iss` avec Inno Setup Compiler
3. Cliquez sur "Compile" (ou appuyez sur F9)
4. L'installateur sera créé dans le dossier `installer/`

## 🎯 Utilisation

1. **Sélectionner un fichier audio**
   - Cliquez sur "Sélectionner un fichier WAV"
   - Choisissez votre fichier audio

2. **Configurer les paramètres**
   - **Modèle**: Choisissez entre rapidité et précision
     - `tiny`: Très rapide, moins précis
     - `base`: Bon compromis (recommandé)
     - `small`: Plus précis
     - `medium`: Très précis
     - `large`: Maximum de précision
   - **Langue**: Sélectionnez la langue ou laissez en auto-détection

3. **Transcrire**
   - Cliquez sur "Démarrer la transcription"
   - Attendez la fin du traitement

4. **Utiliser le résultat**
   - Copiez le texte dans le presse-papiers
   - Enregistrez dans un fichier .txt
   - Éditez directement dans l'application

## 🔧 Configuration système

### Pour utilisation CPU uniquement
L'application fonctionnera sur n'importe quel PC moderne, mais la transcription sera plus lente.

### Pour accélération GPU (recommandé)
- Carte graphique NVIDIA avec support CUDA
- Pilotes NVIDIA à jour
- CUDA Toolkit 11.8 ou supérieur

Pour installer PyTorch avec support CUDA:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 📊 Modèles disponibles

| Modèle | Taille | RAM requise | Vitesse | Précision |
|--------|--------|-------------|---------|-----------|
| tiny   | ~75 MB | ~1 GB       | ⚡⚡⚡⚡⚡ | ⭐⭐⭐   |
| base   | ~150 MB| ~1 GB       | ⚡⚡⚡⚡  | ⭐⭐⭐⭐  |
| small  | ~500 MB| ~2 GB       | ⚡⚡⚡    | ⭐⭐⭐⭐  |
| medium | ~1.5 GB| ~5 GB       | ⚡⚡     | ⭐⭐⭐⭐⭐ |
| large  | ~3 GB  | ~10 GB      | ⚡      | ⭐⭐⭐⭐⭐ |

## 🌍 Langues supportées

- Français
- Anglais
- Espagnol
- Allemand
- Italien
- Portugais
- Et bien d'autres...

## 📝 Structure du projet

```
VocaNote/
├── main.py              # Application principale
├── build.py             # Script de build
├── requirements.txt     # Dépendances Python
├── setup.iss           # Script Inno Setup
├── README.md           # Ce fichier
├── README.txt          # Documentation pour l'installateur
├── LICENSE.txt         # Licence MIT
└── exemple.wav         # Fichier audio d'exemple
```

## 🐛 Dépannage

### L'application ne démarre pas
- Vérifiez que Python 3.8+ est installé
- Assurez-vous que toutes les dépendances sont installées

### La transcription est très lente
- Utilisez un modèle plus petit (tiny ou base)
- Installez PyTorch avec support CUDA si vous avez une carte NVIDIA

### Erreur de mémoire
- Utilisez un modèle plus petit
- Fermez les autres applications
- Augmentez la RAM de votre système

### Le modèle ne se télécharge pas
- Vérifiez votre connexion Internet
- Les modèles sont téléchargés automatiquement lors de la première utilisation

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE.txt](LICENSE.txt) pour plus de détails.

## 🙏 Remerciements

- [OpenAI Whisper](https://github.com/openai/whisper) pour le modèle de transcription
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) pour l'interface graphique
- [PyInstaller](https://www.pyinstaller.org/) pour la création d'exécutables
- [Inno Setup](https://jrsoftware.org/isinfo.php) pour l'installateur Windows

## 📧 Support

Pour toute question ou problème, veuillez ouvrir une issue sur GitHub.

---

Développé avec ❤️ par VocaNote Team
