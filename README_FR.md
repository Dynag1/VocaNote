# 🎤 VocaNote - Transcription Audio Intelligente

> **Transformez vos fichiers audio en texte avec l'intelligence artificielle**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper-orange.svg)](https://github.com/openai/whisper)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)

---

## 🚀 Démarrage Ultra-Rapide

### En 3 clics :
1. **Double-cliquez** sur `lancer_vocanote.bat`
2. **Sélectionnez** `exemple.wav`
3. **Cliquez** sur "Démarrer la transcription"

✨ **C'est tout !** Votre texte transcrit apparaît en quelques secondes.

---

## ✨ Fonctionnalités

- 🎯 **Transcription précise** avec l'IA Whisper d'OpenAI
- 🌍 **Multilingue** : Français, Anglais, Espagnol, Allemand, Italien, Portugais...
- 🎨 **Interface moderne** et intuitive
- ⚡ **Accélération GPU** (NVIDIA CUDA)
- 📁 **Formats multiples** : WAV, MP3, M4A, FLAC, OGG
- 💾 **Export facile** : Copie, sauvegarde TXT
- 🔧 **5 modèles** : du plus rapide au plus précis

---

## 📦 Installation

### Méthode 1 : Automatique (Recommandé)
```powershell
# 1. Installer FFmpeg (obligatoire)
installer_ffmpeg.bat

# 2. Lancer l'application
lancer_vocanote.bat
```
Le script installera automatiquement tout ce qui est nécessaire !

### Méthode 2 : Manuelle
```powershell
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'application
python main.py
```

---

## 🎯 Utilisation

### Interface Simple

```
┌─────────────────────────────────────┐
│        🎤 VocaNote                  │
│  Transcription audio vers texte     │
├─────────────────────────────────────┤
│                                     │
│  📁 Sélectionner un fichier WAV    │
│                                     │
│  Modèle: [base ▼]  Langue: [Auto ▼]│
│                                     │
│  ▶️ Démarrer la transcription       │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ Transcription...              │ │
│  └───────────────────────────────┘ │
│                                     │
│  [📋 Copier] [💾 Enregistrer] [🗑️]  │
└─────────────────────────────────────┘
```

### Choix du Modèle

| Modèle | Vitesse | Précision | Usage |
|--------|---------|-----------|-------|
| **tiny** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | Tests rapides |
| **base** | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ✅ **Recommandé** |
| **small** | ⚡⚡⚡ | ⭐⭐⭐⭐ | Meilleure qualité |
| **medium** | ⚡⚡ | ⭐⭐⭐⭐⭐ | Haute précision |
| **large** | ⚡ | ⭐⭐⭐⭐⭐ | Maximum précision |

---

## 📚 Documentation

| Document | Description | Pour qui ? |
|----------|-------------|------------|
| **[INDEX_DOCUMENTATION.md](INDEX_DOCUMENTATION.md)** | 📖 Index de toute la doc | Tous |
| **[DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md)** | 🚀 Guide 3 étapes | Débutants |
| **[INSTALLATION.md](INSTALLATION.md)** | 📦 Installation détaillée | Tous |
| **[GUIDE_VISUEL.md](GUIDE_VISUEL.md)** | 🎨 Interface et design | Utilisateurs |
| **[RESUME.md](RESUME.md)** | 📝 Résumé du projet | Tous |
| **[STRUCTURE_PROJET.md](STRUCTURE_PROJET.md)** | 📁 Architecture | Développeurs |

**👉 Commencez par : [INDEX_DOCUMENTATION.md](INDEX_DOCUMENTATION.md)**

---

## 🔧 Configuration Système

### Minimum
- Windows 10/11 (64-bit)
- Python 3.8+
- 4 GB RAM
- 2 GB disque libre

### Recommandé
- Windows 10/11 (64-bit)
- Python 3.10+
- 8 GB RAM
- Carte NVIDIA avec CUDA
- 5 GB disque libre

---

## 📦 Créer un Exécutable

