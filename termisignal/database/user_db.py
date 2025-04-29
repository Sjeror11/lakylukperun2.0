"""
Modul pro práci s uživatelskou databází
"""

import os
import json
import hashlib
import base64
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

class UserDatabase:
    """
    Třída pro práci s uživatelskou databází
    """
    
    def __init__(self, db_path=None):
        """
        Inicializace databáze
        """
        if db_path is None:
            # Výchozí umístění databáze v domovském adresáři uživatele
            home_dir = str(Path.home())
            self.db_dir = os.path.join(home_dir, ".termisignal")
            self.db_path = os.path.join(self.db_dir, "users.json")
        else:
            self.db_path = db_path
            self.db_dir = os.path.dirname(db_path)
        
        self.users = {}
    
    def initialize(self):
        """
        Inicializace databáze - vytvoření adresáře a souboru, pokud neexistují
        """
        # Vytvoření adresáře, pokud neexistuje
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        
        # Načtení existující databáze, pokud existuje
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    self.users = json.load(f)
            except json.JSONDecodeError:
                # Pokud je soubor poškozen, vytvoříme nový
                self.users = {}
                self._save_db()
        else:
            # Vytvoření nové databáze
            self._save_db()
    
    def _save_db(self):
        """
        Uložení databáze do souboru
        """
        with open(self.db_path, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def _hash_password(self, password, salt=None):
        """
        Vytvoření hashe hesla pomocí PBKDF2
        """
        if salt is None:
            salt = os.urandom(16)
        
        # Vytvoření PBKDF2 hashe
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        password_hash = kdf.derive(password.encode())
        
        # Vrácení hashe a saltu v Base64
        return {
            'hash': base64.b64encode(password_hash).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8')
        }
    
    def _verify_password(self, password, stored_hash, stored_salt):
        """
        Ověření hesla
        """
        # Dekódování saltu
        salt = base64.b64decode(stored_salt)
        
        # Vytvoření hashe z hesla a saltu
        password_data = self._hash_password(password, salt)
        
        # Porovnání hashů
        return password_data['hash'] == stored_hash
    
    def register_user(self, username, password):
        """
        Registrace nového uživatele
        """
        # Kontrola, zda uživatel již existuje
        if username in self.users:
            return False, "Uživatel již existuje"
        
        # Vytvoření hashe hesla
        password_data = self._hash_password(password)
        
        # Uložení uživatele
        self.users[username] = {
            'password_hash': password_data['hash'],
            'password_salt': password_data['salt'],
            'display_name': username
        }
        
        # Uložení databáze
        self._save_db()
        
        return True, "Uživatel byl úspěšně zaregistrován"
    
    def authenticate_user(self, username, password):
        """
        Ověření uživatele
        """
        # Kontrola, zda uživatel existuje
        if username not in self.users:
            return False, "Uživatel neexistuje"
        
        # Získání dat uživatele
        user_data = self.users[username]
        
        # Ověření hesla
        if self._verify_password(password, user_data['password_hash'], user_data['password_salt']):
            return True, user_data
        else:
            return False, "Nesprávné heslo"
    
    def get_user(self, username):
        """
        Získání dat uživatele
        """
        return self.users.get(username, None)
    
    def update_user(self, username, data):
        """
        Aktualizace dat uživatele
        """
        if username not in self.users:
            return False, "Uživatel neexistuje"
        
        # Aktualizace dat
        self.users[username].update(data)
        
        # Uložení databáze
        self._save_db()
        
        return True, "Data uživatele byla aktualizována"
