#!/usr/bin/env python3
"""
Perun Trading System - Krypto verze
Specializovaná verze pro obchodování s kryptoměnami 24/7.
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

# Kryptoměny pro obchodování
CRYPTO_SYMBOLS = ["BTCUSD", "ETHUSD"]

# Nastavení rizika
MAX_POSITION_SIZE = 50  # Maximální velikost pozice v USD
MAX_TOTAL_POSITIONS = 2  # Maximální počet současných pozic
RISK_LIMIT_PERCENT = 0.02  # Maximální riziko na obchod (2% portfolia)

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
            positions = response.json()
            # Filtrujeme pouze kryptoměnové pozice
            crypto_positions = [p for p in positions if p.get("symbol") in CRYPTO_SYMBOLS]
            return crypto_positions
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
            orders = response.json()
            # Filtrujeme pouze kryptoměnové objednávky
            crypto_orders = [o for o in orders if o.get("symbol") in CRYPTO_SYMBOLS]
            return crypto_orders
        else:
            print(f"❌ Chyba při získávání objednávek: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Výjimka při získávání objednávek: {e}")
        return []

def get_crypto_price(symbol):
    """Získá aktuální cenu kryptoměny."""
    try:
        response = requests.get(f"{BASE_URL}/assets/{symbol}", headers=HEADERS)
        if response.status_code == 200:
            asset = response.json()
            return float(asset.get("price", 0))
        else:
            print(f"❌ Chyba při získávání ceny {symbol}: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání ceny {symbol}: {e}")
        return None

def place_crypto_order(symbol, qty, side, order_type="market", time_in_force="gtc"):
    """Zadá objednávku na kryptoměnu."""
    try:
        data = {
            "symbol": symbol,
            "qty": str(qty),  # Alpaca vyžaduje qty jako string pro kryptoměny
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

def get_crypto_bars(symbol, timeframe="1D", limit=10):
    """Získá historické údaje o ceně kryptoměny."""
    try:
        response = requests.get(
            f"{BASE_URL}/crypto/{symbol}/bars",
            headers=HEADERS,
            params={"timeframe": timeframe, "limit": limit}
        )
        if response.status_code == 200:
            return response.json().get("bars", [])
        else:
            print(f"❌ Chyba při získávání historických dat pro {symbol}: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Výjimka při získávání historických dat pro {symbol}: {e}")
        return []

def calculate_sma(bars, period=20):
    """Vypočítá jednoduchý klouzavý průměr."""
    if len(bars) < period:
        return None
    
    closes = [float(bar.get("c", 0)) for bar in bars[-period:]]
    return sum(closes) / period

def calculate_rsi(bars, period=14):
    """Vypočítá RSI (Relative Strength Index)."""
    if len(bars) < period + 1:
        return None
    
    closes = [float(bar.get("c", 0)) for bar in bars]
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def analyze_crypto(symbol):
    """Analyzuje kryptoměnu a generuje obchodní signál."""
    # Získání historických dat
    bars = get_crypto_bars(symbol, timeframe="1H", limit=50)
    if not bars:
        return None
    
    # Výpočet technických indikátorů
    sma20 = calculate_sma(bars, 20)
    rsi = calculate_rsi(bars, 14)
    
    if not sma20 or not rsi:
        return None
    
    # Aktuální cena
    current_price = float(bars[-1].get("c", 0))
    
    # Jednoduchá obchodní strategie
    signal = None
    confidence = 0.5
    
    # RSI strategie
    if rsi < 30:  # Překoupeno
        signal = "buy"
        confidence += 0.2
    elif rsi > 70:  # Přeprodáno
        signal = "sell"
        confidence += 0.2
    
    # SMA strategie
    if current_price > sma20:  # Cena nad SMA20 - býčí trend
        if signal == "buy":
            confidence += 0.1
        elif signal is None:
            signal = "buy"
            confidence += 0.1
    elif current_price < sma20:  # Cena pod SMA20 - medvědí trend
        if signal == "sell":
            confidence += 0.1
        elif signal is None:
            signal = "sell"
            confidence += 0.1
    
    # Pokud nemáme signál, vrátíme None
    if signal is None:
        return None
    
    # Výpočet množství na základě rizika
    account = get_account()
    if not account:
        return None
    
    portfolio_value = float(account.get("portfolio_value", 0))
    risk_amount = portfolio_value * RISK_LIMIT_PERCENT
    
    # Omezení velikosti pozice
    max_qty_by_risk = risk_amount / current_price
    max_qty_by_limit = MAX_POSITION_SIZE / current_price
    qty = min(max_qty_by_risk, max_qty_by_limit)
    
    # Zaokrouhlení na 8 desetinných míst (běžné pro kryptoměny)
    qty = round(qty, 8)
    
    # Minimální množství pro obchodování
    if qty < 0.0001:
        qty = 0.0001
    
    return {
        "symbol": symbol,
        "side": signal,
        "qty": qty,
        "price": current_price,
        "confidence": confidence,
        "indicators": {
            "sma20": sma20,
            "rsi": rsi
        }
    }

def format_money(amount):
    """Formátuje částku jako peníze."""
    return f"${amount:.2f}"

def format_crypto(amount):
    """Formátuje množství kryptoměny."""
    if amount < 0.001:
        return f"{amount:.8f}"
    elif amount < 1:
        return f"{amount:.6f}"
    else:
        return f"{amount:.4f}"

def run_crypto_trading_system():
    """Spouští obchodní systém pro kryptoměny."""
    print("=" * 50)
    print("PERUN TRADING SYSTEM - KRYPTO VERZE")
    print("=" * 50)
    print("Spouštím obchodní systém pro kryptoměny 24/7.")
    print(f"Obchodované symboly: {', '.join(CRYPTO_SYMBOLS)}")
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
            
            # Získání aktuálních pozic
            positions = get_positions()
            print(f"\n📈 Aktuální krypto pozice ({len(positions)}):")
            for position in positions:
                symbol = position.get("symbol")
                qty = float(position.get("qty", 0))
                avg_entry_price = float(position.get("avg_entry_price", 0))
                current_price = float(position.get("current_price", 0))
                market_value = float(position.get("market_value", 0))
                unrealized_pl = float(position.get("unrealized_pl", 0))
                unrealized_plpc = float(position.get("unrealized_plpc", 0)) * 100
                
                print(f"  {symbol}: {format_crypto(qty)} @ {format_money(avg_entry_price)} | Aktuální cena: {format_money(current_price)} | P/L: {format_money(unrealized_pl)} ({unrealized_plpc:.2f}%)")
            
            # Získání aktuálních objednávek
            orders = get_orders()
            print(f"\n📋 Aktuální krypto objednávky ({len(orders)}):")
            for order in orders:
                order_id = order.get("id")
                symbol = order.get("symbol")
                side = order.get("side")
                qty = float(order.get("qty", 0))
                order_type = order.get("type")
                status = order.get("status")
                
                print(f"  {symbol}: {side.upper()} {format_crypto(qty)} ({order_type}) | Status: {status}")
            
            # Analýza a generování obchodních signálů
            print(f"\n🔍 Analyzuji kryptoměny...")
            for symbol in CRYPTO_SYMBOLS:
                signal = analyze_crypto(symbol)
                if signal:
                    side = signal.get("side")
                    qty = signal.get("qty")
                    price = signal.get("price")
                    confidence = signal.get("confidence")
                    indicators = signal.get("indicators", {})
                    
                    print(f"\n🔔 Obchodní signál pro {symbol}:")
                    print(f"  Akce: {side.upper()}")
                    print(f"  Množství: {format_crypto(qty)}")
                    print(f"  Cena: {format_money(price)}")
                    print(f"  Důvěra: {confidence:.2f}")
                    print(f"  Indikátory: SMA20={indicators.get('sma20'):.2f}, RSI={indicators.get('rsi'):.2f}")
                    
                    # Provedení obchodu na základě signálu
                    if confidence > 0.7:  # Pouze signály s vysokou důvěrou
                        # Kontrola, zda již nemáme otevřenou pozici
                        existing_position = next((p for p in positions if p.get("symbol") == symbol), None)
                        
                        # Pokud máme pozici a signál je stejný směr, přeskočíme
                        if existing_position:
                            position_side = "sell" if float(existing_position.get("qty", 0)) < 0 else "buy"
                            if position_side == side:
                                print(f"  ⚠️ Již máme otevřenou pozici {position_side.upper()} pro {symbol}, přeskakuji")
                                continue
                        
                        print(f"  ✅ Provádím obchod: {side.upper()} {format_crypto(qty)} {symbol} @ {format_money(price)}")
                        result = place_crypto_order(symbol, qty, side)
                        if result:
                            print(f"  ✅ Obchod zadán: ID objednávky {result.get('id')}")
                        else:
                            print(f"  ❌ Obchod se nezdařil")
                    else:
                        print(f"  ⚠️ Důvěra signálu je příliš nízká ({confidence:.2f}), neprovádím obchod")
                else:
                    print(f"  {symbol}: Žádný obchodní signál")
            
            # Čekání na další cyklus
            wait_time = 300  # 5 minut mezi cykly
            print(f"\n⏱️ Čekám {wait_time} sekund na další cyklus...")
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Obchodní systém ukončen uživatelem")
        
        # Získání aktuálních informací o účtu
        final_account = get_account()
        if final_account:
            final_value = float(final_account.get("portfolio_value", 0))
            initial_value = float(account.get("portfolio_value", 0))
            profit = final_value - initial_value
            profit_percent = (profit / initial_value) * 100 if initial_value > 0 else 0
            
            print(f"💰 Konečná hodnota portfolia: {format_money(final_value)}")
            print(f"📊 Zisk/Ztráta: {format_money(profit)} ({profit_percent:.2f}%)")
        
        sys.exit(0)

if __name__ == "__main__":
    run_crypto_trading_system()
