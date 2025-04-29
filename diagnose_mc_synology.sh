#!/bin/bash
# Diagnostický skript pro zjištění problémů s Midnight Commander na Synology NAS

echo "=== Diagnostika Midnight Commander na Synology NAS ==="
echo ""

# Kontrola verze systému
echo "Verze systému:"
uname -a
echo ""

if [ -f /etc/synoinfo.conf ]; then
    echo "Informace o Synology:"
    grep -E "^(majorversion|minorversion|buildnumber)" /etc/synoinfo.conf
    echo ""
fi

# Kontrola instalace mc
echo "Kontrola instalace Midnight Commander:"
which mc 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Midnight Commander je nainstalován v: $(which mc)"
    echo "Verze: $(mc --version | head -1)"
else
    echo "Midnight Commander není nainstalován nebo není v PATH."
fi
echo ""

# Hledání mc v systému
echo "Hledání mc v systému:"
find / -name mc -type f -executable 2>/dev/null
echo ""

# Kontrola PATH
echo "Aktuální PATH:"
echo $PATH
echo ""

# Kontrola terminálu
echo "Nastavení terminálu:"
echo "TERM=$TERM"
echo "COLORTERM=$COLORTERM"
echo ""

# Kontrola balíčkovacích systémů
echo "Dostupné balíčkovací systémy:"
for pkg in apt-get opkg ipkg; do
    if command -v $pkg &> /dev/null; then
        echo "$pkg je dostupný"
    else
        echo "$pkg není dostupný"
    fi
done
echo ""

# Kontrola Entware
echo "Kontrola Entware:"
if [ -d /opt/bin ] || [ -d /opt/sbin ]; then
    echo "Entware je pravděpodobně nainstalován"
    ls -la /opt/bin /opt/sbin 2>/dev/null | grep mc
else
    echo "Entware pravděpodobně není nainstalován"
fi
echo ""

# Kontrola SynoCommunity
echo "Kontrola SynoCommunity:"
if [ -d /var/packages/mc ]; then
    echo "Balíček mc z SynoCommunity je nainstalován"
    ls -la /var/packages/mc
else
    echo "Balíček mc z SynoCommunity není nainstalován"
fi
echo ""

# Kontrola oprávnění
echo "Kontrola oprávnění uživatele:"
id
echo ""

# Kontrola závislostí
echo "Kontrola závislostí (pokud je mc nainstalován):"
MC_PATH=$(which mc 2>/dev/null)
if [ -n "$MC_PATH" ] && command -v ldd &> /dev/null; then
    ldd "$MC_PATH" 2>&1
else
    echo "Nelze zkontrolovat závislosti"
fi
echo ""

echo "=== Diagnostika dokončena ==="
