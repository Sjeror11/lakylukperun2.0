#!/bin/bash

# Skript pro vytvoření .deb balíčku

# Instalace potřebných nástrojů
echo "Instalace potřebných nástrojů..."
sudo apt-get update
sudo apt-get install -y python3-stdeb dh-python python3-all debhelper

# Příprava prostředí
echo "Příprava prostředí..."
cd "$(dirname "$0")"
rm -rf deb_dist

# Vytvoření .deb balíčku pomocí stdeb
echo "Vytváření .deb balíčku..."
python3 setup.py --command-packages=stdeb.command bdist_deb

# Přejmenování a přesunutí balíčku
echo "Dokončování..."
DEB_FILE=$(find deb_dist -name "*.deb" | head -n 1)
if [ -n "$DEB_FILE" ]; then
    cp "$DEB_FILE" "../LakyLinuTermiSignal.deb"
    echo "Balíček byl vytvořen: LakyLinuTermiSignal.deb"
else
    echo "Chyba: .deb balíček nebyl vytvořen"
    exit 1
fi

echo "Hotovo!"
