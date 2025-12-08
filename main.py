#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocaNote - Transcription Audio vers Texte
Application de transcription audio utilisant Whisper d'OpenAI
"""

import sys
import os
import warnings
import traceback
import logging
from datetime import datetime

# --- CONFIGURATION LOGGING ---
# Définir le chemin du fichier de log
if getattr(sys, 'frozen', False):
    # En mode exe, écrire dans le dossier utilisateur ou à côté de l'exe
    # Dossier AppData/Local/VocaNote pour être propre sous Windows
    log_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.getcwd()), 'VocaNote')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'vocanote.log')
else:
    # En dev, écrire à la racine
    log_file = 'vocanote.log'

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Rediriger stdout et stderr vers les logs
class LogStream:
    def __init__(self, level):
        self.level = level
    def write(self, message):
        if message.strip():
            self.level(message.strip())
    def flush(self):
        pass

# Ne rediriger que si pas de console (mode frozen sans console)
# sys.stdout = LogStream(logging.info)
# sys.stderr = LogStream(logging.error)

# Capturer les exceptions non gérées
def exception_hook(exctype, value, tb):
    logging.critical("CRITICAL ERROR: Uncaught exception", exc_info=(exctype, value, tb))
    # Afficher une boite de dialogue si possible, sinon juste logger
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        if QApplication.instance():
            error_msg = "".join(traceback.format_exception(exctype, value, tb))
            QMessageBox.critical(None, "Erreur Critique", f"Une erreur est survenue:\n{value}\n\nVoir les logs: {log_file}")
    except:
        pass
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = exception_hook

logging.info("--- Démarrage de VocaNote ---")
logging.info(f"Version Python: {sys.version}")
logging.info(f"Executable: {sys.executable}")

from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog, QProgressBar,
    QMessageBox, QComboBox, QGroupBox, QDialog, QLineEdit, QFormLayout,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

# Import du système de licence
import license as lic

# Import du module de diarisation
from diarization import SpeakerDiarization
# Import du module de résumé
from summarizer import get_summarizer

# Supprimer les avertissements FP16 de Whisper
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

# --- CONFIGURATION FFMPEG ---
print("🔍 Configuration de FFmpeg...")
ffmpeg_dirs = []

# Déterminer le chemin de base (différent en mode développement vs exécutable)
if getattr(sys, 'frozen', False):
    # Mode exécutable PyInstaller
    base_path = sys._MEIPASS
else:
    # Mode développement
    base_path = os.getcwd()

# 1. Chercher dans le dossier local (créé par installer_ffmpeg.bat)
# Vérifier ffmpeg/bin ET ffmpeg/ racine
possible_paths = [
    os.path.join(base_path, "ffmpeg", "bin"),
    os.path.join(base_path, "ffmpeg")
]

for path in possible_paths:
    if os.path.exists(path) and (os.path.exists(os.path.join(path, "ffmpeg.exe")) or os.path.exists(os.path.join(path, "ffmpeg"))):
        print(f"   ✅ FFmpeg local trouvé: {path}")
        ffmpeg_dirs.append(path)
        break

# 2. Chercher via imageio_ffmpeg (si installé)
# 2. Chercher via imageio_ffmpeg (si installé)
try:
    import imageio_ffmpeg
    try:
        # Ppeut échouer en mode frozen
        exe_path = imageio_ffmpeg.get_ffmpeg_exe()
        imageio_path = os.path.dirname(exe_path)
        print(f"   ✅ imageio-ffmpeg trouvé: {imageio_path}")
        ffmpeg_dirs.append(imageio_path)
    except Exception as e:
        print(f"   ℹ️ imageio-ffmpeg erreur runtime: {e}")
except ImportError:
    print("   ℹ️ imageio-ffmpeg non installé")

# Ajouter au PATH
if ffmpeg_dirs:
    current_path = os.environ.get("PATH", "")
    # Ajouter au début du PATH pour être prioritaire
    os.environ["PATH"] = os.pathsep.join(ffmpeg_dirs) + os.pathsep + current_path
    print("   ✅ PATH mis à jour avec FFmpeg")
else:
    print("   ⚠️ Aucun dossier FFmpeg spécifique trouvé (utilisation du PATH système)")

# Vérification finale
import shutil
if shutil.which("ffmpeg"):
    print(f"   🚀 FFmpeg est prêt: {shutil.which('ffmpeg')}")
else:
    print("   ❌ FFmpeg n'est PAS trouvé dans le PATH!")
# ---------------------------

import whisper
import torch

# --- FIX POUR EXÉCUTABLE SANS CONSOLE ---
# Rediriger stdout/stderr si None (cas PyInstaller console=False)
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
# ----------------------------------------


class SummaryThread(QThread):
    """Thread pour générer le résumé sans bloquer l'interface"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, text):
        super().__init__()
        self.text = text
        
    def run(self):
        try:
            summarizer = get_summarizer()
            # Ratio adaptatif en fonction de la longueur (pour les longs textes on compresse plus)
            if len(self.text) > 10000:
                ratio = 0.1
            else:
                ratio = 0.2
                
            summary = summarizer.summarize(self.text, ratio=ratio)
            self.finished.emit(summary)
        except Exception as e:
            self.error.emit(str(e))


