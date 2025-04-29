#!/bin/bash

# Instalační skript pro Perun Trading System
echo "===== Instalace Perun Trading System ====="

# Kontrola závislostí
echo "Kontroluji závislosti..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 není nainstalován. Instaluji..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Vytvoření instalačního adresáře
echo "Vytvářím instalační adresář..."
INSTALL_DIR="$HOME/perun"
mkdir -p "$INSTALL_DIR"

# Kopírování souborů
echo "Kopíruji soubory..."
cp -r perun_taapi_simple.py perun_crypto.py run_simulation.py perun_direct_api.py .env requirements.txt "$INSTALL_DIR/"
cp -r src data "$INSTALL_DIR/"

# Vytvoření virtuálního prostředí
echo "Vytvářím virtuální prostředí..."
cd "$INSTALL_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Vytvoření spouštěcího skriptu
echo "Vytvářím spouštěcí skript..."
cat > "$HOME/.local/bin/perun-trading" << 'EOF'
#!/bin/bash

# Spuštění Perun Trading System
cd "$HOME/perun"
source .venv/bin/activate

# Zobrazení menu
echo "===== Perun Trading System ====="
echo "1) Spustit obchodování s kryptoměnami (TAAPI.IO)"
echo "2) Spustit obchodování s kryptoměnami (přímé API)"
echo "3) Spustit simulaci obchodování"
echo "q) Ukončit"
echo "============================"
echo -n "Vyberte možnost: "
read choice

case $choice in
    1)
        python perun_taapi_simple.py
        ;;
    2)
        python perun_crypto.py
        ;;
    3)
        python run_simulation.py
        ;;
    q|Q)
        echo "Ukončuji..."
        exit 0
        ;;
    *)
        echo "Neplatná volba!"
        exit 1
        ;;
esac
EOF

# Nastavení oprávnění
chmod +x "$HOME/.local/bin/perun-trading"

# Vytvoření zástupce na ploše
echo "Vytvářím zástupce na ploše..."
cat > "$HOME/Plocha/Perun Trading.desktop" << EOF
[Desktop Entry]
Name=Perun Trading System
Comment=Automatický obchodní systém pro kryptoměny
Exec=x-terminal-emulator -e perun-trading
Terminal=true
Type=Application
Categories=Finance;
Keywords=trading;crypto;bitcoin;
EOF

chmod +x "$HOME/Plocha/Perun Trading.desktop"

echo "===== Instalace dokončena ====="
echo "Perun Trading System byl úspěšně nainstalován!"
echo "Spusťte příkazem: perun-trading"
echo "Nebo klikněte na ikonu na ploše."
