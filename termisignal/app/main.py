"""
Hlavní modul aplikace TermiSignal
"""

import os
import sys
from termisignal.ui.login_screen import LoginScreen
from termisignal.ui.chat_screen import ChatScreen
from termisignal.database.user_db import UserDatabase

def main():
    """
    Hlavní funkce aplikace
    """
    # Inicializace databáze
    user_db = UserDatabase()
    user_db.initialize()
    
    # Spuštění přihlašovací obrazovky
    login_screen = LoginScreen(user_db)
    user = login_screen.run()
    
    if user:
        # Pokud je uživatel přihlášen, spustí se chat
        chat_screen = ChatScreen(user)
        chat_screen.run()
    else:
        print("Přihlášení selhalo nebo bylo zrušeno.")
        sys.exit(0)

if __name__ == "__main__":
    main()
