#!/usr/bin/env python3
"""
Perun Trading System - Vylepšená verze s TAAPI.IO
Specializovaná verze pro obchodování s kryptoměnami 24/7 využívající technické indikátory z TAAPI.IO.
"""

import os
import sys
import time
import json
import random
import requests
from datetime import datetime, timedelta

# API klíče
ALPACA_API_KEY = "AKJYB42QYBVD1EKBDQJ8"
ALPACA_API_SECRET = "SczRiShhbzjejIYP8KKcg50XIhJMIyR895vi1hGI"
ALPACA_BASE_URL = "https://api.alpaca.markets/v2"

# TAAPI.IO API klíč
TAAPI_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHVlIjoiNjgwMmRhOGU4MDZmZjE2NTFlYzE0ZTc2IiwiaWF0IjoxNzQ1MDE3ODYxLCJleHAiOjMzMjQ5NDgxODYxfQ.ChH7JUXFCpsjRhdMoYFV1TYSq3u7sX_O53iQ-Z80a30"
TAAPI_BASE_URL = "https://api.taapi.io"

# Hlavičky pro Alpaca API požadavky
ALPACA_HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    "Content-Type": "application/json"
}

# Kryptoměny pro obchodování
CRYPTO_SYMBOLS = ["BTCUSD"]  # Zaměřeno pouze na BTC/USD

# Nastavení rizika
MAX_POSITION_SIZE = 50  # Maximální velikost pozice v USD
MAX_TOTAL_POSITIONS = 1  # Maximální počet současných pozic
RISK_LIMIT_PERCENT = 0.02  # Maximální riziko na obchod (2% portfolia)

# Nastavení obchodní strategie
STRATEGY_NAME = "Multi-Indicator Strategy"
STRATEGY_DESCRIPTION = "Strategie využívající kombinaci RSI, MACD, Bollinger Bands a EMA pro generování obchodních signálů."

# Funkce pro práci s Alpaca API
def get_account():
    """Získá informace o účtu."""
    try:
        response = requests.get(f"{ALPACA_BASE_URL}/account", headers=ALPACA_HEADERS)
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
        response = requests.get(f"{ALPACA_BASE_URL}/positions", headers=ALPACA_HEADERS)
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
        response = requests.get(f"{ALPACA_BASE_URL}/orders", headers=ALPACA_HEADERS)
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
        response = requests.post(f"{ALPACA_BASE_URL}/orders", headers=ALPACA_HEADERS, json=data)
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
        response = requests.delete(f"{ALPACA_BASE_URL}/orders/{order_id}", headers=ALPACA_HEADERS)
        if response.status_code == 204:
            return True
        else:
            print(f"❌ Chyba při rušení objednávky: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Výjimka při rušení objednávky: {e}")
        return False