### Méthode Automatique
```powershell
# Double-cliquez sur :
build_executable.bat
```

### Méthode Manuelle
```powershell
python build.py
```

L'exécutable sera dans : `dist/VocaNote/VocaNote.exe`

---

## 💿 Créer un Installateur

1. **Téléchargez** [Inno Setup](https://jrsoftware.org/isdl.php)
2. **Ouvrez** `setup.iss` avec Inno Setup Compiler
3. **Cliquez** sur Build → Compile (F9)
4. **Récupérez** l'installateur dans `installer/`

---

## 🎓 Exemples d'Utilisation

### Transcrire un podcast
```
1. Sélectionnez votre fichier MP3
2. Modèle : small ou medium
3. Langue : Auto-détection
4. Lancez la transcription
5. Enregistrez en TXT
```

### Transcrire une réunion
```
1. Sélectionnez l'enregistrement WAV
2. Modèle : base (rapide)
3. Langue : Français
4. Transcrivez
5. Copiez dans votre compte-rendu
```

### Sous-titres vidéo
```
1. Extrayez l'audio de votre vidéo
2. Modèle : medium (précis)
3. Langue : selon la vidéo
4. Transcrivez
5. Formatez en SRT (manuel)
```

---

## 🐛 Dépannage

### L'application ne démarre pas
```powershell
# Vérifiez Python
python --version

# Installez les dépendances
pip install -r requirements.txt
```

### Transcription lente
```powershell
# Utilisez un modèle plus petit
Modèle : tiny ou base

# Ou installez CUDA (NVIDIA)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Erreur de mémoire
```
Solution : Utilisez un modèle plus petit (tiny ou base)
```

**Plus de solutions** : Consultez [INSTALLATION.md](INSTALLATION.md)

---

## 🌟 Points Forts

### ✅ Facile à utiliser
- Interface intuitive
- Pas de configuration complexe
- Fonctionne immédiatement

### ✅ Puissant
- IA de pointe (Whisper)
- Précision exceptionnelle
- Support multilingue

### ✅ Flexible
- 5 modèles au choix
- Formats audio variés
- Export facile

### ✅ Gratuit
- Open source
- Pas d'abonnement
- Pas de limite d'utilisation

---

## 📊 Technologies

- **Python** - Langage de programmation
- **PyQt6** - Interface graphique moderne
- **OpenAI Whisper** - Modèle de transcription IA
- **PyTorch** - Framework de deep learning
- **PyInstaller** - Création d'exécutables
- **Inno Setup** - Installateur Windows

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Pushez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT. Voir [LICENSE.txt](LICENSE.txt) pour plus de détails.

---

## 🙏 Remerciements

- [OpenAI](https://openai.com/) pour le modèle Whisper
- [Riverbank Computing](https://www.riverbankcomputing.com/) pour PyQt6
- [PyInstaller](https://www.pyinstaller.org/) pour la création d'exécutables
- [Inno Setup](https://jrsoftware.org/) pour l'installateur Windows

---

## 📞 Support

- 📖 **Documentation** : Consultez les fichiers .md
- 🐛 **Bugs** : Ouvrez une issue sur GitHub
- 💡 **Suggestions** : Proposez vos idées
- ❓ **Questions** : Consultez la FAQ dans la documentation

---

## 🎉 Prêt à Commencer ?

### Option 1 : Utilisation immédiate
```
Double-cliquez sur : lancer_vocanote.bat
```

### Option 2 : Développement
```powershell
pip install -r requirements.txt
python main.py
```

### Option 3 : Documentation
```
Ouvrez : INDEX_DOCUMENTATION.md
```

---

<div align="center">

**VocaNote** - *Transcription audio intelligente avec l'IA* 🎤✨

Développé avec ❤️ par VocaNote Team

[Documentation](INDEX_DOCUMENTATION.md) • [Installation](INSTALLATION.md) • [Guide Rapide](DEMARRAGE_RAPIDE.md)

</div>
