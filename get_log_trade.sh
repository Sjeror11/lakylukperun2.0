#!/bin/bash
ssh sjeror@192.168.1.139 "cd ~/lakylukperun && grep -A 10 'def log_trade' perun_tradingview_multi.py"
