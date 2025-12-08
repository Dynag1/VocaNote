#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de diarisation pour VocaNote
Détecte et identifie les différents locuteurs dans un enregistrement audio
"""

import os
import warnings
from typing import Dict, List, Tuple, Optional
import torch
import tempfile
import subprocess

# Supprimer les avertissements
warnings.filterwarnings("ignore")

import logging


def convert_to_wav_if_needed(audio_file: str) -> str:
    """
    Convertit un fichier audio en WAV 16kHz mono si nécessaire
    pour assurer la compatibilité avec pyannote.audio
    
    Returns:
        Chemin vers le fichier WAV (original ou converti)
    """
    # Si c'est déjà un WAV, on tente quand même la conversion pour s'assurer du format
    ext = os.path.splitext(audio_file)[1].lower()
    
    try:
        import shutil
        ffmpeg_path = shutil.which("ffmpeg")
        
        if ffmpeg_path:
            # Créer un fichier temporaire
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav.close()
            
            # Convertir avec ffmpeg (16kHz mono, format standard)
            cmd = [
                ffmpeg_path,
                '-y',  # Overwrite
                '-i', audio_file,
                '-ar', '16000',  # Sample rate 16kHz
                '-ac', '1',  # Mono
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                temp_wav.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info(f"Audio converti en WAV: {temp_wav.name}")
                return temp_wav.name
            else:
                logging.warning(f"Conversion ffmpeg échouée: {result.stderr}")
                return audio_file
        else:
            return audio_file
            
    except Exception as e:
        logging.warning(f"Erreur conversion audio: {e}")
        return audio_file


class SpeakerDiarization:
    """
    Classe pour effectuer la diarisation des locuteurs
    Utilise pyannote.audio pour détecter qui parle quand
    """
    
    def __init__(self):
        """Initialise le modèle de diarisation"""
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Diarisation init: Device={self.device}")
    
    def _get_token_from_config(self) -> Optional[str]:
        """
        Récupère le token HuggingFace depuis le fichier hf_token.txt
        """
        token_file = os.path.join(os.path.dirname(__file__), "hf_token.txt")
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    token = f.read().strip()
                    if token:
                        return token
            except Exception:
                pass
        return None
        
    def load_model(self):
        """
        Charge le modèle de diarisation
        """
        logging.info("Diarisation: Chargement du modèle...")
        try:
            from pyannote.audio import Pipeline
            
            # Charger le pipeline de diarisation
            # Token HuggingFace: via variable d'environnement ou fichier config
            hf_token = os.environ.get("HF_TOKEN") or self._get_token_from_config()
            
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.0",
                use_auth_token=hf_token
            )
            
            # Déplacer sur GPU si disponible
            if self.device == "cuda":
                self.pipeline.to(torch.device("cuda"))
            
            logging.info("Diarisation: Modèle chargé avec succès")
            return True
            
        except Exception as e:
            logging.error(f"Diarisation ERROR: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def diarize(self, audio_file: str, num_speakers: Optional[int] = None) -> List[Dict]:
        """
        Effectue la diarisation sur un fichier audio
        """
        logging.info(f"Diarisation: Début de l'analyse sur {audio_file}")
        
        if self.pipeline is None:
            if not self.load_model():
                logging.error("Diarisation: Impossible de charger le modèle, abandon.")
                return []
        
        # Convertir le fichier audio en WAV compatible
        converted_file = convert_to_wav_if_needed(audio_file)
        temp_file_created = (converted_file != audio_file)
        
        try:
            # Paramètres de diarisation
            params = {}
            if num_speakers is not None:
                params['num_speakers'] = num_speakers
            
            # Charger l'audio avec scipy/soundfile comme fallback
            try:
                import scipy.io.wavfile as wav
                import numpy as np
                
                sample_rate, audio_data = wav.read(converted_file)
                
                # Convertir en float32 normalisé
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                elif audio_data.dtype == np.int32:
                    audio_data = audio_data.astype(np.float32) / 2147483648.0
                
                # Convertir en mono si stéréo
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)
                
                # Créer un tenseur pour pyannote
                waveform = torch.from_numpy(audio_data).unsqueeze(0)
                
                # Créer le dictionnaire d'entrée pour pyannote
                file_input = {
                    "waveform": waveform,
                    "sample_rate": sample_rate
                }
                
                logging.info(f"Audio chargé: {sample_rate}Hz, {len(audio_data)} samples")
                
                # Effectuer la diarisation avec le waveform
                diarization = self.pipeline(file_input, **params)
                
            except Exception as wav_error:
                logging.warning(f"Fallback scipy échoué: {wav_error}, essai direct...")
                # Fallback: essayer directement avec le chemin du fichier
                diarization = self.pipeline(converted_file, **params)
            
            # Extraire l'annotation depuis DiarizeOutput (nouvelle API pyannote 3.x)
            if hasattr(diarization, 'speaker_diarization'):
                annotation = diarization.speaker_diarization
            else:
                # Ancienne API : diarization est directement une Annotation
                annotation = diarization
            
            # Convertir en format utilisable
            segments = []
            speaker_mapping = {}
            speaker_counter = 1
            
            for turn, _, speaker in annotation.itertracks(yield_label=True):
                # Créer un mapping des labels de locuteurs
                if speaker not in speaker_mapping:
                    speaker_mapping[speaker] = f"Locuteur {speaker_counter}"
                    speaker_counter += 1
                
                segments.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': speaker_mapping[speaker]
                })
            
            logging.info(f"Diarisation: {len(segments)} segments détectés")
            return segments
            
        except Exception as e:
            logging.error(f"Diarisation RUNTIME ERROR: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return []
        
        finally:
            # Nettoyer le fichier temporaire si créé
            if temp_file_created and os.path.exists(converted_file):
                try:
                    os.remove(converted_file)
                    logging.debug(f"Fichier temporaire supprimé: {converted_file}")
                except:
                    pass
    
    def merge_with_transcription(
        self, 
        transcription_segments: List[Dict], 
        diarization_segments: List[Dict]
    ) -> List[Dict]:
        """
        Fusionne les segments de transcription avec les informations de locuteur
        
        Args:
            transcription_segments: Segments de Whisper avec texte et timestamps
            diarization_segments: Segments de diarisation avec locuteurs
            
        Returns:
            Segments fusionnés avec texte et locuteur
        """
        merged = []
        
        for trans_seg in transcription_segments:
            trans_start = trans_seg.get('start', 0)
            trans_end = trans_seg.get('end', 0)
            trans_text = trans_seg.get('text', '')
            
            # Trouver le locuteur correspondant
            speaker = self._find_speaker_for_segment(
                trans_start, 
                trans_end, 
                diarization_segments
            )
            
            merged.append({
                'start': trans_start,
                'end': trans_end,
                'text': trans_text,
                'speaker': speaker
            })
        
        return merged
    
    def _find_speaker_for_segment(
        self, 
        start: float, 
        end: float, 
        diarization_segments: List[Dict]
    ) -> str:
        """
        Trouve le locuteur principal pour un segment donné
        Utilise le critère de chevauchement maximal
        """
        max_overlap = 0
        best_speaker = "Locuteur inconnu"
        
        segment_duration = end - start
        
        for diar_seg in diarization_segments:
            # Calculer le chevauchement
            overlap_start = max(start, diar_seg['start'])
            overlap_end = min(end, diar_seg['end'])
            overlap = max(0, overlap_end - overlap_start)
            
            # Garder le locuteur avec le plus grand chevauchement
            if overlap > max_overlap:
                max_overlap = overlap
                best_speaker = diar_seg['speaker']
        
        # Si le chevauchement est significatif (> 50% du segment)
        if max_overlap > segment_duration * 0.5:
            return best_speaker
        else:
            return "Locuteur inconnu"
    
    def format_segments_for_display(self, segments: List[Dict]) -> str:
        """
        Formate les segments pour l'affichage dans l'interface
        
        Args:
            segments: Segments avec texte et locuteur
            
        Returns:
            Texte formaté avec locuteurs
        """
        formatted_lines = []
        current_speaker = None
        
        for seg in segments:
            speaker = seg.get('speaker', 'Locuteur inconnu')
            text = seg.get('text', '').strip()
            
            if not text:
                continue
            
            # Ajouter le nom du locuteur si changement
            if speaker != current_speaker:
                formatted_lines.append(f"\n[{speaker}]")
                current_speaker = speaker
            
            formatted_lines.append(text)
        
        return "\n".join(formatted_lines)
    
    def format_segments_with_timestamps(self, segments: List[Dict]) -> str:
        """
        Formate les segments avec timestamps et locuteurs
        
        Args:
            segments: Segments avec texte, timestamps et locuteur
            
        Returns:
            Texte formaté avec timestamps et locuteurs
        """
        formatted_lines = []
        
        for seg in segments:
            speaker = seg.get('speaker', 'Locuteur inconnu')
            text = seg.get('text', '').strip()
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            
            if not text:
                continue
            
            # Formater le timestamp
            start_str = self._format_time(start)
            end_str = self._format_time(end)
            
            formatted_lines.append(
                f"[{start_str} → {end_str}] [{speaker}] {text}"
            )
        
        return "\n".join(formatted_lines)
    
    def _format_time(self, seconds: float) -> str:
        """Formate les secondes en MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


# Fonction utilitaire pour tester la diarisation
def test_diarization(audio_file: str):
    """
    Fonction de test pour la diarisation
    
    Args:
        audio_file: Chemin vers le fichier audio à tester
    """
    print("🎤 Test de diarisation...")
    print(f"Fichier: {audio_file}")
    
    diarizer = SpeakerDiarization()
    
    if not diarizer.load_model():
        print("❌ Impossible de charger le modèle")
        return
    
    print("✅ Modèle chargé")
    print("🔍 Analyse en cours...")
    
    segments = diarizer.diarize(audio_file)
    
    if not segments:
        print("❌ Aucun segment détecté")
        return
    
    print(f"✅ {len(segments)} segments détectés")
    print("\n📊 Résultats:")
    
    for seg in segments:
        start_str = diarizer._format_time(seg['start'])
        end_str = diarizer._format_time(seg['end'])
        print(f"  {start_str} → {end_str} : {seg['speaker']}")


if __name__ == "__main__":
    # Test si exécuté directement
    import sys
    
    if len(sys.argv) > 1:
        test_diarization(sys.argv[1])
    else:
        print("Usage: python diarization.py <fichier_audio>")
