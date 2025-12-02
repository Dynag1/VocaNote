#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocaNote - Transcription Audio vers Texte
Application de transcription audio utilisant Whisper d'OpenAI
"""

import sys
import os
import warnings
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
try:
    import imageio_ffmpeg
    imageio_path = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    print(f"   ✅ imageio-ffmpeg trouvé: {imageio_path}")
    ffmpeg_dirs.append(imageio_path)
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


class TranscriptionThread(QThread):
    """Thread pour effectuer la transcription sans bloquer l'interface"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)  # On renvoie le dictionnaire complet (texte + segments)
    error = pyqtSignal(str)
    warning = pyqtSignal(str)  # Pour les avertissements de licence
    
    def __init__(self, audio_file, model_size="base", language=None, max_duration=None):
        super().__init__()
        self.audio_file = audio_file
        self.model_size = model_size
        self.language = language
        self.max_duration = max_duration  # Limite de durée en secondes (pour version sans licence)
        
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
            
            self.progress.emit("Transcription en cours...")
            
            # Effectuer la transcription
            result = model.transcribe(
                audio_to_transcribe,
                language=self.language,
                verbose=False
            )
            
            # Nettoyer le fichier temporaire si créé
            if temp_file is not None:
                try:
                    os.remove(temp_file.name)
                except:
                    pass
            
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
        self.check_timestamps = QCheckBox("Afficher les timestamps (Mode Conversation) - Idéal pour plusieurs interlocuteurs")
        self.check_timestamps.setToolTip("Affiche le temps [00:00 -> 00:05] devant chaque phrase.\nUtile pour distinguer les tours de parole.")
        self.check_timestamps.stateChanged.connect(self.refresh_text_display)
        settings_layout.addWidget(self.check_timestamps)
        
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
        
        self.btn_save = QPushButton("💾 Enregistrer")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_text)
        
        self.btn_clear = QPushButton("🗑️ Effacer")
        self.btn_clear.setEnabled(False)
        self.btn_clear.clicked.connect(self.clear_text)
        
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
            
        # Désactiver les boutons pendant la transcription
        self.btn_select.setEnabled(False)
        self.btn_transcribe.setEnabled(False)
        self.model_combo.setEnabled(False)
        self.lang_combo.setEnabled(False)
        self.check_timestamps.setEnabled(False)
        
        # Afficher la barre de progression
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        
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
            max_duration
        )
        self.transcription_thread.progress.connect(self.update_status)
        self.transcription_thread.finished.connect(self.transcription_finished)
        self.transcription_thread.error.connect(self.transcription_error)
        self.transcription_thread.warning.connect(self.show_warning)
        self.transcription_thread.start()
        
    def update_status(self, message):
        """Mettre à jour le message de statut"""
        self.status_label.setText(message)
        
    def format_timestamp(self, seconds):
        """Formater les secondes en MM:SS"""
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"
        
    def refresh_text_display(self):
        """Rafraîchir l'affichage du texte selon les options"""
        if not self.last_result:
            return
            
        if self.check_timestamps.isChecked():
            # Mode avec timestamps (segments)
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
        
        # Activer les boutons d'action
        self.btn_copy.setEnabled(True)
        self.btn_save.setEnabled(True)
        self.btn_clear.setEnabled(True)
        
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
            self.status_label.setText("")
    
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


def main():
    """Point d'entrée de l'application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = VocaNote()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
