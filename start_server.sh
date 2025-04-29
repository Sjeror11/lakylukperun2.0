#!/bin/bash
cd /volume1/homes/sjeror/termisignal
nohup python3 ts_server.py > server.log 2>&1 &
echo "TermiSignal server spuštěn. Log je v souboru server.log"
