#!/bin/bash
# Skript pro instalaci Entware na Synology NAS

echo "=== Instalace Entware na Synology NAS ==="
echo ""

# Zjištění architektury procesoru
echo "Zjišťuji architekturu procesoru..."
ARCH=$(uname -m)
echo "Architektura: $ARCH"
echo ""

# Výběr správného instalačního skriptu podle architektury
if [[ "$ARCH" == "x86_64" ]]; then
    INSTALLER="generic.sh"
elif [[ "$ARCH" == "aarch64" ]]; then
    INSTALLER="aarch64-installer.sh"
elif [[ "$ARCH" == "armv7l" || "$ARCH" == "armv8l" ]]; then
    INSTALLER="armv7-installer.sh"
elif [[ "$ARCH" == "armv5tel" ]]; then
    INSTALLER="armv5-installer.sh"
elif [[ "$ARCH" == "mips" ]]; then
    INSTALLER="mips-installer.sh"
else
    echo "Nepodporovaná architektura: $ARCH"
    echo "Zkuste ruční instalaci podle návodu na https://github.com/Entware/Entware/wiki/Install-on-Synology-NAS"
    exit 1
fi

# Kontrola, zda je již Entware nainstalován
if [ -d /opt/bin ] && [ -f /opt/bin/opkg ]; then
    echo "Entware je již nainstalován."
    echo "Pokud chcete přeinstalovat, nejprve odstraňte adresář /opt a spusťte skript znovu."
    echo ""
    read -p "Chcete pokračovat s aktualizací balíčků? (a/n): " choice
    if [ "$choice" != "a" ]; then
        exit 0
    fi
else
    # Vytvoření adresáře /opt, pokud neexistuje
    echo "Vytvářím adresář /opt..."
    if [ ! -d /opt ]; then
        sudo mkdir -p /opt
        sudo chown -R admin:users /opt
        sudo chmod -R 775 /opt
    fi
    
    # Stažení a spuštění instalačního skriptu
    echo "Stahuji a spouštím instalační skript Entware..."
    wget -O - https://raw.githubusercontent.com/Entware/Entware/master/installer/$INSTALLER | /bin/sh
    
    if [ $? -ne 0 ]; then
        echo "Instalace Entware selhala."
        exit 1
    fi
fi

# Přidání Entware do PATH
echo "Přidávám Entware do PATH..."
if ! grep -q "PATH=.*\/opt\/bin" ~/.profile; then
    echo 'export PATH=$PATH:/opt/bin:/opt/sbin' >> ~/.profile
fi

if ! grep -q "PATH=.*\/opt\/bin" ~/.bashrc; then
    echo 'export PATH=$PATH:/opt/bin:/opt/sbin' >> ~/.bashrc
fi

# Aktualizace balíčků
echo "Aktualizuji seznam balíčků..."
/opt/bin/opkg update

# Instalace Midnight Commander
echo "Instaluji Midnight Commander..."
/opt/bin/opkg install mc

# Kontrola instalace
if [ -f /opt/bin/mc ]; then
    echo "Midnight Commander byl úspěšně nainstalován!"
    
    # Vytvoření aliasu pro mc
    echo "Vytvářím alias pro mc..."
    if ! grep -q "alias mc=" ~/.bashrc; then
        echo 'alias mc="TERM=xterm-256color /opt/bin/mc -d"' >> ~/.bashrc
    fi
    
    # Vytvoření skriptu pro spouštění mc
    echo "Vytvářím skript pro spouštění mc..."
    cat > ~/mc_run.sh << 'EOF'
#!/bin/bash
export TERM=xterm-256color
export COLORTERM=truecolor
/opt/bin/mc -d "$@"
EOF
    
    chmod +x ~/mc_run.sh
    
    echo ""
    echo "=== Instalace dokončena ==="
    echo "Midnight Commander můžete spustit následujícími způsoby:"
    echo "1. Příkazem: /opt/bin/mc"
    echo "2. Pomocí skriptu: ~/mc_run.sh"
    echo "3. Po načtení aliasů (source ~/.bashrc): mc"
    echo ""
    echo "Pro aplikaci změn v aktuální relaci spusťte:"
    echo "source ~/.bashrc"
else
    echo "Instalace Midnight Commander selhala."
    exit 1
fi
