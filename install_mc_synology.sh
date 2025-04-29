#!/bin/bash
# Skript pro instalaci Midnight Commander na Synology NAS
# Spusťte tento skript po připojení k NAS přes SSH s sudo oprávněními

# Aktualizace seznamu balíčků
echo "Aktualizuji seznam balíčků..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
elif command -v opkg &> /dev/null; then
    sudo opkg update
elif command -v ipkg &> /dev/null; then
    sudo ipkg update
else
    echo "Nepodařilo se najít správce balíčků. Zkontrolujte, zda je povolen balíček Entware nebo SynoCommunity."
    exit 1
fi

# Instalace Midnight Commander
echo "Instaluji Midnight Commander..."
if command -v apt-get &> /dev/null; then
    sudo apt-get install -y mc
elif command -v opkg &> /dev/null; then
    sudo opkg install mc
elif command -v ipkg &> /dev/null; then
    sudo ipkg install mc
else
    echo "Nepodařilo se nainstalovat mc. Zkuste ruční instalaci."
    exit 1
fi

# Kontrola instalace
if command -v mc &> /dev/null; then
    echo "Midnight Commander byl úspěšně nainstalován!"
else
    echo "Instalace Midnight Commander selhala."
    
    # Zkusíme zjistit, proč instalace selhala
    echo "Kontroluji možné příčiny problému..."
    
    # Kontrola cesty
    echo "Aktuální PATH: $PATH"
    
    # Kontrola, zda je mc nainstalován, ale není v PATH
    find / -name mc 2>/dev/null
    
    # Kontrola závislostí
    if command -v ldd &> /dev/null; then
        echo "Kontrola závislostí pro mc (pokud existuje):"
        MC_PATH=$(find / -name mc -type f -executable 2>/dev/null | head -1)
        if [ -n "$MC_PATH" ]; then
            ldd "$MC_PATH" 2>&1
        fi
    fi
    
    exit 1
fi

# Vytvoření aliasu pro snadnější spouštění
echo "Vytvářím alias pro mc..."
echo 'alias mc="TERM=xterm-256color mc -d"' >> ~/.bashrc
echo 'export TERM=xterm-256color' >> ~/.bashrc

# Vytvoření skriptu pro spouštění mc s potřebnými nastaveními
echo "Vytvářím pomocný skript pro spouštění mc..."
cat > ~/run_mc.sh << 'EOF'
#!/bin/bash
export TERM=xterm-256color
export COLORTERM=truecolor
mc -d "$@"
EOF

chmod +x ~/run_mc.sh

echo "Instalace dokončena. Midnight Commander můžete spustit příkazem 'mc' nebo './run_mc.sh'"
echo "Pro aplikaci změn v aktuální relaci spusťte: source ~/.bashrc"
