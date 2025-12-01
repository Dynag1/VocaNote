# 🚀 Guide d'Installation Rapide - VocaNote

## 📋 Étape 1 : Installation des dépendances

Ouvrez PowerShell dans le dossier VocaNote et exécutez :

```powershell
pip install -r requirements.txt
```

**Note importante** : L'installation peut prendre plusieurs minutes car PyTorch est un package volumineux (~2 GB).

### Pour accélération GPU (optionnel mais recommandé)

Si vous avez une carte graphique NVIDIA :

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 🎯 Étape 2 : Tester l'application

```powershell
python main.py
```

## 🎤 Étape 3 : Générer un fichier audio d'exemple (optionnel)

```powershell
pip install gTTS
python generate_example_audio.py
```

## 📦 Étape 4 : Créer l'exécutable

```powershell
python build.py
```

L'exécutable sera créé dans `dist/VocaNote/VocaNote.exe`

## 💿 Étape 5 : Créer l'installateur Windows

1. **Téléchargez et installez Inno Setup** :
   - Visitez : https://jrsoftware.org/isdl.php
   - Téléchargez "Inno Setup 6.x"
   - Installez avec les options par défaut

2. **Compilez l'installateur** :
   - Ouvrez `setup.iss` avec Inno Setup Compiler
   - Cliquez sur "Build" → "Compile" (ou F9)
   - L'installateur sera créé dans `installer/VocaNote_Setup_1.0.0.exe`

## ✅ Vérification

Après l'installation, vous devriez avoir :

```
VocaNote/
├── main.py                    ✅ Application principale
├── build.py                   ✅ Script de build
├── requirements.txt           ✅ Dépendances
├── setup.iss                  ✅ Script Inno Setup
├── dist/VocaNote/            ⬜ (après build)
│   └── VocaNote.exe          ⬜ Exécutable
└── installer/                ⬜ (après compilation Inno Setup)
    └── VocaNote_Setup_1.0.0.exe ⬜ Installateur
```

## 🐛 Problèmes courants

### Erreur : "pip n'est pas reconnu"
```powershell
python -m pip install -r requirements.txt
```

### Erreur : "Impossible d'installer PyTorch"
Essayez d'installer une version spécifique :
```powershell
pip install torch==2.1.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu118
```

### L'application est lente
- Utilisez le modèle "tiny" ou "base"
- Installez PyTorch avec support CUDA (voir ci-dessus)

### Erreur lors du build
Assurez-vous que :
- Toutes les dépendances sont installées
- Vous êtes dans le bon répertoire
- PyInstaller est installé : `pip install pyinstaller`

## 📞 Besoin d'aide ?

Consultez le fichier README.md pour plus de détails ou ouvrez une issue sur GitHub.

---

Bon développement ! 🎉
