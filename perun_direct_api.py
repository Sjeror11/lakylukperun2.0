#!/usr/bin/env python3
"""
Perun Trading System s přímým přístupem k Alpaca API.
Tato verze používá přímé HTTP požadavky místo knihovny alpaca_trade_api.
"""

import os
import sys
import time
import json
import random
import requests
from datetime import datetime, timedelta

# API klíče
API_KEY = "AKJYB42QYBVD1EKBDQJ8"
API_SECRET = "SczRiShhbzjejIYP8KKcg50XIhJMIyR895vi1hGI"
BASE_URL = "https://api.alpaca.markets/v2"

# Hlavičky pro API požadavky
HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET,
    "Content-Type": "application/json"
}

# Symboly pro obchodování
SYMBOLS = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]

# Nastavení rizika
MAX_POSITION_SIZE = 1000  # Maximální velikost pozice v USD
MAX_TOTAL_POSITIONS = 5   # Maximální počet současných pozic
RISK_LIMIT_PERCENT = 0.02 # Maximální riziko na obchod (2% portfolia)

# Funkce pro práci s Alpaca API
def get_account():
    """Získá informace o účtu."""
    try:
        response = requests.get(f"{BASE_URL}/account", headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Chyba při získávání informací o účtu: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání informací o účtu: {e}")
        return None

def get_positions():
    """Získá aktuální pozice."""
    try:
        response = requests.get(f"{BASE_URL}/positions", headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Chyba při získávání pozic: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Výjimka při získávání pozic: {e}")
        return []

def get_orders():
    """Získá aktuální objednávky."""
    try:
        response = requests.get(f"{BASE_URL}/orders", headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Chyba při získávání objednávek: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Výjimka při získávání objednávek: {e}")
        return []

def get_market_data(symbol):
    """Získá tržní data pro symbol."""
    # V reálné implementaci byste použili Alpaca Market Data API
    # Pro jednoduchost zde generujeme náhodná data
    return {
        "price": random.uniform(100, 500),
        "change": random.uniform(-0.05, 0.05),
        "volume": random.randint(100000, 10000000)
    }

def place_order(symbol, qty, side, order_type="market", time_in_force="day"):
    """Zadá objednávku."""
    try:
        data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force
        }
        response = requests.post(f"{BASE_URL}/orders", headers=HEADERS, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Chyba při zadávání objednávky: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při zadávání objednávky: {e}")
        return None

def cancel_order(order_id):
    """Zruší objednávku."""
    try:
        response = requests.delete(f"{BASE_URL}/orders/{order_id}", headers=HEADERS)
        if response.status_code == 204:
            return True
        else:
            print(f"❌ Chyba při rušení objednávky: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Výjimka při rušení objednávky: {e}")
        return False

def is_market_open():
    """Zkontroluje, zda je trh otevřený."""
    try:
        response = requests.get(f"{BASE_URL}/clock", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            return data.get("is_open", False)
        else:
            print(f"❌ Chyba při kontrole otevření trhu: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Výjimka při kontrole otevření trhu: {e}")
        return False

def get_trading_signals():
    """Generuje obchodní signály na základě analýzy trhu."""
    # V reálné implementaci byste použili AI pro generování signálů
    # Pro jednoduchost zde generujeme náhodné signály
    signals = []
    for symbol in SYMBOLS:
        if random.random() < 0.2:  # 20% šance na signál
            side = random.choice(["buy", "sell"])
            qty = random.randint(1, 5)
            signals.append({
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "confidence": random.uniform(0.5, 1.0)
            })
    return signals

def format_money(amount):
    """Formátuje částku jako peníze."""
    return f"${amount:.2f}"

def run_trading_system():
    """Spouští obchodní systém."""
    print("=" * 50)
    print("PERUN TRADING SYSTEM - PŘÍMÉ API")
    print("=" * 50)
    print("Spouštím obchodní systém s přímým přístupem k Alpaca API.")
    print("=" * 50)
    
    # Získání informací o účtu
    account = get_account()
    if not account:
        print("❌ Nelze získat informace o účtu. Ukončuji.")
        return
    
    print(f"\n📊 Informace o účtu:")
    print(f"ID účtu: {account.get('id')}")
    print(f"Status účtu: {account.get('status')}")
    print(f"Hotovost: {format_money(float(account.get('cash', 0)))}")
    print(f"Hodnota portfolia: {format_money(float(account.get('portfolio_value', 0)))}")
    
    # Hlavní smyčka
    try:
        cycle = 0
        while True:
            cycle += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'=' * 20} CYKLUS {cycle} ({now}) {'=' * 20}")
            
            # Kontrola, zda je trh otevřený
            market_open = is_market_open()
            print(f"🕒 Trh je {'otevřený' if market_open else 'zavřený'}")
            
            # Získání aktuálních pozic
            positions = get_positions()
            print(f"\n📈 Aktuální pozice ({len(positions)}):")
            for position in positions:
                symbol = position.get("symbol")
                qty = float(position.get("qty", 0))
                avg_entry_price = float(position.get("avg_entry_price", 0))
                current_price = float(position.get("current_price", 0))
                market_value = float(position.get("market_value", 0))
                unrealized_pl = float(position.get("unrealized_pl", 0))
                unrealized_plpc = float(position.get("unrealized_plpc", 0)) * 100
                
                print(f"  {symbol}: {qty} akcií @ {format_money(avg_entry_price)} | Aktuální cena: {format_money(current_price)} | P/L: {format_money(unrealized_pl)} ({unrealized_plpc:.2f}%)")
            
            # Získání aktuálních objednávek
            orders = get_orders()
            print(f"\n📋 Aktuální objednávky ({len(orders)}):")
            for order in orders:
                order_id = order.get("id")
                symbol = order.get("symbol")
                side = order.get("side")
                qty = float(order.get("qty", 0))
                order_type = order.get("type")
                status = order.get("status")
                
                print(f"  {symbol}: {side.upper()} {qty} akcií ({order_type}) | Status: {status}")
            
            # Generování obchodních signálů
            if market_open:
                signals = get_trading_signals()
                if signals:
                    print(f"\n🔔 Obchodní signály ({len(signals)}):")
                    for signal in signals:
                        symbol = signal.get("symbol")
                        side = signal.get("side")
                        qty = signal.get("qty")
                        confidence = signal.get("confidence")
                        
                        print(f"  {symbol}: {side.upper()} {qty} akcií | Důvěra: {confidence:.2f}")
                        
                        # Provedení obchodu na základě signálu
                        if confidence > 0.7:  # Pouze signály s vysokou důvěrou
                            print(f"  ✅ Provádím obchod: {side.upper()} {qty} akcií {symbol}")
                            result = place_order(symbol, qty, side)
                            if result:
                                print(f"  ✅ Obchod zadán: ID objednávky {result.get('id')}")
                            else:
                                print(f"  ❌ Obchod se nezdařil")
                else:
                    print("\n🔍 Žádné obchodní signály")
            else:
                print("\n🔒 Trh je zavřený, žádné obchody nebudou provedeny")
            
            # Čekání na další cyklus
            print(f"\n⏱️ Čekám 60 sekund na další cyklus...")
            time.sleep(60)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Obchodní systém ukončen uživatelem")
        print(f"💰 Konečná hodnota portfolia: {format_money(float(account.get('portfolio_value', 0)))}")
        sys.exit(0)

if __name__ == "__main__":
    run_trading_system()
