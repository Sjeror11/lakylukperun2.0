#!/bin/bash

# Kontrola, zda byl zadán argument pro SSH připojení
if [ $# -lt 1 ]; then
    echo "Použití: $0 [uživatel@]server [cesta]"
    exit 1
fi

SERVER=$1
PATH_TO_OPEN=${2:-.}

# Připojení přes SSH a spuštění mc
ssh -t $SERVER "export TERM=xterm-256color && export COLORTERM=truecolor && cd $PATH_TO_OPEN && mc -d"