# Funkce pro práci s TAAPI.IO API
def get_rsi(symbol, interval="1h"):
    """Získá hodnotu RSI (Relative Strength Index) pro daný symbol a interval."""
    try:
        params = {
            "secret": TAAPI_API_KEY,
            "exchange": "binance",
            "symbol": symbol,
            "interval": interval
        }
        response = requests.get(f"{TAAPI_BASE_URL}/rsi", params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("value")
        else:
            print(f"❌ Chyba při získávání RSI: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání RSI: {e}")
        return None

def get_macd(symbol, interval="1h"):
    """Získá hodnoty MACD (Moving Average Convergence Divergence) pro daný symbol a interval."""
    try:
        params = {
            "secret": TAAPI_API_KEY,
            "exchange": "binance",
            "symbol": symbol,
            "interval": interval
        }
        response = requests.get(f"{TAAPI_BASE_URL}/macd", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Chyba při získávání MACD: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání MACD: {e}")
        return None

def get_bbands(symbol, interval="1h"):
    """Získá hodnoty Bollinger Bands pro daný symbol a interval."""
    try:
        params = {
            "secret": TAAPI_API_KEY,
            "exchange": "binance",
            "symbol": symbol,
            "interval": interval
        }
        response = requests.get(f"{TAAPI_BASE_URL}/bbands", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Chyba při získávání Bollinger Bands: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání Bollinger Bands: {e}")
        return None

def get_ema(symbol, interval="1h", period=20):
    """Získá hodnotu EMA (Exponential Moving Average) pro daný symbol a interval."""
    try:
        params = {
            "secret": TAAPI_API_KEY,
            "exchange": "binance",
            "symbol": symbol,
            "interval": interval,
            "period": period
        }
        response = requests.get(f"{TAAPI_BASE_URL}/ema", params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("value")
        else:
            print(f"❌ Chyba při získávání EMA: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání EMA: {e}")
        return None

def get_price(symbol):
    """Získá aktuální cenu pro daný symbol z Binance přes TAAPI.IO."""
    try:
        params = {
            "secret": TAAPI_API_KEY,
            "exchange": "binance",
            "symbol": symbol,
            "interval": "1m"  # Nejkratší interval pro aktuální cenu
        }
        response = requests.get(f"{TAAPI_BASE_URL}/price", params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("value")
        else:
            print(f"❌ Chyba při získávání ceny: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání ceny: {e}")
        return None

# Funkce pro analýzu a generování obchodních signálů
def analyze_crypto(symbol):
    """Analyzuje kryptoměnu a generuje obchodní signál na základě technických indikátorů."""
    print(f"🔍 Analyzuji {symbol}...")
    
    # Převod symbolu na formát pro TAAPI.IO (např. BTCUSD -> BTC/USDT)
    taapi_symbol = f"{symbol[:3]}/USDT"
    
    # Získání hodnot technických indikátorů
    rsi = get_rsi(taapi_symbol)
    macd = get_macd(taapi_symbol)
    bbands = get_bbands(taapi_symbol)
    ema20 = get_ema(taapi_symbol, period=20)
    ema50 = get_ema(taapi_symbol, period=50)
    current_price = get_price(taapi_symbol)
    
    # Kontrola, zda se podařilo získat všechny indikátory
    if not all([rsi, macd, bbands, ema20, ema50, current_price]):
        print(f"❌ Nepodařilo se získat všechny indikátory pro {symbol}")
        return None
    
    # Inicializace signálu a důvěry
    signal = None
    confidence = 0.5
    reasons = []
    
    # Analýza RSI
    if rsi < 30:  # Překoupeno
        signal = "buy"
        confidence += 0.1
        reasons.append(f"RSI je nízké ({rsi:.2f} < 30) - překoupeno")
    elif rsi > 70:  # Přeprodáno
        signal = "sell"
        confidence += 0.1
        reasons.append(f"RSI je vysoké ({rsi:.2f} > 70) - přeprodáno")
    
    # Analýza MACD
    if macd["valueMACD"] > macd["valueMACDSignal"]:  # MACD nad signální linií - býčí signál
        if signal == "buy":
            confidence += 0.1
            reasons.append(f"MACD ({macd['valueMACD']:.2f}) je nad signální linií ({macd['valueMACDSignal']:.2f}) - býčí signál")
        elif signal is None:
            signal = "buy"
            confidence += 0.1
            reasons.append(f"MACD ({macd['valueMACD']:.2f}) je nad signální linií ({macd['valueMACDSignal']:.2f}) - býčí signál")
    elif macd["valueMACD"] < macd["valueMACDSignal"]:  # MACD pod signální linií - medvědí signál
        if signal == "sell":
            confidence += 0.1
            reasons.append(f"MACD ({macd['valueMACD']:.2f}) je pod signální linií ({macd['valueMACDSignal']:.2f}) - medvědí signál")
        elif signal is None:
            signal = "sell"
            confidence += 0.1
            reasons.append(f"MACD ({macd['valueMACD']:.2f}) je pod signální linií ({macd['valueMACDSignal']:.2f}) - medvědí signál")
    
    # Analýza Bollinger Bands
    if current_price < bbands["valueLowerBand"]:  # Cena pod dolní hranicí - potenciální nákup
        if signal == "buy":
            confidence += 0.15
            reasons.append(f"Cena ({current_price:.2f}) je pod dolní hranicí BB ({bbands['valueLowerBand']:.2f}) - potenciální nákup")
        elif signal is None:
            signal = "buy"
            confidence += 0.15
            reasons.append(f"Cena ({current_price:.2f}) je pod dolní hranicí BB ({bbands['valueLowerBand']:.2f}) - potenciální nákup")
    elif current_price > bbands["valueUpperBand"]:  # Cena nad horní hranicí - potenciální prodej
        if signal == "sell":
            confidence += 0.15
            reasons.append(f"Cena ({current_price:.2f}) je nad horní hranicí BB ({bbands['valueUpperBand']:.2f}) - potenciální prodej")
        elif signal is None:
            signal = "sell"
            confidence += 0.15
            reasons.append(f"Cena ({current_price:.2f}) je nad horní hranicí BB ({bbands['valueUpperBand']:.2f}) - potenciální prodej")
    
    # Analýza EMA křížení
    if ema20 > ema50:  # EMA20 nad EMA50 - býčí trend
        if signal == "buy":
            confidence += 0.1
            reasons.append(f"EMA20 ({ema20:.2f}) je nad EMA50 ({ema50:.2f}) - býčí trend")
        elif signal is None:
            signal = "buy"
            confidence += 0.05
            reasons.append(f"EMA20 ({ema20:.2f}) je nad EMA50 ({ema50:.2f}) - býčí trend")
    elif ema20 < ema50:  # EMA20 pod EMA50 - medvědí trend
        if signal == "sell":
            confidence += 0.1
            reasons.append(f"EMA20 ({ema20:.2f}) je pod EMA50 ({ema50:.2f}) - medvědí trend")
        elif signal is None:
            signal = "sell"
            confidence += 0.05
            reasons.append(f"EMA20 ({ema20:.2f}) je pod EMA50 ({ema50:.2f}) - medvědí trend")
    
    # Pokud nemáme signál, vrátíme None
    if signal is None:
        print(f"❌ Žádný obchodní signál pro {symbol}")
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
        "reasons": reasons,
        "indicators": {
            "rsi": rsi,
            "macd": macd,
            "bbands": bbands,
            "ema20": ema20,
            "ema50": ema50
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

def log_to_file(message, log_file="trading_log.txt"):
    """Zapíše zprávu do logovacího souboru."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def run_crypto_trading_system():
    """Spouští obchodní systém pro kryptoměny."""
    print("=" * 50)
    print("PERUN TRADING SYSTEM - TAAPI.IO VERZE")
    print("=" * 50)
    print("Spouštím obchodní systém pro kryptoměny 24/7 s využitím TAAPI.IO.")
    print(f"Obchodované symboly: {', '.join(CRYPTO_SYMBOLS)}")
    print(f"Strategie: {STRATEGY_NAME}")
    print(f"Popis: {STRATEGY_DESCRIPTION}")
    print("=" * 50)
    
    # Vytvoření logovacího souboru
    log_file = "trading_log.txt"
    log_to_file("=== SPUŠTĚNÍ OBCHODNÍHO SYSTÉMU ===", log_file)
    
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
    
    log_to_file(f"Počáteční hodnota portfolia: {format_money(float(account.get('portfolio_value', 0)))}", log_file)
    
    # Hlavní smyčka
    try:
        cycle = 0
        while True:
            cycle += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'=' * 20} CYKLUS {cycle} ({now}) {'=' * 20}")
            log_to_file(f"CYKLUS {cycle} ({now})", log_file)
            
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
                
                position_info = f"{symbol}: {format_crypto(qty)} @ {format_money(avg_entry_price)} | Aktuální cena: {format_money(current_price)} | P/L: {format_money(unrealized_pl)} ({unrealized_plpc:.2f}%)"
                print(f"  {position_info}")
                log_to_file(f"Pozice: {position_info}", log_file)
            
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
                
                order_info = f"{symbol}: {side.upper()} {format_crypto(qty)} ({order_type}) | Status: {status}"
                print(f"  {order_info}")
                log_to_file(f"Objednávka: {order_info}", log_file)
            
            # Analýza a generování obchodních signálů
            for symbol in CRYPTO_SYMBOLS:
                signal = analyze_crypto(symbol)
                if signal:
                    side = signal.get("side")
                    qty = signal.get("qty")
                    price = signal.get("price")
                    confidence = signal.get("confidence")
                    reasons = signal.get("reasons", [])
                    indicators = signal.get("indicators", {})
                    
                    print(f"\n🔔 Obchodní signál pro {symbol}:")
                    print(f"  Akce: {side.upper()}")
                    print(f"  Množství: {format_crypto(qty)}")
                    print(f"  Cena: {format_money(price)}")
                    print(f"  Důvěra: {confidence:.2f}")
                    print(f"  Důvody:")
                    for reason in reasons:
                        print(f"    - {reason}")
                    
                    print(f"  Indikátory:")
                    print(f"    - RSI: {indicators['rsi']:.2f}")
                    print(f"    - MACD: {indicators['macd']['valueMACD']:.2f} (Signal: {indicators['macd']['valueMACDSignal']:.2f}, Hist: {indicators['macd']['valueMACDHist']:.2f})")
                    print(f"    - Bollinger Bands: Upper: {indicators['bbands']['valueUpperBand']:.2f}, Middle: {indicators['bbands']['valueMiddleBand']:.2f}, Lower: {indicators['bbands']['valueLowerBand']:.2f}")
                    print(f"    - EMA20: {indicators['ema20']:.2f}")
                    print(f"    - EMA50: {indicators['ema50']:.2f}")
                    
                    signal_info = f"{symbol}: {side.upper()} {format_crypto(qty)} @ {format_money(price)} | Důvěra: {confidence:.2f}"
                    log_to_file(f"Signál: {signal_info}", log_file)
                    for reason in reasons:
                        log_to_file(f"  - {reason}", log_file)
                    
                    # Provedení obchodu na základě signálu
                    if confidence > 0.7:  # Pouze signály s vysokou důvěrou
                        # Kontrola, zda již nemáme otevřenou pozici
                        existing_position = next((p for p in positions if p.get("symbol") == symbol), None)
                        
                        # Pokud máme pozici a signál je stejný směr, přeskočíme
                        if existing_position:
                            position_side = "sell" if float(existing_position.get("qty", 0)) < 0 else "buy"
                            if position_side == side:
                                skip_message = f"Již máme otevřenou pozici {position_side.upper()} pro {symbol}, přeskakuji"
                                print(f"  ⚠️ {skip_message}")
                                log_to_file(f"Přeskočeno: {skip_message}", log_file)
                                continue
                        
                        trade_message = f"Provádím obchod: {side.upper()} {format_crypto(qty)} {symbol} @ {format_money(price)}"
                        print(f"  ✅ {trade_message}")
                        log_to_file(f"Obchod: {trade_message}", log_file)
                        
                        result = place_crypto_order(symbol, qty, side)
                        if result:
                            success_message = f"Obchod zadán: ID objednávky {result.get('id')}"
                            print(f"  ✅ {success_message}")
                            log_to_file(f"Úspěch: {success_message}", log_file)
                        else:
                            error_message = f"Obchod se nezdařil"
                            print(f"  ❌ {error_message}")
                            log_to_file(f"Chyba: {error_message}", log_file)
                    else:
                        low_confidence_message = f"Důvěra signálu je příliš nízká ({confidence:.2f}), neprovádím obchod"
                        print(f"  ⚠️ {low_confidence_message}")
                        log_to_file(f"Nízká důvěra: {low_confidence_message}", log_file)
                else:
                    no_signal_message = f"{symbol}: Žádný obchodní signál"
                    print(f"  {no_signal_message}")
                    log_to_file(no_signal_message, log_file)
            
            # Čekání na další cyklus
            wait_time = 300  # 5 minut mezi cykly
            print(f"\n⏱️ Čekám {wait_time} sekund na další cyklus...")
            log_to_file(f"Čekání {wait_time} sekund na další cyklus", log_file)
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Obchodní systém ukončen uživatelem")
        log_to_file("=== UKONČENÍ OBCHODNÍHO SYSTÉMU UŽIVATELEM ===", log_file)
        
        # Získání aktuálních informací o účtu
        final_account = get_account()
        if final_account:
            final_value = float(final_account.get("portfolio_value", 0))
            initial_value = float(account.get("portfolio_value", 0))
            profit = final_value - initial_value
            profit_percent = (profit / initial_value) * 100 if initial_value > 0 else 0
            
            print(f"💰 Konečná hodnota portfolia: {format_money(final_value)}")
            print(f"📊 Zisk/Ztráta: {format_money(profit)} ({profit_percent:.2f}%)")
            
            log_to_file(f"Konečná hodnota portfolia: {format_money(final_value)}", log_file)
            log_to_file(f"Zisk/Ztráta: {format_money(profit)} ({profit_percent:.2f}%)", log_file)
        
        sys.exit(0)

if __name__ == "__main__":
    run_crypto_trading_system()