class TranscriptionThread(QThread):
    """Thread pour effectuer la transcription sans bloquer l'interface"""
    progress = pyqtSignal(str)
    progress_percent = pyqtSignal(int)  # Signal pour la progression en pourcentage
    progress_indeterminate = pyqtSignal(bool) # Signal pour passer en mode indéterminé
    finished = pyqtSignal(dict)  # On renvoie le dictionnaire complet (texte + segments)
    error = pyqtSignal(str)
    warning = pyqtSignal(str)  # Pour les avertissements de licence
    
    def __init__(self, audio_file, model_size="base", language=None, max_duration=None, enable_diarization=False):
        super().__init__()
        self.audio_file = audio_file
        self.model_size = model_size
        self.language = language
        self.max_duration = max_duration  # Limite de durée en secondes (pour version sans licence)
        self.enable_diarization = enable_diarization  # Activer la diarisation des locuteurs
        
    def run(self):
        try:
            import tempfile
            import numpy as np
            
            self.progress.emit("Chargement du modèle Whisper...")
            
            # Vérifier si CUDA est disponible
            device = "cuda" if torch.cuda.is_available() else "cpu"
            device_name = "🚀 GPU (CUDA)" if device == "cuda" else "💻 CPU"
            self.progress.emit(f"Périphérique: {device_name}")
            
            # Charger le modèle
            model = whisper.load_model(self.model_size, device=device)
            
            audio_to_transcribe = self.audio_file
            temp_file = None
            
            # Vérifier la limite de durée (version sans licence)
            if self.max_duration is not None:
                # Charger l'audio avec Whisper pour vérifier la durée
                audio = whisper.load_audio(self.audio_file)
                audio_duration = len(audio) / whisper.audio.SAMPLE_RATE
                
                if audio_duration > self.max_duration:
                    self.warning.emit(f"⚠️ Version d'évaluation : transcription limitée à {self.max_duration} secondes")
                    
                    # Tronquer l'audio à la limite
                    max_samples = int(self.max_duration * whisper.audio.SAMPLE_RATE)
                    audio_truncated = audio[:max_samples]
                    
                    # Sauvegarder l'audio tronqué dans un fichier temporaire
                    import scipy.io.wavfile as wav
                    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                    temp_file.close()
                    
                    # Convertir en int16 pour le fichier WAV
                    audio_int16 = (audio_truncated * 32767).astype(np.int16)
                    wav.write(temp_file.name, whisper.audio.SAMPLE_RATE, audio_int16)
                    
                    audio_to_transcribe = temp_file.name
            
            # Charger l'audio pour calculer la durée et les segments
            audio = whisper.load_audio(audio_to_transcribe)
            audio_duration = len(audio) / whisper.audio.SAMPLE_RATE
            
            # Whisper traite par segments de 30 secondes
            SEGMENT_DURATION = 30
            num_segments = max(1, int(np.ceil(audio_duration / SEGMENT_DURATION)))
            
            self.progress.emit(f"Transcription en cours... ({int(audio_duration)}s d'audio)")
            self.progress_percent.emit(0)
            
            # Transcription segment par segment pour progression réelle
            all_segments = []
            full_text = ""
            
            for i in range(num_segments):
                start_sample = i * SEGMENT_DURATION * whisper.audio.SAMPLE_RATE
                end_sample = min((i + 1) * SEGMENT_DURATION * whisper.audio.SAMPLE_RATE, len(audio))
                
                segment_audio = audio[int(start_sample):int(end_sample)]
                
                # Émettre la progression AVANT de transcrire ce segment
                progress_percent = int((i / num_segments) * 95)
                self.progress_percent.emit(progress_percent)
                self.progress.emit(f"Transcription segment {i+1}/{num_segments}...")
                
                # Transcrire ce segment
                # Utiliser pad_or_trim pour s'assurer que l'audio fait exactement 30s
                segment_audio_padded = whisper.pad_or_trim(segment_audio)
                mel = whisper.log_mel_spectrogram(segment_audio_padded).to(device)
                
                # Détecter la langue si pas spécifiée (seulement pour le premier segment)
                if i == 0 and self.language is None:
                    _, probs = model.detect_language(mel)
                    detected_lang = max(probs, key=probs.get)
                    self.progress.emit(f"Langue détectée: {detected_lang}")
                    decode_language = detected_lang
                else:
                    decode_language = self.language if self.language else "fr"
                
                # Options de décodage
                options = whisper.DecodingOptions(
                    language=decode_language,
                    without_timestamps=False
                )
                
                # Décoder le segment
                decode_result = whisper.decode(model, mel, options)
                
                segment_text = decode_result.text.strip()
                if segment_text:
                    # Calculer les timestamps réels
                    segment_start_time = i * SEGMENT_DURATION
                    
                    # Ajouter au texte complet
                    full_text += segment_text + " "
                    
                    # Créer un segment avec les timestamps
                    all_segments.append({
                        'start': segment_start_time,
                        'end': min(segment_start_time + SEGMENT_DURATION, audio_duration),
                        'text': segment_text
                    })
            
            # Créer le résultat final
            result = {
                'text': full_text.strip(),
                'segments': all_segments,
                'language': decode_language if 'decode_language' in dir() else self.language
            }
            
            self.progress_percent.emit(100)
            
            # Nettoyer le fichier temporaire si créé
            if temp_file is not None:
                try:
                    os.remove(temp_file.name)
                except:
                    pass
            
            # Effectuer la diarisation si activée
            if self.enable_diarization:
                try:
                    self.progress.emit("Détection des locuteurs en cours... (Cela peut prendre plusieurs minutes la première fois lors du téléchargement des modèles)")
                    self.progress_indeterminate.emit(True) # Mode indéterminé
                    
                    diarizer = SpeakerDiarization()
                    
                    if diarizer.load_model():
                        # Effectuer la diarisation
                        diarization_segments = diarizer.diarize(self.audio_file)
                        
                        if diarization_segments:
                            # Fusionner avec la transcription
                            merged_segments = diarizer.merge_with_transcription(
                                result.get('segments', []),
                                diarization_segments
                            )
                            
                            # Ajouter les segments fusionnés au résultat
                            result['diarized_segments'] = merged_segments
                            self.progress.emit("Diarisation terminée!")
                        else:
                            self.warning.emit("⚠️ Aucun locuteur détecté")
                    else:
                        self.warning.emit("⚠️ Impossible de charger le modèle de diarisation")
                    
                    self.progress_indeterminate.emit(False) # Retour au mode normal
                except Exception as e:
                    self.progress_indeterminate.emit(False)
                    self.warning.emit(f"⚠️ Erreur lors de la diarisation: {str(e)}")
            
            self.progress.emit("Transcription terminée!")
            self.finished.emit(result)  # Renvoyer tout le résultat
            
        except Exception as e:
            self.error.emit(f"Erreur lors de la transcription: {str(e)}")


