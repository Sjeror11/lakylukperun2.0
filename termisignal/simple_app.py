#!/usr/bin/env python3
"""
Jednoduchá terminálová aplikace pro TermiSignal
"""

import os
import sys
import time
import random
import getpass
import json
from pathlib import Path

# Barvy pro terminál
class Colors:
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

# Třída pro uživatele
class User:
    def __init__(self, username, display_name=None):
        self.username = username
        self.display_name = display_name or username
        self.color = self._generate_color()
    
    def _generate_color(self):
        colors = [Colors.RED, Colors.GREEN, Colors.BLUE, Colors.YELLOW, 
                 Colors.MAGENTA, Colors.CYAN]
        return random.choice(colors)

# Třída pro zprávu
class Message:
    def __init__(self, sender, content, timestamp=None):
        self.sender = sender
        self.content = content
        self.timestamp = timestamp or time.time()
    
    def format(self):
        time_str = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        return f"[{time_str}] {self.sender.color}{self.sender.username}@termisignal{Colors.RESET}: {self.content}"

# Třída pro databázi uživatelů
class UserDatabase:
    def __init__(self):
        # Výchozí umístění databáze v domovském adresáři uživatele
        home_dir = str(Path.home())
        self.db_dir = os.path.join(home_dir, ".termisignal")
        self.db_path = os.path.join(self.db_dir, "users.json")
        self.users = {}
    
    def initialize(self):
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
        with open(self.db_path, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def register_user(self, username, password):
        # Kontrola, zda uživatel již existuje
        if username in self.users:
            return False, "Uživatel již existuje"
        
        # Uložení uživatele (v reálné aplikaci by bylo heslo hashováno)
        self.users[username] = {
            'password': password,
            'display_name': username
        }
        
        # Uložení databáze
        self._save_db()
        
        return True, "Uživatel byl úspěšně zaregistrován"
    
    def authenticate_user(self, username, password):
        # Kontrola, zda uživatel existuje
        if username not in self.users:
            return False, "Uživatel neexistuje"
        
        # Ověření hesla
        if self.users[username]['password'] == password:
            return True, User(username, self.users[username]['display_name'])
        else:
            return False, "Nesprávné heslo"

# Třída pro chat
class Chat:
    def __init__(self):
        self.messages = []
        self.users = {}
    
    def add_message(self, message):
        self.messages.append(message)
    
    def add_user(self, user):
        self.users[user.username] = user
    
    def display_messages(self, count=10):
        start_idx = max(0, len(self.messages) - count)
        for i in range(start_idx, len(self.messages)):
            print(self.messages[i].format())

# Hlavní funkce aplikace
def main():
    # Vyčištění obrazovky
    os.system('clear')
    
    # Zobrazení úvodní obrazovky
    print(f"{Colors.GREEN}{Colors.BOLD}TermiSignal - Terminálová šifrovaná komunikační aplikace{Colors.RESET}")
    print(f"{Colors.CYAN}Verze: 0.1.0{Colors.RESET}")
    print()
    
    # Inicializace databáze
    user_db = UserDatabase()
    user_db.initialize()
    
    # Přihlášení nebo registrace
    while True:
        print(f"{Colors.YELLOW}1. Přihlásit se{Colors.RESET}")
        print(f"{Colors.YELLOW}2. Registrovat se{Colors.RESET}")
        print(f"{Colors.YELLOW}3. Ukončit{Colors.RESET}")
        print()
        
        choice = input("Vyberte možnost (1-3): ")
        
        if choice == "1":
            # Přihlášení
            username = input("Uživatelské jméno: ")
            password = getpass.getpass("Heslo: ")
            
            success, result = user_db.authenticate_user(username, password)
            
            if success:
                user = result
                print(f"{Colors.GREEN}Přihlášení úspěšné!{Colors.RESET}")
                time.sleep(1)
                chat_screen(user)
                break
            else:
                print(f"{Colors.RED}Chyba: {result}{Colors.RESET}")
                time.sleep(2)
                os.system('clear')
        
        elif choice == "2":
            # Registrace
            username = input("Uživatelské jméno: ")
            password = getpass.getpass("Heslo: ")
            password_confirm = getpass.getpass("Heslo znovu: ")
            
            if password != password_confirm:
                print(f"{Colors.RED}Chyba: Hesla se neshodují{Colors.RESET}")
                time.sleep(2)
                os.system('clear')
                continue
            
            success, message = user_db.register_user(username, password)
            
            if success:
                print(f"{Colors.GREEN}{message}{Colors.RESET}")
                time.sleep(2)
                os.system('clear')
            else:
                print(f"{Colors.RED}Chyba: {message}{Colors.RESET}")
                time.sleep(2)
                os.system('clear')
        
        elif choice == "3":
            # Ukončení
            print(f"{Colors.GREEN}Děkujeme za použití TermiSignal!{Colors.RESET}")
            sys.exit(0)
        
        else:
            print(f"{Colors.RED}Neplatná volba!{Colors.RESET}")
            time.sleep(1)
            os.system('clear')

# Funkce pro chatovací obrazovku
def chat_screen(user):
    # Vyčištění obrazovky
    os.system('clear')
    
    # Inicializace chatu
    chat = Chat()
    
    # Přidání uživatele do chatu
    chat.add_user(user)
    
    # Přidání uvítací zprávy
    system_user = User("system", "System")
    system_user.color = Colors.GREEN
    
    welcome_message = Message(system_user, "Vítejte v TermiSignal chatu!")
    chat.add_message(welcome_message)
    
    # Přidání ukázkové zprávy
    lucky_user = User("lucky", "Lucky")
    lucky_user.color = Colors.RED
    
    sample_message = Message(lucky_user, "Ahoj, jak se máš?")
    chat.add_message(sample_message)
    
    # Hlavní smyčka chatu
    while True:
        # Vyčištění obrazovky
        os.system('clear')
        
        # Zobrazení hlavičky
        print(f"{Colors.GREEN}{Colors.BOLD}TermiSignal - Chat{Colors.RESET}")
        print(f"{Colors.CYAN}Přihlášen jako: {user.color}{user.username}{Colors.RESET}")
        print()
        
        # Zobrazení zpráv
        chat.display_messages()
        
        print()
        print(f"{Colors.YELLOW}Napište zprávu nebo /exit pro ukončení{Colors.RESET}")
        
        # Vstup uživatele
        message_text = input("> ")
        
        if message_text.strip() == "/exit":
            # Ukončení chatu
            break
        
        if message_text.strip():
            # Přidání zprávy
            message = Message(user, message_text)
            chat.add_message(message)
            
            # Simulace odpovědi
            if random.random() > 0.5:
                time.sleep(random.uniform(0.5, 1.5))
                response = Message(lucky_user, f"Odpověď na: {message_text}")
                chat.add_message(response)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}Děkujeme za použití TermiSignal!{Colors.RESET}")
        sys.exit(0)
