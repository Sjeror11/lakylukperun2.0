#!/usr/bin/env python3
"""
Perun Trading System - Multi-Crypto verze s TradingView API
Specializovaná verze pro obchodování s více kryptoměnami 24/7 využívající technické indikátory z TradingView.
Podporuje obchodování s více kryptoměnami současně.
"""

import os
import sys
import time
import json
import random
import requests
import traceback
from tradingview_ta import TA_Handler, Interval
from datetime import datetime, timedelta

# API klíče
ALPACA_API_KEY = "AKJYB42QYBVD1EKBDQJ8"
ALPACA_API_SECRET = "SczRiShhbzjejIYP8KKcg50XIhJMIyR895vi1hGI"
ALPACA_BASE_URL = "https://api.alpaca.markets/v2"

# Nastavení pro TradingView API
TV_EXCHANGE = "BINANCE"
TV_SCREENER = "crypto"
TV_INTERVAL = Interval.INTERVAL_1_HOUR

# Hlavičky pro Alpaca API požadavky
ALPACA_HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    "Content-Type": "application/json"
}

# Kryptoměny pro obchodování
CRYPTO_SYMBOLS = ["BTCUSD"]  # Zaměřeno pouze na BTC/USD

# Nastavení rizika
MAX_POSITION_SIZE = 25  # Maximální velikost pozice v USD
MAX_TOTAL_POSITIONS = 2  # Maximální počet současných pozic
RISK_LIMIT_PERCENT = 0.02  # Maximální riziko na obchod (2% portfolia)

# Nastavení obchodní strategie
STRATEGY_NAME = "TradingView Strategy"
STRATEGY_DESCRIPTION = "Strategie využívající technické indikátory z TradingView pro generování obchodních signálů."

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
def get_tradingview_analysis(symbol):
    """Získá analýzu z TradingView pro daný symbol."""
    try:
        # Převod symbolu na formát pro TradingView (např. BTCUSD -> BINANCE:BTCUSDT)
        if symbol == "BTCUSD":
            tv_symbol = "BTCUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "ETHUSD":
            tv_symbol = "ETHUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "SOLUSD":
            tv_symbol = "SOLUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "AVAXUSD":
            tv_symbol = "AVAXUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "LINKUSD":
            tv_symbol = "LINKUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "MATICUSD":
            tv_symbol = "MATICUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "DOTUSD":
            tv_symbol = "DOTUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "UNIUSD":
            tv_symbol = "UNIUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "AAVEUSD":
            tv_symbol = "AAVEUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "LTCUSD":
            tv_symbol = "LTCUSDT"
            exchange = TV_EXCHANGE
        else:
            tv_symbol = symbol
            exchange = TV_EXCHANGE
            
        print(f"�� Získávám analýzu z TradingView pro {exchange}:{tv_symbol}...")
        
        # Vytvoření handleru pro TradingView
        handler = TA_Handler(
            symbol=tv_symbol,
            exchange=exchange,
            screener=TV_SCREENER,
            interval=TV_INTERVAL,
            timeout=10
        )
        
        # Získání analýzy
        analysis = handler.get_analysis()
        
        # Výpis výsledků
        print(f"  Doporučení: {analysis.summary["RECOMMENDATION"]}")
        print(f"  RSI: {analysis.indicators["RSI"]}")
        print(f"  MACD: {analysis.indicators["MACD.macd"]}")
        print(f"  MACD Signal: {analysis.indicators["MACD.signal"]}")
        print(f"  Bollinger Bands (horní): {analysis.indicators["BB.upper"]}")
        print(f"  Bollinger Bands (dolní): {analysis.indicators["BB.lower"]}")
        
        return analysis
    except Exception as e:
        print(f"❌ Výjimka při získávání analýzy z TradingView: {e}")
        traceback.print_exc()
        return None

