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
    QMessageBox, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

# Supprimer les avertissements FP16 de Whisper
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

# --- CONFIGURATION FFMPEG ---
print("🔍 Configuration de FFmpeg...")
ffmpeg_dirs = []

# 1. Chercher dans le dossier local (créé par installer_ffmpeg.bat)
# Vérifier ffmpeg/bin ET ffmpeg/ racine
possible_paths = [
    os.path.join(os.getcwd(), "ffmpeg", "bin"),
    os.path.join(os.getcwd(), "ffmpeg")
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


class TranscriptionThread(QThread):
    """Thread pour effectuer la transcription sans bloquer l'interface"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)  # On renvoie le dictionnaire complet (texte + segments)
    error = pyqtSignal(str)
    
    def __init__(self, audio_file, model_size="base", language=None):
        super().__init__()
        self.audio_file = audio_file
        self.model_size = model_size
        self.language = language
        
    def run(self):
        try:
            self.progress.emit("Chargement du modèle Whisper...")
            
            # Vérifier si CUDA est disponible
            device = "cuda" if torch.cuda.is_available() else "cpu"
            device_name = "🚀 GPU (CUDA)" if device == "cuda" else "💻 CPU"
            self.progress.emit(f"Périphérique: {device_name}")
            
            # Charger le modèle
            model = whisper.load_model(self.model_size, device=device)
            
            self.progress.emit("Transcription en cours...")
            
            # Effectuer la transcription
            result = model.transcribe(
                self.audio_file,
                language=self.language,
                verbose=False
            )
            
            self.progress.emit("Transcription terminée!")
            self.finished.emit(result)  # Renvoyer tout le résultat
            
        except Exception as e:
            self.error.emit(f"Erreur lors de la transcription: {str(e)}")


class VocaNote(QMainWindow):
    """Fenêtre principale de l'application VocaNote"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.transcription_thread = None
        self.last_result = None  # Pour stocker le résultat brut
        self.init_ui()
        
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
        
        # === En-tête ===
        header_label = QLabel("🎤 VocaNote")
        header_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #2196F3; padding: 10px;")
        main_layout.addWidget(header_label)
        
        subtitle_label = QLabel("Transcription audio vers texte avec intelligence artificielle")
        subtitle_font = QFont("Segoe UI", 10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; padding-bottom: 10px;")
        main_layout.addWidget(subtitle_label)
        
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
        
        # Créer et démarrer le thread de transcription
        self.transcription_thread = TranscriptionThread(
            self.current_file,
            model_size,
            language
        )
        self.transcription_thread.progress.connect(self.update_status)
        self.transcription_thread.finished.connect(self.transcription_finished)
        self.transcription_thread.error.connect(self.transcription_error)
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


def main():
    """Point d'entrée de l'application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = VocaNote()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
