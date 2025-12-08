#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de résumé de texte pour VocaNote.
Utilise HuggingFace Transformers pour générer des résumés.
"""

import logging
import torch
import warnings
import os
import sys
from threading import Thread
from typing import Optional, Callable

# Supprimer les avertissements transformers
warnings.filterwarnings("ignore")
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("transformers").setLevel(logging.ERROR)

# Patch pour éviter l'erreur torchcodec manquant dans PyInstaller
# torchcodec est optionnel pour transformers
try:
    import importlib.metadata
    _original_version = importlib.metadata.version
    def _patched_version(package):
        if package == "torchcodec":
            return "0.0.0"  # Version fictive pour éviter l'erreur
        return _original_version(package)
    importlib.metadata.version = _patched_version
    logging.info("[SUMMARIZER] Patch torchcodec appliqué")
except Exception as e:
    logging.warning(f"[SUMMARIZER] Patch torchcodec échoué: {e}")


def get_base_path() -> str:
    """Retourne le chemin de base de l'application (compatible PyInstaller)"""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
        logging.info(f"[SUMMARIZER] Mode PyInstaller, base path: {base}")
    else:
        base = os.path.dirname(os.path.abspath(__file__))
        logging.info(f"[SUMMARIZER] Mode dev, base path: {base}")
    return base

