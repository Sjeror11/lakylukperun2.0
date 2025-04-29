#!/bin/bash
# Skript pro instalaci Perun Trading System na Synology NAS

# Nastavení proměnných
NAS_USER="sjeror"
NAS_IP="192.168.1.139"
LOCAL_SCRIPT="simple_perun.py"
REMOTE_DIR="lakylukperun"

# Vytvoření adresáře na NAS
sudo ssh $NAS_USER@$NAS_IP "mkdir -p ~/$REMOTE_DIR && chmod 755 ~/$REMOTE_DIR"

# Kopírování skriptu na NAS
sudo scp $LOCAL_SCRIPT $NAS_USER@$NAS_IP:~/$REMOTE_DIR/perun_tradingview_multi.py

# Vytvoření virtuálního prostředí a instalace závislostí
sudo ssh $NAS_USER@$NAS_IP "cd ~/$REMOTE_DIR && python3 -m venv .venv && source .venv/bin/activate && pip install requests"

# Vytvoření spouštěcího skriptu
sudo ssh $NAS_USER@$NAS_IP "cat > ~/$REMOTE_DIR/run_perun.sh << 'EOFINNER'
#!/bin/bash
cd ~/$REMOTE_DIR
source .venv/bin/activate
python perun_tradingview_multi.py
EOFINNER"

# Nastavení oprávnění pro spouštěcí skript
sudo ssh $NAS_USER@$NAS_IP "chmod +x ~/$REMOTE_DIR/run_perun.sh"

# Vytvoření skriptu pro automatické spuštění po restartu
sudo ssh $NAS_USER@$NAS_IP "cat > ~/$REMOTE_DIR/autostart.sh << 'EOFINNER'
#!/bin/bash
# Tento skript se spustí po restartu NAS
sleep 60  # Počkáme 60 sekund, aby se systém plně načetl
cd ~/$REMOTE_DIR
nohup ./run_perun.sh > perun.log 2>&1 &
EOFINNER"

# Nastavení oprávnění pro autostart skript
sudo ssh $NAS_USER@$NAS_IP "chmod +x ~/$REMOTE_DIR/autostart.sh"

# Přidání do crontab pro automatické spuštění po restartu
sudo ssh $NAS_USER@$NAS_IP "(crontab -l 2>/dev/null; echo '@reboot ~/$REMOTE_DIR/autostart.sh') | crontab -"

echo "Instalace dokončena. Perun Trading System je nainstalován na Synology NAS."
echo "Pro ruční spuštění se připojte k NAS a spusťte: ~/$REMOTE_DIR/run_perun.sh"
echo "Po restartu NAS se Perun Trading System spustí automaticky."
