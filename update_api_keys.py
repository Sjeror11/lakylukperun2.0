#!/usr/bin/env python3
"""
Skript pro aktualizaci API klíčů v Perun Trading System.
Tento skript aktualizuje API klíče v souboru perun_tradingview_multi.py.
"""

import os
import re
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
        content = f.read()
    
    # Nové API klíče
    api_key = "AKJ7JX2TTYIGDCDQMQOS"
    secret_key = "LgAiUxTXA7rSJE5QGhLmOLctGRJSsjQb7rWYorFB"
    
    # Nahrazení API klíčů pomocí regulárních výrazů
    content = re.sub(r'ALPACA_API_KEY\s*=\s*"[^"]*"', f'ALPACA_API_KEY = "{api_key}"', content)
    content = re.sub(r'ALPACA_API_SECRET\s*=\s*"[^"]*"', f'ALPACA_API_SECRET = "{secret_key}"', content)
    
    # Uložení aktualizovaného souboru
    with open('perun_tradingview_multi.py', 'w') as f:
        f.write(content)
    
    print(f"API klíče byly aktualizovány:")
    print(f"API_KEY = {api_key}")
    print(f"SECRET_KEY = {secret_key[:5]}...{secret_key[-5:]}")
    return True

def update_crypto_symbols():
    """Aktualizuje seznam kryptoměn pro obchodování."""
    with open('perun_tradingview_multi.py', 'r') as f:
        content = f.read()
    
    # Nový seznam kryptoměn
    new_symbols = '["BTCUSD", "ETHUSD", "XRPUSD", "SOLUSD", "DOGEUSD", "XMRUSD"]'
    
    # Nahrazení seznamu kryptoměn
    content = re.sub(r'CRYPTO_SYMBOLS\s*=\s*\[[^\]]*\]', f'CRYPTO_SYMBOLS = {new_symbols}', content)
    
    # Uložení aktualizovaného souboru
    with open('perun_tradingview_multi.py', 'w') as f:
        f.write(content)
    
    print(f"Seznam kryptoměn byl aktualizován na: {new_symbols}")
    return True

def main():
    """Hlavní funkce pro aktualizaci API klíčů."""
    try:
        print("Začínám aktualizaci konfigurace...")
        create_backup()
        update_api_keys()
        update_crypto_symbols()
        print("Aktualizace konfigurace dokončena!")
        print("Pro aplikaci změn spusťte:")
        print("./run_perun.sh")
    except Exception as e:
        print(f"Chyba při aktualizaci konfigurace: {e}")
        return False
    return True

if __name__ == "__main__":
    main()
