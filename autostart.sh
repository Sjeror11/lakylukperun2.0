#!/bin/bash
# Tento skript se spustí po restartu NAS
sleep 60  # Počkáme 60 sekund, aby se systém plně načetl
cd ~/lakylukperun
nohup ./run_perun.sh > perun.log 2>&1 &
