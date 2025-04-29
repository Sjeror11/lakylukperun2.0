#!/bin/bash
# Skript pro opravu oprávnění pro Midnight Commander

echo "=== Oprava oprávnění pro Midnight Commander ==="
echo ""

# Hledání instalace mc
echo "Hledám instalaci Midnight Commander..."
MC_PATHS=(
    "/usr/bin/mc"
    "/usr/local/bin/mc"
    "/opt/bin/mc"
    "/volume1/@appstore/mc/bin/mc"
    "/var/packages/mc/target/bin/mc"
    "$HOME/mc_install/bin/mc"
)

MC_PATH=""
for path in "${MC_PATHS[@]}"; do
    if [ -f "$path" ]; then
        MC_PATH="$path"
        echo "Nalezen Midnight Commander: $MC_PATH"
        break
    fi
done

if [ -z "$MC_PATH" ]; then
    echo "Midnight Commander nebyl nalezen."
    echo "Zkuste ho nejprve nainstalovat pomocí jednoho z instalačních skriptů."
    exit 1
fi

# Kontrola oprávnění
echo "Kontroluji oprávnění..."
ls -l "$MC_PATH"

# Oprava oprávnění
echo "Opravuji oprávnění..."
sudo chmod +x "$MC_PATH"
sudo chmod 755 "$MC_PATH"

# Kontrola oprávnění po opravě
echo "Oprávnění po opravě:"
ls -l "$MC_PATH"

# Kontrola závislostí
echo "Kontroluji závislosti..."
if command -v ldd &> /dev/null; then
    ldd "$MC_PATH"
    
    # Oprava oprávnění pro závislosti
    echo "Opravuji oprávnění pro závislosti..."
    DEPS=$(ldd "$MC_PATH" | grep -o "/[^ ]*" | grep -v ":")
    for dep in $DEPS; do
        if [ -f "$dep" ]; then
            echo "Opravuji oprávnění pro: $dep"
            sudo chmod +x "$dep"
            sudo chmod 755 "$dep"
        fi
    done
else
    echo "Nelze zkontrolovat závislosti. Chybí příkaz ldd."
fi

# Kontrola adresářů
echo "Kontroluji adresáře..."
MC_DIR=$(dirname "$MC_PATH")
ls -ld "$MC_DIR"

# Oprava oprávnění pro adresáře
echo "Opravuji oprávnění pro adresáře..."
sudo chmod 755 "$MC_DIR"

# Kontrola konfiguračního adresáře
echo "Kontroluji konfigurační adresář..."
CONFIG_DIR="$HOME/.config/mc"
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Vytvářím konfigurační adresář: $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR"
fi

# Oprava oprávnění pro konfigurační adresář
echo "Opravuji oprávnění pro konfigurační adresář..."
chmod 755 "$CONFIG_DIR"

echo ""
echo "=== Oprava oprávnění dokončena ==="
echo "Zkuste nyní spustit Midnight Commander příkazem:"
echo "$MC_PATH"
