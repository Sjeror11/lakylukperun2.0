# Návod na instalaci Perun Trading System na Synology NAS

Tento návod popisuje, jak nainstalovat a spustit Perun Trading System na Synology NAS.

## Požadavky
- Synology NAS s DSM 7.0 nebo novějším
- Python 3.8 nebo novější
- Přístup k NAS přes SSH

## Kroky instalace

### 1. Příprava adresářové struktury
```bash
# Připojení k NAS přes SSH
ssh sjeror@192.168.1.139

# Vytvoření adresáře pro Perun
mkdir -p ~/lakylukperun
chmod 755 ~/lakylukperun
cd ~/lakylukperun
```

### 2. Vytvoření virtuálního prostředí Python
```bash
# Vytvoření virtuálního prostředí
python3 -m venv .venv

# Aktivace virtuálního prostředí
source .venv/bin/activate

# Instalace potřebných balíčků
pip install requests
```

### 3. Vytvoření skriptu Perun Trading System
```bash
# Vytvoření souboru perun_tradingview_multi.py
cat > perun_tradingview_multi.py << 'EOF'
#!/usr/bin/env python3
"""
Jednoduchá verze Perun Trading System pro Synology NAS
"""

import time
from datetime import datetime

def run_trading_system():
    """Spouští obchodní systém."""
    print("=" * 50)
    print("PERUN TRADING SYSTEM - SYNOLOGY NAS VERZE")
    print("=" * 50)
    print("Spouštím obchodní systém pro kryptoměny na Synology NAS.")
    print("=" * 50)

    # Vytvoření logovacího souboru
    log_file = "trading_log.txt"
    with open(log_file, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === SPUŠTĚNÍ OBCHODNÍHO SYSTÉMU ===\n")

    # Hlavní smyčka
    try:
        cycle = 0
        while True:
            cycle += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'=' * 20} CYKLUS {cycle} ({now}) {'=' * 20}")
            with open(log_file, "a") as f:
                f.write(f"[{now}] CYKLUS {cycle}\n")

            # Simulace obchodní logiky
            print("Analyzuji trh...")
            time.sleep(5)
            print("Generuji obchodní signály...")
            time.sleep(5)
            print("Provádím obchody...")
            time.sleep(5)

            # Čekání na další cyklus
            wait_time = 60  # 1 minuta mezi cykly
            print(f"\n⏱️ Čekám {wait_time} sekund na další cyklus...")
            with open(log_file, "a") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Čekání {wait_time} sekund na další cyklus\n")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        print("\n\n🛑 Obchodní systém ukončen uživatelem")
        with open(log_file, "a") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === UKONČENÍ OBCHODNÍHO SYSTÉMU UŽIVATELEM ===\n")

if __name__ == "__main__":
    run_trading_system()