class LicenseDialog(QDialog):
    """Dialogue pour gérer la licence"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion de la licence")
        self.setMinimumWidth(450)
        self.setup_ui()
        self.update_status()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Statut actuel
        self.status_group = QGroupBox("Statut de la licence")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        self.status_group.setLayout(status_layout)
        layout.addWidget(self.status_group)
        
        # Code d'activation de la machine
        activation_group = QGroupBox("Code d'activation de votre machine")
        activation_layout = QVBoxLayout()
        
        activation_info = QLabel("Communiquez ce code pour obtenir une licence :")
        activation_info.setStyleSheet("color: #666;")
        activation_layout.addWidget(activation_info)
        
        # Affichage du code d'activation
        activation_code = lic.generate_activation_code()
        self.activation_code_input = QLineEdit(activation_code)
        self.activation_code_input.setReadOnly(True)
        self.activation_code_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: 2px solid #2196F3;
                border-radius: 5px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                font-weight: bold;
                color: #1976D2;
            }
        """)
        activation_layout.addWidget(self.activation_code_input)
        
        # Bouton copier le code
        self.btn_copy_code = QPushButton("📋 Copier le code")
        self.btn_copy_code.clicked.connect(self.copy_activation_code)
        self.btn_copy_code.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        activation_layout.addWidget(self.btn_copy_code)
        
        activation_group.setLayout(activation_layout)
        layout.addWidget(activation_group)
        
        # Saisie de la clé
        key_group = QGroupBox("Activer une licence")
        key_layout = QFormLayout()
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Entrez votre clé de licence...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_layout.addRow("Clé de licence:", self.key_input)
        
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # Boutons
        btn_layout = QHBoxLayout()
        
        self.btn_activate = QPushButton("✅ Activer")
        self.btn_activate.clicked.connect(self.activate_license)
        self.btn_activate.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_layout.addWidget(self.btn_activate)
        
        self.btn_deactivate = QPushButton("❌ Désactiver")
        self.btn_deactivate.clicked.connect(self.deactivate_license)
        self.btn_deactivate.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        btn_layout.addWidget(self.btn_deactivate)
        
        self.btn_close = QPushButton("Fermer")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
        
        # Info
        info_label = QLabel("💡 Pour obtenir une licence, rendez-vous sur prog.dynag.co")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        layout.addWidget(info_label)
    
    def update_status(self):
        """Met à jour l'affichage du statut"""
        status = lic.get_license_status()
        
        if status['is_valid']:
            # Construire le texte avec les infos d'expiration
            expiry_info = ""
            if status['is_perpetual']:
                expiry_info = "Licence perpétuelle"
            else:
                days = status['days_remaining']
                if days is not None:
                    if days <= 7:
                        expiry_info = f"<span style='color: #FF5722;'>⏰ {status['days_remaining_text']}</span>"
                    elif days <= 30:
                        expiry_info = f"<span style='color: #FF9800;'>⏰ {status['days_remaining_text']}</span>"
                    else:
                        expiry_info = f"⏰ {status['days_remaining_text']}"
                    
                    if status['expiry_date']:
                        expiry_info += f"<br>Expire le: {status['expiry_date']}"
            
            self.status_label.setText(
                "✅ <b style='color: #4CAF50;'>Licence active</b><br>"
                f"Clé: {status['key_masked']}<br>"
                f"{expiry_info}<br>"
                "Transcription illimitée"
            )
            self.status_label.setStyleSheet("padding: 10px; background-color: #E8F5E9; border-radius: 5px;")
            self.btn_deactivate.setEnabled(True)
        else:
            # Vérifier si c'est une licence expirée
            if status['expiry_date'] and status['days_remaining'] is not None and status['days_remaining'] < 0:
                self.status_label.setText(
                    "❌ <b style='color: #F44336;'>Licence expirée</b><br>"
                    f"Expirée le: {status['expiry_date']}<br>"
                    f"Transcription limitée à {status['limit_seconds']} secondes"
                )
                self.status_label.setStyleSheet("padding: 10px; background-color: #FFEBEE; border-radius: 5px;")
            else:
                self.status_label.setText(
                    "⚠️ <b style='color: #FF9800;'>Version d'évaluation</b><br>"
                    f"Transcription limitée à {status['limit_seconds']} secondes"
                )
                self.status_label.setStyleSheet("padding: 10px; background-color: #FFF3E0; border-radius: 5px;")
            self.btn_deactivate.setEnabled(False)
    
    def activate_license(self):
        """Active la licence avec la clé saisie"""
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une clé de licence.")
            return
        
        if lic.activate_license(key):
            QMessageBox.information(self, "Succès", "✅ Licence activée avec succès!\n\nVous pouvez maintenant transcrire sans limite de durée.")
            self.key_input.clear()
            self.update_status()
        else:
            QMessageBox.critical(self, "Erreur", "❌ Clé de licence invalide.\n\nVérifiez votre clé et réessayez.")
    
    def deactivate_license(self):
        """Désactive la licence"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment désactiver votre licence?\n\nLa transcription sera limitée à 30 secondes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            lic.deactivate_license()
            self.update_status()
    
    def copy_activation_code(self):
        """Copie le code d'activation dans le presse-papiers"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.activation_code_input.text())
        QMessageBox.information(self, "Copié", "✅ Code d'activation copié dans le presse-papiers!")


