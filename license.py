## Copyright Dynag ##
## https://prog.dynag.co ##
## license.py - Système de licence sécurisé VocaNote (compatible PHP) ##

"""
Système de licence sécurisé pour VocaNote.
Sans licence valide, la transcription est limitée à 30 secondes.
Supporte les licences chiffrées AES-256-CBC générées par PHP.
"""

import os
import hashlib
import hmac
import json
import platform
import uuid
import base64
from pathlib import Path
from datetime import datetime

# Import conditionnel de cryptography (pour les licences chiffrées)
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding as sym_padding
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

class LicenseManager:
    """Gestionnaire de licence sécurisé pour VocaNote (compatible avec génération PHP)"""
    
    # Clés de chiffrement (doivent être identiques côté PHP)
    # ⚠️ CHANGEZ CES VALEURS EN PRODUCTION !
    _MASTER_KEY = b'DynagSecureLicenseVocaNote2025'  # 30 bytes
    _SALT = b'VocaNote2025Salt'  # 16 bytes
    
    # Limite de transcription sans licence (en secondes)
    TRANSCRIPTION_LIMIT = 30
    
    def __init__(self):
        """Initialise le gestionnaire de licence"""
        self.config_file = self._get_config_path()
        self._license_key = None
        self._is_valid = False
        self._expiry_date = None
        self._activation_date = None
        self._aes_key = self._derive_key() if HAS_CRYPTOGRAPHY else None
        self._load_license()
    
    def _derive_key(self):
        """Dérive une clé AES-256 depuis la clé maître"""
        # PBKDF2 avec 100k itérations pour ralentir les attaques
        key = hashlib.pbkdf2_hmac(
            'sha256',
            self._MASTER_KEY,
            self._SALT,
            100000,
            dklen=32  # 256 bits pour AES-256
        )
        return key
    
    def _get_hardware_id(self):
        """
        Génère un ID matériel unique et stable.
        DOIT être identique à la version PHP pour la validation.
        """
        # Composants matériels
        components = [
            platform.node(),                    # Nom de la machine
            str(uuid.getnode()),                # Adresse MAC
            platform.machine(),                 # Architecture (x86_64, etc.)
            platform.processor()[:50],          # Processeur (limité à 50 chars)
        ]
        
        # Combinaison
        combined = '|'.join(components).encode()
        
        # Triple hash pour sécurité maximale
        hash1 = hashlib.sha256(combined + self._SALT).digest()
        hash2 = hashlib.sha512(hash1).digest()
        hash3 = hashlib.blake2b(hash2, digest_size=32).digest()
        
        # Encodage Base64 et tronquer à 32 caractères
        return base64.b64encode(hash3).decode()[:32]
    
    def generate_activation_code(self):
        """
        Génère un code d'activation unique pour cette machine.
        Ce code doit être envoyé au serveur PHP pour obtenir une licence.
        Format: ACT-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX-YYYYMMDD-XXXXXXXX
        """
        hw_id = self._get_hardware_id()
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # Checksum pour valider le code (8 caractères)
        checksum = hashlib.sha256(
            f"{hw_id}{timestamp}{self._MASTER_KEY.decode('latin-1')}".encode()
        ).hexdigest()[:8].upper()
        
        return f"ACT-{hw_id}-{timestamp}-{checksum}"
    
    def _get_config_path(self):
        """Retourne le chemin du fichier de configuration de licence"""
        # Chercher dans le répertoire de l'application
        if getattr(os.sys, 'frozen', False):
            # Mode exécutable PyInstaller
            base_path = os.path.dirname(os.sys.executable)
        else:
            # Mode développement
            base_path = os.getcwd()
        
        return os.path.join(base_path, "vocanote_license.json")
    
    def _decrypt_license(self, license_key):
        """
        Déchiffre une licence générée par PHP.
        
        Format de la licence chiffrée (base64) :
        - 16 bytes : IV
        - N bytes  : Données chiffrées (JSON)
        - 32 bytes : HMAC-SHA256 de (IV + données chiffrées)
        
        Returns:
            dict: Données de licence déchiffrées ou None
        """
        if not HAS_CRYPTOGRAPHY or not self._aes_key:
            return None
            
        try:
            # Décoder depuis Base64
            encrypted_data = base64.b64decode(license_key)
            
            # Extraire IV, données chiffrées et HMAC
            iv = encrypted_data[:16]
            hmac_received = encrypted_data[-32:]
            ciphertext = encrypted_data[16:-32]
            
            # Vérifier le HMAC
            hmac_calculated = hmac.new(
                self._aes_key,
                iv + ciphertext,
                hashlib.sha256
            ).digest()
            
            if not hmac.compare_digest(hmac_calculated, hmac_received):
                return None
            
            # Déchiffrer avec AES-256-CBC
            cipher = Cipher(
                algorithms.AES(self._aes_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Retirer le padding PKCS7
            unpadder = sym_padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            
            # Parser le JSON
            license_data = json.loads(data.decode('utf-8'))
            
            return license_data
            
        except Exception as e:
            return None
    
    def _verify_encrypted_license(self, license_key):
        """
        Vérifie une licence chiffrée.
        
        Returns:
            tuple: (is_valid, expiry_date) ou (False, None)
        """
        license_data = self._decrypt_license(license_key)
        
        if not license_data:
            return False, None
        
        try:
            # Vérifier l'ID matériel
            current_hw_id = self._get_hardware_id()
            if license_data.get('hw_id') != current_hw_id:
                return False, None
            
            # Vérifier le logiciel
            if license_data.get('software') != 'VocaNote':
                return False, None
            
            # Récupérer la date d'expiration
            expiry_str = license_data.get('expiry')
            if not expiry_str:
                return False, None
            
            # Vérifier si pas expirée
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            if datetime.now() > expiry_date:
                return False, expiry_str  # Expirée mais on retourne la date
            
            return True, expiry_str
            
        except Exception:
            return False, None
    
    def _is_key_valid(self, key):
        """
        Vérifie si une clé de licence est valide.
        Supporte les clés simples ET les licences chiffrées.
        """
        if not key:
            return False
        
        key = key.strip()
        
        # 1. Essayer de déchiffrer comme licence chiffrée
        is_valid, expiry = self._verify_encrypted_license(key)
        if is_valid:
            self._expiry_date = expiry
            return True
        
        # 2. Si déchiffrement échoue, vérifier la clé simple
        # Clé de licence simple valide (pour tests/développement)
        valid_key = "vRW37J494nJNQu4pvx69MBehE9r7Yk"
        
        # Extraire la clé de base (sans date éventuelle)
        base_key = key.split('-')[0] if '-' in key and len(key) > 40 else key
        
        return self._constant_time_compare(base_key, valid_key)
    
    def _constant_time_compare(self, a, b):
        """Comparaison en temps constant pour éviter les attaques timing"""
        if len(a) != len(b):
            return False
        result = 0
        for x, y in zip(a.encode(), b.encode()):
            result |= x ^ y
        return result == 0
    
    def _load_license(self):
        """Charge la licence depuis le fichier de configuration"""
        try:
            if os.path.isfile(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._license_key = data.get('license_key', '')
                    self._expiry_date = data.get('expiry_date', None)
                    self._activation_date = data.get('activation_date', None)
                    
                    # Vérifier si la clé est valide ET non expirée
                    if self._is_key_valid(self._license_key):
                        if self._is_expired():
                            self._is_valid = False
                        else:
                            self._is_valid = True
                    else:
                        self._is_valid = False
        except Exception:
            self._license_key = None
            self._expiry_date = None
            self._activation_date = None
            self._is_valid = False
    
    def _save_license(self):
        """Sauvegarde la licence dans le fichier de configuration"""
        try:
            data = {
                'license_key': self._license_key or '',
                'expiry_date': self._expiry_date,
                'activation_date': self._activation_date,
                'version': '1.0'
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False
    
    def _is_expired(self):
        """Vérifie si la licence est expirée"""
        if not self._expiry_date:
            return False  # Pas de date d'expiration = licence perpétuelle
        
        try:
            expiry = datetime.strptime(self._expiry_date, '%Y-%m-%d')
            return datetime.now() > expiry
        except:
            return False
    
    def _parse_license_key(self, key):
        """
        Parse une clé de licence pour extraire la date d'expiration si présente.
        Format: CLE ou CLE-YYYYMMDD
        Retourne: (clé_base, date_expiration ou None)
        """
        if not key:
            return None, None
        
        key = key.strip()
        
        # Vérifier si la clé contient une date d'expiration (format: CLE-YYYYMMDD)
        if '-' in key and len(key.split('-')[-1]) == 8:
            parts = key.rsplit('-', 1)
            base_key = parts[0]
            date_str = parts[1]
            
            # Vérifier si c'est une date valide
            try:
                expiry_date = datetime.strptime(date_str, '%Y%m%d')
                return base_key, expiry_date.strftime('%Y-%m-%d')
            except:
                pass
        
        return key, None
    
    def is_licensed(self):
        """Retourne True si une licence valide est activée"""
        return self._is_valid
    
    def get_transcription_limit(self):
        """
        Retourne la limite de transcription en secondes.
        None si pas de limite (licence valide).
        """
        if self._is_valid:
            return None  # Pas de limite
        return self.TRANSCRIPTION_LIMIT
    
    def activate_license(self, key):
        """
        Active une licence avec la clé fournie.
        Formats supportés:
        - Licence chiffrée (Base64) générée par PHP
        - Clé simple: CLE
        - Clé simple avec date: CLE-YYYYMMDD
        
        Args:
            key: str - Clé de licence à activer
            
        Returns:
            bool: True si activation réussie, False sinon
        """
        if not key:
            return False
            
        key = key.strip()
        
        # 1. Essayer comme licence chiffrée
        is_valid, expiry_date = self._verify_encrypted_license(key)
        if is_valid or (expiry_date and not is_valid):
            # Licence chiffrée reconnue (valide ou expirée)
            self._license_key = key
            self._activation_date = datetime.now().strftime('%Y-%m-%d')
            self._expiry_date = expiry_date
            
            if is_valid:
                self._is_valid = True
                self._save_license()
                return True
            else:
                # Licence chiffrée mais expirée
                self._is_valid = False
                return False
        
        # 2. Sinon, traiter comme clé simple
        base_key, expiry_date = self._parse_license_key(key)
        
        if self._is_key_valid(base_key):
            self._license_key = key
            self._activation_date = datetime.now().strftime('%Y-%m-%d')
            
            # Utiliser la date extraite de la clé simple OU celle déjà définie par _is_key_valid
            if expiry_date:
                self._expiry_date = expiry_date
            
            # Vérifier si la licence n'est pas déjà expirée
            if self._is_expired():
                self._is_valid = False
                return False
            
            self._is_valid = True
            self._save_license()
            return True
            
        return False
    
    def deactivate_license(self):
        """Désactive la licence actuelle"""
        self._license_key = None
        self._expiry_date = None
        self._activation_date = None
        self._is_valid = False
        self._save_license()
    
    def get_days_remaining(self):
        """
        Retourne le nombre de jours restants avant expiration.
        
        Returns:
            int ou None: Nombre de jours restants, None si perpétuelle, -1 si expirée
        """
        if not self._expiry_date:
            return None  # Licence perpétuelle
        
        try:
            expiry = datetime.strptime(self._expiry_date, '%Y-%m-%d')
            days = (expiry - datetime.now()).days
            return max(days, -1)  # -1 minimum si expirée
        except:
            return None
    
    def get_days_remaining_text(self):
        """
        Retourne le texte formaté des jours restants.
        
        Returns:
            str: Texte descriptif
        """
        days = self.get_days_remaining()
        
        if days is None:
            return "Perpétuelle"
        elif days < 0:
            return "Expirée"
        elif days == 0:
            return "Expire aujourd'hui"
        elif days == 1:
            return "1 jour restant"
        else:
            return f"{days} jours restants"
    
    def get_license_status(self):
        """
        Retourne le statut de la licence.
        
        Returns:
            dict: {
                'is_valid': bool,
                'key_masked': str ou None,
                'limit_seconds': int ou None,
                'expiry_date': str ou None,
                'days_remaining': int ou None,
                'days_remaining_text': str,
                'activation_date': str ou None,
                'is_perpetual': bool
            }
        """
        # Recharger pour vérifier l'expiration
        self._load_license()
        
        masked_key = None
        if self._license_key:
            # Masquer la clé sauf les 4 premiers et 4 derniers caractères
            key = self._license_key
            if len(key) > 8:
                masked_key = f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"
            else:
                masked_key = '*' * len(key)
        
        days_remaining = self.get_days_remaining()
        
        return {
            'is_valid': self._is_valid,
            'key_masked': masked_key,
            'limit_seconds': None if self._is_valid else self.TRANSCRIPTION_LIMIT,
            'expiry_date': self._expiry_date,
            'days_remaining': days_remaining,
            'days_remaining_text': self.get_days_remaining_text(),
            'activation_date': self._activation_date if hasattr(self, '_activation_date') else None,
            'is_perpetual': days_remaining is None and self._is_valid
        }


# ═══════════════════════════════════════════════════════════
# SINGLETON ET FONCTIONS DE COMPATIBILITÉ
# ═══════════════════════════════════════════════════════════

_license_manager = None

def get_license_manager():
    """Retourne l'instance singleton du gestionnaire de licence"""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager

def is_licensed():
    """Vérifie si l'application est sous licence"""
    return get_license_manager().is_licensed()

def get_transcription_limit():
    """Retourne la limite de transcription (None si pas de limite)"""
    return get_license_manager().get_transcription_limit()

def activate_license(key):
    """Active une licence"""
    return get_license_manager().activate_license(key)

def deactivate_license():
    """Désactive la licence"""
    return get_license_manager().deactivate_license()

def get_license_status():
    """Retourne le statut de la licence"""
    return get_license_manager().get_license_status()

def generate_activation_code():
    """Génère le code d'activation de cette machine"""
    return get_license_manager().generate_activation_code()

def get_days_remaining():
    """Retourne le nombre de jours restants"""
    return get_license_manager().get_days_remaining()

def get_days_remaining_text():
    """Retourne le texte des jours restants"""
    return get_license_manager().get_days_remaining_text()