def get_rsi(symbol):
    """Získá RSI hodnotu z TradingView API."""
    analysis = get_tradingview_analysis(symbol)
    if analysis:
        return analysis.indicators["RSI"]
    else:
        # Pokud se nepodařilo získat analýzu, vrátíme simulovanou hodnotu
        print("Používám simulovaný RSI indikátor")
        base = random.random()  # 0.0 až 1.0
        if base < 0.1:  # 10% šance na přeprodanost (nízké RSI)
            return random.uniform(20, 30)
        elif base > 0.9:  # 10% šance na překoupenost (vysoké RSI)
            return random.uniform(70, 80)
        else:  # 80% šance na neutrální hodnotu
            return random.uniform(40, 60)
def get_price(symbol):
    """Získá aktuální cenu pro daný symbol."""
    # Simulovaná cena pro testování
    if symbol == "BTCUSD":
        return 87000.0
    elif symbol == "ETHUSD":
        return 3200.0
    elif symbol == "SOLUSD":
        return 150.0
    elif symbol == "AVAXUSD":
        return 35.0
    elif symbol == "LINKUSD":
        return 15.0
    elif symbol == "MATICUSD":
        return 0.8
    elif symbol == "DOTUSD":
        return 7.5
    elif symbol == "UNIUSD":
        return 10.0
    elif symbol == "AAVEUSD":
        return 90.0
    elif symbol == "LTCUSD":
        return 80.0
    else:
        return 100.0

