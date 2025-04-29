#!/bin/bash

# Skript pro instalaci vylepšeného logování na Synology NAS

# Vytvoření záložní kopie
echo "Vytvářím záložní kopii perun_tradingview_multi.py..."
ssh sjeror@192.168.1.139 "cd ~/lakylukperun && cp perun_tradingview_multi.py perun_tradingview_multi.py.backup_$(date +%Y%m%d%H%M%S)"

# Nahrání vylepšených funkcí
echo "Nahrávám vylepšené funkce..."
scp enhance_log_trade.py sjeror@192.168.1.139:~/lakylukperun/

# Spuštění skriptu pro aktualizaci funkcí
echo "Aktualizuji funkce v perun_tradingview_multi.py..."
ssh sjeror@192.168.1.139 "cd ~/lakylukperun && python3 -c \"
import re

# Načtení vylepšených funkcí
with open('enhance_log_trade.py', 'r') as f:
    code = f.read()
    exec(code)

# Načtení původního souboru
with open('perun_tradingview_multi.py', 'r') as f:
    content = f.read()

# Nahrazení funkce log_trade
log_trade_pattern = r'def log_trade\([^)]*\):.*?(?=def |$)'
enhanced_log_trade = enhance_log_trade().strip()
content = re.sub(log_trade_pattern, enhanced_log_trade, content, flags=re.DOTALL)

# Nahrazení funkce execute_trade
execute_trade_pattern = r'def execute_trade\([^)]*\):.*?(?=def |$)'
enhanced_execute_trade = enhance_execute_trade().strip()
content = re.sub(execute_trade_pattern, enhanced_execute_trade, content, flags=re.DOTALL)

# Uložení aktualizovaného souboru
with open('perun_tradingview_multi.py', 'w') as f:
    f.write(content)

print('Funkce byly úspěšně aktualizovány!')
\""

# Restart služby
echo "Restartuji službu Perun..."
ssh sjeror@192.168.1.139 "cd ~/lakylukperun && ./autostart.sh"

echo "Instalace dokončena!"
