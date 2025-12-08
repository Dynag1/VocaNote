#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour générer un fichier audio d'exemple avec plusieurs locuteurs
Utilise la synthèse vocale pour créer une conversation simulée
"""

import os
from pathlib import Path

try:
    from gtts import gTTS
    import numpy as np
    from scipy.io import wavfile
    import scipy.signal as signal
except ImportError:
    print("❌ Dépendances manquantes. Installez avec:")
    print("   pip install gtts numpy scipy")
    exit(1)


def create_multi_speaker_audio():
    """
    Crée un fichier audio d'exemple avec plusieurs locuteurs
    """
    print("🎤 Génération d'un audio multi-locuteurs...")
    
    # Textes pour chaque locuteur
    conversations = [
        ("Bonjour, comment allez-vous aujourd'hui ?", "fr", 1.0),
        ("Très bien merci, et vous ?", "fr", 0.8),
        ("Ça va bien, merci de demander. Parlons de notre projet.", "fr", 1.0),
        ("Oui, j'ai préparé le rapport que vous m'aviez demandé.", "fr", 0.8),
        ("Excellent, pouvez-vous nous le présenter ?", "fr", 1.0),
        ("Bien sûr, voici les résultats de notre analyse.", "fr", 0.8),
    ]
    
    # Créer les fichiers temporaires
    temp_files = []
    
    for i, (text, lang, speed) in enumerate(conversations):
        print(f"  Génération du segment {i+1}/{len(conversations)}...")
        
        # Générer le fichier audio avec gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        temp_file = f"temp_segment_{i}.mp3"
        tts.save(temp_file)
        temp_files.append(temp_file)
    
    print("✅ Segments générés")
    print("ℹ️  Note: Pour un vrai test de diarisation, utilisez un enregistrement")
    print("   avec de vraies voix différentes. Ce script génère juste un exemple.")
    
    # Nettoyer les fichiers temporaires
    print("\n🧹 Nettoyage des fichiers temporaires...")
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
        except:
            pass
    
    print("\n💡 Conseil: Pour tester la diarisation:")
    print("   1. Enregistrez une vraie conversation avec plusieurs personnes")
    print("   2. Ou téléchargez un exemple depuis:")
    print("      https://github.com/pyannote/pyannote-audio/tree/develop/tutorials/assets")


def download_example_audio():
    """
    Télécharge un fichier audio d'exemple depuis Internet
    """
    print("📥 Téléchargement d'un exemple audio...")
    
    try:
        import urllib.request
        
        # URL d'un exemple audio (à remplacer par une vraie URL)
        url = "https://github.com/pyannote/pyannote-audio/raw/develop/tutorials/assets/sample.wav"
        output_file = "exemple_multi_locuteurs.wav"
        
        print(f"  Téléchargement depuis: {url}")
        urllib.request.urlretrieve(url, output_file)
        print(f"✅ Fichier téléchargé: {output_file}")
        
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        print("\n💡 Vous pouvez:")
        print("   1. Enregistrer votre propre conversation")
        print("   2. Utiliser un fichier audio existant avec plusieurs voix")


if __name__ == "__main__":
    print("=" * 60)
    print("  Génération d'audio d'exemple pour la diarisation")
    print("=" * 60)
    print()
    
    print("⚠️  IMPORTANT:")
    print("   La synthèse vocale (TTS) génère la même voix pour tous les segments.")
    print("   Pour tester réellement la diarisation, vous devez utiliser un")
    print("   enregistrement avec de vraies voix différentes.")
    print()
    
    choice = input("Voulez-vous continuer ? (o/n): ")
    
    if choice.lower() == 'o':
        create_multi_speaker_audio()
    else:
        print("\n💡 Recommandations pour tester la diarisation:")
        print("   1. Enregistrez une conversation avec 2-3 personnes")
        print("   2. Utilisez un bon microphone")
        print("   3. Assurez-vous que chaque personne parle clairement")
        print("   4. Évitez les chevauchements de parole")
        print("   5. Enregistrez au format WAV pour la meilleure qualité")
