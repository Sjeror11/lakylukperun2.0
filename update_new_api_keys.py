#!/usr/bin/env python3

import os
from datetime import datetime

def create_backup():
    """Vytvoří záložní kopii hlavního souboru."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file = f"perun_tradingview_multi.py.backup_{timestamp}"
    os.system(f"cp perun_tradingview_multi.py {backup_file}")
    print(f"Vytvořena záložní kopie: {backup_file}")

def update_api_keys():
    """Aktualizuje API klíče v konfiguračním souboru."""
    with open('perun_tradingview_multi.py', 'r') as f:
        lines = f.readlines()
    
    # Nové API klíče
    api_key = "AKJ7JX2TTYIGDCDQMQOS"
    secret_key = "LgAiUxTXA7rSJE5QGhLmOLctGRJSsjQb7rWYorFB"
    
    # Nahrazení API klíčů
    for i, line in enumerate(lines):
        if 'ALPACA_API_KEY =' in line:
            lines[i] = f'ALPACA_API_KEY = "{api_key}"\n'
        elif 'ALPACA_API_SECRET =' in line:
            lines[i] = f'ALPACA_API_SECRET = "{secret_key}"\n'
    
    # Uložení opraveného souboru
    with open('perun_tradingview_multi.py', 'w') as f:
        f.writelines(lines)
    
    print(f"API klíče byly aktualizovány:")
    print(f"API_KEY = {api_key}")
    print(f"SECRET_KEY = {secret_key[:5]}...{secret_key[-5:]}")
    return True

def main():
    """Hlavní funkce pro aktualizaci API klíčů."""
    try:
        print("Začínám aktualizaci API klíčů...")
        create_backup()
        update_api_keys()
        print("Aktualizace API klíčů dokončena!")
        print("Pro aplikaci změn spusťte:")
        print("./autostart.sh")
    except Exception as e:
        print(f"Chyba při aktualizaci API klíčů: {e}")
        return False
    return True

if __name__ == "__main__":
    main()
