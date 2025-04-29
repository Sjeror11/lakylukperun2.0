#!/bin/bash
# Skript pro ruční kompilaci Midnight Commander na Synology NAS

echo "=== Ruční kompilace Midnight Commander na Synology NAS ==="
echo ""

# Kontrola, zda jsou nainstalovány potřebné nástroje
echo "Kontroluji, zda jsou nainstalovány potřebné nástroje..."
MISSING_TOOLS=()

for tool in gcc make wget tar gzip; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS+=($tool)
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo "Chybí následující nástroje: ${MISSING_TOOLS[*]}"
    echo "Musíte je nejprve nainstalovat."
    
    # Pokus o instalaci chybějících nástrojů
    if command -v /opt/bin/opkg &> /dev/null; then
        echo "Nalezen Entware, pokusím se nainstalovat chybějící nástroje..."
        for tool in "${MISSING_TOOLS[@]}"; do
            /opt/bin/opkg install $tool
        done
    else
        echo "Entware není nainstalován. Nainstalujte chybějící nástroje ručně nebo nainstalujte Entware."
        exit 1
    fi
fi

# Vytvoření pracovního adresáře
WORK_DIR=~/mc_build
echo "Vytvářím pracovní adresář: $WORK_DIR"
mkdir -p $WORK_DIR
cd $WORK_DIR

# Stažení zdrojového kódu
echo "Stahuji zdrojový kód Midnight Commander..."
MC_VERSION="4.8.28"
wget -O mc-$MC_VERSION.tar.gz https://github.com/MidnightCommander/mc/archive/$MC_VERSION.tar.gz

if [ $? -ne 0 ]; then
    echo "Stažení zdrojového kódu selhalo."
    exit 1
fi

# Rozbalení zdrojového kódu
echo "Rozbaluji zdrojový kód..."
tar -xzf mc-$MC_VERSION.tar.gz
cd mc-$MC_VERSION

# Instalace závislostí
echo "Instaluji závislosti..."
if command -v /opt/bin/opkg &> /dev/null; then
    /opt/bin/opkg install glib ncurses-dev libslang2-dev
fi

# Konfigurace
echo "Konfiguruji..."
./autogen.sh
./configure --prefix=$HOME/mc_install --without-x --disable-nls

if [ $? -ne 0 ]; then
    echo "Konfigurace selhala."
    exit 1
fi

# Kompilace
echo "Kompiluji..."
make -j$(nproc)

if [ $? -ne 0 ]; then
    echo "Kompilace selhala."
    exit 1
fi

# Instalace
echo "Instaluji..."
make install

if [ $? -ne 0 ]; then
    echo "Instalace selhala."
    exit 1
fi

# Vytvoření aliasu
echo "Vytvářím alias pro mc..."
if ! grep -q "alias mc=" ~/.bashrc; then
    echo 'alias mc="TERM=xterm-256color ~/mc_install/bin/mc -d"' >> ~/.bashrc
fi

# Vytvoření skriptu pro spouštění mc
echo "Vytvářím skript pro spouštění mc..."
cat > ~/mc_compiled.sh << 'EOF'
#!/bin/bash
export TERM=xterm-256color
export COLORTERM=truecolor
~/mc_install/bin/mc -d "$@"
EOF

chmod +x ~/mc_compiled.sh

echo ""
echo "=== Kompilace dokončena ==="
echo "Midnight Commander můžete spustit následujícími způsoby:"
echo "1. Příkazem: ~/mc_install/bin/mc"
echo "2. Pomocí skriptu: ~/mc_compiled.sh"
echo "3. Po načtení aliasů (source ~/.bashrc): mc"
echo ""
echo "Pro aplikaci změn v aktuální relaci spusťte:"
echo "source ~/.bashrc"