class TextSummarizer:
    """
    Classe gérant le résumé de texte via Transformers.
    """
    
    def __init__(self, model_name="facebook/bart-large-cnn"):
        # Modèles disponibles par ordre de préférence
        self.pipeline = None
        self.tokenizer = None
        self.model = None
        self.model_name = model_name 
        self.max_input_tokens = 1024
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self) -> bool:
        """Charge le modèle de résumé (téléchargement si nécessaire)"""
        logging.info(f"[SUMMARIZER] === Chargement du modèle de résumé ===")
        logging.info(f"[SUMMARIZER] Device: {self.device}")
        logging.info(f"[SUMMARIZER] CWD: {os.getcwd()}")
        logging.info(f"[SUMMARIZER] sys.executable: {sys.executable}")
        logging.info(f"[SUMMARIZER] frozen: {getattr(sys, 'frozen', False)}")
        
        # Modèles par ordre de préférence (français d'abord)
        models_to_try = [
            "moussaKam/barthez-orangesum-abstract",  # Français - abstractif
            "lincoln/mbart-mlsum-automatic-summarization",  # Multilingue
            "facebook/bart-large-cnn",  # Anglais mais robuste
            "sshleifer/distilbart-cnn-12-6",  # Fallback léger
        ]
        
        for model_name in models_to_try:
            try:
                logging.info(f"[SUMMARIZER] Import transformers...")
                from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
                logging.info(f"[SUMMARIZER] Import OK, tentative avec {model_name}...")
                
                logging.info(f"[SUMMARIZER] Chargement tokenizer...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                logging.info(f"[SUMMARIZER] Tokenizer OK")
                
                logging.info(f"[SUMMARIZER] Chargement modèle...")
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                logging.info(f"[SUMMARIZER] Modèle téléchargé, déplacement sur {self.device}...")
                
                self.model = self.model.to(self.device)
                self.model.eval()
                self.model_name = model_name
                logging.info(f"[SUMMARIZER] === Modèle {model_name} chargé avec succès ===")
                return True
            except ImportError as e:
                logging.error(f"[SUMMARIZER] ERREUR IMPORT: {e}")
                import traceback
                logging.error(traceback.format_exc())
                break  # Pas la peine d'essayer d'autres modèles si l'import échoue
            except Exception as e:
                logging.warning(f"[SUMMARIZER] Échec avec {model_name}: {e}")
                import traceback
                logging.warning(traceback.format_exc())
                continue
        logging.error("[SUMMARIZER] Impossible de charger un modèle!")
        return False

    def _truncate_text(self, text: str) -> str:
        """Tronque le texte pour qu'il tienne dans la limite de tokens du modèle"""
        if self.tokenizer is None:
            # Fallback: estimation grossière (1 token ~ 4 caractères)
            max_chars = self.max_input_tokens * 3
            if len(text) > max_chars:
                text = text[:max_chars]
            return text
        
        # Tokeniser et tronquer proprement
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        
        if len(tokens) > self.max_input_tokens - 10:  # Marge de sécurité
            tokens = tokens[:self.max_input_tokens - 10]
            text = self.tokenizer.decode(tokens, skip_special_tokens=True)
            logging.info(f"Summarizer: Texte tronqué à {len(tokens)} tokens")
        
        return text

    def summarize(self, text: str, ratio: float = 0.2, min_length: int = 30, max_length: int = 200) -> str:
        """
        Résume le texte donné avec une approche hybride extractive + abstractive
        pour garantir une couverture complète du contenu.
        
        Args:
            text: Le texte à résumer
            ratio: Ratio approximatif de la taille du résumé (non strict)
            min_length: Taille minimale du résumé en tokens
            max_length: Taille maximale du résumé en tokens
        """
        if not text or not text.strip():
            return ""
            
        if self.model is None:
            if not self.load_model():
                return "Erreur: Impossible de charger le modèle de résumé."
        
        # Nettoyer le texte (enlever timestamps, locuteurs, etc.)
        cleaned_text = self._clean_text(text)
        
        logging.info(f"Summarizer: Résumé d'un texte de {len(cleaned_text)} caractères...")
        
        # S'assurer que le texte n'est pas trop court
        word_count = len(cleaned_text.split())
        if word_count < 30:
            return cleaned_text  # Texte trop court pour être résumé
        
        try:
            tokens = self.tokenizer.encode(cleaned_text, add_special_tokens=False)
            logging.info(f"Summarizer: Texte nettoyé: {len(tokens)} tokens")
            
            # Extraire les informations clés de manière structurée
            key_points = self._extract_key_points(cleaned_text)
            
            if key_points:
                # Formater en résumé structuré
                summary = self._format_key_points(key_points)
                logging.info(f"Summarizer: Résumé structuré: {len(summary)} chars")
                return summary
            
            # Fallback: résumé extractif simple
            extractive = self._extractive_summary(cleaned_text, max_sentences=6)
            return extractive
            
        except Exception as e:
            logging.error(f"Summarizer RUNTIME ERROR: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
            # Fallback: résumé simple par extraction
            return self._extractive_summary(cleaned_text, max_sentences=8)
    
    def _summarize_long_text(self, text: str, ratio: float, min_length: int, max_length: int) -> str:
        """
        Résume un texte long en combinant résumé abstractif et extractif
        pour garantir une couverture complète de la conversation.
        """
        # Découper le texte en morceaux de ~700 tokens
        chunk_size = 700
        chunks = self._split_into_chunks(text, chunk_size)
        
        logging.info(f"Summarizer: Texte découpé en {len(chunks)} morceaux")
        
        # Résumer chaque morceau
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logging.info(f"Summarizer: Résumé du morceau {i+1}/{len(chunks)}")
            chunk_max = max(120, min(180, max_length))
            summary = self._summarize_chunk(chunk, 50, chunk_max)
            if summary and summary.strip() and len(summary.strip()) > 30:
                chunk_summaries.append(summary)
                logging.info(f"  -> Morceau {i+1}: {len(summary)} chars")
            else:
                # Fallback: résumé extractif du morceau
                extractive = self._extractive_summary(chunk, max_sentences=3)
                if extractive and len(extractive) > 30:
                    chunk_summaries.append(extractive)
                    logging.info(f"  -> Morceau {i+1} (extractif): {len(extractive)} chars")
        
        if not chunk_summaries:
            return self._extractive_summary(text, max_sentences=10)
        
        # Combiner tous les résumés de morceaux
        combined = self._merge_summaries(chunk_summaries)
        logging.info(f"Summarizer: Résumé combiné: {len(combined)} chars")
        
        # Si le combiné est de taille raisonnable, le garder
        # Cela préserve plus d'information de toute la conversation
        if len(combined) <= max_length * 6:  # ~1200 chars max
            return combined
        
        # Si trop long, tronquer intelligemment plutôt que re-résumer
        # (le re-résumé perd souvent les parties début/milieu)
        combined_tokens = len(self.tokenizer.encode(combined, add_special_tokens=False))
        if combined_tokens > self.max_input_tokens - 50:
            logging.info("Summarizer: Texte combiné trop long, utilisation du résumé extractif")
            return self._extractive_summary(combined, max_sentences=8)
        
        return combined
    
    def _merge_summaries(self, summaries: list) -> str:
        """Fusionne et nettoie une liste de résumés partiels"""
        import re
        
        merged = []
        for summary in summaries:
            # Nettoyer chaque résumé
            summary = summary.strip()
            
            # Enlever les phrases tronquées au début/fin
            if summary and not summary[0].isupper() and len(merged) > 0:
                # Phrase incomplète au début, essayer de la fusionner
                words = summary.split()
                if len(words) > 5:
                    # Chercher le début d'une vraie phrase
                    for i, word in enumerate(words):
                        if word[0].isupper() if word else False:
                            summary = ' '.join(words[i:])
                            break
            
            # Ajouter un point si manquant
            if summary and summary[-1] not in '.!?':
                summary += '.'
            
            if summary:
                merged.append(summary)
        
        # Joindre avec des espaces
        result = ' '.join(merged)
        
        # Nettoyer les espaces multiples
        result = re.sub(r'\s+', ' ', result)
        
        return result.strip()
    
    def _split_into_chunks(self, text: str, max_tokens: int) -> list:
        """Découpe le texte en morceaux de taille maximale"""
        # Découper par phrases
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence, add_special_tokens=False))
            
            if current_tokens + sentence_tokens > max_tokens:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # Si pas assez de phrases, découper par mots
        if len(chunks) == 1 and len(self.tokenizer.encode(chunks[0], add_special_tokens=False)) > max_tokens:
            words = text.split()
            chunks = []
            current_chunk = []
            current_tokens = 0
            
            for word in words:
                word_tokens = len(self.tokenizer.encode(word, add_special_tokens=False))
                if current_tokens + word_tokens > max_tokens:
                    if current_chunk:
                        chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_tokens = word_tokens
                else:
                    current_chunk.append(word)
                    current_tokens += word_tokens
            
            if current_chunk:
                chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _summarize_chunk(self, text: str, min_length: int, max_length: int) -> str:
        """Résume un morceau de texte pour produire un résumé cohérent"""
        try:
            # Tokeniser l'entrée
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                max_length=self.max_input_tokens,
                truncation=True,
                padding=True
            ).to(self.device)
            
            input_length = inputs['input_ids'].shape[1]
            
            # Ajuster la longueur cible pour un résumé substantiel
            target_max = max(min_length + 30, min(max_length, input_length))
            target_min = max(20, min(min_length, target_max - 20))
            
            # Générer le résumé avec des paramètres optimisés pour la cohérence
            with torch.no_grad():
                summary_ids = self.model.generate(
                    inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    max_length=target_max,
                    min_length=target_min,
                    num_beams=5,           # Plus de beams pour meilleure qualité
                    length_penalty=1.0,    # Équilibré pour longueur naturelle
                    no_repeat_ngram_size=3,
                    repetition_penalty=1.2, # Éviter les répétitions
                    do_sample=False
                )
            
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            return summary.strip()
            
        except Exception as e:
            logging.error(f"Summarizer chunk error: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte des caractères problématiques et du formatage de transcription"""
        import re
        
        # Supprimer les timestamps [00:00 -> 00:02], (00:00 -> 00:02), etc.
        text = re.sub(r'\[?\(?\d{1,2}:\d{2}\s*[-–>]+\s*\d{1,2}:\d{2}\]?\)?', '', text)
        
        # Supprimer les labels de locuteurs [Locuteur 1], [Locuteur inconnu], etc.
        text = re.sub(r'\[?\(?[Ll]ocute[ua]r\s*\w*\s*\d*\]?\)?', '', text)
        text = re.sub(r'\[\s*Speaker\s*\d*\s*\]', '', text, flags=re.IGNORECASE)
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', text)
        
        # Supprimer les crochets et parenthèses vides ou avec juste des espaces
        text = re.sub(r'\[\s*\]|\(\s*\)', '', text)
        
        # NOUVEAU: Supprimer les répétitions de mots (ex: "non non non non" -> "non")
        text = re.sub(r'\b(\w+)(\s+\1){2,}\b', r'\1', text, flags=re.IGNORECASE)
        
        # NOUVEAU: Supprimer les hésitations courantes répétées
        hesitations = ['hein', 'euh', 'bah', 'ben', 'ah', 'oh', 'hum', 'mmh']
        for h in hesitations:
            text = re.sub(rf'\b{h}(\s*,?\s*{h})+\b', h, text, flags=re.IGNORECASE)
        
        # Normaliser les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Nettoyer les tirets/flèches isolés
        text = re.sub(r'\s*[-–>]+\s*', ' ', text)
        
        # Nettoyer la ponctuation multiple
        text = re.sub(r'[,;:]{2,}', ',', text)
        text = re.sub(r'\s+,', ',', text)
        
        # Garder les phrases de salutation/conclusion pour extraction des noms
        # Mais les traiter séparément
        salutations = re.findall(r'(?:[Mm]erci|[Ss]alut|[Bb]onjour|[Aa]u revoir)[,\s]+[A-Z][a-zé]+', text)
        
        # Supprimer les phrases/segments trop courts ou sans verbe
        sentences = re.split(r'[.!?]+', text)
        good_sentences = []
        
        # Mots qui indiquent une phrase avec du sens
        meaningful_words = ['médecine', 'travail', 'visite', 'reprise', 'poste', 'adapter',
                          'jour', 'jours', 'congé', 'congés', 'campagne', 'restrictions',
                          'solutions', 'permettre', 'permet', 'faire', 'prendre', 'avoir',
                          'décembre', 'janvier', 'février', 'mars', 'avril', 'mai']
        
        for sent in sentences:
            sent = sent.strip()
            words = sent.split()
            
            # Garder si au moins 5 mots ET contient un mot significatif
            if len(words) >= 5:
                has_meaning = any(mw in sent.lower() for mw in meaningful_words)
                if has_meaning or len(words) >= 10:
                    good_sentences.append(sent)
        
        # Ajouter les salutations à la fin (pour extraction des noms)
        for sal in salutations:
            good_sentences.append(sal)
        
        # Reconstruire le texte
        if good_sentences:
            text = '. '.join(good_sentences) + '.'
        
        return text.strip()
    
    def _extract_key_points(self, text: str) -> list:
        """Extrait les informations clés du texte sous forme de points"""
        import re
        
        text_lower = text.lower()
        original_text = text  # Garder l'original pour les extraits
        
        # Nettoyer les mots répétés
        text_lower = re.sub(r'\b(\w+)(\s+\1)+\b', r'\1', text_lower)
        
        extractions = []
        
        # 1. Tous les nombres avec contexte (jours, euros, etc.)
        jours_matches = re.findall(r'(\d+)\s*(jours?|journée?s?)', text_lower)
        for num, unit in jours_matches:
            if int(num) > 0:
                extractions.append(('congés', f"{num} jours"))
        
        # 2. Dates mentionnées
        mois = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 
                'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
        for m in mois:
            date_match = re.search(rf'(\d+)\s*{m}', text_lower)
            if date_match:
                extractions.append(('dates', f"{date_match.group(1)} {m}"))
        
        # Années
        annees = re.findall(r'\b(202[4-9]|203\d)\b', text_lower)
        annees_uniques = list(set(annees))[:2]
        for a in annees_uniques:
            extractions.append(('dates', f"année {a}"))
        
        # 3. Sujets de discussion
        sujets_patterns = {
            'mail': ['mail', 'message', 'courriel', 'courrier'],
            'appel': ['appel', 'appelais', 'téléphone'],
            'reprise': ['reprise', 'reprendre', 'retour'],
            'congés': ['congé', 'congés', 'vacances', 'repos'],
            'travail': ['travail', 'boulot', 'poste', 'bureau'],
            'médical': ['médecin', 'médical', 'visite', 'santé', 'maladie', 'médecine'],
            'réunion': ['réunion', 'rendez-vous', 'rdv'],
            'projet': ['projet', 'campagne', 'dossier'],
        }
        
        for sujet, mots in sujets_patterns.items():
            for mot in mots:
                if mot in text_lower:
                    extractions.append(('sujet', sujet.capitalize()))
                    break
        
        # 4. Personnes mentionnées
        mots_exclus = {'donc', 'mais', 'alors', 'après', 'avant', 'pour', 'dans', 'avec', 
                      'bonne', 'journée', 'oui', 'non', 'bon', 'bien', 'salut',
                      'saint', 'sainte', 'peut', 'être', 'fait', 'dire', 'voir', 'aller',
                      'tout', 'tous', 'elle', 'lui', 'eux', 'nous', 'vous'}
        
        prenoms_patterns = [
            r'[Mm]erci[,\s]+([A-Z][a-z]{2,})',
            r'[Ss]alut[,\s]+([A-Z][a-z]{2,})',
            r'[Bb]onjour[,\s]+([A-Z][a-z]{2,})',
            r'(?:de|à|chez|avec)\s+([A-Z][a-z]{2,})\b',
            r'(?:mail|message|appel)\s+(?:de|à)\s+([A-Z][a-z]{2,})',
        ]
        
        for pattern in prenoms_patterns:
            matches = re.findall(pattern, original_text)
            for p in matches:
                if p.lower() not in mots_exclus and len(p) >= 3:
                    extractions.append(('personnes', p))
        
        # 5. NOUVEAU: Extraire les phrases clés complètes
        phrases_cles = self._extract_key_sentences(original_text)
        for phrase in phrases_cles:
            extractions.append(('phrase', phrase))
        
        # 6. NOUVEAU: Détecter les actions/décisions
        actions_patterns = [
            (r'(?:on va|il faut|je vais|tu vas|nous allons)\s+([^.!?]{10,60})', 'action'),
            (r'(?:problème|souci|difficulté)\s+([^.!?]{10,60})', 'problème'),
        ]
        
        actions_vues = set()
        for pattern, cat in actions_patterns:
            matches = re.findall(pattern, text_lower)
            for m in matches[:2]:
                m_clean = m.strip()
                # Éviter les doublons (mêmes 5 premiers mots)
                key = ' '.join(m_clean.split()[:5])
                if len(m_clean) > 10 and key not in actions_vues:
                    actions_vues.add(key)
                    extractions.append((cat, m_clean.capitalize()))
        
        return extractions
    
    def _extract_key_sentences(self, text: str) -> list:
        """Extrait les phrases les plus importantes du texte"""
        import re
        
        # Diviser en phrases
        sentences = re.split(r'[.!?]+', text)
        
        # Mots-clés importants
        keywords = ['médecine', 'travail', 'visite', 'reprise', 'adapter', 'poste',
                   'congé', 'jours', 'prendre', 'avant', 'restriction', 'solution',
                   'problème', 'campagne', 'projet']
        
        scored_sentences = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent.split()) < 6 or len(sent.split()) > 25:
                continue
            
            score = 0
            sent_lower = sent.lower()
            
            for kw in keywords:
                if kw in sent_lower:
                    score += 2
            
            # Bonus pour les phrases avec des verbes d'action
            if any(v in sent_lower for v in ['permet', 'pouvoir', 'faire', 'prendre', 'adapter']):
                score += 1
            
            # Pénalité pour les hésitations
            if sent_lower.count('oui') > 1 or 'du coup' in sent_lower:
                score -= 2
            
            if score > 2:
                scored_sentences.append((sent, score))
        
        # Trier par score et prendre les 3 meilleures
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored_sentences[:3]]
    
    def _format_key_points(self, key_points: list, original_text: str = "") -> str:
        """Formate les points clés en résumé lisible et détaillé"""
        if not key_points:
            return ""
        
        # Grouper par catégorie
        themes = {
            'sujet': [],
            'personnes': [],
            'congés': [],
            'dates': [],
            'action': [],
            'médical': [],
            'phrase': [],
            'problème': [],
        }
        
        for category, value in key_points:
            if category in themes:
                if value not in themes[category]:
                    themes[category].append(value)
        
        # Construire le résumé en phrases naturelles et détaillées
        parts = []
        
        # 1. Introduction avec contexte
        if themes['sujet']:
            sujets = list(set(themes['sujet']))[:5]
            if 'Appel' in sujets:
                intro = "📞 Conversation téléphonique"
            elif 'Réunion' in sujets:
                intro = "👥 Discussion lors d'une réunion"
            else:
                intro = "💬 Échange"
            
            if themes['personnes']:
                personnes = list(set(themes['personnes']))[:2]
                intro += f" avec {', '.join(personnes)}"
            
            autres_sujets = [s for s in sujets if s not in ['Appel', 'Réunion']]
            if autres_sujets:
                intro += f" concernant : {', '.join(autres_sujets).lower()}"
            
            parts.append(intro)
        
        # 2. Phrases clés extraites (le cœur du contenu)
        if themes['phrase']:
            phrases = themes['phrase'][:3]
            parts.append("\n📝 Points clés de la discussion :")
            for i, phrase in enumerate(phrases, 1):
                # Nettoyer et limiter la longueur
                phrase_clean = phrase.strip()
                if len(phrase_clean) > 100:
                    phrase_clean = phrase_clean[:100] + "..."
                parts.append(f"   • {phrase_clean}")
        
        # 3. Informations chiffrées
        info_parts = []
        
        if themes['congés']:
            jours = list(set(themes['congés']))
            info_parts.append(f"Durées : {', '.join(jours)}")
        
        if themes['dates']:
            dates = list(set(themes['dates']))[:4]
            dates_clean = []
            mois_vus = set()
            for d in dates:
                d_lower = d.lower()
                if any(m in d_lower for m in ['mai', 'juin', 'juillet']) and 'année' not in d_lower and len(d.split()) > 1:
                    continue
                if d_lower.startswith('année'):
                    annee = d.split()[-1] if len(d.split()) > 1 else d
                    if annee in mois_vus:
                        continue
                    mois_vus.add(annee)
                dates_clean.append(d)
            if dates_clean:
                info_parts.append(f"Dates : {', '.join(dates_clean)}")
        
        if info_parts:
            parts.append("\n📅 Informations : " + " | ".join(info_parts))
        
        # 4. Actions identifiées
        if themes['action']:
            actions = list(set(themes['action']))[:3]
            parts.append("\n✅ Actions à prévoir :")
            for action in actions:
                action_clean = action.strip()
                if len(action_clean) > 80:
                    action_clean = action_clean[:80] + "..."
                parts.append(f"   • {action_clean}")
        
        # 5. Problèmes soulevés
        if themes['problème']:
            problemes = list(set(themes['problème']))[:2]
            parts.append("\n⚠️ Points d'attention :")
            for prob in problemes:
                prob_clean = prob.strip()
                if len(prob_clean) > 80:
                    prob_clean = prob_clean[:80] + "..."
                parts.append(f"   • {prob_clean}")
        
        if parts:
            return "\n".join(parts)
        else:
            return ""

    def _extractive_summary(self, text: str, max_sentences: int = 8) -> str:
        """
        Résumé extractif - sélectionne les passages du DÉBUT, MILIEU et FIN
        pour garantir une couverture complète de la conversation.
        """
        import re
        try:
            words = text.split()
            total_words = len(words)
            
            if total_words < 50:
                return text
            
            # Mots-clés importants
            keywords = ['reprise', 'travail', 'médecine', 'medecine', 'conge', 'congé',
                       'jour', 'jours', 'décembre', 'decembre', 'janvier', 'poste', 
                       'visite', 'mail', 'problème', 'probleme', 'solution', 'adapter',
                       'restriction', 'demenagement', 'déménagement', 'campagne', 'merci',
                       'bonne', 'journée', 'journee', 'appelais']
            
            def score_passage(passage):
                score = 0
                lower = passage.lower()
                words = lower.split()
                
                # Bonus pour mots-clés importants
                for kw in keywords:
                    if kw in lower:
                        score += 20
                
                # Bonus pour début de phrase
                if passage and passage[0].isupper():
                    score += 10
                
                # PÉNALITÉS FORTES pour mauvaise qualité
                
                # Pénalité pour répétitions de mots
                word_counts = {}
                for w in words:
                    if len(w) > 2:  # Ignorer les petits mots
                        word_counts[w] = word_counts.get(w, 0) + 1
                for w, count in word_counts.items():
                    if count > 3:
                        score -= count * 10  # Forte pénalité pour répétitions
                
                # Pénalité pour hésitations
                hesitations = ['hein', 'euh', 'bah', 'ben', 'ah', 'oh', 'donc', 'voilà', 'quoi']
                for h in hesitations:
                    count = lower.count(h)
                    if count > 2:
                        score -= count * 5
                
                # Pénalité pour "du coup", "en fait", etc.
                fillers = ['du coup', 'en fait', 'c\'est à dire', 'c\'est-à-dire', 'peut être', 'peut-être']
                for f in fillers:
                    if f in lower:
                        score -= 10
                
                # Pénalité si trop de "oui", "non"
                if lower.count('oui') > 2:
                    score -= lower.count('oui') * 5
                if lower.count('non') > 2:
                    score -= lower.count('non') * 5
                
                # Bonus pour phrases complètes (avec verbes d'action)
                action_verbs = ['permet', 'adapter', 'entamer', 'pouvoir', 'faire', 'prendre', 
                               'reste', 'avoir', 'donner', 'voir', 'dit', 'demande']
                for v in action_verbs:
                    if v in lower:
                        score += 5
                
                return score
            
            # Diviser en 3 zones
            zone_size = total_words // 3
            zones = [
                (0, zone_size),                    # DÉBUT
                (zone_size, 2 * zone_size),        # MILIEU
                (2 * zone_size, total_words)       # FIN
            ]
            
            summaries = []
            window_size = 50  # mots par extrait (augmenté pour plus de contenu)
            
            for idx, (zone_start, zone_end) in enumerate(zones):
                zone_words = words[zone_start:zone_end]
                
                if len(zone_words) <= window_size:
                    summaries.append(' '.join(zone_words))
                    continue
                
                # Pour le DÉBUT (idx=0): prendre les premiers mots + un passage clé
                if idx == 0:
                    # Prendre le début
                    start_passage = ' '.join(zone_words[:window_size])
                    summaries.append(start_passage)
                    
                    # Chercher un autre passage important dans cette zone
                    if len(zone_words) > window_size * 1.5:
                        best_passage = ""
                        best_score = -100
                        for j in range(window_size, len(zone_words) - 30, 5):
                            passage = ' '.join(zone_words[j:j + 30])
                            score = score_passage(passage)
                            if score > best_score:
                                best_score = score
                                best_passage = passage
                        if best_passage and best_score > 20:
                            summaries.append(best_passage)
                    continue
                
                # Pour la FIN (idx=2): prendre le meilleur passage + la vraie fin
                if idx == 2:
                    # Chercher le meilleur passage
                    best_passage = ""
                    best_score = -100
                    
                    for j in range(0, max(1, len(zone_words) - 40), 5):
                        passage = ' '.join(zone_words[j:j + 40])
                        score = score_passage(passage)
                        if score > best_score:
                            best_score = score
                            best_passage = passage
                    
                    if best_passage:
                        summaries.append(best_passage)
                    
                    # Toujours inclure la vraie fin
                    end_passage = ' '.join(zone_words[-35:])
                    if end_passage != best_passage:
                        summaries.append(end_passage)
                    continue
                
                # Pour le MILIEU: prendre les 2 meilleurs passages
                passages_found = []
                
                for j in range(0, len(zone_words) - 40, 5):
                    passage = ' '.join(zone_words[j:j + 40])
                    score = score_passage(passage)
                    passages_found.append((passage, score, j))
                
                # Trier par score et prendre les 2 meilleurs (non-chevauchants)
                passages_found.sort(key=lambda x: x[1], reverse=True)
                selected = []
                for passage, score, pos in passages_found:
                    # Vérifier qu'il ne chevauche pas avec les déjà sélectionnés
                    overlap = False
                    for _, _, prev_pos in selected:
                        if abs(pos - prev_pos) < 35:
                            overlap = True
                            break
                    if not overlap:
                        selected.append((passage, score, pos))
                        if len(selected) >= 2:
                            break
                
                for passage, _, _ in selected:
                    summaries.append(passage)
            
            # Assembler le résumé en évitant les doublons
            result_parts = []
            all_words_seen = []
            
            for s in summaries:
                s = s.strip()
                if not s:
                    continue
                
                # Vérifier si ce contenu chevauche trop avec ce qui a déjà été ajouté
                s_words = s.lower().split()
                overlap_count = sum(1 for w in s_words if w in all_words_seen)
                
                # Si plus de 60% des mots sont déjà vus, c'est un doublon
                if len(s_words) > 0 and overlap_count / len(s_words) > 0.6:
                    continue
                
                # Ajouter les mots à la liste des mots vus
                all_words_seen.extend(s_words)
                
                if s[-1] not in '.!?,;:':
                    s += '.'
                result_parts.append(s)
            
            result = ' '.join(result_parts)
            result = re.sub(r'\s+', ' ', result).strip()
            
            return result if result else text[:600]
            
        except Exception as e:
            logging.error(f"Extractive summary error: {e}")
            return text[:600] + '...' if len(text) > 600 else text

# Variable globale
_summarizer_instance = None

def get_summarizer():
    global _summarizer_instance
    if _summarizer_instance is None:
        _summarizer_instance = TextSummarizer()
    return _summarizer_instance
