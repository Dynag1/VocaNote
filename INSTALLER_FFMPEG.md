# 🎬 Installation de FFmpeg pour VocaNote

## ⚠️ Problème

Si vous voyez cette erreur :
```
Erreur lors de la transcription: [WinError 2] Le fichier spécifié est introuvable
```

Cela signifie que **FFmpeg n'est pas installé** sur votre système.

---

## 🔧 Solution : Installer FFmpeg

### **Méthode 1 : Chocolatey (Recommandé - Automatique)**

#### 1. Installer Chocolatey (si pas déjà installé)

Ouvrez PowerShell **en tant qu'administrateur** et exécutez :

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

#### 2. Installer FFmpeg

```powershell
choco install ffmpeg -y
```

#### 3. Redémarrer le terminal

Fermez et rouvrez votre terminal pour que les changements prennent effet.

#### 4. Vérifier l'installation

```powershell
ffmpeg -version
```

Si vous voyez la version de FFmpeg, c'est installé ! ✅

---

### **Méthode 2 : Installation Manuelle**

#### 1. Télécharger FFmpeg

Visitez : https://www.gyan.dev/ffmpeg/builds/

Téléchargez : **ffmpeg-release-essentials.zip**

#### 2. Extraire l'archive

Extrayez le fichier ZIP dans un dossier, par exemple :
```
C:\ffmpeg
```

#### 3. Ajouter au PATH

1. Ouvrez les **Paramètres système avancés**
   - Clic droit sur "Ce PC" → Propriétés
   - Paramètres système avancés
   - Variables d'environnement

2. Dans **Variables système**, trouvez **Path**

3. Cliquez sur **Modifier**

4. Cliquez sur **Nouveau**

5. Ajoutez le chemin vers le dossier `bin` de FFmpeg :
   ```
   C:\ffmpeg\bin
   ```

6. Cliquez sur **OK** partout

#### 4. Redémarrer le terminal

Fermez et rouvrez votre terminal.

#### 5. Vérifier l'installation

```powershell
ffmpeg -version
```

---

### **Méthode 3 : Winget (Windows 11)**

Si vous avez Windows 11 :

```powershell
winget install ffmpeg
```

---

## ✅ Vérification

Après l'installation, vérifiez que FFmpeg fonctionne :

```powershell
ffmpeg -version
```

Vous devriez voir quelque chose comme :
```
ffmpeg version 8.0.1 Copyright (c) 2000-2024 the FFmpeg developers
built with gcc 13.2.0 (Rev1, Built by MSYS2 project)
...
```

---

## 🚀 Relancer VocaNote

Une fois FFmpeg installé :

1. **Fermez VocaNote** (si ouvert)
2. **Relancez** l'application :
   ```powershell
   python main.py
   ```
   Ou double-cliquez sur `lancer_vocanote.bat`

3. **Testez** la transcription avec `exemple.wav`

---

## 🐛 Dépannage

### FFmpeg n'est toujours pas reconnu

**Solution 1** : Redémarrez complètement votre ordinateur

**Solution 2** : Vérifiez le PATH
```powershell
echo $env:Path
```
Vous devriez voir le chemin vers FFmpeg.

**Solution 3** : Réinstallez FFmpeg
```powershell
choco uninstall ffmpeg
choco install ffmpeg -y
```

### Erreur "choco n'est pas reconnu"

Chocolatey n'est pas installé. Utilisez la **Méthode 2 (Installation Manuelle)** ci-dessus.

### Erreur de permissions

Exécutez PowerShell **en tant qu'administrateur** :
- Clic droit sur PowerShell
- "Exécuter en tant qu'administrateur"

---

## 📝 Pourquoi FFmpeg est nécessaire ?

**FFmpeg** est un outil qui permet de :
- ✅ Lire différents formats audio (MP3, M4A, FLAC, OGG)
- ✅ Convertir les fichiers audio
- ✅ Extraire l'audio des vidéos
- ✅ Traiter les fichiers audio pour Whisper

Sans FFmpeg, VocaNote ne peut traiter que les fichiers WAV bruts.

---

## 🎯 Résumé

| Méthode | Difficulté | Temps | Recommandé |
|---------|------------|-------|------------|
| **Chocolatey** | ⭐ Facile | 2 min | ✅ Oui |
| **Manuelle** | ⭐⭐ Moyen | 5 min | Si Chocolatey échoue |
| **Winget** | ⭐ Facile | 2 min | Windows 11 uniquement |

---

## 📞 Besoin d'aide ?

Si vous rencontrez toujours des problèmes :

1. Vérifiez que FFmpeg est dans le PATH
2. Redémarrez votre ordinateur
3. Réinstallez FFmpeg
4. Consultez la documentation FFmpeg : https://ffmpeg.org/

---

**Une fois FFmpeg installé, VocaNote fonctionnera parfaitement ! 🎉**

---

*Dernière mise à jour : 2025-12-01*