class VocaNote(QMainWindow):
    """Fenêtre principale de l'application VocaNote"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.transcription_thread = None
        self.last_result = None  # Pour stocker le résultat brut
        self.init_ui()
        self.update_license_display()
        
    def init_ui(self):
        """Initialiser l'interface utilisateur"""
        self.setWindowTitle("VocaNote - Transcription Audio")
        self.setGeometry(100, 100, 900, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # === En-tête avec bouton licence ===
        header_layout = QHBoxLayout()
        
        # Spacer gauche
        header_layout.addStretch()
        
        # Titre central
        title_layout = QVBoxLayout()
        header_label = QLabel("🎤 VocaNote")
        header_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #2196F3; padding: 10px;")
        title_layout.addWidget(header_label)
        
        subtitle_label = QLabel("Transcription audio vers texte avec intelligence artificielle")
        subtitle_font = QFont("Segoe UI", 10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; padding-bottom: 10px;")
        title_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(title_layout)
        
        # Spacer droite + bouton licence
        header_layout.addStretch()
        
        # Bouton licence
        self.btn_license = QPushButton("🔑 Licence")
        self.btn_license.setFixedSize(100, 35)
        self.btn_license.clicked.connect(self.show_license_dialog)
        self.btn_license.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        header_layout.addWidget(self.btn_license)
        
        main_layout.addLayout(header_layout)
        
        # Indicateur de statut de licence
        self.license_status_label = QLabel()
        self.license_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.license_status_label)
        
        # === Section Fichier ===
        file_group = QGroupBox("Fichier Audio")
        file_layout = QVBoxLayout()
        
        # Affichage du fichier sélectionné
        self.file_label = QLabel("Aucun fichier sélectionné")
        self.file_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 5px;
                color: #666;
            }
        """)
        file_layout.addWidget(self.file_label)
        
        # Bouton de sélection
        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("📁 Sélectionner un fichier WAV")
        self.btn_select.setMinimumHeight(40)
        self.btn_select.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.btn_select.clicked.connect(self.select_file)
        btn_layout.addWidget(self.btn_select)
        
        file_layout.addLayout(btn_layout)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # === Section Paramètres ===
        settings_group = QGroupBox("Paramètres de transcription")
        settings_layout = QVBoxLayout()
        
        # Ligne 1 : Modèle et Langue
        params_row = QHBoxLayout()
        
        # Sélection du modèle
        model_layout = QVBoxLayout()
        model_label = QLabel("Modèle:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.model_combo.setCurrentText("base")
        self.model_combo.setToolTip(
            "tiny: Rapide mais moins précis\n"
            "base: Bon compromis (recommandé)\n"
            "small: Plus précis\n"
            "medium: Très précis mais plus lent\n"
            "large: Maximum de précision"
        )
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        params_row.addLayout(model_layout)
        
        # Sélection de la langue
        lang_layout = QVBoxLayout()
        lang_label = QLabel("Langue:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems([
            "Auto-détection",
            "Français (fr)",
            "Anglais (en)",
            "Espagnol (es)",
            "Allemand (de)",
            "Italien (it)",
            "Portugais (pt)"
        ])
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        params_row.addLayout(lang_layout)
        
        settings_layout.addLayout(params_row)
        
        # Ligne 2 : Options d'affichage
        from PyQt6.QtWidgets import QCheckBox
        self.check_timestamps = QCheckBox("⏱️ Afficher les timestamps")
        self.check_timestamps.setStyleSheet("QCheckBox { color: #000000; font-size: 11pt; }")
        self.check_timestamps.setToolTip(
            "Mode Conversation - Affiche le temps [00:00 -> 00:05] devant chaque phrase.\n"
            "Idéal pour plusieurs interlocuteurs et pour distinguer les tours de parole."
        )
        self.check_timestamps.stateChanged.connect(self.refresh_text_display)
        settings_layout.addWidget(self.check_timestamps)
        
        # Option de diarisation
        self.check_diarization = QCheckBox("🎤 Détecter les locuteurs")
        self.check_diarization.setStyleSheet("QCheckBox { color: #000000; font-size: 11pt; }")
        self.check_diarization.setToolTip(
            "Diarisation - Identifie automatiquement qui parle.\n"
            "Affiche 'Locuteur 1', 'Locuteur 2', etc. dans la transcription.\n"
            "Active automatiquement les timestamps.\n"
            "Note: Nécessite un token HuggingFace (gratuit) pour le premier usage."
        )
        self.check_diarization.stateChanged.connect(self.on_diarization_changed)
        settings_layout.addWidget(self.check_diarization)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # === Bouton de transcription ===
        self.btn_transcribe = QPushButton("▶️ Démarrer la transcription")
        self.btn_transcribe.setMinimumHeight(50)
        self.btn_transcribe.setEnabled(False)
        self.btn_transcribe.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #45a049;
            }
            QPushButton:pressed:enabled {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.btn_transcribe.clicked.connect(self.start_transcription)
        main_layout.addWidget(self.btn_transcribe)
        
        # === Barre de progression ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # === Label de statut ===
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        # === Zone de texte pour la transcription ===
        transcription_group = QGroupBox("Transcription")
        transcription_layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("La transcription apparaîtra ici...")
        self.text_edit.setFont(QFont("Segoe UI", 11))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
                color: #000000;
            }
        """)
        transcription_layout.addWidget(self.text_edit)
        
        # Boutons d'action
        action_layout = QHBoxLayout()
        
        self.btn_copy = QPushButton("📋 Copier")
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self.copy_text)
        
        # Bouton Résumer
        self.btn_summarize = QPushButton("📝 Résumer (IA)")
        self.btn_summarize.setEnabled(False)
        self.btn_summarize.clicked.connect(self.generate_summary)
        # Style spécifique pour le différencier
        self.btn_summarize.setStyleSheet("""
            QPushButton {
                background-color: #673AB7; 
                color: white;
                font-weight: bold; 
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover:enabled { background-color: #5E35B1; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        
        self.btn_save = QPushButton("💾 Enregistrer")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_text)
        
        self.btn_clear = QPushButton("🗑️ Effacer")
        self.btn_clear.setEnabled(False)
        self.btn_clear.clicked.connect(self.clear_text)
        
        # On ajoute le résumé au layout
        action_layout.addWidget(self.btn_summarize)
        
        # Styles communs pour les autres boutons
        for btn in [self.btn_copy, self.btn_save, self.btn_clear]:
            btn.setMinimumHeight(35)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #607D8B;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover:enabled {
                    background-color: #546E7A;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """)
            action_layout.addWidget(btn)
        
        transcription_layout.addLayout(action_layout)
        transcription_group.setLayout(transcription_layout)
        main_layout.addWidget(transcription_group, 1)
        
        central_widget.setLayout(main_layout)
        
        # Style global
        self.setStyleSheet("""
            QMainWindow {
                background-color: #fafafa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
    def select_file(self):
        """Ouvrir le dialogue de sélection de fichier"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier audio",
            "",
            "Fichiers Audio (*.wav *.mp3 *.m4a *.flac *.ogg);;Tous les fichiers (*.*)"
        )
        
        if file_name:
            self.current_file = file_name
            self.file_label.setText(f"📄 {Path(file_name).name}")
            self.file_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #E8F5E9;
                    border: 2px solid #4CAF50;
                    border-radius: 5px;
                    color: #2E7D32;
                    font-weight: bold;
                }
            """)
            self.btn_transcribe.setEnabled(True)
            
    def start_transcription(self):
        """Démarrer le processus de transcription"""
        if not self.current_file:
            return
            
        # Si la diarisation est activée, avertir du téléchargement potentiel
        enable_diarization = self.check_diarization.isChecked()
        if enable_diarization:
            reply = QMessageBox.question(
                self, 
                "Téléchargement de modèles", 
                "La diarisation nécessite le téléchargement de modèles externes (~500 Mo) lors de la première utilisation.\n\n"
                "La détection des locuteurs prolongera également le temps de traitement.\n\n"
                "Voulez-vous continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Désactiver les boutons pendant la transcription
        self.btn_select.setEnabled(False)
        self.btn_transcribe.setEnabled(False)
        self.model_combo.setEnabled(False)
        self.lang_combo.setEnabled(False)
        self.check_timestamps.setEnabled(False)
        self.check_diarization.setEnabled(False)
        
        # Afficher la barre de progression
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)  # Mode avec pourcentage (0-100%)
        
        # Effacer le texte précédent
        self.text_edit.clear()
        self.last_result = None
        
        # Obtenir les paramètres
        model_size = self.model_combo.currentText()
        lang_text = self.lang_combo.currentText()
        language = None if lang_text == "Auto-détection" else lang_text.split("(")[1].strip(")")
        
        # Vérifier la limite de licence
        max_duration = lic.get_transcription_limit()
        
        # Créer et démarrer le thread de transcription
        self.transcription_thread = TranscriptionThread(
            self.current_file,
            model_size,
            language,
            max_duration,
            enable_diarization
        )
        self.transcription_thread.progress.connect(self.update_status)
        self.transcription_thread.progress_percent.connect(self.update_progress_bar)
        self.transcription_thread.progress_indeterminate.connect(self.on_progress_indeterminate)
        self.transcription_thread.finished.connect(self.transcription_finished)
        self.transcription_thread.error.connect(self.transcription_error)
        self.transcription_thread.warning.connect(self.show_warning)
        self.transcription_thread.start()
        
    def on_progress_indeterminate(self, indeterminate):
        """Passer la barre de progression en mode indéterminé (busy)"""
        if indeterminate:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            
    def update_status(self, message):
        """Mettre à jour le message de statut"""
        self.status_label.setText(message)
    
    def update_progress_bar(self, percent):
        """Mettre à jour la barre de progression avec le pourcentage"""
        self.progress_bar.setValue(percent)
        
    def format_timestamp(self, seconds):
        """Formater les secondes en MM:SS"""
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"
        
    def refresh_text_display(self):
        """Rafraîchir l'affichage du texte selon les options"""
        if not self.last_result:
            return
        
        # Vérifier si on a des segments diarisés
        diarized_segments = self.last_result.get("diarized_segments", [])
        
        if diarized_segments:
            # Mode avec diarisation
            if self.check_timestamps.isChecked():
                # Avec timestamps et locuteurs
                full_text = ""
                for segment in diarized_segments:
                    start = self.format_timestamp(segment.get("start", 0))
                    end = self.format_timestamp(segment.get("end", 0))
                    speaker = segment.get("speaker", "Locuteur inconnu")
                    text = segment.get("text", "").strip()
                    if text:
                        full_text += f"[{start} -> {end}] [{speaker}] {text}\n"
                self.text_edit.setPlainText(full_text)
            else:
                # Sans timestamps, juste les locuteurs
                full_text = ""
                current_speaker = None
                for segment in diarized_segments:
                    speaker = segment.get("speaker", "Locuteur inconnu")
                    text = segment.get("text", "").strip()
                    if not text:
                        continue
                    # Ajouter le nom du locuteur si changement
                    if speaker != current_speaker:
                        full_text += f"\n[{speaker}]\n"
                        current_speaker = speaker
                    full_text += text + " "
                self.text_edit.setPlainText(full_text.strip())
        elif self.check_timestamps.isChecked():
            # Mode avec timestamps (segments) sans diarisation
            full_text = ""
            segments = self.last_result.get("segments", [])
            for segment in segments:
                start = self.format_timestamp(segment["start"])
                end = self.format_timestamp(segment["end"])
                text = segment["text"].strip()
                full_text += f"[{start} -> {end}] {text}\n"
            self.text_edit.setPlainText(full_text)
        else:
            # Mode texte simple
            self.text_edit.setPlainText(self.last_result["text"])
            
    def transcription_finished(self, result):
        """Appelé quand la transcription est terminée"""
        self.last_result = result
        self.refresh_text_display()
        
        self.progress_bar.setVisible(False)
        self.status_label.setText("✅ Transcription terminée avec succès!")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # Réactiver les boutons
        self.btn_select.setEnabled(True)
        self.btn_transcribe.setEnabled(True)
        self.model_combo.setEnabled(True)
        self.lang_combo.setEnabled(True)
        self.check_timestamps.setEnabled(True)
        self.check_diarization.setEnabled(True)
        
        # Activer les boutons d'action
        self.btn_copy.setEnabled(True)
        self.btn_save.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_summarize.setEnabled(True)
        
    def transcription_error(self, error_message):
        """Appelé en cas d'erreur"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ Erreur!")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        
        QMessageBox.critical(self, "Erreur", error_message)
        
        # Réactiver les boutons
        self.btn_select.setEnabled(True)
        self.btn_transcribe.setEnabled(True)
        self.model_combo.setEnabled(True)
        self.lang_combo.setEnabled(True)
        self.check_timestamps.setEnabled(True)
        self.check_diarization.setEnabled(True)
        
    def copy_text(self):
        """Copier le texte dans le presse-papiers"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        self.status_label.setText("📋 Texte copié dans le presse-papiers!")
        self.status_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        
    def save_text(self):
        """Enregistrer le texte dans un fichier"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer la transcription",
            "",
            "Fichiers texte (*.txt);;Tous les fichiers (*.*)"
        )
        
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                self.status_label.setText(f"💾 Transcription enregistrée: {Path(file_name).name}")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer le fichier:\n{str(e)}")
                
    def clear_text(self):
        """Effacer le texte"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment effacer la transcription?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.text_edit.clear()
            self.btn_copy.setEnabled(False)
            self.btn_save.setEnabled(False)
            self.btn_clear.setEnabled(False)
            self.btn_summarize.setEnabled(False)
            self.status_label.setText("")
    
    def on_diarization_changed(self):
        """Appelé quand l'option de diarisation change"""
        if self.check_diarization.isChecked():
            # Activer automatiquement les timestamps si diarisation activée
            self.check_timestamps.setChecked(True)
        # Rafraîchir l'affichage si on a déjà un résultat
        self.refresh_text_display()
    
    def show_warning(self, message):
        """Afficher un avertissement (utilisé pour la limite de licence)"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
    
    def show_license_dialog(self):
        """Affiche le dialogue de gestion de licence"""
        dialog = LicenseDialog(self)
        dialog.exec()
        # Mettre à jour l'affichage après fermeture
        self.update_license_display()
    
    def update_license_display(self):
        """Met à jour l'affichage du statut de licence"""
        status = lic.get_license_status()
        
        if status['is_valid']:
            # Afficher les jours restants si ce n'est pas perpétuelle
            if status['is_perpetual']:
                display_text = "✅ Licence active (perpétuelle) - Transcription illimitée"
            else:
                days = status['days_remaining']
                if days is not None and days <= 30:
                    display_text = f"✅ Licence active ({status['days_remaining_text']}) - Transcription illimitée"
                else:
                    display_text = f"✅ Licence active ({status['days_remaining_text']}) - Transcription illimitée"
            
            self.license_status_label.setText(display_text)
            
            # Couleur selon les jours restants
            days = status['days_remaining']
            if days is not None and days <= 7:
                # Avertissement urgent (moins de 7 jours)
                self.license_status_label.setStyleSheet(
                    "color: #FF5722; font-weight: bold; padding: 5px; "
                    "background-color: #FBE9E7; border-radius: 3px;"
                )
                self.btn_license.setStyleSheet("""
                    QPushButton {
                        background-color: #FF5722;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #E64A19;
                    }
                """)
            elif days is not None and days <= 30:
                # Avertissement modéré (moins de 30 jours)
                self.license_status_label.setStyleSheet(
                    "color: #FF9800; font-weight: bold; padding: 5px; "
                    "background-color: #FFF3E0; border-radius: 3px;"
                )
                self.btn_license.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #F57C00;
                    }
                """)
            else:
                # Licence OK
                self.license_status_label.setStyleSheet(
                    "color: #4CAF50; font-weight: bold; padding: 5px; "
                    "background-color: #E8F5E9; border-radius: 3px;"
                )
                self.btn_license.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
        else:
            # Vérifier si c'est une licence expirée
            if status['expiry_date'] and status['days_remaining'] is not None and status['days_remaining'] < 0:
                self.license_status_label.setText(
                    f"❌ Licence expirée - Transcription limitée à {status['limit_seconds']} secondes"
                )
                self.license_status_label.setStyleSheet(
                    "color: #F44336; font-weight: bold; padding: 5px; "
                    "background-color: #FFEBEE; border-radius: 3px;"
                )
                self.btn_license.setStyleSheet("""
                    QPushButton {
                        background-color: #F44336;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #D32F2F;
                    }
                """)
            else:
                self.license_status_label.setText(
                    f"⚠️ Version d'évaluation - Transcription limitée à {status['limit_seconds']} secondes"
                )
                self.license_status_label.setStyleSheet(
                    "color: #FF9800; font-weight: bold; padding: 5px; "
                    "background-color: #FFF3E0; border-radius: 3px;"
                )
                self.btn_license.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #F57C00;
                    }
                """)


    def generate_summary(self):
        """Générer le résumé du texte actuel"""
        text = self.text_edit.toPlainText()
        if not text:
            return
            
        # Confirmation (surtout pour le premier chargement)
        reply = QMessageBox.question(
            self, 
            "Générer un résumé ?", 
            "La génération du résumé utilise un modèle d'IA supplémentaire (~500 Mo téléchargés la 1ère fois).\n\n"
            "Voulez-vous continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
            
        self.status_label.setText("⏳ Génération du résumé en cours...")
        self.status_label.setStyleSheet("color: #673AB7; font-weight: bold;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0) # Indéterminé (barre qui bouge)
        
        # Désactiver les boutons
        self.btn_summarize.setEnabled(False)
        self.text_edit.setEnabled(False)
        
        # Lancer le thread
        self.summary_thread = SummaryThread(text)
        self.summary_thread.finished.connect(self.on_summary_finished)
        self.summary_thread.error.connect(self.on_summary_error)
        self.summary_thread.start()
        
    def on_summary_finished(self, summary):
        """Action quand le résumé est terminé"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("✅ Résumé généré !")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # Réactiver les boutons
        self.btn_summarize.setEnabled(True)
        self.text_edit.setEnabled(True)
        
        # Afficher le résumé dans une boite de dialogue stylée
        dialog = QDialog(self)
        dialog.setWindowTitle("Résumé (IA)")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        lbl = QLabel("Résumé généré :")
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(lbl)
        
        txt_edit = QTextEdit()
        txt_edit.setPlainText(summary)
        txt_edit.setReadOnly(True)
        txt_edit.setFont(QFont("Segoe UI", 11))
        layout.addWidget(txt_edit)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Save)
        btns.accepted.connect(dialog.accept)
        # Gestion du bouton Save
        def save_summary():
            path, _ = QFileDialog.getSaveFileName(dialog, "Sauvegarder le résumé", "resume.txt", "Fichiers Texte (*.txt)")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                QMessageBox.information(dialog, "Succès", "Résumé enregistré !")
                
        btns.button(QDialogButtonBox.StandardButton.Save).clicked.connect(save_summary)
        
        layout.addWidget(btns)
        dialog.setLayout(layout)
        dialog.exec()
        
    def on_summary_error(self, error_msg):
        """Erreur lors du résumé"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ Erreur de résumé")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.btn_summarize.setEnabled(True)
        self.text_edit.setEnabled(True)
        
        QMessageBox.critical(self, "Erreur Résumé", f"Une erreur est survenue :\n{error_msg}")


def main():
    """Point d'entrée de l'application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = VocaNote()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
