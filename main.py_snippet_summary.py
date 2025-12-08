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
