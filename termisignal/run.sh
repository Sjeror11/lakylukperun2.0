#!/bin/bash

# Skript pro spuštění aplikace TermiSignal

# Přejít do adresáře skriptu
cd "$(dirname "$0")"

# Kontrola, zda je nainstalován Python 3
if ! command -v python3 &> /dev/null; then
    echo "Python 3 není nainstalován. Nainstalujte jej pomocí:"
    echo "sudo apt-get install python3 python3-pip"
    exit 1
fi

# Kontrola, zda jsou nainstalovány závislosti
if ! python3 -c "import textual" &> /dev/null; then
    echo "Instalace závislostí..."
    pip3 install -r requirements.txt
fi

# Spuštění aplikace
python3 -m termisignal
