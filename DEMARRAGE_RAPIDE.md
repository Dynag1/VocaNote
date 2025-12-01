# 🚀 Démarrage Rapide - VocaNote

Bienvenue dans **VocaNote**, votre application de transcription audio intelligente !

## ⚡ Lancement rapide (3 étapes)

### 1️⃣ Double-cliquez sur `lancer_vocanote.bat`

C'est tout ! Le script va :
- ✅ Vérifier que Python est installé
- ✅ Installer les dépendances si nécessaire
- ✅ Lancer l'application

### 2️⃣ Sélectionnez un fichier audio

Dans l'application :
1. Cliquez sur **"📁 Sélectionner un fichier WAV"**
2. Choisissez `exemple.wav` (ou votre propre fichier)

### 3️⃣ Lancez la transcription

1. Sélectionnez le modèle (recommandé : **base**)
2. Choisissez la langue (ou laissez en **Auto-détection**)
3. Cliquez sur **"▶️ Démarrer la transcription"**
4. Attendez quelques secondes... ✨

**C'est fait !** Le texte transcrit apparaît dans la zone de texte.

---

## 📖 Guide complet

### Formats audio supportés
- ✅ WAV (recommandé)
- ✅ MP3
- ✅ M4A
- ✅ FLAC
- ✅ OGG

### Choix du modèle

| Modèle | Quand l'utiliser ? |
|--------|-------------------|
| **tiny** | Tests rapides, fichiers courts |
| **base** | ⭐ **RECOMMANDÉ** - Bon compromis vitesse/qualité |
| **small** | Meilleure qualité, fichiers importants |
| **medium** | Haute précision, si vous avez le temps |
| **large** | Maximum de précision, fichiers longs |

### Choix de la langue

- **Auto-détection** ⭐ Recommandé - Détecte automatiquement
- **Français (fr)** - Si vous êtes sûr que c'est du français
- **Anglais (en)** - Pour l'anglais uniquement
- Etc.

---

## 💡 Conseils d'utilisation

### ✨ Pour de meilleurs résultats :

1. **Qualité audio** : Utilisez des fichiers avec une bonne qualité sonore
2. **Bruit de fond** : Évitez les fichiers avec beaucoup de bruit
3. **Débit de parole** : Les enregistrements clairs fonctionnent mieux
4. **Durée** : Pour les fichiers longs (>30 min), utilisez "small" ou "medium"

### ⚡ Pour aller plus vite :

1. **Utilisez "tiny"** pour les tests rapides
2. **Carte graphique NVIDIA ?** Installez CUDA pour 5-10x plus rapide :
   ```powershell
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

---

## 🎯 Après la transcription

Une fois la transcription terminée, vous pouvez :

### 📋 Copier le texte
Cliquez sur **"📋 Copier"** pour copier dans le presse-papiers

### 💾 Enregistrer
Cliquez sur **"💾 Enregistrer"** pour sauvegarder dans un fichier .txt

### ✏️ Éditer
Modifiez directement le texte dans la zone de texte

### 🗑️ Effacer
Cliquez sur **"🗑️ Effacer"** pour recommencer

---

## 🔧 Résolution de problèmes

### ❓ L'application ne démarre pas

**Solution 1** : Lancez manuellement
```powershell
python main.py
```

**Solution 2** : Installez les dépendances
```powershell
pip install -r requirements.txt
```

### ❓ La transcription est très lente

**Solution 1** : Utilisez un modèle plus petit (tiny ou base)

**Solution 2** : Installez PyTorch avec CUDA (si carte NVIDIA)
```powershell
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### ❓ Erreur "No module named..."

**Solution** : Installez les dépendances
```powershell
pip install -r requirements.txt
```

### ❓ Le modèle ne se télécharge pas

**Solution** : Vérifiez votre connexion Internet. Le modèle se télécharge automatiquement lors de la première utilisation.

---

## 📦 Créer un exécutable

Pour distribuer VocaNote sans Python :

### Méthode 1 : Script automatique
Double-cliquez sur **`build_executable.bat`**

### Méthode 2 : Manuelle
```powershell
python build.py
```

L'exécutable sera dans : `dist/VocaNote/VocaNote.exe`

---

## 💿 Créer un installateur Windows

1. **Téléchargez Inno Setup** : https://jrsoftware.org/isdl.php
2. **Installez Inno Setup**
3. **Ouvrez `setup.iss`** avec Inno Setup Compiler
4. **Cliquez sur Build → Compile** (ou F9)
5. L'installateur sera dans : `installer/VocaNote_Setup_1.0.0.exe`

---

## 📚 Documentation complète

Pour plus d'informations, consultez :
- **README.md** - Documentation complète
- **INSTALLATION.md** - Guide d'installation détaillé
- **RESUME.md** - Résumé du projet

---

## 🎉 Vous êtes prêt !

**VocaNote** est maintenant prêt à transcrire vos fichiers audio.

### Commencez maintenant :
1. Double-cliquez sur **`lancer_vocanote.bat`**
2. Sélectionnez **`exemple.wav`**
3. Cliquez sur **"Démarrer la transcription"**

**Bonne transcription ! 🎤✨**

---

*Développé avec ❤️ par VocaNote Team*
