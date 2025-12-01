# 📸 Guide Visuel - VocaNote

## 🎯 Interface de l'application

VocaNote présente une interface moderne et intuitive divisée en plusieurs sections :

### 1. En-tête
```
┌─────────────────────────────────────────────┐
│           🎤 VocaNote                       │
│  Transcription audio vers texte avec IA     │
└─────────────────────────────────────────────┘
```

### 2. Section Fichier Audio
```
┌─────────────────────────────────────────────┐
│ Fichier Audio                               │
│ ┌─────────────────────────────────────────┐ │
│ │ 📄 exemple.wav                          │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │  📁 Sélectionner un fichier WAV        │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 3. Paramètres de transcription
```
┌─────────────────────────────────────────────┐
│ Paramètres de transcription                 │
│                                             │
│  Modèle:          Langue:                  │
│  ┌──────────┐    ┌──────────────────┐     │
│  │ base ▼   │    │ Auto-détection ▼ │     │
│  └──────────┘    └──────────────────┘     │
└─────────────────────────────────────────────┘
```

### 4. Bouton de transcription
```
┌─────────────────────────────────────────────┐
│  ▶️ Démarrer la transcription               │
└─────────────────────────────────────────────┘
```

### 5. Zone de transcription
```
┌─────────────────────────────────────────────┐
│ Transcription                               │
│ ┌─────────────────────────────────────────┐ │
│ │                                         │ │
│ │  Le texte transcrit apparaît ici...    │ │
│ │                                         │ │
│ │                                         │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ┌──────┐ ┌────────────┐ ┌────────┐        │
│ │📋Copier│ │💾Enregistrer│ │🗑️Effacer│        │
│ └──────┘ └────────────┘ └────────┘        │
└─────────────────────────────────────────────┘
```

## 🎨 Palette de couleurs

### Couleurs principales
- **Bleu principal** : `#2196F3` - Boutons et accents
- **Vert succès** : `#4CAF50` - Bouton de transcription
- **Rouge erreur** : `#F44336` - Messages d'erreur
- **Gris neutre** : `#607D8B` - Boutons d'action
- **Fond** : `#fafafa` - Arrière-plan général

### États des boutons
```
┌─────────────────────────────────────┐
│ Normal    : Couleur principale      │
│ Hover     : Couleur plus foncée     │
│ Pressed   : Couleur encore plus foncée │
│ Disabled  : Gris (#cccccc)          │
└─────────────────────────────────────┘
```

## 📊 États de l'interface

### État initial
```
✅ Bouton "Sélectionner un fichier" : ACTIF
❌ Bouton "Démarrer la transcription" : INACTIF
❌ Boutons d'action (Copier, Enregistrer, Effacer) : INACTIFS
```

### Après sélection de fichier
```
✅ Bouton "Sélectionner un fichier" : ACTIF
✅ Bouton "Démarrer la transcription" : ACTIF
❌ Boutons d'action : INACTIFS
```

### Pendant la transcription
```
❌ Bouton "Sélectionner un fichier" : INACTIF
❌ Bouton "Démarrer la transcription" : INACTIF
❌ Sélecteurs (Modèle, Langue) : INACTIFS
🔄 Barre de progression : VISIBLE
📝 Message de statut : "Transcription en cours..."
```

### Après transcription réussie
```
✅ Bouton "Sélectionner un fichier" : ACTIF
✅ Bouton "Démarrer la transcription" : ACTIF
✅ Boutons d'action : ACTIFS
✅ Texte transcrit : AFFICHÉ
✅ Message de statut : "✅ Transcription terminée avec succès!"
```

## 🔄 Flux de travail

```
┌─────────────────┐
│  Lancer l'app   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Sélectionner    │
│  fichier audio  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Choisir modèle  │
│   et langue     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Démarrer la   │
│  transcription  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Téléchargement │
│   du modèle     │
│  (1ère fois)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Transcription  │
│   en cours...   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Affichage du    │
│     résultat    │
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│ Copier │ │Enregistrer│
└────────┘ └──────────┘
```

## 💡 Indicateurs visuels

### Fichier sélectionné
```
┌─────────────────────────────────────┐
│ 📄 exemple.wav                      │
│                                     │
│ Bordure : Verte (#4CAF50)          │
│ Fond : Vert clair (#E8F5E9)        │
└─────────────────────────────────────┘
```

### Aucun fichier
```
┌─────────────────────────────────────┐
│ Aucun fichier sélectionné          │
│                                     │
│ Bordure : Grise pointillée (#ccc)  │
│ Fond : Gris clair (#f5f5f5)        │
└─────────────────────────────────────┘
```

### Messages de statut

**En cours** :
```
🔄 Chargement du modèle Whisper...
   Couleur : Bleu (#2196F3)
```

**Succès** :
```
✅ Transcription terminée avec succès!
   Couleur : Vert (#4CAF50)
```

**Erreur** :
```
❌ Erreur lors de la transcription
   Couleur : Rouge (#F44336)
```

## 📐 Dimensions

### Fenêtre principale
- **Largeur** : 900 pixels
- **Hauteur** : 700 pixels
- **Position** : Centrée à l'écran

### Éléments
- **Boutons principaux** : Hauteur minimale 40-50px
- **Boutons d'action** : Hauteur minimale 35px
- **Espacement** : 15px entre les sections
- **Marges** : 20px autour du contenu
- **Bordures** : Rayon de 5px pour les coins arrondis

## 🎭 Thème visuel

### Style général
- **Design** : Material Design moderne
- **Coins** : Arrondis (5px)
- **Ombres** : Subtiles sur les boutons
- **Transitions** : Douces au survol
- **Police** : Segoe UI (Windows native)

### Hiérarchie visuelle
1. **Titre principal** : 24pt, gras, bleu
2. **Sous-titre** : 10pt, normal, gris
3. **Titres de sections** : Gras, noir
4. **Texte normal** : 11pt, normal
5. **Boutons** : 14-16pt, gras, blanc sur couleur

---

Cette interface a été conçue pour être :
- ✨ **Moderne** et professionnelle
- 🎯 **Intuitive** et facile à utiliser
- 🎨 **Visuellement agréable** avec des couleurs harmonieuses
- ♿ **Accessible** avec des contrastes suffisants
- 📱 **Responsive** aux différentes tailles d'écran

