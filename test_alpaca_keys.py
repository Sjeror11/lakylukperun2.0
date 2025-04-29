#!/usr/bin/env python3
"""
Jednoduchý skript pro testování Alpaca API klíčů.
"""

import os
import requests
import json

# API klíče
API_KEY = "AKJYB42QYBVD1EKBDQJ8"
API_SECRET = "SczRiShhbzjejIYP8KKcg50XIhJMIyR895vi1hGI"

# Testování Paper Trading API
paper_url = "https://paper-api.alpaca.markets/v2/account"
paper_headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

print("=" * 50)
print("TESTOVÁNÍ ALPACA API KLÍČŮ")
print("=" * 50)

# Test Paper Trading API
print("\nTestuji Paper Trading API...")
try:
    response = requests.get(paper_url, headers=paper_headers)
    if response.status_code == 200:
        account = response.json()
        print(f"✅ Úspěšné připojení k Paper Trading API!")
        print(f"ID účtu: {account.get('id')}")
        print(f"Status účtu: {account.get('status')}")
        print(f"Hotovost: ${float(account.get('cash', 0)):.2f}")
        print(f"Hodnota portfolia: ${float(account.get('portfolio_value', 0)):.2f}")
    else:
        print(f"❌ Chyba při připojení k Paper Trading API: {response.status_code}")
        print(f"Odpověď: {response.text}")
except Exception as e:
    print(f"❌ Výjimka při připojení k Paper Trading API: {e}")

# Testování Live Trading API
live_url = "https://api.alpaca.markets/v2/account"
live_headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

print("\nTestuji Live Trading API...")
try:
    response = requests.get(live_url, headers=live_headers)
    if response.status_code == 200:
        account = response.json()
        print(f"✅ Úspěšné připojení k Live Trading API!")
        print(f"ID účtu: {account.get('id')}")
        print(f"Status účtu: {account.get('status')}")
        print(f"Hotovost: ${float(account.get('cash', 0)):.2f}")
        print(f"Hodnota portfolia: ${float(account.get('portfolio_value', 0)):.2f}")
    else:
        print(f"❌ Chyba při připojení k Live Trading API: {response.status_code}")
        print(f"Odpověď: {response.text}")
except Exception as e:
    print(f"❌ Výjimka při připojení k Live Trading API: {e}")

print("\n" + "=" * 50)