def get_price_from_api(symbol):
    """Získá aktuální cenu pro daný symbol z Alpaca API."""
    try:
        url = f"{ALPACA_BASE_URL}/crypto/{symbol}/snapshot"
        response = requests.get(url, headers=ALPACA_HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            return float(data.get("latestTrade", {}).get("p", 0))
        else:
            print(f"❌ Chyba při získávání ceny: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání ceny: {e}")
        return None
        return analysis.indicators["RSI"]
    else:
        # Pokud se nepodařilo získat analýzu, vrátíme simulovanou hodnotu
        print("Používám simulovaný RSI indikátor")
        base = random.random()  # 0.0 až 1.0
        if base < 0.1:  # 10% šance na přeprodanost (nízké RSI)
            return random.uniform(20, 30)
        elif base > 0.9:  # 10% šance na překoupenost (vysoké RSI)
            return random.uniform(70, 80)
        else:  # 80% šance na neutrální hodnotu
            return random.uniform(40, 60)
    """Získá aktuální cenu pro daný symbol z Alpaca API."""
    try:
        # Použijeme Alpaca API místo TAAPI.IO pro získání ceny
        response = requests.get(f"{ALPACA_BASE_URL}/assets/{symbol}", headers=ALPACA_HEADERS)
        if response.status_code == 200:
            data = response.json()
            return float(data.get("price", 0))
        else:
            print(f"❌ Chyba při získávání ceny z Alpaca: {response.status_code}")
            print(f"Odpověď: {response.text}")
            
            # Záložní metoda - použijeme cenu z pozice, pokud existuje
            positions = get_positions()
            for position in positions:
                if position.get("symbol") == symbol:
                    return float(position.get("current_price", 0))
            
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání ceny: {e}")
        return None

# Funkce pro analýzu a generování obchodních signálů
# Funkce pro analýzu a generování obchodních signálů
def analyze_crypto(symbol):
    """Analyzuje kryptoměnu a generuje obchodní signál na základě TradingView indikátorů."""
    print(f"🔍 Analyzuji {symbol}...")

    # Získání ceny z Alpaca API
    current_price = get_price(symbol)

    # Získání analýzy z TradingView
    analysis = get_tradingview_analysis(symbol)
    
    # Kontrola, zda se podařilo získat analýzu
    if not analysis or not current_price:
        print(f"❌ Nepodařilo se získat všechny indikátory pro {symbol}")
        return None

    # Inicializace signálu a důvěry
    signal = None
    confidence = 0.5
    reasons = []

    # Analýza doporučení
    recommendation = analysis.summary["RECOMMENDATION"]
    if "BUY" in recommendation or "STRONG_BUY" in recommendation:
        signal = "buy"
        confidence += 0.3
        reasons.append(f"TradingView doporučuje {recommendation}")
    elif "SELL" in recommendation or "STRONG_SELL" in recommendation:
        signal = "sell"
        confidence += 0.3
        reasons.append(f"TradingView doporučuje {recommendation}")

    # Analýza RSI
    rsi = analysis.indicators["RSI"]
    if rsi < 30:  # Překoupeno - signál k nákupu
        if signal != "buy":
            confidence += 0.1
        signal = "buy"
        reasons.append(f"RSI je nízké ({rsi:.2f} < 30) - překoupeno, signál k nákupu")
    elif rsi > 70:  # Přeprodáno - signál k prodeji
        if signal != "sell":
            confidence += 0.1
        signal = "sell"
        reasons.append(f"RSI je vysoké ({rsi:.2f} > 70) - přeprodáno, signál k prodeji")

    # Analýza MACD
    macd = analysis.indicators["MACD.macd"]
    macd_signal = analysis.indicators["MACD.signal"]
    if macd > macd_signal:  # MACD nad signální linií - signál k nákupu
        if signal != "buy":
            confidence += 0.1
        signal = "buy"
        reasons.append(f"MACD ({macd:.2f}) je nad signální linií ({macd_signal:.2f}) - signál k nákupu")
    elif macd < macd_signal:  # MACD pod signální linií - signál k prodeji
        if signal != "sell":
            confidence += 0.1
        signal = "sell"
        reasons.append(f"MACD ({macd:.2f}) je pod signální linií ({macd_signal:.2f}) - signál k prodeji")

    # Analýza Bollinger Bands
    bb_upper = analysis.indicators["BB.upper"]
    bb_lower = analysis.indicators["BB.lower"]
    if current_price <= bb_lower:  # Cena pod dolní hranicí - signál k nákupu
        if signal != "buy":
            confidence += 0.1
        signal = "buy"
        reasons.append(f"Cena ({current_price:.2f}) je pod dolní hranicí Bollinger Bands ({bb_lower:.2f}) - signál k nákupu")
    elif current_price >= bb_upper:  # Cena nad horní hranicí - signál k prodeji
        if signal != "sell":
            confidence += 0.1
        signal = "sell"
        reasons.append(f"Cena ({current_price:.2f}) je nad horní hranicí Bollinger Bands ({bb_upper:.2f}) - signál k prodeji")

    # Pokud nemáme signál, vrátíme None
    if signal is None:
        print(f"  {symbol}: Žádný obchodní signál")
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
            "recommendation": recommendation,
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_signal,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower
        }
    }

def format_money(amount):
    """Formátuje peněžní částku."""
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
    print("PERUN TRADING SYSTEM - MULTI-CRYPTO TRADINGVIEW VERZE")
    print("=" * 50)
    print("Spouštím obchodní systém pro více kryptoměn 24/7 s využitím TradingView.")
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
                    print(f"    - Doporučení: {indicators['recommendation']}")
                    print(f"    - RSI: {indicators['rsi']:.2f}")
                    print(f"    - MACD: {indicators['macd']:.2f}")
                    print(f"    - MACD Signal: {indicators['macd_signal']:.2f}")
                    print(f"    - BB Upper: {indicators['bb_upper']:.2f}")
                    print(f"    - BB Lower: {indicators['bb_lower']:.2f}")
                    
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
            wait_time = 900  # 15 minut mezi cykly (prodlouženo pro úsporu požadavků)
            print(f"\n⏱️ Čekám {wait_time} sekund na další cyklus...")
            log_to_file(f"Čekání {wait_time} sekund na další cyklus", log_file)
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("\n\n�� Obchodní systém ukončen uživatelem")
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
