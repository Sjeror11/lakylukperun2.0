#!/bin/bash
# Skript pro instalaci Midnight Commander přes SynoCommunity

echo "=== Instalace Midnight Commander přes SynoCommunity ==="
echo ""

# Kontrola, zda je nainstalován SynoCommunity
echo "Kontroluji, zda je nainstalován SynoCommunity..."
if [ -f /usr/syno/bin/pkgctl ]; then
    # DSM 7.x
    SYNOCOMMUNITY_INSTALLED=$(sudo /usr/syno/bin/pkgctl list | grep SynoCommunity)
else
    # DSM 6.x
    SYNOCOMMUNITY_INSTALLED=$(sudo synopkg list | grep SynoCommunity)
fi

if [ -z "$SYNOCOMMUNITY_INSTALLED" ]; then
    echo "SynoCommunity není nainstalován."
    echo "Musíte nejprve přidat SynoCommunity jako zdroj balíčků v DSM:"
    echo "1. Otevřete DSM (Diskstation Manager)"
    echo "2. Jděte do Package Center > Settings > Package Sources"
    echo "3. Klikněte na Add a zadejte:"
    echo "   - Name: SynoCommunity"
    echo "   - Location: https://packages.synocommunity.com/"
    echo "4. Klikněte na OK"
    echo ""
    read -p "Až přidáte SynoCommunity, stiskněte Enter pro pokračování..."
fi

# Kontrola verze DSM
echo "Zjišťuji verzi DSM..."
if [ -f /etc/VERSION ]; then
    DSM_VERSION=$(grep -oP '(?<=productversion=").*?(?=")' /etc/VERSION)
    echo "DSM verze: $DSM_VERSION"
else
    echo "Nelze zjistit verzi DSM."
    DSM_VERSION="unknown"
fi

# Instalace Midnight Commander
echo "Instaluji Midnight Commander..."
if [[ "$DSM_VERSION" == 7* ]]; then
    # DSM 7.x
    sudo /usr/syno/bin/synopkg install mc
elif [[ "$DSM_VERSION" == 6* ]]; then
    # DSM 6.x
    sudo synopkg install mc
else
    echo "Nepodporovaná verze DSM. Zkuste ruční instalaci."
    exit 1
fi

# Kontrola instalace
echo "Kontroluji instalaci..."
if [ -d /var/packages/mc ]; then
    echo "Midnight Commander byl úspěšně nainstalován!"
    
    # Zjištění cesty k mc
    MC_PATH=$(find /var/packages/mc -name mc -type f -executable 2>/dev/null)
    
    if [ -n "$MC_PATH" ]; then
        echo "Cesta k mc: $MC_PATH"
        
        # Vytvoření aliasu pro mc
        echo "Vytvářím alias pro mc..."
        if ! grep -q "alias mc=" ~/.bashrc; then
            echo "alias mc=\"TERM=xterm-256color $MC_PATH -d\"" >> ~/.bashrc
        fi
        
        # Vytvoření skriptu pro spouštění mc
        echo "Vytvářím skript pro spouštění mc..."
        cat > ~/mc_syno.sh << EOF
#!/bin/bash
export TERM=xterm-256color
export COLORTERM=truecolor
$MC_PATH -d "\$@"
EOF
        
        chmod +x ~/mc_syno.sh
        
        echo ""
        echo "=== Instalace dokončena ==="
        echo "Midnight Commander můžete spustit následujícími způsoby:"
        echo "1. Příkazem: $MC_PATH"
        echo "2. Pomocí skriptu: ~/mc_syno.sh"
        echo "3. Po načtení aliasů (source ~/.bashrc): mc"
        echo ""
        echo "Pro aplikaci změn v aktuální relaci spusťte:"
        echo "source ~/.bashrc"
    else
        echo "Midnight Commander byl nainstalován, ale nelze najít spustitelný soubor."
    fi
else
    echo "Instalace Midnight Commander selhala."
    exit 1
fi
